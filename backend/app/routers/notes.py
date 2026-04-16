from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.note import Note
from app.models.slot import Slot
from app.models.user import User
from app.schemas.note import (
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)

router = APIRouter()


def _to_response(n: Note) -> NoteResponse:
    return NoteResponse(
        id=str(n.id),
        tenant_id=str(n.tenant_id),
        user_id=str(n.user_id) if n.user_id else None,
        slot_id=str(n.slot_id),
        content=n.content,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


@router.get("", response_model=NoteListResponse)
async def list_notes(
    slot_id: UUID | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    query = select(Note).where(Note.tenant_id == user.tenant_id)
    if slot_id:
        query = query.where(Note.slot_id == slot_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Note.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    notes = result.scalars().all()

    return NoteListResponse(items=[_to_response(n) for n in notes], total=total)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
async def create_note(
    body: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot add notes")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    slot_result = await db.execute(
        select(Slot).where(Slot.id == UUID(body.slot_id), Slot.tenant_id == user.tenant_id)
    )
    if slot_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    note = Note(
        tenant_id=user.tenant_id,
        user_id=user.id,
        slot_id=UUID(body.slot_id),
        content=body.content,
    )
    db.add(note)
    await db.flush()

    return _to_response(note)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: UUID,
    body: NoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.tenant_id == user.tenant_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if user.role not in ("super_admin", "tenant_admin") and note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only edit your own notes")

    note.content = body.content
    await db.flush()

    return _to_response(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Note).where(Note.id == note_id, Note.tenant_id == user.tenant_id))
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if user.role not in ("super_admin", "tenant_admin") and note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only delete your own notes")

    await db.delete(note)
    await db.flush()
