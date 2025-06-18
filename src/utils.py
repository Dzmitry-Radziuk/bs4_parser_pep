import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from requests import RequestException
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from src.constants import (BACKOFF_FACTOR, DEFAULT_INT, EXPECTED_STATUS,
                           FIVE_INT, FOUR_INT, MAIN_PEP_URL, ONE_INT,
                           STATUS_FORCE_LIST, TOTAL_RETRIES,
                           VERSION_PYTHON_STATUS_PATTERN, ZERO_INT)
from src.exceptions import ParserFindTagException


# --------------------
# Работа с HTTP сессией и запросами
# --------------------

def create_session_with_retries():
    """Создает сессию requests с ретраями и кэшированием."""
    session = requests_cache.CachedSession()
    retries = Retry(
        total=TOTAL_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCE_LIST
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_response(session, url, encoding='utf-8'):
    """Отправить GET-запрос и вернуть Response."""
    response = session.get(url, timeout=FIVE_INT)
    response.encoding = encoding
    response.raise_for_status()
    return response


# --------------------
# Работа с BeautifulSoup: получение и поиск тегов
# --------------------

def get_soup(response):
    """Возвращает объект BeautifulSoup из ответа."""
    return BeautifulSoup(response.text, 'lxml')


def fetch_and_parse(session, base_url, relative_path=''):
    """Получить и распарсить страницу по URL."""
    url = urljoin(base_url, relative_path)
    response = get_response(session, url)
    return get_soup(response)


def find_tag(soup, tag, attrs=None):
    """Найти тег в BeautifulSoup или вызвать исключение, если не найден."""
    searched_tag = soup.find(tag, attrs=attrs or {})
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg)
        raise ParserFindTagException(error_msg)
    return searched_tag


# --------------------
# Парсинг таблицы PEP и анализ статусов
# --------------------

def get_pep_rows(session):
    """Получает строки таблицы PEP и базовый URL страницы."""
    numerical_url = urljoin(MAIN_PEP_URL, 'numerical')
    try:
        response = get_response(session, numerical_url)
    except RequestException as e:
        logging.error(f'Ошибка загрузки таблицы PEP: {e}')
        return None

    soup = get_soup(response)
    table = find_tag(soup, 'table')
    rows = table.find_all('tr')
    return rows, numerical_url


def extract_status_from_dl(dl_tag):
    """Извлекает статус из тега <dl>."""
    dt_tags = dl_tag.find_all('dt')
    dd_tags = dl_tag.find_all('dd')
    for dt_tag, dd_tag in zip(dt_tags, dd_tags):
        if dt_tag.text.strip() == 'Status:':
            return dd_tag.text.strip()
    return None


def process_pep_row(session, row, base_url):
    """Обрабатывает одну строку таблицы PEP и возвращает статус и URL."""
    columns = row.find_all('td')
    if len(columns) < FOUR_INT:
        return None

    code = columns[ZERO_INT].text.strip()
    preview_status = code[ONE_INT:]
    expected_variants = EXPECTED_STATUS.get(preview_status, ())

    pep_link_tag = columns[ONE_INT].find('a')
    if pep_link_tag is None:
        return None

    href = pep_link_tag.get('href')
    pep_url = urljoin(base_url, href)

    try:
        response = get_response(session, pep_url)
    except RequestException:
        return None

    soup = get_soup(response)
    dl_tag = soup.find('dl')
    if dl_tag is None:
        return None

    real_status = extract_status_from_dl(dl_tag)
    if real_status is None:
        logging.warning(f'Не найден статус на странице {pep_url}')
        return None

    return real_status, expected_variants, pep_url


