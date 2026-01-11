import duckdb
import time
from typing import List, Dict, Any, Tuple
from datetime import date, datetime
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor


class SQLExecutor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _create_connection(self):
        return duckdb.connect(":memory:")

    def _setup_schema(self, conn: duckdb.DuckDBPyConnection, schema_definition: dict):
        tables = schema_definition.get("tables", [])
        for table in tables:
            table_name = table.get("name", "unknown")
            columns = table.get("columns", [])

            column_defs = []
            constraints = []

            for col in columns:
                if "type" not in col:
                    if "name" in col:
                        constraints.append(col["name"])
                    continue

                col_def = f"{col['name']} {col['type']}"
                if "constraints" in col and col["constraints"]:
                    col_def += f" {col['constraints']}"
                column_defs.append(col_def)

            all_defs = column_defs + constraints
            create_table_sql = f"CREATE TABLE {table_name} ({', '.join(all_defs)})"
            conn.execute(create_table_sql)

    def _insert_data(
        self, conn: duckdb.DuckDBPyConnection, data: Dict[str, List[Dict[str, Any]]]
    ):
        for table_name, rows in data.items():
            if not rows:
                continue

            for row in rows:
                columns = list(row.keys())
                values = [row[col] for col in columns]

                placeholders = ", ".join(["?" for _ in values])
                columns_str = ", ".join(columns)

                insert_sql = (
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                )
                conn.execute(insert_sql, values)

    def _execute_query(
        self, conn: duckdb.DuckDBPyConnection, query: str
    ) -> List[Dict[str, Any]]:
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]

        return [dict(zip(columns, row)) for row in result]

    def _normalize_result(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not result:
            return []

        normalized = []
        for row in result:
            normalized_row = {}
            for key, value in row.items():
                if isinstance(value, (date, datetime)):
                    normalized_row[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    float_value = float(value)
                    if float_value.is_integer():
                        normalized_row[key] = int(float_value)
                    else:
                        normalized_row[key] = round(float_value, 6)
                elif isinstance(value, float):
                    if value.is_integer():
                        normalized_row[key] = int(value)
                    else:
                        normalized_row[key] = round(value, 6)
                else:
                    normalized_row[key] = value
            normalized.append(normalized_row)

        return normalized

    def _compare_results(
        self, expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]
    ) -> bool:
        if len(expected) != len(actual):
            return False

        expected_normalized = self._normalize_result(expected)
        actual_normalized = self._normalize_result(actual)

        expected_sorted = sorted(
            expected_normalized, key=lambda x: str(sorted(x.items()))
        )
        actual_sorted = sorted(actual_normalized, key=lambda x: str(sorted(x.items())))

        return expected_sorted == actual_sorted

    def _execute_single_test(
        self, query: str, schema_definition: dict, test_case: dict
    ) -> dict:
        conn = self._create_connection()

        try:
            self._setup_schema(conn, schema_definition)
            self._insert_data(conn, test_case["input_data"])

            actual_result = self._execute_query(conn, query)
            expected_result = test_case["expected_output"]

            passed = self._compare_results(expected_result, actual_result)

            normalized_actual = self._normalize_result(actual_result)

            return {
                "test_name": test_case["name"],
                "passed": passed,
                "expected": expected_result,
                "actual": normalized_actual,
                "error": None,
            }

        except Exception as e:
            return {
                "test_name": test_case["name"],
                "passed": False,
                "expected": test_case["expected_output"],
                "actual": None,
                "error": str(e),
            }

        finally:
            conn.close()

    async def execute_and_test(
        self, query: str, schema_definition: dict, test_cases: List[dict]
    ) -> Tuple[List[dict], float, str]:
        start_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    self.executor,
                    self._execute_single_test,
                    query,
                    schema_definition,
                    test_case,
                )
                for test_case in test_cases
            ]

            test_results = await asyncio.gather(*tasks)

            execution_time = time.time() - start_time
            return list(test_results), execution_time, None

        except Exception as e:
            execution_time = time.time() - start_time
            return [], execution_time, str(e)


executor = SQLExecutor()
