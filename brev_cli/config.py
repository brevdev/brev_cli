import sys
import logging

logging.basicConfig(
    format="[%(levelname)s] [%(name)s] %(asctime)s %(message)s", level=logging.INFO
)
logging.StreamHandler(sys.stdout)
logger = logging.getLogger("brev-cli")


class Dev:
    api_url = "http://localhost:5000"
    log_level = logging.DEBUG
    cotter_api_key_id = "19024767-a0b2-4221-8faa-ef116dc853d0"


class Staging:
    api_url = "https://staging.brev.dev"
    log_level = logging.INFO
    cotter_api_key_id = "19024767-a0b2-4221-8faa-ef116dc853d0"


class Prod:
    api_url = "https://app.brev.dev"
    log_level = logging.WARNING
    cotter_api_key_id = "19024767-a0b2-4221-8faa-ef116dc853d0"


config = Dev

logger.setLevel(config.log_level)
