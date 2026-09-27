from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.user import User
from app.services import application_assistant as service
from app.services.application_files import DOCX_MIME, resume_docx
from app.services.application_profile import (
    ApplicationFactUpdate,
    ProfileUpdate,
    get_application_profile,
    save_application_fact,
    save_application_profile,
    save_application_surname,
)
from app.services.assisted_apply import assisted_pack

router = APIRouter(prefix="/application-assistant", tags=["application assistant"])
DB = Annotated[AsyncSession, Depends(get_db_session)]
Owner = Annotated[User, Depends(get_current_user)]


class FinalApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_digest: str = Field(min_length=64, max_length=64)
    explicit_final_approval: bool = False


class SubmitDryRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_digest: str = Field(min_length=64, max_length=64)


class ApplicationSurname(BaseModel):
    model_config = ConfigDict(extra="forbid")
    application_surname: str = Field(min_length=1, max_length=150)


@router.put("/profile/fact")
async def save_fact(payload: ApplicationFactUpdate, user: Owner, session: DB):
    try:
        return await save_application_fact(
            session, user.id, payload.field, payload.value
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/applications/{workflow_id}/assisted")
async def read_assisted(workflow_id: int, user: Owner, session: DB):
    try:
        return await assisted_pack(session, user.id, workflow_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/applications/{workflow_id}/continue")
async def continue_assisted(workflow_id: int, user: Owner, session: DB):
    try:
        return await assisted_pack(
            session, user.id, workflow_id, continue_application=True
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/applications/{workflow_id}/cover-letter.txt")
async def download_cover(workflow_id: int, user: Owner, session: DB):
    try:
        pack = await assisted_pack(session, user.id, workflow_id)
        return Response(
            pack["cover_letter"],
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="Falcon-application-{workflow_id}'
                    '-cover-letter.txt"'
                ),
                "Cache-Control": "no-store",
            },
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/profile/application-surname")
async def surname(payload: ApplicationSurname, user: Owner, session: DB):
    try:
        return await save_application_surname(
            session, user.id, payload.application_surname
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/applications/{workflow_id}/prepare-local")
async def prepare_local(workflow_id: int, user: Owner, session: DB):
    try:
        return await service.prepare_assistant(
            session, user.id, workflow_id, local_browser=True
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/sessions/{session_id}/refresh-local")
async def refresh_local(session_id: str, user: Owner, session: DB):
    try:
        return await service.refresh_local(session, user.id, session_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/profile")
async def profile(user: Owner, session: DB):
    try:
        return await get_application_profile(session, user.id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/profile")
async def update_profile(payload: ProfileUpdate, user: Owner, session: DB):
    try:
        return await save_application_profile(session, user.id, payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/applications/{workflow_id}/resume.docx")
async def download_resume(workflow_id: int, user: Owner, session: DB):
    try:
        _, _, resume, *_ = await service.inputs(session, user.id, workflow_id)
        return Response(
            resume_docx(resume.content),
            media_type=DOCX_MIME,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="Falcon-application-{workflow_id}'
                    f'-resume-{resume.id}.docx"'
                ),
                "Cache-Control": "no-store",
            },
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/applications/{workflow_id}/prepare")
async def prepare(workflow_id: int, user: Owner, session: DB):
    try:
        return await service.prepare_assistant(session, user.id, workflow_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/sessions/{session_id}")
async def read_session(session_id: str, user: Owner, session: DB):
    try:
        return service.public_session(
            await service.get_session(session, user.id, session_id)
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/sessions/{session_id}/final-approve")
async def approve(session_id: str, payload: FinalApproval, user: Owner, session: DB):
    try:
        return await service.final_approve(
            session,
            user.id,
            session_id,
            payload.snapshot_digest,
            payload.explicit_final_approval,
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/sessions/{session_id}/submit-dry-run")
async def submit(session_id: str, payload: SubmitDryRun, user: Owner, session: DB):
    try:
        return await service.dry_run_submit(
            session, user.id, session_id, payload.snapshot_digest
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
