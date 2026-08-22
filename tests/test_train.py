from pathlib import Path

import joblib

from train import parse_args, train


def test_train_creates_valid_artifact_and_metrics(tmp_path: Path) -> None:
    output_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "model-metrics.json"

    metrics = train(output=output_path, metrics_output=metrics_path)

    assert output_path.exists()
    assert metrics_path.exists()
    assert metrics["accuracy"] >= 0.90
    assert "precision_macro" in metrics
    assert "recall_macro" in metrics
    assert "f1_macro" in metrics

    loaded = joblib.load(output_path)
    assert isinstance(loaded, dict)
    assert set(loaded.keys()) == {
        "model",
        "classes",
        "feature_names",
        "model_version",
    }
    assert len(loaded["classes"]) == 3
    assert len(loaded["feature_names"]) == 4


def test_parse_args_defaults_and_custom() -> None:
    args_default = parse_args([])
    assert args_default.random_state == 42
    assert args_default.test_size == 0.20
    assert args_default.n_estimators == 100
    assert args_default.max_depth == 5

    args_custom = parse_args(
        [
            "--output",
            "custom.joblib",
            "--metrics",
            "custom.json",
            "--random-state",
            "123",
            "--test-size",
            "0.3",
            "--n-estimators",
            "50",
            "--max-depth",
            "3",
        ]
    )
    assert str(args_custom.output) == "custom.joblib"
    assert str(args_custom.metrics) == "custom.json"
    assert args_custom.random_state == 123
    assert args_custom.test_size == 0.3
    assert args_custom.n_estimators == 50
    assert args_custom.max_depth == 3
