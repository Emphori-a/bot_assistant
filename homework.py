from http import HTTPStatus
import logging
from logging import StreamHandler, Formatter
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    APIError, CheckHomeworkError, CheckResponseError, EnviromentTokenError
)

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(
    Formatter(
        '[%(asctime)s: %(funcName)s-%(lineno)d [%(levelname)s]]: %(message)s'
    )
)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing_variables = [var for var in variables
                         if variables.get(var) is None]
    if missing_variables:
        error_message = (
            f'Отсутствуют переменные окружения: {missing_variables}. '
            'Программа принудительно остановлена.')
        logger.critical(error_message, exc_info=True)
        raise EnviromentTokenError(error_message)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    logger.debug(
        'Запуск функции send_message, начало отправки сообщения.'
    )
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: {message}')
    except telegram.TelegramError:
        logger.error('Сбой отправки сообщения.')


def get_api_answer(timestamp):
    """Запрос к эндпоинту."""
    logger.debug(
        f'Запуск функции get_api_answer. Запроса к API {ENDPOINT}, '
        f'передан параметр from_date: {timestamp}.'
    )
    error_message = (
        f'Ошибка при запросе к основному API: {ENDPOINT}. '
        f'Передан параметр from_date: {timestamp}.'
    )
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except requests.RequestException:
        raise ConnectionError(error_message)
    else:
        if response.status_code != HTTPStatus.OK:
            raise APIError(error_message)
        logger.info(
            f'Запрос к API {ENDPOINT} успешно отправлен. '
            f'Передан параметр from_date: {timestamp}'
        )
        return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    logger.debug(
        'Запуск функции check_response. '
        f'Начало проверки ответа от API: {ENDPOINT}.'
    )

    if not isinstance(response, dict):
        raise TypeError(
            f'Тип данных полученного ответа API - {type(response)}.'
            'Ожидаемый - dict'
        )

    api_keys = ['homeworks', 'current_date']
    for key in api_keys:
        if key not in response:
            raise CheckResponseError(
                f'Ответ API не содержит ожидаемые ключи: {api_keys}'
            )

    if not isinstance(response['homeworks'], list):
        raise TypeError(
            f'Тип данных ответа API - {type(response["homeworks"])}.'
            'Ожидаемый - list'
        )

    logger.info(f'Ответ от API: {ENDPOINT} успешно проверен.')


def parse_status(homework):
    """Возврат статуса домашней работы."""
    logger.debug('Запуск функции parse_status.')

    homework_properties = ['status', 'homework_name']
    if not all(homework.get(key) for key in homework_properties):
        raise CheckHomeworkError(
            'Ответ API содержит не полную информацию.'
            f'Ожидаемые поля: {homework_properties}.'
        )

    homework_name = homework['homework_name']
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise CheckHomeworkError(
            f'Статус работы {homework_name} - {homework["status"]}, '
            'не соответствует ожидаемому.'
            f'Возможные статусы: {HOMEWORK_VERDICTS.keys()}.'
        )

    verdict = HOMEWORK_VERDICTS[homework['status']]
    logger.info(f'Статус работы {homework_name} успешно проверен.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    homeworks = {}
    error_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if not response.get('homeworks'):
                logger.debug(
                    f'Запрос к API {ENDPOINT} вернул пустой список homeworks, '
                    'статус работ не изменился.'
                )
            else:
                for hw in response.get('homeworks'):
                    message = parse_status(hw)
                    if (
                        hw.get('homework_name') not in homeworks
                        or hw.get('status') != homeworks['homework_name']
                    ):
                        homeworks[hw['homework_name']] = hw['status']
                        send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error_message, exc_info=True)
            if not error_message or error_message != message:
                error_message = message
            send_message(bot, error_message)
        else:
            timestamp = response.get('current_date')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
