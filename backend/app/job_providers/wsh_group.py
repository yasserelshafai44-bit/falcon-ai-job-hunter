from app.job_providers.smartrecruiters import SmartRecruitersProvider


class WSHGroupUKProvider(SmartRecruitersProvider):
    """Official public SmartRecruiters postings for WSH Group UK."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="wsh_group_uk",
            display_name="WSH Group UK Careers",
            company_identifier="WSHGroup",
            employer="WSH Group UK",
            **kwargs,
        )
