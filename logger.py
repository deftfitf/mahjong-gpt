import logging
from logging.handlers import RotatingFileHandler

from appconfig import appconfig


def __setup_global_logger():
    logger = get_logger()
    logger.setLevel(logging.DEBUG)

    log_file = appconfig.logging.log_file_name
    max_log_size = 10 * 1024 * 1024  # 10 MB
    backup_count = 5

    file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size,
                                       backupCount=backup_count)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def get_logger():
    return logging.getLogger("global_logger")


__setup_global_logger()
