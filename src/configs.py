import argparse
import logging
from logging.handlers import RotatingFileHandler

from src import constants


def configure_argument_parser(available_modes):
    """Создаёт и настраивает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=(constants.PRETTY, constants.FILE),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    """Настраивает логирование с ротацией файлов и выводом в терминал."""
    constants.LOG_DIR_NAME.mkdir(exist_ok=True)

    rotating_handler = RotatingFileHandler(
        constants.LOG_FILE_NAME,
        maxBytes=constants.TEN_INT ** constants.SIX_INT,
        backupCount=constants.FIVE_INT
    )

    logging.basicConfig(
        datefmt=constants.LOG_DT_FORMAT,
        format=constants.LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler())
    )
