from app.core.config import get_settings
from app.job_providers.base import JobProvider
from app.job_providers.bayt import BaytProvider
from app.job_providers.deliveroo import DeliverooProvider
from app.job_providers.dominos import DominosUKProvider
from app.job_providers.greene_king import GreeneKingUKProvider
from app.job_providers.indeed import IndeedProvider
from app.job_providers.kfc import KFCUKProvider
from app.job_providers.lever import LeverUKProvider
from app.job_providers.linkedin import LinkedInProvider
from app.job_providers.local import LocalJobProvider
from app.job_providers.raising_canes import RaisingCanesUKProvider
from app.job_providers.remoteok import RemoteOKProvider
from app.job_providers.wsh_group import WSHGroupUKProvider


def build_job_providers(enabled: set[str] | None = None) -> list[JobProvider]:
    settings = get_settings()
    providers: dict[str, JobProvider] = {
        "local": LocalJobProvider(),
        "dominos_uk": DominosUKProvider(),
        "gopuff_uk": LeverUKProvider(
            name="gopuff_uk", employer="Gopuff", site="gopuff"
        ),
        "deliverect_uk": LeverUKProvider(
            name="deliverect_uk", employer="Deliverect", site="deliverect"
        ),
        "remoteok": RemoteOKProvider(
            endpoint=settings.remoteok_api_url,
            timeout_seconds=settings.remoteok_timeout_seconds,
        ),
        "deliveroo": DeliverooProvider(),
        "greene_king_uk": GreeneKingUKProvider(),
        "kfc_uk": KFCUKProvider(),
        "raising_canes_uk": RaisingCanesUKProvider(),
        "wsh_group_uk": WSHGroupUKProvider(),
        "linkedin": LinkedInProvider(),
        "indeed": IndeedProvider(),
        "bayt": BaytProvider(),
    }
    selected = enabled or {"remoteok"}
    return [provider for key, provider in providers.items() if key in selected]
