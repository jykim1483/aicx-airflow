# AICX Airflow

## 프로젝트 구조

```text
aicx-airflow/
├── dags/
│   └── etl/
│       └── raw_ingestion_domino.py     # Airflow DAG 진입점
├── src/
│   ├── common/
│   │   ├── mongodb.py                  # MongoDB 공통 연결/조회
│   │   ├── clickhouse.py               # ClickHouse 공통 연결/SQL 실행
│   │   └── postgres.py                 # PostgreSQL 공통 연결/조회
│   ├── ingestion/
│   │   └── recommand_cart_item.py      # Domino cart item 조회/검증 로직
│   └── utils/
│       └── email_sender.py             # SMTP 이메일 발송 유틸
├── configs/
│   ├── database.example.yaml           # DB 접속 설정 예시
│   └── domino_tables.yaml              # Domino 원천 테이블 설정
├── sql/
│   └── dl/
│       └── clickhouse_connection_test.sql
├── docs/
├── tests/
├── requirements.txt
├── requirements-airflow.txt
└── pyproject.toml
```

세부 설계 메모는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참고합니다.

## 개발 환경

Python 3.11 이상

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

패키지 형태로 설치하려면 다음을 사용할 수 있습니다.

```bash
pip install -e .
```

로컬에서 `src` 패키지를 import할 때는 프로젝트 루트를 `PYTHONPATH`에 포함

```bash
export PYTHONPATH=.
```

## Airflow 환경

Airflow 실행 환경은 별도 가상환경을 사용하는 것을 권장

```bash
python3.12 -m venv .venv-airflow
source .venv-airflow/bin/activate
python -m pip install --upgrade pip
```

Airflow는 버전에 맞는 constraints 파일로 설치합니다.

```bash
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION=3.12
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install -r requirements.txt -r requirements-airflow.txt --constraint "${CONSTRAINT_URL}"
```

현재 ClickHouse 연결은 `clickhouse-connect`를 사용합니다. `requirements-airflow.txt`의 `clickhouse-driver`는 기존 검토 흔적으로, 실제 공통 모듈은 [src/common/clickhouse.py](src/common/clickhouse.py)를 기준으로 합니다.

## 설정

DB 접속 설정 예시는 [configs/database.example.yaml](configs/database.example.yaml)에 있습니다.

운영 원칙:

- 실제 비밀번호, 토큰, private key는 Git에 커밋하지 않습니다.
- 운영 배포에서는 Airflow Connection, Secret Backend, Kubernetes Secret 또는 환경변수로 주입합니다.
- `configs/database.yaml`, `.env`, Secret YAML은 커밋 대상이 아닙니다.

현재 개발 단계에서는 `database.example.yaml`을 직접 읽어 MongoDB/ClickHouse 연결을 테스트합니다.

## 주요 모듈

MongoDB 공통 모듈:

```python
from src.common.mongodb import MongoDBConnection

mongo = MongoDBConnection(config)
rows = mongo.select(
    collection="Cart.0fc41973695d406784c04e121a04cb64",
    query={},
    limit=10,
)
mongo.close()
```

ClickHouse 공통 모듈:

```python
from src.common.clickhouse import ClickHouseConnection

clickhouse = ClickHouseConnection(config)
result = clickhouse.execute("SELECT 1")
clickhouse.close()
```

Domino cart item 처리 모듈:

```bash
PYTHONPATH=. .venv/bin/python -m src.ingestion.recommand_cart_item
```

## Airflow DAG

현재 DAG:

```text
dags/etl/raw_ingestion_domino.py
```

현재 task:

```text
recommand_cart_item
```

DAG는 비즈니스 로직을 직접 들고 있지 않고, `src.ingestion.recommand_cart_item`의 함수를 호출합니다.

## 로컬 검증

문법 확인:

```bash
python -m compileall src dags
```

DAG import 확인:

```bash
AIRFLOW_HOME=$PWD/.airflow PYTHONPATH=. \
.venv-airflow/bin/python -c "import dags.etl.raw_ingestion_domino as d; print(d.dag.dag_id); print([t.task_id for t in d.dag.tasks])"
```

Airflow import error 확인:

```bash
AIRFLOW_HOME=$PWD/.airflow PYTHONPATH=. \
.venv-airflow/bin/airflow dags list-import-errors
```

Task 단독 실행:

```bash
AIRFLOW_HOME=$PWD/.airflow PYTHONPATH=. \
.venv-airflow/bin/airflow tasks test raw_ingestion_domino recommand_cart_item 2026-10-13
```