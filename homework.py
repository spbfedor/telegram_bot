from http import HTTPStatus
import logging
import os
import requests
import sys
import time

from dotenv import load_dotenv
import telegram
import telegram.ext

load_dotenv()


PRACTICUM_TOKEN = os.getenv(
    'PRACTICUM_TOKEN'
)
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_TOKEN'
)
TELEGRAM_CHAT_ID = os.getenv(
    'TELEGRAM_CHAT_ID'
)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {
    'Authorization': f'OAuth {PRACTICUM_TOKEN}'
}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(
    __name__
)
logger.setLevel(
    logging.INFO
)
handler = logging.StreamHandler(
    sys.stdout
)
logger.addHandler(
    handler
)


def send_message(
    bot,
    message
):
    """Отправка сообщения в Telegram чат."""
    text = message
    try:
        bot.send_message(
            TELEGRAM_CHAT_ID,
            text
        )
        logger.info(
            'Сообщение успешно отправлено'
        )
    except Exception as e:
        logger.error(
            e,
            exc_info=True
        )
        raise e


def get_api_answer(
    current_timestamp
):
    """Делаем запрос к API, преобразуем ответ из JSON в формат Python."""
    timestamp = current_timestamp or int(
        time.time()
    )
    params = {
        'from_date': timestamp
    }
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            logger.error(
                'Эндпоинт недоступен'
            )
            raise Exception(
                'Ответ сервера не соответствует ожиданию'
            )
        response = response.json()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(
            e,
            exc_info=True
        )
        raise requests.RequestException(
            f'Не удалось выполнить запрос: {e}'
        )


def check_response(
    response
):
    """Проверка ответа API на корректность."""
    homework = response[
        'homeworks'
    ]
    if not isinstance(
        homework,
        list
    ):
        logger
        raise TypeError(
            'Тип ответа не соответствует ожиданию. Объект не является списком'
        )
    if [
        'homeworks'
    ] is None:
        raise KeyError(
            'Ключ не существует'
        )
    if not isinstance(
        response,
        dict
    ):
        raise(
            'Тип ответа не соответствует ожиданию. Объект не является словарем'
        )
    return homework


def parse_status(
    homework
):
    """Извлечение информации из словаря, подготовка к отправке."""
    homework_name = homework.get(
        'homework_name'
    )
    if homework_name is None:
        raise KeyError(
            'Ключ "homework_name" не существует'
        )
    homework_status = homework.get(
        'status'
    )
    if homework_status is None:
        raise KeyError(
            'Ключ "status" не существует'
        )
    verdict = HOMEWORK_STATUSES.get(
        homework_status
    )
    if verdict is None:
        raise KeyError(
            'Ключ "vedict" не существует'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка обязательных переменных окружения."""
    if (
        PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    ) is not None:
        return True
    else:
        if PRACTICUM_TOKEN is None:
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                'PRACTICUM_TOKEN'
            )
        if TELEGRAM_TOKEN is None:
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                'TELEGRAM_TOKEN'
            )
        if TELEGRAM_CHAT_ID is None:
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                'TELEGRAM_CHAT_ID'
            )
        return False


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(
        token=TELEGRAM_TOKEN
    )
    current_timestamp = int(
        time.time()
    )

    while True:
        try:
            response = get_api_answer(
                current_timestamp
            )
            homework = check_response(
                response
            )
            if not homework:
                logger.debug(
                    'Статус домашней работы не обновился'
                )
            else:
                send_message(
                    bot,
                    parse_status(
                        homework[
                            0
                        ]
                    )
                )
                current_timestamp = int(
                    time.time()
                )
                time.sleep(
                    RETRY_TIME
                )

        except Exception as e:
            message = f'Сбой в работе программы: {e}'
            send_message(
                bot,
                message
            )
            logger.error(
                e,
                exc_info=True
            )
            time.sleep(
                RETRY_TIME
            )


if __name__ == '__main__':
    main()
