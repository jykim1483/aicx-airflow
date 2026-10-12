"""ClickHouse 공통 연결 모듈."""

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

    def execute(self, sql: str, parameters: Mapping[str, Any] | None = None) -> Any:
        """DDL/DML SQL을 실행한다."""
        if self.client is None:
            self.connect()
        return self.client.command(sql, parameters=parameters)

    # def select(
    #     self,
    #     sql: str,
    #     parameters: Mapping[str, Any] | None = None,
    # ) -> list[tuple[Any, ...]]:
    #     """SELECT SQL을 실행하고 row 목록을 반환한다."""
    #     if self.client is None:
    #         self.connect()
    #     result = self.client.query(sql, parameters=parameters)
    #     return result.result_rows
    #
    # def create_database(self, database: str) -> None:
    #     """Database를 생성한다."""
    #     self.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    #
    # def create_table(self, sql: str) -> None:
    #     """CREATE TABLE SQL을 실행한다."""
    #     self.execute(sql)

    def close(self) -> None:
        """ClickHouse 연결을 종료한다."""
        if self.client is not None and hasattr(self.client, "close"):
            self.client.close()
        self.client = None
