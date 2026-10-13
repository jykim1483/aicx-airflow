"""프로젝트 설정/SQL 파일 로딩 공통 유틸."""

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_CONFIG_PATH = PROJECT_ROOT / "configs" / "database.example.yaml"
DEFAULT_ENVIRONMENT = "prod"


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
