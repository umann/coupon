"""Data model for project Coupon"""
# pylint: disable=no-name-in-module # https://github.com/pydantic/pydantic/issues/1961
from pydantic import BaseModel


class CreateCoupon(BaseModel):
    """Record Structure for Create Coupon"""

    coupon_name: str | None = None  # None means generate
    params: dict = {}
    max_use_count_per_user: int | None = 1  # None means unlimited
    max_use_count_global: int | None = None  # None means unlimited
    user_name: str | None = None  # None means for everyone


class CreateQitem(BaseModel):
    """Record Structure for Create Queue Item (place order)"""

    user_name: str | None = None
    coupon_name: str | None = None
    list_price: int
    order_id: str  # API client's own reference. Note it's str, not int
