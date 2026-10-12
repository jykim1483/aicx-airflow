"""PostgreSQL 공통 연결 모듈."""

from __future__ import annotations

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
        # todo : airflow connection 등록 필요
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

    def select(self, sql: str, parameters: tuple | None = None) -> list[tuple]:
        """SELECT SQL을 실행하고 결과를 반환한다."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            return cursor.fetchall()

    def insert(self, sql: str, rows: list[tuple]) -> int:
        """INSERT 작업을 수행한다. batch insert 구현은 후속 단계에서 추가한다."""
        # TODO: psycopg2.extras.execute_values로 batch insert
        raise NotImplementedError

    def merge(self, sql: str, parameters: tuple | None = None) -> None:
        """UPSERT/MERGE SQL을 실행한다."""
        # TODO: transaction, commit/rollback, idempotency 정책 적용
        raise NotImplementedError

    def close(self) -> None:
        """PostgreSQL connection을 종료한다."""
        if self.connection is not None:
            self.connection.close()
        self.connection = None
