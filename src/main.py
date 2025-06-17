import logging
from pathlib import Path
from urllib.parse import urljoin

from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import MAIN_DOC_URL  # Дописать импорт после ревью.
from outputs import control_output
from utils import (analyze_peps, create_session_with_retries,
                   download_pdf_archive, find_tag, get_pep_rows,
                   get_python_new_features_sections, get_response,
                   get_sidebar_ul_tags, log_inappropriate_statuses,
                   parse_python_version_page, parse_versions_list)

BASE_DIR = Path(__file__).resolve().parent  # Оставил для тестов, потом уберу.


def pep(session):
    """Парсинг PEP и подсчет статусов."""
    pep_data = get_pep_rows(session)
    if not pep_data:
        return

    status_counter, inappropriate_statuses, total = analyze_peps(
        session, pep_data)
    log_inappropriate_statuses(inappropriate_statuses)

    result = [['Status', 'Count']]
    for status, count in sorted(status_counter.items()):
        result.append([status, count])
    result.append(['Total', total])
    return result


def whats_new(session):
    """Сбор новостей о Python."""
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    sections = get_python_new_features_sections(response)

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        parsed_data = parse_python_version_page(session, version_link)
        if parsed_data:
            results.append(parsed_data)
    return results


def latest_versions(session):
    """Получение последних версий Python."""
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    ul_tags = get_sidebar_ul_tags(response)

    for ul in ul_tags:
        if 'All versions' in ul.text:
            return parse_versions_list(ul)
    raise Exception('Ничего не нашлось')


def download(session):
    """Загрузка документации и сохранение в папке."""
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    save_dir = BASE_DIR / 'downloads'  # Оставил для тестов.
    download_pdf_archive(session, MAIN_DOC_URL, save_dir)


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    """Точка входа в приложение."""
    configure_logging()
    logging.info('Парсер запущен!')

    try:
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(f'Аргументы командной строки: {args}')

        parser_mode = args.mode
        if parser_mode not in MODE_TO_FUNCTION:
            logging.error(f'Неизвестный режим: {parser_mode}')
            return

        session = create_session_with_retries()

        if args.clear_cache:
            session.cache.clear()

        results = MODE_TO_FUNCTION[parser_mode](session)

        if results is not None:
            control_output(results, args)

        logging.info('Парсер завершил работу.')

    except Exception as error:
        logging.exception(f'Во время выполнения произошла ошибка: {error}')


if __name__ == '__main__':
    main()
