from __future__ import annotations

import json
from collections import Counter
from importlib.resources import files

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .training_data import generate_training_rows


def train() -> tuple[Pipeline, dict[str, object]]:
    rows = generate_training_rows()
    model = Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "characters",
                            TfidfVectorizer(
                                analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True
                            ),
                        ),
                        (
                            "words",
                            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42),
            ),
        ]
    )
    model.fit([row["query"] for row in rows], [row["intent"] for row in rows])

    benchmark_path = files("fleet_assistant").joinpath("data/public_benchmark.json")
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    predictions = model.predict([case["query"] for case in benchmark])
    failures = [
        {
            "id": case["id"],
            "expected": case["expected_intent"],
            "actual": str(prediction),
        }
        for case, prediction in zip(benchmark, predictions, strict=True)
        if prediction != case["expected_intent"]
    ]
    language_counts = Counter(case["language"] for case in benchmark)
    language_correct = Counter(
        case["language"]
        for case, prediction in zip(benchmark, predictions, strict=True)
        if prediction == case["expected_intent"]
    )
    metrics: dict[str, object] = {
        "model": "public-char-word-ngram-logistic-v1",
        "training_provenance": "programmatically generated synthetic templates",
        "training_rows": len(rows),
        "benchmark_provenance": "hand-curated synthetic portfolio cases",
        "benchmark_rows": len(benchmark),
        "accuracy": round((len(benchmark) - len(failures)) / len(benchmark), 4),
        "accuracy_by_language": {
            language: round(language_correct[language] / count, 4)
            for language, count in sorted(language_counts.items())
        },
        "failures": failures,
    }
    return model, metrics


def main() -> None:
    model, metrics = train()
    model_path = files("fleet_assistant").joinpath("models/public_intent_classifier.joblib")
    metrics_path = files("fleet_assistant").joinpath("models/public_intent_classifier_metrics.json")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
