"""MongoDB 공통 연결 모듈."""

from typing import Any, Iterable, Mapping

from pymongo import MongoClient

try:
    from airflow.providers.mongo.hooks.mongo import MongoHook
except ImportError:  # Airflow 외부 단위 테스트·로컬 실행 지원
    MongoHook = None


class MongoDBConnection:
    """Airflow MongoHook 또는 PyMongo를 통해 MongoDB를 사용하는 공통 클래스."""

    def __init__(self, connection_config: Mapping[str, Any]) -> None:
        self.connection_config = connection_config
        self.client = None
        self.database = None

    def connect(self) -> None:
        """MongoDB client와 database handle을 생성한다."""
        conn_id = self.connection_config.get("conn_id")
        database_name = self.connection_config["database"]

        # Airflow task에서는 Airflow Connection을 사용하는 것을 우선한다.
        if conn_id and MongoHook is not None:
            self.client = MongoHook(mongo_conn_id=conn_id).get_conn()
        else:
            # Airflow 외부 실행·단위 테스트에서는 직접 PyMongo 연결을 사용한다.
            uri = self.connection_config.get("uri")
            if uri:
                self.client = MongoClient(uri)
            else:
                self.client = MongoClient(
                    host=self.connection_config["host"],
                    port=int(self.connection_config.get("port", 27017)),
                    username=self.connection_config.get("username"),
                    password=self.connection_config.get("password"),
                    authSource=self.connection_config.get(
                        "authentication_database",
                        database_name,
                    ),
                    authMechanism=self.connection_config.get(
                        "authentication_mechanism",
                    ),
                )

        self.database = self.client[database_name]

    def select(
        self,
        collection: str,
        query: Mapping[str, Any] | None = None,
        projection: Mapping[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:

        if self.database is None:
            self.connect()
        cursor = self.database[collection].find(query or {}, projection)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def insert(self, collection: str, documents: Iterable[Mapping[str, Any]]) -> int:
        """문서 목록을 삽입하고 삽입 건수를 반환한다."""
        if self.database is None:
            self.connect()
        result = self.database[collection].insert_many(list(documents), ordered=False)
        return len(result.inserted_ids)

    def merge(
        self,
        collection: str,
        documents: Iterable[Mapping[str, Any]],
        key_fields: Iterable[str],
    ) -> int:
        """키 기준 upsert를 수행한다. 실제 bulk 정책은 후속 구현에서 확정한다."""
        # TODO: bulk_write와 UpdateOne(upsert=True)로 batch 처리
        # TODO: key_fields 누락·중복·변경 불가 필드 검증
        raise NotImplementedError

    def close(self) -> None:
        """MongoDB client를 종료한다."""
        if self.client is not None and hasattr(self.client, "close"):
            self.client.close()
        self.client = None
        self.database = None
