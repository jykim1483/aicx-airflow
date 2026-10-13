"""ClickHouse 공통 연결 모듈."""

from pathlib import Path
from typing import Any, Mapping

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None


class ClickHouseConnection:
    """clickhouse-connect 기반 ClickHouse 공통 클래스."""

    def __init__(self, connection_config: Mapping[str, Any] | None = None) -> None:
        self.connection_config = connection_config or {}
        self.client = None

    def connect(self) -> None:
        """ClickHouse client를 생성한다."""
        if clickhouse_connect is None:
            raise RuntimeError("clickhouse-connect is not installed")

        self.client = clickhouse_connect.get_client(
            host=self.connection_config.get("host", "localhost"),
            port=int(self.connection_config.get("port", 8123)),
            username=self.connection_config.get("username", "default"),
            password=self.connection_config.get("password", ""),
            database=self.connection_config.get("database", "default"),
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
        parameters: Mapping[str, Any] | None = None,
    ) -> Any:
        """DDL/DML SQL을 실행한다."""
        if self.client is None:
            self.connect()
        return self.client.command(self._resolve_sql(sql), parameters=parameters)


    def close(self) -> None:
        """ClickHouse 연결을 종료한다."""
        if self.client is not None and hasattr(self.client, "close"):
            self.client.close()
        self.client = None
