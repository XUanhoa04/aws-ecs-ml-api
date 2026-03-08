from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Iris XGBoost ML API - AWS ECS")

# Load model
model = joblib.load("model.joblib")
classes = ["setosa", "versicolor", "virginica"]

class IrisFeatures(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

@app.get("/")
def home():
    return {"message": "ML API đang chạy trên AWS ECS! 🎉"}

@app.post("/predict")
def predict(features: IrisFeatures):
    data = np.array([[features.sepal_length, features.sepal_width,
                      features.petal_length, features.petal_width]])
    pred = model.predict(data)[0]
    return {"prediction": classes[pred], "probability": float(model.predict_proba(data).max())}