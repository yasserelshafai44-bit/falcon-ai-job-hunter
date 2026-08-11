import pytest

from app.schemas.application_workflow import ApplicationWorkflowStatus
from app.services.application_workflow import (
    ApplicationWorkflowError,
    can_transition,
)


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
