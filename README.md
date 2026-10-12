# AICX Airflow

고객사별 MongoDB, PostgreSQL, Athena, S3 원천 데이터를 수집하고 이후 ClickHouse Data Layer로 적재하기 위한 Airflow 기반 데이터 파이프라인 프로젝트입니다.

## 디렉터리

```text
aicx-airflow/
├── dags/                    # Airflow가 로드하는 DAG 진입점
├── src/connections/        # 공통 MongoDB/PostgreSQL connection factory
├── utils/                   # 이메일 등 공통 보조 모듈
├── configs/                # YAML 기반 설정 예시
├── tests/
├── scripts/
└── docs/
```

세부 아키텍처는 [ARCHITECTURE.md](docs/ARCHITECTURE.md)를 참고합니다.

## 설치

Python 3.11 이상을 권장합니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Airflow Scheduler/Worker 또는 작업용 이미지에는 Provider 의존성을 별도로 설치합니다.

```bash
pip install -r requirements-airflow.txt
```

Airflow는 Provider와 함께 설치할 때 반드시 Airflow 버전에 맞는 constraints 파일을 사용해야 합니다. 예시는 다음과 같습니다.

```bash
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION=3.11
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install -r requirements-airflow.txt --constraint "${CONSTRAINT_URL}"
```

Provider 역할:

```text
apache-airflow-providers-mongo       → MongoHook
apache-airflow-providers-postgres    → PostgresHook
apache-airflow-providers-clickhouse  → ClickHouseHook
apache-airflow-providers-common-sql  → 공통 SQL Hook/Operator
```

실제 EKS 배포에서는 Scheduler/Webserver/Worker의 Airflow와 Provider 버전을 동일하게 고정합니다.

`pyproject.toml`을 사용하는 경우에는 다음과 같이 설치할 수 있습니다.

```bash
pip install -e .
```

Airflow는 배포 환경의 버전과 Python 버전에 맞춰 별도로 설치해야 합니다. 특히 EKS의 Airflow 이미지에 포함된 Airflow 버전과 호환되는 provider 패키지를 사용해야 합니다.

## 데이터베이스 설정

설정 예시는 [configs/database.example.yaml](configs/database.example.yaml)에 있습니다.

비밀번호와 실제 접속정보는 YAML에 직접 저장하지 않고 환경변수 또는 Kubernetes Secret/Airflow Secret Backend로 주입합니다.

`configs/database.example.yaml`은 구조와 환경변수 이름만 담은 예시 파일이며 Git에 커밋해도 됩니다. 실제 값을 넣은 `configs/database.yaml`, `.env`, Secret YAML은 커밋하지 않습니다. 해당 파일들은 `.gitignore`에 등록되어 있습니다.

EKS 운영에서는 다음 우선순위를 권장합니다.

```text
AWS Secrets Manager
  → External Secrets Operator 또는 Airflow Secrets Backend
  → Airflow Connection / 작업 Pod 환경변수
  → MongoHook·PostgresHook 또는 내부 connection factory
```

개발 환경에서만 임시로 로컬 환경변수를 사용할 수 있습니다.

```bash
export PROD_MONGO_SERVICE_HOST="172.16.14.58"
export PROD_MONGO_USERNAME="..."
export PROD_MONGO_PASSWORD="..."
```

비밀번호가 이미 Git 커밋이나 공유 채팅에 노출된 경우에는 Git에서 파일만 지우는 것으로 충분하지 않습니다. 해당 계정·URI의 비밀번호를 먼저 교체하고, 필요하면 저장소 이력 정리 작업을 별도로 수행해야 합니다.

```bash
export MONGODB_HOST="mongodb.example.internal"
export MONGODB_USERNAME="app_user"
export MONGODB_PASSWORD="***"
export MONGODB_DATABASE="Statistics"

export POSTGRES_HOST="postgres.example.internal"
export POSTGRES_USERNAME="app_user"
export POSTGRES_PASSWORD="***"
export POSTGRES_DATABASE="groobee_bi"
```

공통 connection factory 사용 예시는 다음과 같습니다.

```python
import yaml

from common import (
    create_mongodb_client,
    create_postgres_connection,
)

with open("configs/database.example.yaml", encoding="utf-8") as file:
    config = yaml.safe_load(file)

mongo_client = create_mongodb_client(config["mongodb"])
postgres_connection = create_postgres_connection(config["postgres"])
```

현재 `src`를 import하려면 프로젝트 루트에서 실행하거나 `PYTHONPATH=src`를 설정합니다.

## 이메일 발송

`src/utils`의 `send_email()`을 사용합니다.

```bash
export SMTP_HOST="smtp.example.internal"
export SMTP_PORT="587"
export SMTP_SENDER="airflow@example.com"
export SMTP_USERNAME="airflow@example.com"
export SMTP_PASSWORD="***"
```

```python
from utils.email_sender import send_email

send_email(
    recipients=["data-owner@example.com"],
    subject="원천 적재 완료",
    body="Domino orders 적재가 완료되었습니다.",
)
```

## Airflow/EKS 운영 원칙

- DAG에는 스케줄과 task 의존성만 두고, DB 조회·변환·적재 로직은 `src` 모듈로 분리합니다.
- DAG와 작업용 Python 의존성은 EKS 배포 이미지 또는 Git-sync 정책으로 동일하게 배포합니다.
- Airflow Connection과 Kubernetes Secret에는 인증정보를 저장하고 소스코드와 Git에는 비밀값을 커밋하지 않습니다.
- 연결 확인, 스키마 검증, 건수 검증, 적재, 재처리 기준을 DAG 단계로 분리합니다.

## 테스트

```bash
pytest
```

실제 DB·SMTP 정보가 없는 환경에서는 연결 통합 테스트를 수행할 수 없으며, 단위 테스트와 모킹 테스트를 우선 사용합니다.
