import logging
import sys
import homework


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
homework.logger.setLevel(
    logging.INFO
)
handler = logging.StreamHandler(
    sys.stdout
)
homework.logger.addHandler(
    handler
)
