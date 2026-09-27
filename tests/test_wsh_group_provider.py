from app.job_providers.factory import build_job_providers
from app.job_providers.role_filter import classify_role
from app.job_providers.wsh_group import WSHGroupUKProvider


def test_wsh_group_uses_the_reusable_public_smartrecruiters_adapter() -> None:
    provider = WSHGroupUKProvider()

    assert provider.name == "wsh_group_uk"
    assert provider.company_identifier == "WSHGroup"
    assert provider.employer == "WSH Group UK"
    assert provider.postings_endpoint.endswith("/companies/WSHGroup/postings")


def test_factory_exposes_wsh_group_only_when_selected() -> None:
    providers = build_job_providers({"wsh_group_uk"})

    assert [provider.name for provider in providers] == ["wsh_group_uk"]


def test_learning_and_development_manager_is_not_an_operations_role() -> None:
    result = classify_role(
        "Learning & Development Manager",
        "Lead training delivery, manager capability, KPIs and regional leadership.",
    )

    assert result.eligible is False
    assert result.family == "specialist_profession"
