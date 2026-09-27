from pathlib import Path

from scripts.evaluate_ranking import evaluate

DATASET = Path("evaluation/ranking_v1.json")


def test_versioned_ranking_benchmark_meets_beta_acceptance_criteria() -> None:
    report = evaluate(DATASET)

    assert report["version"] == "1.1.0"
    assert report["case_count"] >= 30
    assert report["passed"] is True
    assert report["metrics"]["strong_precision_at_78"] >= 0.90
    assert report["metrics"]["negative_false_positive_rate"] <= 0.05
    assert report["metrics"]["strong_false_negative_rate"] <= 0.15
    assert report["metrics"]["pairwise_ordering_accuracy"] >= 0.90


def test_benchmark_has_strong_adjacent_and_deceptive_negative_coverage() -> None:
    report = evaluate(DATASET)
    results = {item["id"]: item for item in report["results"]}

    assert report["score_distribution"]["strong"]["count"] >= 12
    assert report["score_distribution"]["adjacent"]["count"] >= 8
    assert report["score_distribution"]["negative"]["count"] >= 12
    assert results["strong-regional-qsr"]["score"] > results["adj-store"]["score"]
    assert results["strong-area-franchise"]["score"] > results["adj-rgm"]["score"]
    assert (
        results["strong-remote-us-location-outside"]["location_fit"]
        == "outside_preference"
    )
    for case_id in (
        "neg-beauty",
        "neg-sales",
        "neg-field",
        "neg-estimator",
        "neg-engineer",
        "neg-finance",
        "neg-product",
    ):
        assert results[case_id]["recommendation"] == "reject"
        assert results[case_id]["score"] <= 34
