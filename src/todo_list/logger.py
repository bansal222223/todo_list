import logging
import os
from logging.handlers import RotatingFileHandler

# ── Log directory — root level ───────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ── Log files ────────────────────────────────────────────────────────────────
APP_LOG   = os.path.join(LOG_DIR, "app.log")
AUTH_LOG  = os.path.join(LOG_DIR, "auth.log")
TASK_LOG  = os.path.join(LOG_DIR, "tasks.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")

# ── Formatter ────────────────────────────────────────────────────────────────
LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
formatter   = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)


def _file_handler(path: str, level=logging.DEBUG) -> RotatingFileHandler:
    h = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    h.setFormatter(formatter)
    h.setLevel(level)
    return h


def _console_handler(level=logging.INFO) -> logging.StreamHandler:
    h = logging.StreamHandler()
    h.setFormatter(formatter)
    h.setLevel(level)
    return h


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler(APP_LOG))
        logger.addHandler(_console_handler())
        logger.addHandler(_file_handler(ERROR_LOG, level=logging.ERROR))
        logger.propagate = False
    return logger


def get_auth_logger() -> logging.Logger:
    logger = logging.getLogger("auth")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler(AUTH_LOG))
        logger.addHandler(_console_handler())
        logger.addHandler(_file_handler(ERROR_LOG, level=logging.ERROR))
        logger.propagate = False
    return logger


def get_task_logger() -> logging.Logger:
    logger = logging.getLogger("tasks")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler(TASK_LOG))
        logger.addHandler(_console_handler())
        logger.addHandler(_file_handler(ERROR_LOG, level=logging.ERROR))
        logger.propagate = False
    return logger


# ── Helpers ──────────────────────────────────────────────────────────────────

def log_user_action(logger: logging.Logger, action: str, username: str, detail: str = ""):
    logger.info(f"[USER] action={action} | user={username} | {detail}".strip(" |"))

def log_task_change(logger: logging.Logger, action: str, task_id, user_id, detail: str = ""):
    logger.info(f"[TASK] action={action} | task_id={task_id} | user_id={user_id} | {detail}".strip(" |"))

def log_error(logger: logging.Logger, location: str, error: Exception):
    logger.exception(f"[ERROR] location={location} | error={str(error)}")