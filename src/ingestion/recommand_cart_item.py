from __future__ import annotations

import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import yaml

if not __package__:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    from src.common.clickhouse import ClickHouseConnection
    from src.common.mongodb import MongoDBConnection
except ModuleNotFoundError:
    from common.clickhouse import ClickHouseConnection
    from common.mongodb import MongoDBConnection


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_CONFIG_PATH = PROJECT_ROOT / "configs" / "database.example.yaml"
CLICKHOUSE_TEST_SQL_PATH = PROJECT_ROOT / "sql" / "dl" / "clickhouse_connection_test.sql"
DEFAULT_ENVIRONMENT = "prod"
DEFAULT_MONGODB_CONNECTION_NAME = "G2_MongoDB_Recom"
DEFAULT_CLICKHOUSE_CONNECTION_NAME = "groobee"
DEFAULT_COLLECTION = "Cart.0fc41973695d406784c04e121a04cb64"


def load_database_config(
    db_type: str,
    connection_name: str,
    environment: str = DEFAULT_ENVIRONMENT,
    config_path: Path = DATABASE_CONFIG_PATH,
) -> dict[str, Any]:
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    return config[environment][db_type][connection_name]


def load_sql(sql_path: Path) -> str:
    return sql_path.read_text(encoding="utf-8").strip()


def select_recommand_cart_item(
    collection: str = DEFAULT_COLLECTION,
    query: Mapping[str, Any] | None = None,
    projection: Mapping[str, Any] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """MongoDB cart item 데이터 조회"""
    logger.info("select mongodb collection=%s limit=%s", collection, limit)
    mongo = MongoDBConnection(
        load_database_config("mongodb", DEFAULT_MONGODB_CONNECTION_NAME)
    )
    try:
        rows = mongo.select(
            collection=collection,
            query=query,
            projection=projection,
            limit=limit,
        )
        logger.info("selected rows=%s", len(rows))
        return rows
    finally:
        mongo.close()


def flatten_document(
    document: Mapping[str, Any],
    prefix: str = "",
) -> dict[str, Any]:
    flattened = {}
    for key, value in document.items():
        field_name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(flatten_document(value, field_name))
        else:
            flattened[field_name] = value
    return flattened


def sample_mongodb_schema(
    collection: str = DEFAULT_COLLECTION,
    query: Mapping[str, Any] | None = None,
    limit: int = 100,
) -> dict[str, set[str]]:
    """MongoDB 샘플 문서 기준으로 필드별 Python 타입을 확인한다."""
    rows = select_recommand_cart_item(
        collection=collection,
        query=query,
        limit=limit,
    )
    schema: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        for field_name, value in flatten_document(row).items():
            schema[field_name].add(type(value).__name__)

    for field_name in sorted(schema):
        logger.info("field=%s types=%s", field_name, sorted(schema[field_name]))

    return dict(schema)


def test_clickhouse_connection() -> None:
    sql = load_sql(CLICKHOUSE_TEST_SQL_PATH)
    clickhouse = ClickHouseConnection(
        load_database_config("clickhouse", DEFAULT_CLICKHOUSE_CONNECTION_NAME)
    )
    try:
        result = clickhouse.execute(sql)
        logger.info("clickhouse connected result=%s", result)
    finally:
        clickhouse.close()

# todo : 클릭하우스 테이블생성/적재

if __name__ == "__main__":

    mongo_query = {}
    schema = sample_mongodb_schema(
        collection=DEFAULT_COLLECTION,
        query=mongo_query,
        limit=100,
    )
    logger.info("sample schema fields=%s", len(schema))
    test_clickhouse_connection()
