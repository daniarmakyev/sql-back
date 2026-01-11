from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import Challenge, Submission
from app.schemas import HistoryItemResponse, HistoryStatsResponse, SubmissionResponse
from app.config import settings
from typing import List, Optional

router = APIRouter()


@router.get("/submissions", response_model=List[HistoryItemResponse])
async def get_submission_history(
    difficulty: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(
        Submission, Challenge.title, Challenge.difficulty, Challenge.topics
    ).join(Challenge, Submission.challenge_id == Challenge.id)

    query = query.filter(Submission.user_id == settings.ADMIN_USER_ID)

    if difficulty:
        query = query.filter(Challenge.difficulty == difficulty)

    if topic:
        query = query.filter(Challenge.topics.contains([topic]))

    if status:
        query = query.filter(Submission.status == status)

    query = query.order_by(desc(Submission.submitted_at))
    query = query.limit(limit).offset(offset)

    results = query.all()

    history_items = []
    for submission, title, difficulty, topics in results:
        history_items.append(
            HistoryItemResponse(
                id=submission.id,
                challenge_id=submission.challenge_id,
                challenge_title=title,
                difficulty=difficulty,
                topics=topics,
                status=submission.status,
                passed_tests=submission.passed_tests,
                total_tests=submission.total_tests,
                submitted_at=submission.submitted_at,
            )
        )

    return history_items


@router.get("/stats", response_model=HistoryStatsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    total_submissions = (
        db.query(Submission)
        .filter(Submission.user_id == settings.ADMIN_USER_ID)
        .count()
    )

    solved_count = (
        db.query(Submission)
        .filter(
            Submission.user_id == settings.ADMIN_USER_ID, Submission.status == "solved"
        )
        .count()
    )

    by_difficulty = {}
    difficulty_stats = (
        db.query(Challenge.difficulty, func.count(Submission.id))
        .join(Challenge, Submission.challenge_id == Challenge.id)
        .filter(
            Submission.user_id == settings.ADMIN_USER_ID, Submission.status == "solved"
        )
        .group_by(Challenge.difficulty)
        .all()
    )

    for diff, count in difficulty_stats:
        by_difficulty[diff] = count

    by_topic = {}
    topic_submissions = (
        db.query(Challenge.topics, Submission.status)
        .join(Submission, Challenge.id == Submission.challenge_id)
        .filter(Submission.user_id == settings.ADMIN_USER_ID)
        .all()
    )

    for topics, status in topic_submissions:
        if status == "solved":
            for topic in topics:
                by_topic[topic] = by_topic.get(topic, 0) + 1

    success_rate = (
        (solved_count / total_submissions * 100) if total_submissions > 0 else 0.0
    )

    return HistoryStatsResponse(
        total_solved=solved_count,
        total_attempted=total_submissions,
        by_difficulty=by_difficulty,
        by_topic=by_topic,
        success_rate=round(success_rate, 2),
    )


@router.get(
    "/challenges/{challenge_id}/submissions", response_model=List[SubmissionResponse]
)
async def get_challenge_submissions(challenge_id: int, db: Session = Depends(get_db)):
    submissions = (
        db.query(Submission)
        .filter(
            Submission.challenge_id == challenge_id,
            Submission.user_id == settings.ADMIN_USER_ID,
        )
        .order_by(desc(Submission.submitted_at))
        .all()
    )

    return submissions
