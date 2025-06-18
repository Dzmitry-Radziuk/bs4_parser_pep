from pathlib import Path

# --- Настройки путей ---
BASE_DIR = Path(__file__).parent
RESULTS_DIR_NAME = 'results'
LOG_DIR_NAME = BASE_DIR / 'logs'
LOG_FILE_NAME = LOG_DIR_NAME / 'parser.log'
DOWNLOAD_DIR = BASE_DIR / 'downloads'
DOWNLOAD_DIR_NAME = 'downloads'
DOWNLOAD_HTML_NAME = 'download.html'

# --- URL-адреса ---
MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEP_URL = 'https://peps.python.org/'
WHATS_NEW_SLUG = 'whatsnew/'

# --- Форматы даты и логирования ---
LOG_DT_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'


# --- Настройки логики обработки ---
TABLE_ALIGN = 'l'
PRETTY = 'pretty'
FILE = 'file'


# --- Паттерны для регулярных выражений ---
VERSION_PYTHON_STATUS_PATTERN = (
    r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
)


# --- HTTP-настройки ---
TOTAL_RETRIES = 3
STATUS_FORCE_LIST = [500, 502, 503, 504]
BACKOFF_FACTOR = 0.3
TIME_OUT_GET_RESPOSE = 1


# --- Числовые константы ---
DEFAULT_INT = 0
ZERO_INT = 0
ONE_INT = 1
FOUR_INT = 4
FIVE_INT = 5
SIX_INT = 6
TEN_INT = 10


# --- Ожидаемые статусы PEP ---
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
