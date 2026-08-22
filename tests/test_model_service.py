from pathlib import Path

import joblib
import pytest

from app.main import ModelService


def test_model_service_starts_unavailable(tmp_path: Path) -> None:
    service = ModelService(tmp_path / "missing.joblib")

    assert service.ready is False
    assert service.model_version == "unavailable"
    with pytest.raises(RuntimeError, match="not loaded"):
        service.predict([5.1, 3.5, 1.4, 0.2])
    with pytest.raises(RuntimeError, match="not loaded"):
        service.predict_batch([[5.1, 3.5, 1.4, 0.2]])



def test_model_service_rejects_legacy_artifact(tmp_path: Path) -> None:
    model_path = tmp_path / "legacy.joblib"
    joblib.dump({"model": "missing metadata"}, model_path)

    with pytest.raises(ValueError, match="unsupported format"):
        ModelService(model_path).load()
