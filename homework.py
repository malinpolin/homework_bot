import os

import sys

import requests

import logging

import time

import telegram

import json

from dotenv import load_dotenv

from http import HTTPStatus

from exceptions import (
    HomeworksKeyError,
    InvalidTypeResponseError,
    HomeworksTypeError,
    MissingEnvVarError,
    StatusCodeError,
    StatusKeyError,
    UnknownHomeworkStatusError,
    EmptyHomeworkNameError,
)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENV_VARS = {
    'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
}
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


def send_message(bot, message):
    """Отправляем сообщение в Telegram и логгируем событие."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Бот отправил сообщение "{message}"')
    except telegram.TelegramError as error:
        logging.error(f'Сбой при отправке сообщения "{message}": {error}')
    return True


def get_api_answer(current_timestamp):
    """Запрашиваем данные с сервера Яндекс.Практикум."""
    message = ''
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        logging.error(f'Сервер Яндекс.Практикум вернул ошибку "{error}"')
    if response.status_code != HTTPStatus.OK:
        message = (
            'Запрос к эндпоинту вернул код ошибки '
            f'{response.status_code}'
        )
        logging.error(message)
        raise StatusCodeError(message)
    try:
        return response.json()
    except json.JSONDecodeError:
        message = 'Сервер вернул невалидный json'
        logging.error(message)


def check_response(response):
    """Проверяем ответ API на корректность."""
    message = ''
    if type(response) is not dict:
        message = (
            'Запрос к эндпоинту вернул невалидный ответ в формате "'
            f'{type(response)}"'
        )
        logging.error(message)
        raise InvalidTypeResponseError(message)
    if 'homeworks' not in response.keys():
        message = (
            "В ответе от API отсутствует ключ 'homeworks': "
            f'{response.keys()}'
        )
        logging.error(message)
        raise HomeworksKeyError(message)
    if len(response.get('homeworks')) == 0:
        message = 'API вернул пустой список домашних работ'
        logging.info(message)
    if type(response.get('homeworks')) is not list:
        message = (
            'Некорректный формат списка домашних работ '
            f"{type(response.get('homeworks'))}"
        )
        logging.error(message)
        raise HomeworksTypeError(message)
    return response.get('homeworks')


def parse_status(homework):
    """Получаем статус конкретной домашней работы."""
    verdict = ''
    message = ''
    homework_name = homework.get('homework_name')
    if 'status' not in homework.keys():
        message = (
            "В домашней работе отсутствует ключ 'status':"
            f'{homework.keys()}'
        )
        logging.error(message)
        raise StatusKeyError(message)
    homework_status = homework.get('status')
    if homework_name is None:
        message = "В ответе от API отсутствует ключ 'homework_name'"
        logging.error(message)
        raise EmptyHomeworkNameError(message)
    if homework_status not in HOMEWORK_STATUSES.keys():
        message = f'Неизвестный статус домашней работы: {homework_status}'
        logging.error(message)
        raise UnknownHomeworkStatusError(message)
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем доступность переменных окружения."""
    flag = True
    for name, value in ENV_VARS.items():
        if (name not in dict(os.environ).keys()) or (value is None):
            flag = False
            message = 'Отсутствует обязательная переменная окружения'
            logging.critical(f'{message}: {name}.')
            raise MissingEnvVarError(name, message)
    return flag


def main():
    """Основная логика работы бота."""
    logging.debug('Бот запущен')
    prev_error = ''
    curr_status = ''
    prev_status = ''
    check_tokens()
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except telegram.error.InvalidToken:
        logging.error(f'Невалидный Telegram-token "{TELEGRAM_TOKEN}"')
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            status = check_response(response)
            if len(status) > 0:
                homework = status[0]
                curr_status = parse_status(homework)
                current_timestamp = response.get('current_timestamp')
            if curr_status != prev_status:
                if send_message(bot, curr_status):
                    prev_status = curr_status
            else:
                logging.debug(
                    'Отсутствует обновление статуса домашней работы.'
                )
        except Exception as error:
            logging.error(error)
            if str(error) != prev_error:
                if send_message(bot, f'Сбой в работе программы: {error}'):
                    prev_error = str(error)
        finally:
            logging.info('Бот в режиме ожидания')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
