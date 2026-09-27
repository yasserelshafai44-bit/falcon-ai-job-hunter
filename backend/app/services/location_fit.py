"""Explicit job geography preferences; never contributes to career fit."""

from app.job_providers.location import normalize_location


def assess_location(
    preferences: dict, location: str, *, remote=False, workplace_type="unknown"
) -> tuple[int, str, str]:
    place = normalize_location(location, remote=remote, workplace_type=workplace_type)
    mode = place.workplace_type
    selected = list(preferences.get("preferred_locations") or []) + list(
        preferences.get("preferred_regions") or []
    )
    home = preferences.get("home_location")
    london = place.canonical in {"gb:london", "gb:greater-london"}

    def result(status, reason):
        return 0, status, f"Location — {reason} (listed: {place.display})"

    if mode in {"remote", "hybrid"}:
        accepted = preferences.get(f"{mode}_acceptable")
        if place.is_uk is False and (
            accepted is True
            or any(
                normalize_location(v).is_uk for v in selected + ([home] if home else [])
            )
        ):
            return result(
                "mismatched",
                "UK work preferences do not cover the stated overseas location",
            )
        if accepted is False:
            return result("mismatched", f"{mode.title()} work is explicitly declined")
        if accepted is not True:
            return result("unknown", f"{mode.title()} work preference is unconfirmed")
        if place.is_uk is True:
            return result(
                "matched",
                f"{mode.title()} UK is explicitly selected; "
                "confirm attendance/travel requirements with the employer",
            )
        if place.is_uk is False:
            return result(
                "mismatched",
                f"{mode.title()} UK preference does not cover "
                "the stated overseas location",
            )
        return result("unknown", "UK work eligibility/geography is not stated")

    if london and preferences.get("london_acceptable") is False:
        return result("mismatched", "London is explicitly declined")
    if london and preferences.get("london_acceptable") is True:
        return result("matched", "London is explicitly selected")
    if preferences.get("anywhere_uk_acceptable") is True and place.is_uk is True:
        return result("matched", "Anywhere UK is explicitly selected")
    # Home is a town, not permission for its entire county or country.
    if home and normalize_location(home).canonical == place.canonical:
        return result("matched", "Matches the saved home town")
    for value in selected:
        target = normalize_location(value)
        if target.country_code != place.country_code:
            continue
        region_selected = target.region_code and target.canonical.endswith(
            ":" + target.region_code
        )
        if (
            target.canonical == place.canonical
            or (region_selected and target.region_code == place.region_code)
            or target.canonical.endswith(":countrywide")
        ):
            if target.country_code is not None:
                return result("matched", f"Matches explicitly selected {value}")
    if place.is_uk is False and (home or selected):
        return result(
            "mismatched", "Stated overseas location is outside saved preferences"
        )
    if preferences.get("anywhere_uk_acceptable") is False and place.is_uk is True:
        return result(
            "mismatched", "Outside selected locations; anywhere UK is declined"
        )
    return result(
        "unknown",
        "This location has not been explicitly selected; "
        "home country, willingness to travel or relocate is not approval",
    )
