"""Configuration for project Coupon"""
import json
import string
from pydantic import BaseSettings


SECS_PER_DAY = 24 * 60 * 60
DEFAULT_CURRENCY = "HUF"
SOME_MONEY = 1000


def jdump(**kwargs) -> str:
    """shorthand"""
    return json.dumps(kwargs)


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """Config elements"""

    db_url = "postgresql://couponmaster:k9u8P7o6n@localhost:5432/coupon"
    init_db_records = {
        "user": [{"user_name": "john_smith"}, {"user_name": "maria_de_silva"}],
    }

    coupon_alphabet = string.ascii_uppercase + string.digits
    coupon_name_len = 5
    max_queue_len = 30
    min_frequenter_orders = 10  # returning customer


settings = Settings()
