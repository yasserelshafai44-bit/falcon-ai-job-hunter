"""Authenticated, non-submitting verification of the UI all-provider workflow."""

from __future__ import annotations

import asyncio
import json

import httpx
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal
from app.models.candidate_analysis import CandidateAnalysis
from sqlalchemy import select


async def main() -> None:
    async with AsyncSessionLocal() as session:
        analysis = await session.scalar(
            select(CandidateAnalysis)
            .where(CandidateAnalysis.cv_document_id == 2)
            .limit(1)
        )
        if analysis is None:
            analysis = await session.scalar(
                select(CandidateAnalysis).order_by(CandidateAnalysis.id).limit(1)
            )
    if analysis is None:
        raise RuntimeError("No existing analysed CV is available for verification")

    token = create_access_token(str(analysis.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000/api/v1", timeout=600
    ) as client:
        sync = await client.post(
            "/jobs/sync",
            headers=headers,
            json={
                "providers": ["all_verified_direct"],
                "limit_per_provider": 100,
                "candidate_analysis_id": analysis.id,
            },
        )
        sync.raise_for_status()
        sync_data = sync.json()
        jobs: list[dict] = []
        for provider in sync_data["providers_requested"]:
            response = await client.get(
                "/jobs",
                headers=headers,
                params={"provider": provider, "page_size": 100},
            )
            response.raise_for_status()
            jobs.extend(response.json()["items"])
        matches_response = await client.get("/matches", headers=headers)
        matches_response.raise_for_status()
        job_ids = {job["id"] for job in jobs}
        ranked = [
            match
            for match in matches_response.json()["items"]
            if match["candidate_analysis_id"] == analysis.id
            and match["job_id"] in job_ids
        ]

    jobs_by_id = {job["id"]: job for job in jobs}
    ranked.sort(key=lambda item: item["career_fit_score"], reverse=True)
    recommendation_counts = {
        recommendation: sum(
            match["recommendation"] == recommendation for match in ranked
        )
        for recommendation in (
            "strong_apply",
            "apply",
            "review",
            "weak_match",
            "reject",
        )
    }
    displayed = [
        match
        for match in ranked
        if match["career_fit_score"] >= 35
        and jobs_by_id[match["job_id"]]["provider"] in sync_data["providers_requested"]
    ]

    print(
        json.dumps(
            {
                "providers": sync_data["providers_requested"],
                "vacancies": len(jobs),
                "ranked_jobs": len(ranked),
                "analysis_id": analysis.id,
                "cv_document_id": analysis.cv_document_id,
                "score_at_least_35": sum(
                    match["career_fit_score"] >= 35 for match in ranked
                ),
                "recommendation_counts": recommendation_counts,
                "displayed_with_owner_filters": len(displayed),
                "top_10": [
                    {
                        "employer": jobs_by_id[match["job_id"]]["company"],
                        "title": jobs_by_id[match["job_id"]]["title"],
                        "score": match["career_fit_score"],
                        "recommendation": match["recommendation"],
                        "location": jobs_by_id[match["job_id"]]["location"],
                    }
                    for match in displayed[:10]
                ],
                "provider_errors": sync_data["provider_errors"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
