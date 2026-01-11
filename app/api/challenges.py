from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Challenge, Submission
from app.schemas import (
    GenerateChallengeRequest,
    ChallengeResponse,
    ChallengeCreateRequest,
)
from app.services.ai_generator import generate_challenge
from app.config import settings

router = APIRouter()


@router.post("/preview")
async def preview_challenge(request: GenerateChallengeRequest):
    try:
        challenge_data = await generate_challenge(
            difficulty=request.difficulty, topics=request.topics
        )
        return challenge_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка генерации задачи: {str(e)}"
        )


@router.post("/approve", response_model=ChallengeResponse)
async def approve_challenge(
    request: ChallengeCreateRequest, db: Session = Depends(get_db)
):
    try:
        test_cases_dict = [test_case.dict() for test_case in request.test_cases]

        challenge = Challenge(
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            topics=request.topics,
            schema_definition=request.schema_definition,
            sample_data=request.sample_data,
            expected_output=request.expected_output,
            solution_query=request.solution_query,
            test_cases=test_cases_dict,
            hints=request.hints or [],
            user_id=settings.ADMIN_USER_ID,
        )

        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        submission = Submission(
            challenge_id=challenge.id,
            user_id=settings.ADMIN_USER_ID,
            query=request.solution_query,
            status="accepted",
            passed_tests=len(test_cases_dict),
            total_tests=len(test_cases_dict),
            execution_time=0.0,
            test_results=[],
        )
        db.add(submission)
        db.commit()

        return challenge

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка сохранения задачи: {str(e)}"
        )


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return challenge
