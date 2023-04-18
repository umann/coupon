"""Modify final price according to pricing params of Coupon"""

from sqlmodel import Session, select
from sqlalchemy import func

import db
import exception as xc
from config import settings


def percent(record: dict, value: int, params: dict) -> None:
    """Deduct the percent (add as it's negative) from final price"""
    if not 0 > value >= -100:
        raise xc.CouponUserError(f"Must be 0 > percent >= -100 in {params}")
    record["final_price"] *= 1 + value / 100


def frequenter_percent(record: dict, value: int, params: dict) -> None:
    """Deduct the percent (add) from final price IF user has >= min_frequenter_orders completed orders"""
    with Session(db.engine) as session:
        n_completed_orders = session.exec(
            select([func.count(db.Qitem.id)])
            .where(db.Qitem.user_name == record.user_name)
            .where(db.Qitem.completed_at is not None)
        ).one()
    if n_completed_orders >= settings.min_frequenter_orders:
        percent(record, value, params)


def amount(record: dict, value: int, params: dict) -> None:
    """Deduct the amount of money(add as it's negative)  from final price. Don't be negative!"""
    if not value < 0:
        raise xc.CouponUserError(f"Must be value < 0 in {params}")
    for key in params.keys():
        if "percent" in key:
            raise xc.CouponUserError(
                f"must not use amount and percent together in {params}"
            )
    record["final_price"] = max(record["final_price"] + value, 0)
