"""Domino cart item MongoDB 조회 DAG."""

from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from src.common.logger import get_logger
from src.utils.email_sender import send_email
from src.ingestion.recommand_cart_item import (
    DEFAULT_COLLECTION,
    select_recommand_cart_item,
)


logger = get_logger(__name__)

ALERT_EMAIL_RECIPIENTS = [
    # "aicx-airflow@example.com",
]


DEFAULT_ARGS = {
    "owner": "aicx-airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
    "sla": timedelta(hours=1),
    "email_on_failure": False,
    "email_on_retry": False,
    # "on_failure_callback": [],
}


def run_recommand_cart_item() -> None:
    """recommand_cart_item.py의 MongoDB 조회 함수를 실행한다."""
    select_recommand_cart_item(
        collection=DEFAULT_COLLECTION,
        query={},
        limit=5,
    )


with DAG(
    dag_id="raw_ingestion_domino",
    description="Domino cart item MongoDB 조회",
    start_date=days_ago(1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["ETL", "domino", "mongodb"],
) as dag:

    recommand_cart_item = PythonOperator(
        task_id="recommand_cart_item",
        python_callable=run_recommand_cart_item,
    )
