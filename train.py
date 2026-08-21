"""Train and evaluate the deterministic Iris model artifact."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
MINIMUM_ACCURACY = 0.90


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("model.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("model-metrics.json"))
    return parser.parse_args()


def train(output: Path, metrics_output: Path) -> dict[str, float | str]:
    dataset = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data,
        dataset.target,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=dataset.target,
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(x_train, y_train)
    accuracy = float(accuracy_score(y_test, model.predict(x_test)))

    if accuracy < MINIMUM_ACCURACY:
        raise RuntimeError(
            f"Model accuracy {accuracy:.3f} is below {MINIMUM_ACCURACY:.3f}"
        )

    model_version = f"iris-rf-{RANDOM_STATE}"
    artifact = {
        "model": model,
        "classes": [str(name) for name in dataset.target_names],
        "feature_names": [str(name) for name in dataset.feature_names],
        "model_version": model_version,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output, compress=3)

    metrics: dict[str, float | str] = {
        "accuracy": round(accuracy, 6),
        "minimum_accuracy": MINIMUM_ACCURACY,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
    }
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    arguments = parse_args()
    result = train(arguments.output, arguments.metrics)
    print(json.dumps(result, indent=2))
