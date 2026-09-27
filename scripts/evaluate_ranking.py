"""Evaluate Falcon ranking against the versioned senior-operations benchmark."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from app.services.match_scoring import JobInput, score_candidate_against_job

DEFAULT_DATASET = Path("evaluation/ranking_v1.json")
LABEL_ORDER = {"negative": 0, "adjacent": 1, "strong": 2}


def benchmark_candidate() -> dict:
    return {
        "years_experience": {
            "value": "22",
            "source_text": "22+ years in QSR, restaurant and delivery operations.",
        },
        "seniority": {
            "value": "Director",
            "source_text": "Regional Operations Director",
        },
        "role_family": {
            "value": "Regional Operations Director",
            "source_text": "Regional Operations Director",
        },
        "skills": [
            {"value": "multi-site operations", "source_text": "Led 156 outlets."},
            {"value": "P&L management", "source_text": "Full P&L ownership."},
            {
                "value": "delivery operations",
                "source_text": "Directed delivery operations.",
            },
            {"value": "KPI management", "source_text": "Owned regional KPIs."},
            {
                "value": "team leadership",
                "source_text": "Coached regional and site managers.",
            },
            {
                "value": "inventory control",
                "source_text": "Owned inventory and suppliers.",
            },
            {"value": "food safety", "source_text": "Led food safety compliance."},
            {
                "value": "stakeholder management",
                "source_text": "Managed franchise partners.",
            },
            {
                "value": "cost control",
                "source_text": "Improved labour and operating margin.",
            },
            {
                "value": "operational performance",
                "source_text": "Led operational excellence and service improvement.",
            },
        ],
        "industries": [
            {"value": "QSR", "source_text": "QSR and restaurant operations."},
            {"value": "franchise", "source_text": "Multi-brand franchise operations."},
            {"value": "food delivery", "source_text": "Food delivery marketplace."},
            {"value": "hospitality", "source_text": "Hospitality operations."},
        ],
        "leadership_scope": [
            {
                "value": "156-outlet regional portfolio",
                "source_text": "Led managers across a 156-outlet regional portfolio.",
            }
        ],
        "career_tracks": [
            "Regional and Multi-Site Operations",
            "Delivery and Marketplace Operations",
            "Commercial Operations",
        ],
        "preferred_locations": ["London", "UK"],
    }


def evaluate(dataset_path: Path) -> dict:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    results = []
    for case in dataset["cases"]:
        score = score_candidate_against_job(
            candidate_analysis=benchmark_candidate(),
            job=JobInput(
                title=case["title"],
                company="Evaluation Employer",
                location=case["location"],
                description=case["description"],
                remote=case.get("remote", False),
                workplace_type=case.get("workplace_type", "unknown"),
            ),
        )
        results.append(
            {
                "id": case["id"],
                "label": case["label"],
                "title": case["title"],
                "score": score.overall_score,
                "recommendation": score.recommendation.value,
                "location_fit": score.location_fit,
            }
        )

    strong_predictions = [item for item in results if item["score"] >= 78]
    precision = (
        sum(item["label"] == "strong" for item in strong_predictions)
        / len(strong_predictions)
        if strong_predictions
        else 0.0
    )
    negatives = [item for item in results if item["label"] == "negative"]
    positives = [item for item in results if item["label"] == "strong"]
    false_positive_rate = sum(item["score"] >= 60 for item in negatives) / len(
        negatives
    )
    false_negative_rate = sum(item["score"] < 60 for item in positives) / len(positives)
    ordered, total = 0, 0
    for left in results:
        for right in results:
            if LABEL_ORDER[left["label"]] <= LABEL_ORDER[right["label"]]:
                continue
            total += 1
            ordered += left["score"] > right["score"]
    ordering_accuracy = ordered / total
    distribution = {
        label: {
            "count": len(values),
            "min": min(values),
            "median": statistics.median(values),
            "max": max(values),
        }
        for label in LABEL_ORDER
        if (values := [r["score"] for r in results if r["label"] == label])
    }
    criteria = {
        "strong_precision_at_78": precision >= 0.90,
        "negative_false_positive_rate": false_positive_rate <= 0.05,
        "strong_false_negative_rate": false_negative_rate <= 0.15,
        "pairwise_ordering_accuracy": ordering_accuracy >= 0.90,
        "strong_median_separation": (
            distribution["strong"]["median"] - distribution["adjacent"]["median"] >= 15
        ),
    }
    return {
        "dataset": str(dataset_path),
        "version": dataset["version"],
        "case_count": len(results),
        "metrics": {
            "strong_precision_at_78": round(precision, 4),
            "negative_false_positive_rate": round(false_positive_rate, 4),
            "strong_false_negative_rate": round(false_negative_rate, 4),
            "pairwise_ordering_accuracy": round(ordering_accuracy, 4),
        },
        "score_distribution": distribution,
        "acceptance": criteria,
        "passed": all(criteria.values()),
        "results": sorted(results, key=lambda item: item["score"], reverse=True),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--no-fail", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.dataset)
    print(json.dumps(report, indent=2))
    if not report["passed"] and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
