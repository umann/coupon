"""Queue service layer for project Coupon"""

from sqlmodel import Session, select

import coupon
import base_model as bm
import db

import exception as xc
from config import settings


def create(qitem: bm.CreateQitem) -> dict:
    """implement POST /qitem"""
    # to make sure user exists in user table
    db.get_one_record("user", "user_name", qitem.user_name)
    record = dict(
        user_name=qitem.user_name,
        order_id=qitem.order_id,
        coupon_name=qitem.coupon_name,
        final_price=qitem.list_price,  # might be modified later
        _check_queue_len=True,
    )

    ret = coupon.apply(qitem, record)

    queue_len = get_len()
    _check_queue_len = record.pop("_check_queue_len")
    if _check_queue_len and queue_len >= settings.max_queue_len:
        raise xc.CouponUserError(
            "Sorry, the waiting room is full. Please try again later"
        )
    insert = db.Qitem(**record)
    with Session(db.engine) as session:
        session.add(insert)
        session.commit()
        session.refresh(insert)  # to get insert.id
        statement = (
            select(db.Qitem)
            .where(db.Qitem.completed_at is not None)
            .where(db.Qitem.vip >= insert.vip)
        )
        results = session.exec(statement)
        queue_position = len(list(results))
    return dict(
        final_price=insert.final_price,
        queue_position=queue_position,
        id=insert.id,
        queue_len=queue_len,
    )


def get_all() -> dict:
    """implement GET /queue"""
    queue_items = []
    with Session(db.engine) as session:
        # -1 order by desc
        statement = (
            select(db.Qitem)
            .where(db.Qitem.completed_at is not None)
            .order_by(-1 * db.Qitem.vip, db.Qitem.id)
        )
        results = session.exec(statement)
        queue_position = 0
        for record in results:
            queue_items.append(
                {
                    "queue_position": queue_position,
                    **{
                        k: getattr(record, k)
                        for k in (
                            "id",
                            "created_at",
                            "vip",
                            "user_name",
                            "order_id",
                            "coupon_name",
                            "final_price",
                        )
                    },
                }
            )
            queue_position += 1
        return {"queue_items": queue_items}


def shift(count: int) -> dict:
    """implement PUT /queue/shift/{count}"""
    with Session(db.engine) as session:
        statement = (
            select(db.Qitem)
            .where(db.Qitem.completed_at is not None)
            .order_by(-1 * db.Qitem.vip, db.Qitem.id)
            .limit(count)
        )
        results = session.exec(statement)
        db.delete_results(session, results)
        shifted = len(list(results))
        session.commit()
        return {"shifted": shifted, "queue_len": get_len()}


def get_len() -> int:
    """Return the number of not completed items in the queue"""
    with Session(db.engine) as session:
        statement = select(db.Qitem).where(db.Qitem.completed_at is not None)
        results = session.exec(statement)
        return len(list(results))  # func.count .one()
