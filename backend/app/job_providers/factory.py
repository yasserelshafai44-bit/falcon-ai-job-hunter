from app.job_providers.base import JobProvider
from app.job_providers.bayt import BaytProvider
from app.job_providers.indeed import IndeedProvider
from app.job_providers.linkedin import LinkedInProvider
from app.job_providers.remoteok import RemoteOKProvider


def build_job_providers(enabled: set[str] | None = None) -> list[JobProvider]:
    providers: dict[str, JobProvider] = {
        "remoteok": RemoteOKProvider(),
        "linkedin": LinkedInProvider(),
        "indeed": IndeedProvider(),
        "bayt": BaytProvider(),
    }
    selected = enabled or {"remoteok"}
    return [provider for key, provider in providers.items() if key in selected]
