from app.job_providers.smartrecruiters import SmartRecruitersProvider


class RaisingCanesUKProvider(SmartRecruitersProvider):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            name="raising_canes_uk",
            display_name="Raising Cane's UK Careers",
            company_identifier="RaisingCanes",
            employer="Raising Cane's UK",
            **kwargs,
        )
