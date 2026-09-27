from app.job_providers.smartrecruiters import SmartRecruitersProvider


class GreeneKingUKProvider(SmartRecruitersProvider):
    """Public Greene King postings limited to senior operations search families."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="greene_king_uk",
            display_name="Greene King UK Operations Careers",
            company_identifier="GreeneKing",
            employer="Greene King",
            search_queries=(
                "area manager",
                "regional manager",
                "operations manager",
                "district manager",
                "franchise operations",
            ),
            **kwargs,
        )
