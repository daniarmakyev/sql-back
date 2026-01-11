from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class GenerateChallengeRequest(BaseModel):
    difficulty: str
    topics: List[str]


class TestCase(BaseModel):
    name: str
    input_data: Dict[str, List[Dict[str, Any]]]
    expected_output: List[Dict[str, Any]]


class ChallengeCreateRequest(BaseModel):
    title: str
    description: str
    difficulty: str
    topics: List[str]
    schema_definition: Dict[str, Any]
    sample_data: Dict[str, List[Dict[str, Any]]]
    expected_output: List[Dict[str, Any]]
    solution_query: str
    test_cases: List[TestCase]
    hints: Optional[List[str]] = None


class ChallengeResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    topics: List[str]
    schema_definition: Dict[str, Any]
    sample_data: Dict[str, List[Dict[str, Any]]]
    expected_output: List[Dict[str, Any]]
    test_cases: List[TestCase]
    hints: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecuteQueryRequest(BaseModel):
    challenge_id: int
    query: str


class TestResult(BaseModel):
    test_name: str
    passed: bool
    expected: List[Dict[str, Any]]
    actual: Optional[List[Dict[str, Any]]]
    error: Optional[str]


class ExecuteQueryResponse(BaseModel):
    status: str
    passed_tests: int
    total_tests: int
    execution_time: float
    test_results: List[TestResult]
    error_message: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: int
    challenge_id: int
    status: str
    passed_tests: int
    total_tests: int
    execution_time: Optional[float]
    submitted_at: datetime

    class Config:
        from_attributes = True


class HistoryItemResponse(BaseModel):
    id: int
    challenge_id: int
    challenge_title: str
    difficulty: str
    topics: List[str]
    status: str
    passed_tests: int
    total_tests: int
    submitted_at: datetime


class HistoryStatsResponse(BaseModel):
    total_solved: int
    total_attempted: int
    by_difficulty: Dict[str, int]
    by_topic: Dict[str, int]
    success_rate: float
