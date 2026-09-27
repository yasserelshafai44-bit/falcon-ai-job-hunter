import pytest
from app.models.discovered_job import DiscoveredJob
from app.schemas.application_workflow import ApplicationWorkflowStatus
from app.services.application_workflow import (
    can_transition,
    employer_question_state,
)


@pytest.mark.parametrize(
    "sources,url,expected",
    [
        ([], "https://example.com/job", "unknown"),
        ([{"application_questions": []}], "https://example.com/job", "unknown"),
        (
            [{"application_questions": ["Right to work?"]}],
            "https://example.com/job",
            "retrieved",
        ),
        (
            [{"application_questions_status": "none_required"}],
            "https://example.com/job",
            "none_required",
        ),
        (
            [{"application_questions_status": "unavailable"}],
            "https://example.com/job",
            "unavailable",
        ),
        (
            [],
            "https://jobs.smartrecruiters.com/RaisingCanes/123",
            "requires_employer_site",
        ),
    ],
)
def test_employer_questions_distinguish_unknown_from_unanswered(sources, url, expected):
    status, note = employer_question_state(
        DiscoveredJob(source_records=sources, url=url)
    )
    assert status == expected
    assert note


def test_application_workflow_happy_path_transitions() -> None:
    assert can_transition(
        ApplicationWorkflowStatus.DRAFT,
        ApplicationWorkflowStatus.MATERIALS_READY,
    )
    assert can_transition(
        ApplicationWorkflowStatus.MATERIALS_READY,
        ApplicationWorkflowStatus.AWAITING_APPROVAL,
    )
    assert can_transition(
        ApplicationWorkflowStatus.AWAITING_APPROVAL,
        ApplicationWorkflowStatus.APPROVED,
    )
    assert can_transition(
        ApplicationWorkflowStatus.APPROVED,
        ApplicationWorkflowStatus.SUBMITTED,
    )
    assert can_transition(
        ApplicationWorkflowStatus.SUBMITTED,
        ApplicationWorkflowStatus.INTERVIEW,
    )
    assert can_transition(
        ApplicationWorkflowStatus.INTERVIEW,
        ApplicationWorkflowStatus.OFFER,
    )


def test_application_workflow_blocks_invalid_transitions() -> None:
    assert not can_transition(
        ApplicationWorkflowStatus.DRAFT,
        ApplicationWorkflowStatus.SUBMITTED,
    )
    assert not can_transition(
        ApplicationWorkflowStatus.REJECTED,
        ApplicationWorkflowStatus.APPROVED,
    )
