from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.user import User
from app.schemas.application_workflow import (
    ApplicationReview,
    ApplicationWorkflowList,
    ApplicationWorkflowRead,
    ApprovalRequest,
    AttachApplicationDocumentsRequest,
    CreateApplicationWorkflowRequest,
    OutcomeRequest,
    SubmissionRequest,
)
from app.services.application_materials import regenerate_application_materials
from app.services.application_workflow import (
    ApplicationWorkflowError,
    approve_reviewed_materials,
    approve_workflow,
    attach_documents,
    create_workflow,
    get_application_review,
    get_workflow,
    list_workflows,
    mark_reviewed,
    mark_submitted,
    request_approval,
    set_outcome,
)
from app.services.document_generation import GenerationInputError

router = APIRouter(prefix="/application-workflows", tags=["application workflows"])


class MaterialsApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    explicit_review_and_approval: bool = False


@router.post("/{workflow_id}/approve-materials", response_model=ApplicationWorkflowRead)
async def approve_materials(
    workflow_id: int,
    payload: MaterialsApproval,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    if not payload.explicit_review_and_approval:
        raise HTTPException(400, "Explicit review and approval are required")
    try:
        return await approve_reviewed_materials(
            session=session, user_id=user.id, workflow_id=workflow_id
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/prepare", response_model=ApplicationWorkflowRead)
async def prepare_application(
    payload: CreateApplicationWorkflowRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        workflow = await create_workflow(
            session=session, user_id=user.id, job_match_id=payload.job_match_id
        )
        if workflow.status == "draft":
            return await regenerate_application_materials(
                session=session, user_id=user.id, workflow_id=workflow.id
            )
        # Repeated Prepare opens existing material without discarding user revisions.
        await get_application_review(
            session=session, user_id=user.id, workflow_id=workflow.id
        )
        return workflow
    except (ApplicationWorkflowError, GenerationInputError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/{workflow_id}/regenerate-materials", response_model=ApplicationWorkflowRead
)
async def regenerate_materials(
    workflow_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await regenerate_application_materials(
            session=session, user_id=user.id, workflow_id=workflow_id
        )
    except (ApplicationWorkflowError, GenerationInputError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("", response_model=ApplicationWorkflowRead)
async def create_application_workflow(
    payload: CreateApplicationWorkflowRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await create_workflow(
            session=session,
            user_id=user.id,
            job_match_id=payload.job_match_id,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=ApplicationWorkflowList)
async def read_application_workflows(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowList:
    items, total = await list_workflows(session=session, user_id=user.id)
    return ApplicationWorkflowList(items=items, total=total)


@router.get("/{workflow_id}", response_model=ApplicationWorkflowRead)
async def read_application_workflow(
    workflow_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    item = await get_workflow(
        session=session,
        user_id=user.id,
        workflow_id=workflow_id,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Application workflow not found")
    return item


@router.get("/{workflow_id}/review", response_model=ApplicationReview)
async def read_application_review(
    workflow_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationReview:
    try:
        return await get_application_review(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workflow_id}/reviewed", response_model=ApplicationWorkflowRead)
async def mark_application_reviewed(
    workflow_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await mark_reviewed(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/documents", response_model=ApplicationWorkflowRead)
async def attach_application_documents(
    workflow_id: int,
    payload: AttachApplicationDocumentsRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await attach_documents(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
            resume_document_id=payload.resume_document_id,
            cover_letter_document_id=payload.cover_letter_document_id,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/request-approval", response_model=ApplicationWorkflowRead)
async def request_application_approval(
    workflow_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await request_approval(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/approve", response_model=ApplicationWorkflowRead)
async def approve_application(
    workflow_id: int,
    payload: ApprovalRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await approve_workflow(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
            notes=payload.notes,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/submitted", response_model=ApplicationWorkflowRead)
async def submit_application(
    workflow_id: int,
    payload: SubmissionRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    if not payload.confirmed_submitted:
        raise HTTPException(
            status_code=400,
            detail=(
                "Submission status requires explicit confirmation that the user or "
                "an integrated provider actually submitted the application"
            ),
        )
    try:
        return await mark_submitted(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
            external_application_url=(
                str(payload.external_application_url)
                if payload.external_application_url is not None
                else None
            ),
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/outcome", response_model=ApplicationWorkflowRead)
async def update_application_outcome(
    workflow_id: int,
    payload: OutcomeRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationWorkflowRead:
    try:
        return await set_outcome(
            session=session,
            user_id=user.id,
            workflow_id=workflow_id,
            target=payload.status,
        )
    except ApplicationWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
