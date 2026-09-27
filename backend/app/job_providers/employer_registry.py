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
        "careers_url": "https://careers.smartrecruiters.com/WSHGroup",
        "reason": "Westbury Street Holdings public UK postings across "
        "catering/hospitality brands including BaxterStorey "
        "and Caterlink",
    },
    {
        "id": "greene_king_uk",
        "employer": "Greene King",
        "category": "Hospitality & Multi-site",
        "status": "LIVE",
        "provider": "greene_king_uk",
        "careers_url": "https://jobs.greeneking.co.uk/",
        "reason": "Documented SmartRecruiters public UK Posting API; all "
        "occupational families retained",
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
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://costacareers.co.uk/",
        "reason": "Public WordPress vacancy feed exists, but published "
        "website terms prohibit reuse beyond personal print "
        "copies; permission is needed",
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
        "reason": "Public Tribepad HTML board declares a ten-second "
        "crawl delay; no complete machine feed verified in "
        "this assessment",
    },
    {
        "id": "dominos_uk",
        "employer": "Domino's UK & Ireland",
        "category": "QSR & Restaurants",
        "status": "LIVE",
        "provider": "dominos_uk",
        "careers_url": "https://jobs.dominos.co.uk/",
        "reason": "Official corporate live-jobs.xml sitemap and "
        "JobPosting JSON-LD; excludes separately operated "
        "franchise boards",
    },
    {
        "id": "pizza_hut_uk",
        "employer": "Pizza Hut UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.careersatpizzahut.co.uk/",
        "reason": "Official WordPress REST discovery returns HTTP 401; "
        "no authorised public vacancy feed verified",
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
        "reason": "Official careers site uses Talos360; no documented "
        "public complete vacancy interface verified. An "
        "authorised integration is required.",
    },
    {
        "id": "five_guys_uk",
        "employer": "Five Guys UK",
        "category": "QSR & Restaurants",
        "status": "UNAVAILABLE",
        "provider": None,
        "careers_url": "https://jobs.fiveguys.co.uk/jobs/home/",
        "reason": "Official UK careers hostname could not be reached in "
        "this assessment; not a zero-vacancy result",
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
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://careers.justeattakeaway.com/global/en/search-results",
        "reason": "Official Phenom/Workday careers UI; no authorised "
        "public tenant feed verified",
    },
    {
        "id": "uber",
        "employer": "Uber / Uber Eats",
        "category": "Delivery & Marketplace",
        "status": "UNAVAILABLE",
        "provider": None,
        "careers_url": "https://www.uber.com/us/en/careers/list/",
        "reason": "Official careers request returned HTTP 406; no "
        "challenge bypass or alternate private endpoint "
        "attempted",
    },
    {
        "id": "nandos_uk",
        "employer": "Nando's UK",
        "category": "QSR & Restaurants",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://nandos.careers/",
        "reason": "Official vacancies use Workday; no authorised public "
        "feed is verified",
    },
    {
        "id": "wendys_uk",
        "employer": "Wendy's UK",
        "category": "QSR & Restaurants",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://wendys-careers.co.uk/job-search/",
        "reason": "Official page is accessible; REST discovery exposes "
        "ordinary pages, not a verified vacancy collection",
    },
    {
        "id": "caffe_nero",
        "employer": "Caffè Nero",
        "category": "Coffee & Café",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.caffenero.com/",
        "reason": "Legacy careers host points to "
        "caffenero.com/uk/careers; no verified public vacancy "
        "feed",
    },
    {
        "id": "gails",
        "employer": "GAIL's",
        "category": "Coffee & Food-to-go",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.gailsbread.co.uk/en-gb/",
        "reason": "Official inploi careers UI is accessible; no "
        "documented public vacancy feed verified",
    },
    {
        "id": "compass_group_uk",
        "employer": "Compass Group UK & Ireland",
        "category": "Hospitality & Multi-site",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.compass-group.co.uk/",
        "reason": "Official inploi careers UI is accessible; no "
        "documented public vacancy feed verified",
    },
    {
        "id": "ssp_uk",
        "employer": "SSP UK & Ireland",
        "category": "Hospitality & Multi-site",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://careers.foodtravelexperts.com/",
        "reason": "SuccessFactors careers UI is public; no authorised "
        "public tenant feed verified; robots excludes services "
        "paths",
    },
    {
        "id": "mitchells_butlers",
        "employer": "Mitchells & Butlers",
        "category": "Hospitality & Multi-site",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.mbcareersandjobs.com/",
        "reason": "Official Attrax site links Harri recruitment; no "
        "verified public tenant postings feed or authorised "
        "integration",
    },
    {
        "id": "whitbread",
        "employer": "Whitbread",
        "category": "Hospitality & Multi-site",
        "status": "AUTHORIZATION_REQUIRED",
        "provider": None,
        "careers_url": "https://www.whitbreadcareers.com/search-and-apply/",
        "reason": "Official search identifies Dayforce; no authorised "
        "public feed is verified",
    },
    {
        "id": "wagamama",
        "employer": "Wagamama",
        "category": "QSR & Restaurants",
        "status": "MANUAL_ONLY",
        "provider": None,
        "careers_url": "https://jobs.wagamama.uk/search",
        "reason": "Official inploi search is accessible; no documented "
        "public vacancy feed verified",
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
    {
        "id": "gopuff_uk",
        "employer": "Gopuff",
        "category": "Delivery & Marketplace",
        "status": "LIVE",
        "provider": "gopuff_uk",
        "careers_url": "https://www.gopuff.com/go/careers",
        "reason": "Documented public Lever published-postings API; "
        "current UK openings only; talent pools excluded",
    },
    {
        "id": "deliverect_uk",
        "employer": "Deliverect",
        "category": "Delivery & Marketplace",
        "status": "LIVE",
        "provider": "deliverect_uk",
        "careers_url": "https://www.deliverect.com/en/careers-home",
        "reason": "Documented public Lever published-postings API; "
        "current UK openings only; talent pools excluded",
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
