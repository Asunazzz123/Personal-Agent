import logging
import os
from typing import Optional

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "log")
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a configured logger with console and file output.

    Logs are written to both stderr and ``log/{name}.log``.

    Args:
        name (str): Logger name.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = os.path.normpath(_LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{name}.log"), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger

def setup_tool_logger(tool:str, level: int = logging.INFO) -> logging.Logger:
    setup_logger("tool", level = level)
    logger = logging.getLogger(f"tool.{tool}")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    logger.propagate = True
    return logger

def setup_access_logger(level: int = logging.INFO) -> logging.Logger:
    setup_logger("access", level = level)
    logger = logging.getLogger("access")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    logger.propagate = True
    return logger