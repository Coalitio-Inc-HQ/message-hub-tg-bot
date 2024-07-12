import logging
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

def setup_logging():
    # Создаем форматтер для цветного логирования в консоль
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(reset)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # Создаем обработчик для логов в консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Создаем форматтер для логов в файл
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    # Создаем обработчик для логов в файл
    file_handler = RotatingFileHandler("logs/app.log", encoding="utf-8", maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(file_formatter)

    # Настройка основного логгера
    logger = logging.getLogger("tg_bot_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()