class EnviromentTokenError(Exception):
    """Отсутствие обязательных переменных окружения во время запуска бота."""


class APIError(Exception):
    """Ошибка доступа к API."""


class CheckResponseError(Exception):
    """Ответ API не соответствует документации."""


class CheckHomeworkError(Exception):
    """Ошибки при извелечении информации о домашней работе."""
