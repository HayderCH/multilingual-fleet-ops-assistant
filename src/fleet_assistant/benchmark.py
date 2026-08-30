from __future__ import annotations

import json
from collections import Counter
from importlib.resources import files

from .router import route


def evaluate() -> dict[str, object]:
    path = files("fleet_assistant").joinpath("data/public_benchmark.json")
    cases = json.loads(path.read_text(encoding="utf-8"))
    failures: list[dict[str, object]] = []
    by_language: Counter[str] = Counter()
    correct_by_language: Counter[str] = Counter()

    for case in cases:
        decision = route(case["query"])
        by_language[case["language"]] += 1
        correct = decision.intent == case["expected_intent"] and decision.vehicle_id == case.get(
            "vehicle_id"
        )
        if correct:
            correct_by_language[case["language"]] += 1
        else:
            failures.append(
                {
                    "id": case["id"],
                    "expected": case["expected_intent"],
                    "actual": decision.intent,
                    "expected_vehicle": case.get("vehicle_id"),
                    "actual_vehicle": decision.vehicle_id,
                }
            )

    total = len(cases)
    correct = total - len(failures)
    return {
        "dataset": "public_benchmark_v1",
        "provenance": "hand-curated synthetic portfolio cases",
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4),
        "accuracy_by_language": {
            language: round(correct_by_language[language] / count, 4)
            for language, count in sorted(by_language.items())
        },
        "failures": failures,
    }


def main() -> None:
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
