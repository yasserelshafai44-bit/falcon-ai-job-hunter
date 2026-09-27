from datetime import UTC, datetime

from app.job_providers.base import JobProvider, NormalizedJob


class LocalJobProvider(JobProvider):
    """Deterministic development source that keeps the MVP usable offline."""

    name = "local"
    display_name = "Local demo fixtures"
    is_demo = True

    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 50,
    ) -> list[NormalizedJob]:
        requested_title = (keyword or "Operations Manager").strip()
        requested_location = (location or "London / Remote").strip()
        templates = [
            (
                "operations-manager",
                requested_title,
                "Falcon Demo Foods",
                "Lead multi-site operations, KPI management, team leadership, "
                "supplier management and commercial improvement. Required: "
                "strong stakeholder communication.",
                55000,
                70000,
            ),
            (
                "delivery-operations-lead",
                "Delivery Operations Lead",
                "Local Marketplace Co",
                "Own delivery operations, marketplace performance, inventory "
                "control and cross-functional team leadership.",
                50000,
                65000,
            ),
            (
                "regional-manager",
                "Regional Manager",
                "Neighbourhood Hospitality",
                "Manage regional hospitality sites, P&L management, food safety, "
                "franchise compliance and coaching of site managers.",
                60000,
                75000,
            ),
        ]
        now = datetime.now(UTC)
        return [
            NormalizedJob(
                provider=self.name,
                external_id=external_id,
                title=title,
                company=company,
                location=requested_location,
                description=description,
                url=f"https://example.invalid/jobs/{external_id}",
                remote="remote" in requested_location.casefold(),
                workplace_type=(
                    "remote" if "remote" in requested_location.casefold() else "on-site"
                ),
                requirements=tuple(
                    part.strip() for part in description.split(".") if part.strip()
                ),
                employment_type="full-time",
                salary_min=salary_min,
                salary_max=salary_max,
                currency="GBP",
                posted_at=now,
                is_demo=True,
            )
            for (
                external_id,
                title,
                company,
                description,
                salary_min,
                salary_max,
            ) in templates[:limit]
        ]
