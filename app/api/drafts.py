from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Draft
from app.config import settings
from pydantic import BaseModel

router = APIRouter()


class DraftCreateRequest(BaseModel):
    challenge_id: int
    query: str


class DraftResponse(BaseModel):
    id: int
    challenge_id: int
    query: str

    class Config:
        from_attributes = True


@router.post("/save", response_model=DraftResponse)
async def save_draft(request: DraftCreateRequest, db: Session = Depends(get_db)):
    """Save or update draft for a challenge"""
    try:
        # Check if draft exists for this challenge and user
        existing_draft = (
            db.query(Draft)
            .filter(
                Draft.challenge_id == request.challenge_id,
                Draft.user_id == settings.ADMIN_USER_ID,
            )
            .first()
        )

        if existing_draft:
            # Update existing draft
            existing_draft.query = request.query
            db.commit()
            db.refresh(existing_draft)
            return existing_draft
        else:
            # Create new draft
            draft = Draft(
                challenge_id=request.challenge_id,
                user_id=settings.ADMIN_USER_ID,
                query=request.query,
            )
            db.add(draft)
            db.commit()
            db.refresh(draft)
            return draft

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка сохранения черновика: {str(e)}"
        )


@router.get("/{challenge_id}", response_model=DraftResponse)
async def get_draft(challenge_id: int, db: Session = Depends(get_db)):
    """Get draft for a challenge"""
    draft = (
        db.query(Draft)
        .filter(
            Draft.challenge_id == challenge_id,
            Draft.user_id == settings.ADMIN_USER_ID,
        )
        .first()
    )

    if not draft:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    return draft


@router.delete("/{challenge_id}")
async def delete_draft(challenge_id: int, db: Session = Depends(get_db)):
    """Delete draft for a challenge"""
    try:
        draft = (
            db.query(Draft)
            .filter(
                Draft.challenge_id == challenge_id,
                Draft.user_id == settings.ADMIN_USER_ID,
            )
            .first()
        )

        if draft:
            db.delete(draft)
            db.commit()
            return {"message": "Черновик удален"}

        raise HTTPException(status_code=404, detail="Черновик не найден")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка удаления черновика: {str(e)}"
        )
