"""Train and evaluate the deterministic Iris model artifact."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

DEFAULT_RANDOM_STATE = 42
DEFAULT_TEST_SIZE = 0.20
DEFAULT_N_ESTIMATORS = 100
DEFAULT_MAX_DEPTH = 5
MINIMUM_ACCURACY = 0.90


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("model.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("model-metrics.json"))
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Proportion of the dataset to include in the test split (default: 0.20)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Seed used by the random number generator (default: 42)",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=DEFAULT_N_ESTIMATORS,
        help="The number of trees in the forest (default: 100)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help="The maximum depth of the tree (default: 5)",
    )
    return parser.parse_args(args)


def train(
    output: Path,
    metrics_output: Path,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> dict[str, float | str]:
    dataset = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        dataset.data,
        dataset.target,
        test_size=test_size,
        random_state=random_state,
        stratify=dataset.target,
    )

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=1,
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(
        precision_score(y_test, y_pred, average="macro", zero_division=0)
    )
    recall = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    if accuracy < MINIMUM_ACCURACY:
        raise RuntimeError(
            f"Model accuracy {accuracy:.3f} is below {MINIMUM_ACCURACY:.3f}"
        )

    model_version = f"iris-rf-{random_state}"
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
        "precision_macro": round(precision, 6),
        "recall_macro": round(recall, 6),
        "f1_macro": round(f1, 6),
        "minimum_accuracy": MINIMUM_ACCURACY,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
    }
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    arguments = parse_args()
    result = train(
        output=arguments.output,
        metrics_output=arguments.metrics,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        n_estimators=arguments.n_estimators,
        max_depth=arguments.max_depth,
    )
    print(json.dumps(result, indent=2))