def analyze_peps(session, pep_data):
    """
    Анализирует строки PEP, подсчитывает статусы,
    собирает некорректные статусы и ошибки.
    """
    pep_rows, numerical_url = pep_data
    status_counter = {}
    inappropriate_statuses = []
    errors = []
    total = ZERO_INT

    for row in tqdm(pep_rows, desc='Обработка PEP'):
        try:
            result = process_pep_row(session, row, numerical_url)
            if result is None:
                logging.warning(f'Пропущена строка PEP:'
                                'не удалось обработать строку'
                                f'или отсутствуют данные: {row}')
                continue

            real_status, expected_variants, pep_url = result
            if expected_variants and real_status not in expected_variants:
                inappropriate_statuses.append({
                    'pep_url': pep_url,
                    'expected_variants': expected_variants,
                    'real_status': real_status
                })

            status_counter[real_status] = status_counter.get(
                real_status, DEFAULT_INT) + ONE_INT
            total += 1

        except Exception as e:
            errors.append(f'Ошибка при обработке строки PEP: {e}')

    for err_msg in errors:
        logging.warning(err_msg)

    return status_counter, inappropriate_statuses, total


def log_inappropriate_statuses(inappropriate_statuses):
    """Логирует найденные несоответствия статусов PEP."""
    for item in inappropriate_statuses:
        logging.warning(
            f'Несовпадение статуса PEP {item["pep_url"]}\n'
            f'\tОжидался один из: {item["expected_variants"]}\n'
            f'\tПолучен: {repr(item["real_status"])}'
        )


# --------------------
# Парсинг страниц с новыми возможностями Python
# --------------------

def parse_python_version_page(session, url):
    """Парсит страницу нововведений конкретной версии Python."""
    try:
        response = get_response(session, url)
    except RequestException as e:
        logging.warning(f'Не удалось получить страницу {url}: {e}')
        return None

    soup = get_soup(response)
    h1 = find_tag(soup, 'h1')
    dl = find_tag(soup, 'dl')
    dl_text = dl.text.replace('\n', ' ')
    return (url, h1.text if h1 else '', dl_text)


def get_sidebar_ul_tags(soup):
    """Возвращает все теги <ul> из сайдбара документации."""
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    return sidebar.find_all('ul')


def get_python_new_features_sections(soup):
    """Парсит BeautifulSoup и возвращает список секций с новыми функциями."""
    main_div = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li', class_='toctree-l1')
    return sections_by_python


def parse_versions_list(ul_tag, pattern=VERSION_PYTHON_STATUS_PATTERN):
    """Парсит список версий из <ul> по заданному паттерну."""
    results = []
    for a_tag in ul_tag.find_all('a'):
        link = a_tag.get('href')
        text_match = re.search(pattern, a_tag.text)
        if text_match:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text.strip(), ''
        results.append((link, version, status))
    return results


def parse_whats_new_sections(session, sections, base_url):
    """Парсит и возвращает данные по разделам 'Что нового'."""
    results = []
    for section in tqdm(sections, desc='Парсинг секций "What\'s New"'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag.get('href')
        version_link = urljoin(base_url, href)
        parsed_data = parse_python_version_page(session, version_link)
        if parsed_data:
            results.append(parsed_data)
        else:
            logging.warning(
                f'Парсинг страницы {version_link} вернул пустой результат,'
                f'пропуск итерации.')
    return results


# --------------------
# Скачивание PDF архива документации
# --------------------

def download_pdf_archive(session, base_url, save_dir):
    """Скачать PDF архив документации и сохранить его."""
    downloads_url = urljoin(base_url, 'download.html')
    try:
        response = get_response(session, downloads_url)
    except RequestException as e:
        logging.error(f'Ошибка загрузки страницы: {e}')
        return None

    soup = get_soup(response)
    table = find_tag(soup, 'table', {'class': 'docutils'})
    pdf_link_tag = find_tag(
        table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_link = pdf_link_tag.get('href')
    archive_url = urljoin(downloads_url, pdf_link)

    save_dir.mkdir(exist_ok=True, parents=True)
    archive_path = save_dir / archive_url.split('/')[-1]

    try:
        file_response = session.get(archive_url)
        file_response.raise_for_status()
    except RequestException as e:
        logging.exception(f'Ошибка при загрузке архива: {archive_url}: {e}')
        return None

    with open(archive_path, 'wb') as f:
        f.write(file_response.content)

    logging.info(f'Архив успешно загружен и сохранён: {archive_path}')
    return archive_path
