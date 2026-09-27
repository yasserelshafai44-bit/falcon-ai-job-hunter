from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.session import get_db_session
from app.models.cv_document import CVDocument
from app.models.user import User
from app.schemas.cv import CVResponse

router = APIRouter(prefix="/cvs", tags=["CV documents"])
_ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
_ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}


@router.post("", response_model=CVResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    file: Annotated[UploadFile, File(...)],
    career_track: Annotated[str | None, Form(max_length=100)] = None,
) -> CVDocument:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in _ALLOWED_TYPES or suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, DOCX, and TXT CV files are supported",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="CV file is empty")
    if len(content) > settings.max_cv_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CV file is too large")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="File content is not a valid PDF")
    if suffix == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(
            status_code=422, detail="File content is not a valid DOCX archive"
        )
    if suffix == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=422, detail="Text CV must use UTF-8"
            ) from exc

    stored_name = f"{user.id}-{uuid4().hex}{suffix}"
    destination = settings.cv_storage_path / stored_name
    try:
        settings.cv_storage_path.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="CV storage is unavailable. Keep your original and retry later.",
        ) from exc

    document = CVDocument(
        user_id=user.id,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        career_track=career_track,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


@router.get("", response_model=list[CVResponse])
async def list_cvs(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CVDocument]:
    result = await session.scalars(
        select(CVDocument)
        .where(CVDocument.user_id == user.id)
        .order_by(CVDocument.created_at.desc())
    )
    return list(result)
