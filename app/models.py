from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Float
from datetime import datetime
from app.database import Base
import enum


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChallengeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    SOLVED = "solved"
    FAILED = "failed"


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)
    topics = Column(JSON, nullable=False)
    schema_definition = Column(JSON, nullable=False)
    sample_data = Column(JSON, nullable=False)
    expected_output = Column(JSON, nullable=False)
    solution_query = Column(Text, nullable=False)
    test_cases = Column(JSON, nullable=False)
    hints = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, default=1)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, nullable=False)
    user_id = Column(Integer, default=1)
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    execution_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    test_results = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, nullable=False)
    user_id = Column(Integer, default=1)
    query = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
