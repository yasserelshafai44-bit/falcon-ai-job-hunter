"""Reprocess and audit deterministic summaries for every current live vacancy."""

from __future__ import annotations

import asyncio
import json

import httpx
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal
from app.models.calibration_review import CalibrationReview
from app.models.discovered_job import DiscoveredJob
from app.services.vacancy_summary import build_human_review_summary
from sqlalchemy import select


def _snapshot(job: DiscoveredJob) -> dict[str, object]:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
    }


async def main() -> None:
    async with AsyncSessionLocal() as session:
        jobs = list(
            await session.scalars(
                select(DiscoveredJob).where(
                    DiscoveredJob.is_active.is_(True),
                    DiscoveredJob.is_demo.is_(False),
                )
            )
        )

    caterlink: list[dict[str, object]] = []
    caterlink_ids: list[int] = []
    for job in jobs:
        summary = build_human_review_summary(_snapshot(job), job)
        if "operations manager" in job.title.lower() and (
            "caterlink" in job.company.lower() or "caterlink" in job.title.lower()
        ):
            caterlink_ids.append(job.id)
            caterlink.append(
                {
                    "id": job.id,
                    "company": job.company,
                    "title": job.title,
                    "experience_qualifications": summary["experience_qualifications"],
                }
            )

    api_summary: dict[str, object] | None = None
    async with AsyncSessionLocal() as session:
        review = await session.scalar(
            select(CalibrationReview).where(CalibrationReview.job_id.in_(caterlink_ids))
        )
    if review is not None:
        token = create_access_token(str(review.user_id))
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "http://127.0.0.1:8000/api/v1/calibration/reviews",
                headers={"Authorization": f"Bearer {token}"},
                params={"corpus_version": review.corpus_version},
            )
            response.raise_for_status()
            api_item = next(
                item
                for item in response.json()["items"]
                if item["job_id"] in caterlink_ids
            )
            api_summary = api_item["human_review_summary"]

    print(
        json.dumps(
            {
                "summaries_reprocessed": len(jobs),
                "caterlink": caterlink,
                "api_caterlink_summary": api_summary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
