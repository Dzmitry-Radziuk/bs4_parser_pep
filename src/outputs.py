import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, ONE_INT, ZERO_INT


def control_output(results, cli_args):
    """Выбор способа вывода данных по аргументам командной строки."""
    output = cli_args.output
    if output == 'pretty':
        pretty_output(results)
    elif output == 'file':
        file_output(results, cli_args)
    else:
        default_output(results)


def default_output(results):
    """Построчный вывод результатов в терминал."""
    for row in results:
        print(*row)


def pretty_output(results):
    """Вывод результатов в виде красиво отформатированной таблицы."""
    table = PrettyTable()
    table.field_names = results[ZERO_INT]
    table.align = 'l'
    table.add_rows(results[ONE_INT:])
    print(table)


def file_output(results, cli_args):
    """Сохранение результатов в CSV-файл в папке results."""
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name

    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
        writer.writerows(results)
    logging.info(f'Файл с результатами был сохранён: {file_path}')
