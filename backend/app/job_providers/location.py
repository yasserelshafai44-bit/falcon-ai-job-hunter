import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobLocation:
    display: str
    canonical: str
    country_code: str | None
    workplace_type: str
    region_code: str | None = None

    @property
    def is_uk(self) -> bool | None:
        if self.country_code is None:
            return None
        return self.country_code == "GB"


_UK_CITIES = {
    "birmingham",
    "brighton",
    "bristol",
    "cambridge",
    "canterbury",
    "cardiff",
    "chichester",
    "crawley",
    "eastbourne",
    "edinburgh",
    "glasgow",
    "hastings",
    "horsham",
    "leeds",
    "liverpool",
    "london",
    "manchester",
    "maidstone",
    "newcastle upon tyne",
    "nottingham",
    "oxford",
    "sheffield",
    "southampton",
    "worthing",
    "royal tunbridge wells",
    "tunbridge wells",
}
_UK_REGIONS = {
    "kent",
    "east sussex",
    "west sussex",
    "south east england",
    "surrey",
}
_CITY_REGIONS = {
    "brighton": "east-sussex",
    "canterbury": "kent",
    "chichester": "west-sussex",
    "crawley": "west-sussex",
    "eastbourne": "east-sussex",
    "hastings": "east-sussex",
    "horsham": "west-sussex",
    "maidstone": "kent",
    "royal tunbridge wells": "kent",
    "tunbridge wells": "kent",
    "worthing": "west-sussex",
}
_NON_UK_COUNTRIES = {
    "australia": "AU",
    "belgium": "BE",
    "france": "FR",
    "germany": "DE",
    "india": "IN",
    "ireland": "IE",
    "italy": "IT",
    "kuwait": "KW",
    "singapore": "SG",
    "united arab emirates": "AE",
    "united states": "US",
    "usa": "US",
}


def normalize_location(
    value: str,
    *,
    remote: bool = False,
    workplace_type: str = "unknown",
) -> JobLocation:
    display = re.sub(r"\s+", " ", value or "Location not specified").strip(" ,")
    folded = display.casefold()
    mode = workplace_type.casefold().replace("_", "-")
    if "hybrid" in folded or mode == "hybrid":
        mode = "hybrid"
    elif remote or "remote" in folded or mode == "remote":
        mode = "remote"
    elif mode not in {"on-site", "onsite"}:
        mode = "unknown"
    else:
        mode = "on-site"

    country_code: str | None = None
    if re.search(
        r"\b(united kingdom|u\.?k\.?|great britain|england|scotland|wales)\b", folded
    ):
        country_code = "GB"
    elif re.search(r"\b(northern ireland)\b", folded) or re.search(
        r"\bBT\d{1,2}\b", display, re.I
    ):
        country_code = "GB"
    else:
        for country, code in _NON_UK_COUNTRIES.items():
            if re.search(rf"\b{re.escape(country)}\b", folded):
                country_code = code
                break
    city = next(
        (city for city in sorted(_UK_CITIES, key=len, reverse=True) if city in folded),
        None,
    )
    region = next(
        (
            region
            for region in sorted(_UK_REGIONS, key=len, reverse=True)
            if region in folded
        ),
        None,
    )
    if country_code is None and (city or region):
        country_code = "GB"
    region_code = (
        re.sub(r"[^a-z0-9]+", "-", region).strip("-")
        if region
        else _CITY_REGIONS.get(city or "")
    )

    if "greater london" in folded:
        place = "greater-london"
    elif re.search(r"\blondon\b", folded):
        place = "london"
    elif city:
        place = re.sub(r"[^a-z0-9]+", "-", city).strip("-")
    elif region:
        place = re.sub(r"[^a-z0-9]+", "-", region).strip("-")
    elif country_code:
        country_only = folded.strip(" ,.-") in {
            "united kingdom",
            "uk",
            "u.k.",
            "great britain",
            "united states",
            "usa",
        }
        place = (
            "countrywide"
            if mode == "remote" or country_only
            else re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
        )
    else:
        place = re.sub(r"[^a-z0-9]+", "-", folded).strip("-") or "unknown"
    country = country_code.casefold() if country_code else "unknown"
    canonical = f"{country}:{place}"
    return JobLocation(display, canonical, country_code, mode, region_code)
