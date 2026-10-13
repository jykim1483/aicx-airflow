"""프로젝트 로깅 공통 유틸."""

import logging


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format=DEFAULT_LOG_FORMAT)
    return logging.getLogger(name)
