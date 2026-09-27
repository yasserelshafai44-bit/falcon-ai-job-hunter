from typing import Literal, TypedDict

EmployerStatus = Literal["LIVE", "AUTHORIZATION_REQUIRED", "MANUAL_ONLY", "UNAVAILABLE"]


class EmployerRegistryEntry(TypedDict):
    id: str
    employer: str
    category: str
    status: EmployerStatus
    provider: str | None
    careers_url: str
    reason: str


EMPLOYER_REGISTRY: tuple[EmployerRegistryEntry, ...] = (
    {
        "id": "deliveroo",
        "employer": "Deliveroo",
        "category": "Delivery & Marketplace",
        "status": "LIVE",
        "provider": "deliveroo",
        "careers_url": "https://careers.deliveroo.co.uk/",
        "reason": "Verified public employer careers endpoint",
    },
    {
        "id": "kfc_uk",
        "employer": "KFC UK",
        "category": "QSR & Restaurants",
        "status": "LIVE",
        "provider": "kfc_uk",
        "careers_url": "https://careers.kfc.co.uk/",
        "reason": "Verified public employer careers endpoint",
    },
    {
        "id": "raising_canes_uk",
        "employer": "Raising Cane's UK",
        "category": "QSR & Restaurants",
        "status": "LIVE",
        "provider": "raising_canes_uk",
        "careers_url": "https://jobs.raisingcanes.co.uk/",
        "reason": "Verified SmartRecruiters public Posting API",
    },
    {
        "id": "wsh_group_uk",
        "employer": "WSH Group UK",
        "category": "Hospitality & Contract Catering",
        "status": "LIVE",
        "provider": "wsh_group_uk",
        "careers_url": "https://careers.wshgroup.co.uk/",
        "reason": "Verified SmartRecruiters public Posting API",
    },
    {
        "id": "greene_king_uk",
        "employer": "Greene King",
        "category": "Hospitality & Multi-site",
        "status": "LIVE",
        "provider": "greene_king_uk",
        "careers_url": "https://jobs.greeneking.co.uk/",
        "reason": "Verified SmartRecruiters public Posting API",
    },
    {
        "id": "burger_king_uk",
        "employer": "Burger King UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://careers.burgerking.co.uk/",
        "reason": "Harri source requires an authorised machine-access arrangement",
    },
    {
        "id": "wingstop_uk",
        "employer": "Wingstop UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://harri.com/Wingstopuk",
        "reason": "Harri source requires an authorised machine-access arrangement",
    },
    {
        "id": "pret_uk",
        "employer": "Pret A Manger",
        "category": "Coffee & Café",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.pret.co.uk/en-GB/pret-jobs",
        "reason": "No authorised public Cornerstone vacancy feed is verified",
    },
    {
        "id": "costa_coffee",
        "employer": "Costa Coffee",
        "category": "Coffee & Café",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://costacareers.co.uk/",
        "reason": "No reliable authorised public vacancy API is verified",
    },
    {
        "id": "starbucks_uk",
        "employer": "Starbucks UK",
        "category": "Coffee & Café",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.starbucks.com/",
        "reason": "Session-oriented careers search has no verified public vacancy API",
    },
    {
        "id": "mcdonalds_uk",
        "employer": "McDonald's UK",
        "category": "QSR & Restaurants",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://people.mcdonalds.co.uk/job-search",
        "reason": "No reliable authorised public vacancy API is verified",
    },
    {
        "id": "greggs",
        "employer": "Greggs",
        "category": "Food-to-go",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careerssearch.greggs.co.uk/",
        "reason": "Session-oriented recruitment site is unsuitable for automation",
    },
    {
        "id": "dominos_uk",
        "employer": "Domino's UK & Ireland",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://jobs.dominos.co.uk/",
        "reason": "No authorised public Eploy tenant feed is verified",
    },
    {
        "id": "pizza_hut_uk",
        "employer": "Pizza Hut UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.careersatpizzahut.co.uk/",
        "reason": "No documented machine feed with safe reconciliation is verified",
    },
    {
        "id": "taco_bell_uk",
        "employer": "Taco Bell UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://jobs.tacobell.com/jobs/country/United-Kingdom/",
        "reason": "The public careers UI uses an undocumented vacancy endpoint",
    },
    {
        "id": "popeyes_uk",
        "employer": "Popeyes UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://careers.popeyesuk.com/vacancies",
        "reason": "No documented public vacancy feed is verified",
    },
    {
        "id": "five_guys_uk",
        "employer": "Five Guys UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://jobs.fiveguys.co.uk/jobs/home/",
        "reason": "No authorised public Eploy tenant feed is verified",
    },
    {
        "id": "subway_uk",
        "employer": "Subway UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.subway.com/en-gb/careers",
        "reason": "Dayforce and franchise sources require separate authorised access",
    },
    {
        "id": "just_eat",
        "employer": "Just Eat Takeaway.com",
        "category": "Delivery & Marketplace",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.justeattakeaway.com/global/en/search-results",
        "reason": "No verified public careers API is available",
    },
    {
        "id": "uber",
        "employer": "Uber / Uber Eats",
        "category": "Delivery & Marketplace",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://www.uber.com/us/en/careers/list/",
        "reason": "No verified public careers API is available",
    },
    {
        "id": "nandos_uk",
        "employer": "Nando's UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://nandos.careers/",
        "reason": (
            "Official vacancies use Workday; no authorised public feed is verified"
        ),
    },
    {
        "id": "wendys_uk",
        "employer": "Wendy's UK",
        "category": "QSR & Restaurants",
        "status": "UNAVAILABLE",
        "provider": None,
        "careers_url": "https://wendys-careers.co.uk/job-search/",
        "reason": (
            "Careers search enforces browser verification and exposes no public feed"
        ),
    },
    {
        "id": "caffe_nero",
        "employer": "Caffè Nero",
        "category": "Coffee & Café",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.caffenero.com/",
        "reason": "No documented public vacancy endpoint is verified",
    },
    {
        "id": "gails",
        "employer": "GAIL's",
        "category": "Coffee & Food-to-go",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.gailsbread.co.uk/en-gb/",
        "reason": (
            "Official careers UI is accessible but no public machine feed is verified"
        ),
    },
    {
        "id": "compass_group_uk",
        "employer": "Compass Group UK & Ireland",
        "category": "Hospitality & Multi-site",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://jobs.compass-group.co.uk/",
        "reason": (
            "No documented public tenant feed with stable reconciliation is verified"
        ),
    },
    {
        "id": "ssp_uk",
        "employer": "SSP UK & Ireland",
        "category": "Hospitality & Multi-site",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.foodtravelexperts.com/",
        "reason": "No documented public vacancy API is verified",
    },
    {
        "id": "mitchells_butlers",
        "employer": "Mitchells & Butlers",
        "category": "Hospitality & Multi-site",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.mbcareersandjobs.com/",
        "reason": (
            "SmartRecruiters Attrax UI found; a public tenant posting contract is not "
            "verified"
        ),
    },
    {
        "id": "whitbread",
        "employer": "Whitbread",
        "category": "Hospitality & Multi-site",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.whitbreadcareers.com/search-and-apply/",
        "reason": (
            "Official search identifies Dayforce; no authorised public feed is verified"
        ),
    },
    {
        "id": "wagamama",
        "employer": "Wagamama",
        "category": "QSR & Restaurants",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.wagamama.uk/search",
        "reason": "No documented public vacancy API is verified",
    },
    {
        "id": "amazon_operations",
        "employer": "Amazon Operations",
        "category": "Delivery & Operations",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.amazon.co.uk/en/",
        "reason": "Official jobs are public, but no documented vacancy API is verified",
    },
)


def live_direct_provider_keys() -> tuple[str, ...]:
    """Return the provider keys backed by currently searchable employers."""
    return tuple(
        entry["provider"]
        for entry in EMPLOYER_REGISTRY
        if entry["status"] == "LIVE" and entry["provider"] is not None
    )


def resolve_provider_selection(requested: list[str]) -> list[str]:
    """Expand UI group selections from the authoritative employer registry."""
    resolved: list[str] = []
    live = live_direct_provider_keys()
    for provider in requested:
        values = live if provider == "all_verified_direct" else (provider,)
        for value in values:
            if value not in resolved:
                resolved.append(value)
    return resolved
