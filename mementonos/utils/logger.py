import logging
import sys
from datetime import datetime
from pathlib import Path

COLORS = {
    'DEBUG': '\033[94m',    # синий
    'INFO': '\033[92m',     # зелёный
    'WARNING': '\033[93m',  # жёлтый
    'ERROR': '\033[91m',    # красный
    'CRITICAL': '\033[95m', # пурпурный
    'RESET': '\033[0m'
}

class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами в консоли"""
    def format(self, record):
        msg = super().format(record)
        levelname = record.levelname
        if levelname in COLORS and sys.stdout.isatty():
            color = COLORS.get(levelname, '')
            reset = COLORS['RESET']
            return f"{color}{msg}{reset}"
        return msg


def get_logger(
    name: str = "app",
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    Получить логгер с цветным выводом в консоль и опционально записью в файл.
    
    Примеры использования:
        logger = get_logger(__name__)
        logger.debug("Тест debug")
        logger.info("Пользователь %s залогинился", username)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Чтобы не дублировались хендлеры при многократном вызове
    if logger.handlers:
        return logger

    # Формат сообщения
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Консольный хендлер с цветами
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(fmt, datefmt=datefmt))
    logger.addHandler(console_handler)

    return logger