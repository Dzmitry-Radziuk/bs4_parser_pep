from pathlib import Path

MAIN_DOC_URL = 'https://docs.python.org/3/'
BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
MAIN_PEP_URL = 'https://peps.python.org/'
VERSION_PYTHON_STATUS_PATTERN = (
    r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)')
DOWNLOAD_DIR = BASE_DIR / 'downloads'
TOTAL_RETRIES = 3
STATUS_FORCE_LIST = [500, 502, 503, 504]
BACKOFF_FACTOR = 0.3
DEFAULT_INT = 0
ZERO_INT = 0
ONE_INT = 1
FOUR_INT = 4
FIVE_INT = 5
TIME_OUT_GET_RESPOSE = 1
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
