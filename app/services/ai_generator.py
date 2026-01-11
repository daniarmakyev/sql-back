from openai import AsyncOpenAI
from app.config import settings
import json
import logging
from app.services.sql_executor import executor
import asyncio
from typing import Dict, Any, List

logging.basicConfig(level=logging.ERROR)

client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)

SYSTEM_PROMPT = """You are an expert SQL educator creating practice challenges.

CRITICAL: Return ONLY valid JSON with no additional text, no markdown formatting, no ```json blocks.

IMPORTANT RULES:
1. ALL table names, column names, and SQL keywords MUST be in ENGLISH - NO Cyrillic/Russian characters in schema or queries
2. Only descriptive text (title, description, hints, test names) should be in Russian
3. First design solution_query, then create test cases where expected_output is EXACTLY what solution_query returns for input_data
4. For EACH test case: mentally execute solution_query on input_data step-by-step and write that exact result as expected_output
5. Column names in expected_output must EXACTLY match solution_query SELECT clause
6. NEVER use NULL values in test_cases or sample_data - use 0 for numbers, empty string "" for text instead
7. Ensure all input_data only contain keys (columns) that exist in the schema_definition.tables.columns
8. Use appropriate column types: INTEGER for 32-bit, BIGINT for 64-bit, UBIGINT for unsigned 64-bit
9. Ensure all numeric values fit the column type without overflow
10. Description must accurately describe EXACTLY what solution_query does
11. Make tasks interesting and real-world: e-commerce, healthcare, environmental monitoring scenarios
12. CRITICAL: At least 50% of test cases MUST return non-empty results - avoid overly restrictive WHERE/HAVING conditions
13. Keep queries practical - avoid complex nested subqueries in HAVING clauses that filter out most data

NAMING CONVENTION EXAMPLES:
✓ CORRECT: table name "sales", column "manager_id", "total_amount"
✗ WRONG: table name "продажи", column "id_менеджера", "сумма"

CONCRETE EXAMPLES:

Example 1 - CORRECT test case:
solution_query: "SELECT id, total FROM orders WHERE total > (SELECT AVG(total) FROM orders)"
input_data: orders = [{"id": 1, "total": 10}, {"id": 2, "total": 20}, {"id": 3, "total": 30}]
Step 1: AVG(total) = 20
Step 2: Filter WHERE total > 20
expected_output: [{"id": 3, "total": 30}] ✓ CORRECT

Example 2 - CORRECT without NULL:
solution_query: "SELECT u.name, COUNT(o.id) as cnt FROM users u LEFT JOIN orders o ON u.id=o.user_id GROUP BY u.name"
input_data: users=[{"id":1,"name":"Anna"}], orders=[]
Step 1: LEFT JOIN produces empty match
Step 2: COUNT(o.id) = 0
expected_output: [{"name": "Anna", "cnt": 0}] ✓ CORRECT

Example 3 - CORRECT average comparison:
solution_query: "SELECT id, val FROM items WHERE val > (SELECT AVG(val) FROM items)"
input_data: items = [{"id": 1, "val": 10}, {"id": 2, "val": 20}, {"id": 3, "val": 30}]
Step 1: Calculate AVG(val) = (10+20+30)/3 = 20
Step 2: Filter WHERE val > 20
expected_output: [{"id": 3, "val": 30}] ✓ CORRECT (only 30 > 20)

Example 4 - WRONG average comparison:
solution_query: "SELECT id, val FROM items WHERE val > (SELECT AVG(val) FROM items)"
input_data: items = [{"id": 1, "val": 10}, {"id": 2, "val": 20}]
expected_output: [{"id": 2, "val": 20}] ✗ WRONG
Correct: AVG = 15, so 20 > 15 is true, but also val=10 is NOT > 15
expected_output: [{"id": 2, "val": 20}] ✓ CORRECT

Follow these rules for hints and test cases:
- **Test Cases**: Minimum 10 diverse test cases: empty tables, edge cases, typical cases. NO NULL values anywhere.
- **Hints**:
  - **easy**: No hints (empty array [])
  - **medium**: 2 subtle micro-hints
  - **hard**: 4 subtle micro-hints
- **Task Uniqueness**: Generate creative, unique tasks with unusual table/column names (in English)

Response format:
{
  "title": "Краткое название задачи (Russian)",
  "description": "Детальное описание задачи (Russian)",
  "schema_definition": {
    "tables": [
      {
        "name": "table_name (English)",
        "columns": [
          {"name": "column_name (English)", "type": "INTEGER|BIGINT|UBIGINT|TEXT|REAL|DATE", "constraints": "PRIMARY KEY|NOT NULL|UNIQUE"}
        ]
      }
    ]
  },
  "sample_data": {
    "table_name": [
      {"column1": "value1", "column2": 123}
    ]
  },
  "expected_output": [
    {"column1": "value1", "column2": 123}
  ],
  "solution_query": "SELECT column1, column2 FROM table_name WHERE condition (English SQL)",
  "test_cases": [
    {
      "name": "Тест 1: описание (Russian)",
      "input_data": {
        "table_name": [
          {"column1": "value1", "column2": 123}
        ]
      },
      "expected_output": [
        {"column1": "result1", "column2": 456}
      ]
    }
  ],
  "hints": ["Подсказка (Russian)"]
}"""


