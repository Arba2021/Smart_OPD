import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_sms(phone: str, message: str):
    logger.info(f"[SMS to {phone}]: {message}")
    return True

async def send_sms_bulk(phones: list[str], message: str):
    for phone in phones:
        logger.info(f"[BULK SMS to {phone}]: {message}")
    return True