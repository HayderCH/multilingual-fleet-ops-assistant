from fleet_assistant.benchmark import evaluate


def test_public_benchmark_is_reproducible() -> None:
    result = evaluate()
    assert result["total"] == 32
    assert result["accuracy"] >= 0.90
