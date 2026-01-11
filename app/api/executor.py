from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, cast
from app.database import get_db
from app.models import Challenge, Submission
from app.schemas import ExecuteQueryRequest, ExecuteQueryResponse, TestResult
from app.services.sql_executor import executor
from app.config import settings

router = APIRouter()


@router.post("/execute", response_model=ExecuteQueryResponse)
async def execute_query(request: ExecuteQueryRequest, db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.id == request.challenge_id).first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    schema_definition = cast(Dict[str, Any], challenge.schema_definition)
    test_cases = cast(List[Dict[str, Any]], challenge.test_cases)

    try:
        test_results_raw, execution_time, error = await executor.execute_and_test(
            query=request.query,
            schema_definition=schema_definition,
            test_cases=test_cases,
        )

        if error:
            submission = Submission(
                challenge_id=request.challenge_id,
                user_id=settings.ADMIN_USER_ID,
                query=request.query,
                status="failed",
                passed_tests=0,
                total_tests=len(test_cases),
                execution_time=execution_time,
                error_message=error,
                test_results=[],
            )
            db.add(submission)
            db.commit()

            return ExecuteQueryResponse(
                status="failed",
                passed_tests=0,
                total_tests=len(test_cases),
                execution_time=execution_time,
                test_results=[],
                error_message=error,
            )

        test_results = [TestResult(**result) for result in test_results_raw]
        passed_tests = sum(1 for result in test_results if result.passed)
        total_tests = len(test_results)
        status = "solved" if passed_tests == total_tests else "failed"

        submission = Submission(
            challenge_id=request.challenge_id,
            user_id=settings.ADMIN_USER_ID,
            query=request.query,
            status=status,
            passed_tests=passed_tests,
            total_tests=total_tests,
            execution_time=execution_time,
            test_results=test_results_raw,
        )
        db.add(submission)
        db.commit()

        return ExecuteQueryResponse(
            status=status,
            passed_tests=passed_tests,
            total_tests=total_tests,
            execution_time=execution_time,
            test_results=test_results,
            error_message=None,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения: {str(e)}")
