import pytest
from app.job_providers.base import JobProvider, NormalizedJob
from app.models.discovered_job import DiscoveredJob
from app.services.job_search import sync_jobs
from sqlalchemy import select

from tests.conftest import TestSession


class DuplicateProvider(JobProvider):
    def __init__(
        self,
        name: str,
        external_id: str,
        *,
        is_demo: bool = False,
        company: str = "Same Company",
        title: str = "Regional Manager",
        location: str = "London, United Kingdom",
        description: str = "Lead regional operations and multi-site performance.",
        complete_snapshot: bool = False,
    ) -> None:
        self.name = name
        self.external_id = external_id
        self.is_demo = is_demo
        self.company = company
        self.title = title
        self.location = location
        self.description = description
        self.complete_snapshot = complete_snapshot
        self.jobs_visible = True

    async def search(self, *, keyword=None, location=None, limit=50):
        return (
            []
            if not self.jobs_visible
            else [
                NormalizedJob(
                    provider=self.name,
                    external_id=self.external_id,
                    title=self.title,
                    company=self.company,
                    location=self.location,
                    description=self.description,
                    url=f"https://example.invalid/{self.external_id}",
                    remote=False,
                    workplace_type="on-site",
                    is_demo=self.is_demo,
                )
            ]
        )


@pytest.mark.asyncio
async def test_verified_empty_snapshot_closes_without_deleting_saved_record():
    provider = DuplicateProvider("verified", "existing", complete_snapshot=True)
    async with TestSession() as session:
        await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )
        before = await session.scalar(select(DiscoveredJob))
        original_id = before.id
        provider.jobs_visible = False
        provider.authoritative_empty = True
        result = await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )
        after = await session.scalar(select(DiscoveredJob))
        assert after.id == original_id
        assert after.is_active is False
        assert after.closed_at is not None
        assert result.closed == 1


@pytest.mark.asyncio
async def test_cross_provider_duplicate_is_stored_once() -> None:
    async with TestSession() as session:
        first = await sync_jobs(
            session=session,
            providers=[DuplicateProvider("source-a", "one")],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )
        second = await sync_jobs(
            session=session,
            providers=[DuplicateProvider("source-b", "two")],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.updated == 0
    assert second.duplicates == 1
    async with TestSession() as session:
        record = await session.scalar(select(DiscoveredJob))
        assert record is not None
        assert {
            (item["provider"], item["external_id"]) for item in record.source_records
        } == {("source-a", "one"), ("source-b", "two")}


@pytest.mark.asyncio
async def test_demo_job_never_deduplicates_into_real_job() -> None:
    async with TestSession() as session:
        demo = await sync_jobs(
            session=session,
            providers=[DuplicateProvider("local", "demo", is_demo=True)],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )
        real = await sync_jobs(
            session=session,
            providers=[DuplicateProvider("remoteok", "real")],
            keyword=None,
            location=None,
            limit_per_provider=10,
        )

    assert demo.inserted == 1
    assert real.inserted == 1
    assert real.duplicates == 0


@pytest.mark.asyncio
async def test_duplicate_refresh_updates_without_inserting_again() -> None:
    provider = DuplicateProvider("deliveroo", "R100", complete_snapshot=True)
    async with TestSession() as session:
        first = await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        second = await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        records = list(await session.scalars(select(DiscoveredJob)))

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.updated == 1
    assert len(records) == 1


@pytest.mark.asyncio
async def test_sudden_zero_snapshot_does_not_silently_close_vacancy() -> None:
    provider = DuplicateProvider("deliveroo", "R101", complete_snapshot=True)
    async with TestSession() as session:
        await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        provider.jobs_visible = False
        result = await sync_jobs(
            session=session,
            providers=[provider],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        record = await session.scalar(select(DiscoveredJob))

    assert result.closed == 0
    assert record is not None
    assert record.is_active is True
    assert record.closed_at is None
    assert record.source_records[0]["active"] is True


class FailingProvider(JobProvider):
    name = "failing"

    async def search(self, *, keyword=None, location=None, limit=50):
        raise RuntimeError("upstream unavailable")


@pytest.mark.asyncio
async def test_provider_failure_does_not_break_other_provider_or_close_jobs() -> None:
    healthy = DuplicateProvider("deliveroo", "R102", complete_snapshot=True)
    async with TestSession() as session:
        result = await sync_jobs(
            session=session,
            providers=[FailingProvider(), healthy],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        record = await session.scalar(select(DiscoveredJob))

    assert result.inserted == 1
    assert result.errors == {"failing": "upstream unavailable"}
    assert record is not None and record.is_active is True


@pytest.mark.asyncio
async def test_employer_aliases_deduplicate_cross_provider_vacancy() -> None:
    first = DuplicateProvider("kfc_uk", "100", company="KFC UK")
    second = DuplicateProvider(
        "job_board",
        "abc",
        company="KFC (Great Britain) Limited",
        description="Lead regional operations and multi-site performance.",
    )
    async with TestSession() as session:
        result = await sync_jobs(
            session=session,
            providers=[first, second],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        records = list(await session.scalars(select(DiscoveredJob)))

    assert result.inserted == 1
    assert result.duplicates == 1
    assert len(records) == 1


@pytest.mark.asyncio
async def test_smartrecruiters_employer_alias_deduplicates_job_board_copy() -> None:
    direct = DuplicateProvider(
        "raising_canes_uk",
        "744000140850342",
        company="Raising Cane's UK",
        title="Area Leader of Restaurants (Operations Manager)",
        description=(
            "Lead multiple restaurants, coach managers and own P&L and regional "
            "operational performance."
        ),
    )
    board = DuplicateProvider(
        "job_board",
        "copy-42",
        company="Raising Canes",
        title="Area Leader of Restaurants - Operations Manager",
        description=(
            "Lead multiple restaurants, coach managers and own P&L and regional "
            "operational performance."
        ),
    )
    async with TestSession() as session:
        result = await sync_jobs(
            session=session,
            providers=[direct, board],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        records = list(await session.scalars(select(DiscoveredJob)))

    assert result.inserted == 1
    assert result.duplicates == 1
    assert len(records) == 1
    assert {source["provider"] for source in records[0].source_records} == {
        "raising_canes_uk",
        "job_board",
    }


@pytest.mark.asyncio
async def test_same_title_location_with_different_descriptions_stays_distinct() -> None:
    first = DuplicateProvider(
        "deliveroo",
        "R200",
        description="Lead restaurant partner onboarding across multiple sites and P&L.",
    )
    second = DuplicateProvider(
        "deliveroo",
        "R201",
        description=(
            "Lead courier safety incidents, fleet compliance and regional operations."
        ),
    )
    async with TestSession() as session:
        result = await sync_jobs(
            session=session,
            providers=[first, second],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        repeated = await sync_jobs(
            session=session,
            providers=[first, second],
            keyword=None,
            location=None,
            limit_per_provider=20,
        )
        records = list(await session.scalars(select(DiscoveredJob)))

    assert result.inserted == 2
    assert result.duplicates == 0
    assert repeated.inserted == 0
    assert repeated.updated == 2
    assert len(records) == 2
    assert len({record.canonical_key for record in records}) == 2
