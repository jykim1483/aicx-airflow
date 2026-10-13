import sys
from pathlib import Path
from typing import Any, Mapping

from bson import json_util, ObjectId

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.common.clickhouse import ClickHouseConnection
from src.common.config import PROJECT_ROOT, load_database_config, load_sql
from src.common.logger import get_logger
from src.common.mongodb import MongoDBConnection


logger = get_logger(__name__)

CLICKHOUSE_TABLE_DDL_PATH = PROJECT_ROOT / "sql" / "ddl" / "create_recommand_cart_item.sql"
CLICKHOUSE_INSERT_SQL_PATH = PROJECT_ROOT / "sql" / "dml" / "insert_recommand_cart_item.sql"
MONGODB_CONNECTION_NAME = "G2_MongoDB_Recom"
DEFAULT_CLICKHOUSE_CONNECTION_NAME = "groobee"
COLLECTION = "Cart.0fc41973695d406784c04e121a04cb64"
DEFAULT_COLLECTION = COLLECTION
DEFAULT_QUERY: dict[str, Any] = {
    # "_id": ObjectId("6a571046ba0b69612f31d62f"),
}
CLICKHOUSE_DATABASE = "groobee_dev"
CLICKHOUSE_TABLE = "recommand_cart_item_raw"


def convert_clickhouse_row(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(document.get("_id")),
        "reg_dtm": document.get("regDtm"),
        "raw_json": json_util.dumps(document, ensure_ascii=False),
    }


def load_mongodb_to_clickhouse():

    try:
        clickhouse = ClickHouseConnection(
            load_database_config("clickhouse", DEFAULT_CLICKHOUSE_CONNECTION_NAME)
        )
        clickhouse.execute(load_sql(CLICKHOUSE_TABLE_DDL_PATH))

        mongo = MongoDBConnection(
            load_database_config("mongodb", MONGODB_CONNECTION_NAME)
        )

        rows = mongo.select(
            collection=DEFAULT_COLLECTION,
            query=DEFAULT_QUERY,
            projection=None,
            limit=1

        )
        logger.info("selected rows=%s", (rows))

        for row in rows:
            clickhouse.execute(load_sql(CLICKHOUSE_INSERT_SQL_PATH), convert_clickhouse_row(row))
        logger.info("inserted rows=%s", len(rows))
    except Exception as e :
        logger.info("!!!ERROR >> %s", e)


    finally:
        mongo.close()
        clickhouse.close()


if __name__ == "__main__":
    load_mongodb_to_clickhouse()
