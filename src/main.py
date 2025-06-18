import logging
from urllib.parse import urljoin

from src import constants, utils
from src.configs import configure_argument_parser, configure_logging
from src.exceptions import VersionsNotFoundError
from src.outputs import control_output

BASE_DIR = constants.BASE_DIR


def pep(session):
    """Парсинг PEP и подсчет статусов."""
    pep_data = utils.get_pep_rows(session)
    if not pep_data:
        return

    status_counter, inappropriate_statuses, total = utils.analyze_peps(
        session, pep_data)
    utils.log_inappropriate_statuses(inappropriate_statuses)

    result = (
        [['Status', 'Count']]
        + [list(item) for item in sorted(status_counter.items())]
        + [['Total', total]]
    )
    return result


def whats_new(session):
    """Сбор новостей о Python."""
    soup = utils.fetch_and_parse(session, constants.MAIN_DOC_URL, 'whatsnew/')
    if soup is None:
        return

    sections = utils.get_python_new_features_sections(soup)

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    results.extend(
        utils.parse_whats_new_sections(
            session, sections, urljoin(
                constants.MAIN_DOC_URL, constants.WHATS_NEW_SLUG)))
    return results


def latest_versions(session):
    """Получение последних версий Python."""
    soup = utils.fetch_and_parse(session, constants.MAIN_DOC_URL)
    if soup is None:
        return

    ul_tags = utils.get_sidebar_ul_tags(soup)

    for ul in ul_tags:
        if 'All versions' in ul.text:
            return utils.parse_versions_list(ul)
    raise VersionsNotFoundError('Список версий Python не найден')


def download(session):
    """Загрузка документации и сохранение в папке."""
    soup = utils.fetch_and_parse(
        session, constants.MAIN_DOC_URL, constants.DOWNLOAD_HTML_NAME)
    if soup is None:
        return

    save_dir = BASE_DIR / constants.DOWNLOAD_DIR_NAME
    utils.download_pdf_archive(
        session, constants.MAIN_DOC_URL, save_dir)


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    """Точка входа в приложение."""
    try:
        configure_logging()
        logging.info('Парсер запущен!')

        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(f'Аргументы командной строки: {args}')

        parser_mode = args.mode
        if parser_mode not in MODE_TO_FUNCTION:
            logging.error(f'Неизвестный режим: {parser_mode}')
            return

        session = utils.create_session_with_retries()

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
