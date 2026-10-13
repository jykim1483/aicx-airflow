"""PostgreSQL 공통 연결 모듈."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import psycopg2

try:
    from airflow.providers.postgres.hooks.postgres import PostgresHook
except ImportError:  # Airflow 외부 단위 테스트·로컬 실행 지원
    PostgresHook = None


class PostgreSQLConnection:
    """Airflow PostgresHook 또는 psycopg2를 통한 공통 PostgreSQL 클래스."""

    def __init__(self, connection_config: Mapping[str, Any]) -> None:
        self.connection_config = connection_config
        self.connection = None

    def connect(self) -> None:
        """PostgreSQL connection을 생성한다."""
        conn_id = self.connection_config.get("conn_id")
        if conn_id and PostgresHook is not None:
            self.connection = PostgresHook(postgres_conn_id=conn_id).get_conn()
            return

        # Airflow 외부 실행·단위 테스트용 직접 연결
        required = ("host", "database", "username", "password")
        missing = [key for key in required if not self.connection_config.get(key)]
        if missing:
            raise ValueError(f"Missing PostgreSQL config: {', '.join(missing)}")
        self.connection = psycopg2.connect(
            host=self.connection_config["host"],
            port=int(self.connection_config.get("port", 5432)),
            dbname=self.connection_config["database"],
            user=self.connection_config["username"],
            password=self.connection_config["password"],
        )

    def _resolve_sql(self, sql: str | Path) -> str:
        """SQL 문자열 또는 .sql 파일 경로를 실행 가능한 SQL 문자열로 변환한다."""
        if isinstance(sql, Path):
            return sql.read_text(encoding="utf-8").strip()

        sql_path = Path(sql)
        if sql_path.suffix == ".sql" and sql_path.exists():
            return sql_path.read_text(encoding="utf-8").strip()

        return sql

    def execute(
        self,
        sql: str | Path,
        parameters: tuple | Mapping[str, Any] | None = None,
    ) -> int:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(self._resolve_sql(sql), parameters)
            rowcount = cursor.rowcount
        self.connection.commit()
        return rowcount


    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
        self.connection = None
