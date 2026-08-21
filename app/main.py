"""FastAPI application serving the Iris classification model."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("iris-api")

APP_VERSION = os.getenv("APP_VERSION", "local")
MODEL_PATH = Path(os.getenv("MODEL_PATH", "model.joblib"))


class ModelService:
    """Loads the model once and exposes a small, testable prediction API."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.bundle: dict[str, Any] | None = None

    def load(self) -> None:
        loaded = joblib.load(self.model_path)
        required_keys = {"model", "classes", "feature_names", "model_version"}
        if not isinstance(loaded, dict) or not required_keys.issubset(loaded):
            raise ValueError("Model artifact has an unsupported format")
        self.bundle = loaded
        logger.info(
            "Model loaded path=%s version=%s",
            self.model_path,
            loaded["model_version"],
        )

    @property
    def ready(self) -> bool:
        return self.bundle is not None

    @property
    def model_version(self) -> str:
        return str(self.bundle["model_version"]) if self.bundle else "unavailable"

    def predict(self, values: list[float]) -> tuple[int, str, dict[str, float]]:
        if self.bundle is None:
            raise RuntimeError("Model is not loaded")

        model = self.bundle["model"]
        classes: list[str] = self.bundle["classes"]
        matrix = np.asarray([values], dtype=np.float64)
        probabilities_raw = model.predict_proba(matrix)[0]
        class_id = int(np.argmax(probabilities_raw))
        probabilities = {
            class_name: round(float(probability), 6)
            for class_name, probability in zip(classes, probabilities_raw, strict=True)
        }
        return class_id, classes[class_id], probabilities


model_service = ModelService(MODEL_PATH)


@asynccontextmanager
async def lifespan(_: FastAPI):
    model_service.load()
    yield


app = FastAPI(
    title="Iris ML Inference API",
    description="A small production-shaped API used in the AWS ECS CI/CD lab.",
    version=APP_VERSION,
    lifespan=lifespan,
)


class IrisFeatures(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            }
        }
    )

    sepal_length: float = Field(gt=0, le=20)
    sepal_width: float = Field(gt=0, le=20)
    petal_length: float = Field(gt=0, le=20)
    petal_width: float = Field(gt=0, le=20)

    def as_list(self) -> list[float]:
        return [
            self.sepal_length,
            self.sepal_width,
            self.petal_length,
            self.petal_width,
        ]


class PredictionResponse(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    probabilities: dict[str, float]
    model_version: str


@app.middleware("http")
async def request_context(request: Request, call_next) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers["x-request-id"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/", tags=["meta"])
def home() -> dict[str, str]:
    return {
        "service": "iris-ml-api",
        "version": APP_VERSION,
        "docs": "/docs",
        "message": "ML API is running on AWS ECS",
    }


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    if not model_service.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )
    return {"status": "ready", "model_version": model_service.model_version}


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
def predict(features: IrisFeatures) -> PredictionResponse:
    try:
        class_id, class_name, probabilities = model_service.predict(features.as_list())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return PredictionResponse(
        class_id=class_id,
        class_name=class_name,
        confidence=max(probabilities.values()),
        probabilities=probabilities,
        model_version=model_service.model_version,
    )
