# utils.py

import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from requests import RequestException
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from constants import (BACKOFF_FACTOR, DEFAULT_INT, EXPECTED_STATUS,
                       MAIN_PEP_URL, PLUS_ONE_INT, STATUS_FORCE_LIST,
                       TOTAL_RETRIES, VERSION_PYTHON_STATUS_PATTERN)
from exceptions import ParserFindTagException

# --------------------
# Работа с HTTP сессией и запросами
# --------------------

def create_session_with_retries():
    """Создает сессию requests с ретраями и кэшированием."""
    session = requests_cache.CachedSession()
    retries = Retry(total=TOTAL_RETRIES, backoff_factor=BACKOFF_FACTOR,
                    status_forcelist=STATUS_FORCE_LIST)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_response(session, url):
    """Отправить GET-запрос и вернуть Response или None при ошибке."""
    try:
        response = session.get(url, timeout=5)
        response.encoding = 'utf-8'
        response.raise_for_status()
        return response
    except RequestException:
        logging.exception(
            f'Ошибка при загрузке страницы {url}', stack_info=True)
        return None


# --------------------
# Работа с BeautifulSoup: получение и поиск тегов
# --------------------

def get_soup(response):
    """Возвращает объект BeautifulSoup из ответа."""
    return BeautifulSoup(response.text, 'lxml')


def find_tag(soup, tag, attrs=None):
    """Найти тег в BeautifulSoup или вызвать исключение, если не найден."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


# --------------------
# Парсинг таблицы PEP и анализ статусов
# --------------------

def get_pep_rows(session):
    """Получает строки таблицы PEP с URL страницы."""
    numerical_url = MAIN_PEP_URL + 'numerical'
    response = get_response(session, numerical_url)
    if response is None:
        return None

    soup = get_soup(response)
    table = find_tag(soup, 'table')

    return table.find_all('tr')[1:], numerical_url


def process_pep_row(session, row, base_url):
    """Обрабатывает одну строку таблицы PEP и возвращает статус и URL."""
    columns = row.find_all('td')
    if len(columns) < 4:
        return None

    code = columns[0].text.strip()
    preview_status = code[1:]
    expected_variants = EXPECTED_STATUS.get(preview_status, ())

    pep_link_tag = columns[1].find('a')
    if not pep_link_tag:
        return None

    href = pep_link_tag.get('href')
    pep_url = urljoin(base_url, href)
    response = get_response(session, pep_url)
    if response is None:
        return None

    soup = get_soup(response)
    dl_tag = soup.find('dl')
    if not dl_tag:
        return None

    real_status = extract_status_from_dl(dl_tag)
    if real_status is None:
        logging.warning(f'Не найден статус на странице {pep_url}')
        return None

    return real_status, expected_variants, pep_url


def extract_status_from_dl(dl_tag):
    """Извлекает статус из тега <dl>."""
    dt_tags = dl_tag.find_all('dt')
    dd_tags = dl_tag.find_all('dd')
    for dt_tag, dd_tag in zip(dt_tags, dd_tags):
        if dt_tag.text.strip() == 'Status:':
            return dd_tag.text.strip()
    return None


def analyze_peps(session, pep_data):
    """Анализирует строки PEP, подсчитывает статусы и собирает некорректные."""
    pep_rows, numerical_url = pep_data
    status_counter = {}
    inappropriate_statuses = []
    total = 0

    for row in tqdm(pep_rows):
        result = process_pep_row(session, row, numerical_url)
        if result is None:
            continue

        real_status, expected_variants, pep_url = result
        if expected_variants and real_status not in expected_variants:
            inappropriate_statuses.append({
                'pep_url': pep_url,
                'expected_variants': expected_variants,
                'real_status': real_status
            })

        status_counter[real_status] = status_counter.get(
            real_status, DEFAULT_INT) + PLUS_ONE_INT
        total += 1

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
    response = get_response(session, url)
    if response is None:
        return None
    soup = get_soup(response)
    h1 = find_tag(soup, 'h1')
    dl = find_tag(soup, 'dl')
    dl_text = dl.text.replace('\n', ' ')
    return (url, h1.text if h1 else '', dl_text)


def get_sidebar_ul_tags(response):
    """Возвращает все теги <ul> из сайдбара документации."""
    soup = get_soup(response)
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    return sidebar.find_all('ul')


def get_python_new_features_sections(response):
    """Парсит HTML и возвращает список секций с новыми функциями Python."""
    soup = get_soup(response)
    main_div = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', {'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all('li', class_='toctree-l1')
    return sections_by_python


def parse_versions_list(ul_tag, pattern=VERSION_PYTHON_STATUS_PATTERN):
    """Парсит список версий из <ul> по заданному паттерну."""
    results = []
    a_tags = ul_tag.find_all('a')
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


# --------------------
# Скачивание PDF архива документации
# --------------------

def download_pdf_archive(session, base_url, save_dir):
    """Скачать PDF архив документации и сохранить его."""
    downloads_url = urljoin(base_url, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return None

    soup = get_soup(response)
    table = find_tag(soup, 'table', {'class': 'docutils'})
    pdf_link = find_tag(
        table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})['href']
    archive_url = urljoin(downloads_url, pdf_link)

    save_dir.mkdir(exist_ok=True, parents=True)
    archive_path = save_dir / archive_url.split('/')[-1]

    try:
        file_response = session.get(archive_url)
        file_response.raise_for_status()
    except RequestException:
        logging.exception(f'Ошибка при загрузке архива: {archive_url}')
        return None

    with open(archive_path, 'wb') as f:
        f.write(file_response.content)

    logging.info(f'Архив успешно загружен и сохранён: {archive_path}')
    return archive_path
