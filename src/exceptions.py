class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""


class VersionsNotFoundError(Exception):
    """Вызывается, если не удалось найти информацию о версиях Python."""


class NetworkError(Exception):
    """Ошибка при выполнении сетевого запроса."""
