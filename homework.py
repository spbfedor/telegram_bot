import logging
import time
from http import HTTPStatus

import requests
import telegram

import settings
from settings import PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN

logger = logging.getLogger(
    __name__
)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправлено')
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


def get_api_answer(current_timestamp):
    """Делаем запрос к API, преобразуем ответ из JSON в формат Python."""
    timestamp = current_timestamp or int(time.time())
    params = {
        'from_date': timestamp
    }
    try:
        response = requests.get(
            settings.ENDPOINT,
            headers=settings.HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            logger.error('Эндпоинт недоступен')
            raise Exception('Ответ сервера не соответствует ожиданию')
        else:
            response = response.json()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(e, exc_info=True)
        raise requests.RequestException(f'Не удалось выполнить запрос: {e}')


def check_response(response):
    """Проверка ответа API на корректность."""
    if type(response) is not dict:
        logger.error(
            'Тип ответа не соответствует ожиданию. Объект не является словарем'
        )
        raise TypeError(
            'Тип ответа не соответствует ожиданию. Объект не является словарем'
        )
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        logger.error(
            'Тип ответа не соответствует ожиданию. Объект не является списком'
        )
        raise TypeError(
            'Тип ответа не соответствует ожиданию. Объект не является списком'
        )
    if homework is None:
        logger.error('Ключ "homeworks" не существует')
        raise KeyError('Ключ не существует')
    return homework


def parse_status(homework):
    """Извлечение информации из словаря, подготовка к отправке."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        logger.error('Ключ "homework_name" не существует')
        raise KeyError('Ключ "homework_name" не существует')
    homework_status = homework.get('status')
    if not homework_status:
        logger.error('Ключ "status" не существует')
        raise KeyError('Ключ "status" не существует')
    er = 'Неизвестный статус работы'
    verdict = settings.HOMEWORK_STATUSES.get(
        homework_status, er
    )
    if verdict == er:
        logger.error(verdict)
        raise KeyError(verdict)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка обязательных переменных окружения."""
    if not PRACTICUM_TOKEN:
        logger.critical(
            'Отсутствует обязательная переменная окружения: '
            'PRACTICUM_TOKEN'
        )
        return False
    if not TELEGRAM_TOKEN:
        logger.critical(
            'Отсутствует обязательная переменная окружения: '
            'TELEGRAM_TOKEN'
        )
        return False
    if not TELEGRAM_CHAT_ID:
        logger.critical(
            'Отсутствует обязательная переменная окружения: '
            'TELEGRAM_CHAT_ID'
        )
        return False
    return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                logger.debug(
                    'Статус домашней работы не обновился'
                )
            else:
                send_message(bot, parse_status(homework[0]))
                current_timestamp = int(time.time())
                time.sleep(settings.RETRY_TIME)
        except Exception as e:
            message = f'Сбой в работе программы: {e}'
            send_message(bot, message)
            logger.error(e, exc_info=True)
            time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()