def has_null_values(data):
    if isinstance(data, dict):
        for value in data.values():
            if value is None or has_null_values(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if item is None or has_null_values(item):
                return True
    return False


async def generate_challenge(difficulty: str, topics: list[str]) -> Dict[str, Any]:
    if settings.GROQ_API_KEY == "test_key":
        return {
            "title": f"Тестовая задача по {', '.join(topics)} ({difficulty})",
            "description": f"Это тестовая задача сложности {difficulty} по темам: {', '.join(topics)}. Напишите SQL запрос для получения нужных данных.",
            "schema_definition": {
                "tables": [
                    {
                        "name": "users",
                        "columns": [
                            {
                                "name": "id",
                                "type": "INTEGER",
                                "constraints": "PRIMARY KEY",
                            },
                            {"name": "name", "type": "TEXT", "constraints": "NOT NULL"},
                            {"name": "age", "type": "INTEGER"},
                        ],
                    },
                    {
                        "name": "orders",
                        "columns": [
                            {
                                "name": "id",
                                "type": "INTEGER",
                                "constraints": "PRIMARY KEY",
                            },
                            {"name": "user_id", "type": "INTEGER"},
                            {"name": "product", "type": "TEXT"},
                            {"name": "amount", "type": "REAL"},
                        ],
                    },
                ]
            },
            "sample_data": {
                "users": [
                    {"id": 1, "name": "Иван", "age": 25},
                    {"id": 2, "name": "Мария", "age": 30},
                    {"id": 3, "name": "Алексей", "age": 28},
                ],
                "orders": [
                    {"id": 1, "user_id": 1, "product": "Книга", "amount": 500.00},
                    {"id": 2, "user_id": 2, "product": "Ноутбук", "amount": 50000.00},
                    {"id": 3, "user_id": 1, "product": "Ручка", "amount": 50.00},
                ],
            },
            "expected_output": [
                {"user_name": "Мария", "total_orders": 1, "total_amount": 50000.00},
                {"user_name": "Иван", "total_orders": 2, "total_amount": 550.00},
                {"user_name": "Алексей", "total_orders": 0, "total_amount": 0},
            ],
            "solution_query": "SELECT u.name as user_name, COUNT(o.id) as total_orders, COALESCE(SUM(o.amount), 0) as total_amount FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY total_amount DESC",
            "test_cases": [
                {
                    "name": "Основной тест",
                    "input_data": {
                        "users": [
                            {"id": 1, "name": "Иван", "age": 25},
                            {"id": 2, "name": "Мария", "age": 30},
                        ],
                        "orders": [
                            {
                                "id": 1,
                                "user_id": 1,
                                "product": "Книга",
                                "amount": 500.00,
                            },
                            {
                                "id": 2,
                                "user_id": 2,
                                "product": "Ноутбук",
                                "amount": 50000.00,
                            },
                            {
                                "id": 3,
                                "user_id": 1,
                                "product": "Ручка",
                                "amount": 50.00,
                            },
                        ],
                    },
                    "expected_output": [
                        {
                            "user_name": "Мария",
                            "total_orders": 1,
                            "total_amount": 50000.00,
                        },
                        {
                            "user_name": "Иван",
                            "total_orders": 2,
                            "total_amount": 550.00,
                        },
                    ],
                },
                {
                    "name": "Пользователь без заказов",
                    "input_data": {
                        "users": [{"id": 1, "name": "Петр", "age": 40}],
                        "orders": [],
                    },
                    "expected_output": [
                        {"user_name": "Петр", "total_orders": 0, "total_amount": 0}
                    ],
                },
                {
                    "name": "Несколько пользователей, один без заказов",
                    "input_data": {
                        "users": [
                            {"id": 1, "name": "Анна", "age": 22},
                            {"id": 2, "name": "Олег", "age": 35},
                        ],
                        "orders": [
                            {
                                "id": 1,
                                "user_id": 1,
                                "product": "Телефон",
                                "amount": 25000.00,
                            }
                        ],
                    },
                    "expected_output": [
                        {
                            "user_name": "Анна",
                            "total_orders": 1,
                            "total_amount": 25000.00,
                        },
                        {"user_name": "Олег", "total_orders": 0, "total_amount": 0},
                    ],
                },
                {
                    "name": "Пустые таблицы",
                    "input_data": {"users": [], "orders": []},
                    "expected_output": [],
                },
                {
                    "name": "Заказы без пользователей",
                    "input_data": {
                        "users": [],
                        "orders": [
                            {
                                "id": 1,
                                "user_id": 99,
                                "product": "Странный заказ",
                                "amount": 100.00,
                            }
                        ],
                    },
                    "expected_output": [],
                },
            ],
            "hints": [],
        }

    topics_str = ", ".join(topics)

    user_prompt = f"""Create a SQL practice challenge with these parameters:
- Difficulty: {difficulty}
- Topics: {topics_str}

CRITICAL NAMING RULES:
- ALL table names and column names MUST be in ENGLISH (e.g., "sales", "manager_id", "total_amount")
- NO Russian/Cyrillic in table names, column names, or SQL queries
- Russian ONLY for: title, description, hints, test case names

MANDATORY WORKFLOW:
1. Design solution_query first (using English table/column names)
2. Create input_data for each test case
3. CRITICAL: For EACH test case, execute solution_query MANUALLY step-by-step:
   a. Write down all intermediate calculations (AVG, SUM, COUNT, etc.)
   b. Apply WHERE/HAVING filters with exact values
   c. Write ONLY the rows that pass all conditions as expected_output
   d. Double-check: re-execute mentally to verify
4. Common mistakes to AVOID:
   - DO NOT guess expected_output
   - DO NOT include rows that don't match WHERE/HAVING conditions
   - DO NOT forget that > means strictly greater (20 is NOT > 20)
   - DO NOT use different logic in expected_output than in solution_query
5. NEVER use NULL values - use 0 for numbers, "" for text
6. Ensure numeric values fit column types
7. Create 10+ diverse test cases where at least 50% return non-empty results
8. Use creative English table/column names
9. Use Russian for title, description, hints, test names
10. Base task on real-world scenarios

Return ONLY the JSON object with no additional text."""

    max_retries = 5
    last_error = None

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7 if attempt == 0 else 0.5,
                max_tokens=6000,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            try:
                challenge_data = json.loads(content)
            except json.JSONDecodeError as parse_e:
                logging.error(f"Invalid JSON content: {content}")
                raise parse_e

            required_fields = [
                "title",
                "description",
                "schema_definition",
                "sample_data",
                "expected_output",
                "solution_query",
                "test_cases",
                "hints",
            ]
            if not all(field in challenge_data for field in required_fields):
                last_error = "Отсутствуют обязательные поля в ответе"
                continue

            if len(challenge_data.get("test_cases", [])) < 10:
                last_error = f"Недостаточно тест-кейсов: {len(challenge_data.get('test_cases', []))}/10"
                continue

            if difficulty == "easy" and len(challenge_data.get("hints", [])) > 0:
                challenge_data["hints"] = []

            if has_null_values(challenge_data.get("test_cases", [])):
                last_error = "Test cases содержат NULL значения"
                continue

            if has_null_values(challenge_data.get("sample_data", {})):
                last_error = "Sample data содержит NULL значения"
                continue

            schema_columns = {}
            schema_types = {}
            for table in challenge_data["schema_definition"]["tables"]:
                schema_columns[table["name"]] = [
                    col["name"] for col in table["columns"]
                ]
                schema_types[table["name"]] = {
                    col["name"]: col["type"] for col in table["columns"]
                }

            for test_case in challenge_data["test_cases"]:
                for table_name, rows in test_case["input_data"].items():
                    if rows:
                        for row in rows:
                            extra_cols = set(row.keys()) - set(
                                schema_columns.get(table_name, [])
                            )
                            if extra_cols:
                                raise ValueError(
                                    f"Extra columns in test case: {extra_cols}"
                                )
                            for col, val in row.items():
                                col_type = schema_types[table_name].get(col)
                                if col_type in [
                                    "INTEGER",
                                    "BIGINT",
                                    "UBIGINT",
                                ] and isinstance(val, (int, float)):
                                    if col_type == "INTEGER" and not (
                                        -(2**31) <= val <= 2**31 - 1
                                    ):
                                        raise ValueError(f"Overflow for INTEGER: {val}")
                                    if col_type == "BIGINT" and not (
                                        -(2**63) <= val <= 2**63 - 1
                                    ):
                                        raise ValueError(f"Overflow for BIGINT: {val}")
                                    if col_type == "UBIGINT" and not (
                                        0 <= val <= 2**64 - 1
                                    ):
                                        raise ValueError(f"Overflow for UBIGINT: {val}")

            schema_def = challenge_data["schema_definition"]
            failed_tests = []
            for test in challenge_data["test_cases"]:
                try:
                    results, _, err = await executor.execute_and_test(
                        challenge_data["solution_query"],
                        schema_def,
                        [test],
                    )
                    if err:
                        failed_tests.append(f"{test['name']}: execution error - {err}")
                    elif not results[0]["passed"]:
                        actual = results[0].get("actual_output", "unknown")
                        expected = test.get("expected_output", "unknown")
                        failed_tests.append(
                            f"{test['name']}: expected {expected}, got {actual}"
                        )
                except Exception as ve:
                    failed_tests.append(f"{test['name']}: {str(ve)}")

            if failed_tests:
                last_error = f"Tests failed: {'; '.join(failed_tests[:3])}"
                continue

            for table_name, rows in challenge_data["sample_data"].items():
                if rows:
                    for row in rows:
                        extra_cols = set(row.keys()) - set(
                            schema_columns.get(table_name, [])
                        )
                        if extra_cols:
                            raise ValueError(
                                f"Extra columns in sample_data: {extra_cols}"
                            )

            return challenge_data

        except json.JSONDecodeError as e:
            last_error = (
                f"Ошибка парсинга JSON (попытка {attempt + 1}/{max_retries}): {str(e)}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
        except ValueError as ve:
            last_error = f"Validation error: {str(ve)}"
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
        except Exception as e:
            last_error = f"Ошибка API (попытка {attempt + 1}/{max_retries}): {str(e)}"
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue

    raise ValueError(
        f"Не удалось сгенерировать задачу после {max_retries} попыток. Последняя ошибка: {last_error}"
    )
