from app.job_providers.smartrecruiters import SmartRecruitersProvider


class GreeneKingUKProvider(SmartRecruitersProvider):
    """All public UK Greene King postings; relevance is decided by ranking."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="greene_king_uk",
            display_name="Greene King UK Careers",
            company_identifier="GreeneKing",
            employer="Greene King",
            **kwargs,
        )
