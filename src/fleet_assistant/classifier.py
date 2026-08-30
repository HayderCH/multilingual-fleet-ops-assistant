from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import Any

import joblib

from .models import ClassifierCandidate


@lru_cache(maxsize=1)
def load_classifier() -> Any:
    path = files("fleet_assistant").joinpath("models/public_intent_classifier.joblib")
    if not path.is_file():
        raise RuntimeError("Classifier artifact missing. Run fleet-train-classifier.")
    return joblib.load(path)


def classify(text: str, top_k: int = 3) -> list[ClassifierCandidate]:
    model = load_classifier()
    probabilities = model.predict_proba([text])[0]
    labels = model.classes_
    ranked = sorted(zip(labels, probabilities, strict=True), key=lambda row: row[1], reverse=True)
    return [
        ClassifierCandidate(intent=str(label), probability=round(float(probability), 4))
        for label, probability in ranked[:top_k]
    ]
