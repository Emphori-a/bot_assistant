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
    Formatter(fmt='[%(asctime)s: %(levelname)s]: %(message)s')
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
        logger.critical(error_message)
        raise EnviromentTokenError(error_message)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: {message}')
    except Exception:
        error_message = 'Сбой отправки сообщения.'
        logger.error(error_message)


def get_api_answer(timestamp):
    """Запрос к эндпоинту."""
    error_message = f'Ошибка при запросе к основному API: {ENDPOINT}'
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if response.status_code != 200:
            raise APIError(error_message)
    except Exception:
        raise Exception(error_message)
    else:
        return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if type(response) is not dict:
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

    if type(response['homeworks']) is not list:
        raise TypeError(
            f'Тип данных ответа API - {type(response["homeworks"])}.'
            'Ожидаемый - list'
        )

    return response


def parse_status(homework):
    """Возврат статуса домашней работы."""
    homework_properties = [
        'id', 'status', 'homework_name', 'reviewer_comment',
        'date_updated', 'lesson_name'
    ]
    if not all(homework.get(key) for key in homework_properties):
        raise CheckHomeworkError(
            'Ответ API содержит не полную информацию.'
            f'Ожидаемые поля: {homework_properties}.'
        )

    homework_name = homework['homework_name']
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise CheckHomeworkError(
            'Статус работы не соответствует ожидаемому.'
            f'Возможные статусы: {HOMEWORK_VERDICTS.keys()}.'
        )

    verdict = HOMEWORK_VERDICTS[homework['status']]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    homeworks = {}
    message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            response = check_response(response)
            if not response.get('homeworks'):
                timestamp == response.get('current_date')
            elif not homeworks:
                message = 'Текущие статусы работ:\n'
                for hw in response.get('homeworks'):
                    message += (
                        f'{hw["homework_name"]} - '
                        f'{HOMEWORK_VERDICTS[hw["status"]]}\n'
                    )
                timestamp == response.get('current_date')
            else:
                for homework in response.get('homeworks'):
                    if (
                        homework.get('homework_name') in homeworks
                        and homework.get('status')
                        != homeworks['homework_name']
                    ):
                        message = parse_status(homework)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        else:
            homeworks == {
                hw['homework_name']: hw['status']
                for hw in response.get('homeworks')
            }
            timestamp == response.get('current_date')
        finally:
            if message:
                send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
