"""Coupon service layer for project Coupon"""
import json
import sys
import random

from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from config import settings
import base_model as bm
import db
import exception as xc
import coupon_params.pricing
import coupon_params.queuing

coupon_params = {
    "pricing": coupon_params.pricing,
    "queuing": coupon_params.queuing,
}  # sry

coupon = sys.modules[__name__]  # ~import sql_model (self) as db
NTRIES_INSERT_RAND = 10


def create(coupon_item: bm.CreateCoupon) -> dict:
    """Implement POST /coupon"""

    # to make sure user exists in user table
    db.get_one_record("user", "user_name", coupon_item.user_name)

    if coupon_item.coupon_name is None:
        _generate_name(coupon_item)
    else:  # use existing coupon_name
        try:
            _insert(coupon_item)
        except IntegrityError as err:
            if "already exists" in str(err):
                raise xc.CouponUserError("coupon_name already in use") from err
            raise xc.CouponUserError(f"{err}") from err

    return {"coupon_name": coupon_item.coupon_name}


# def XXXXget_by_name(coupon_name: str) -> dict:
#     """Implement GET /coupon/{coupon_name}"""
#     return _coupon_dict(*db.get_one_record("coupon", coupon_name))


def get_by_name(coupon_name: str) -> dict:
    """Implement GET /coupon/{coupon_name}"""
    with Session(db.engine) as session:
        statement = select(db.Coupon).where(db.Coupon.coupon_name == coupon_name)
        first = session.exec(statement).first() or xc.raiser(
            xc.Coupon404("No such coupon_name")
        )
    # raise Exception(str(first))
    return _coupon_dict(first)


def get_all() -> dict:
    """Implement GET /coupon"""
    with Session(db.engine) as session:
        results = session.exec(select(db.Coupon))
        return {"coupons": [_coupon_dict(*record) for record in results]}


def _coupon_dict(coupon_item: bm.CreateCoupon | db.Coupon) -> dict:
    """Return what is to be stored internally in Py data struct, also returned by API"""
    return {
        **{
            i: getattr(coupon_item, i)
            for i in (
                "coupon_name",
                "max_use_count_per_user",
                "max_use_count_global",
                "user_name",
            )
        },
        "params": getattr(
            coupon_item, "params", json.loads(getattr(coupon_item, "params_json", "{}"))
        ),
    }


def apply(qitem: bm.CreateQitem, record: dict) -> None:  # modify in-place
    """Apply coupon params on queue item record before adding to queue"""
    if qitem.coupon_name is None:
        return  # no coupon to apply

    coupon_dict = coupon.get_by_name(qitem.coupon_name)
    cuser = coupon_dict["user_name"]
    if cuser is not None and cuser != qitem.user_name:
        raise xc.CouponUserError("This coupon is reserved for another user")

    if maxc := coupon_dict["max_use_count_per_user"] is not None:
        with Session(db.engine) as session:
            used_count = session.exec(
                select([func.count(db.Qitem.id)])
                .where(db.Qitem.coupon_name == qitem.coupon_name)
                .where(db.Qitem.user_name == qitem.user_name)
            ).one()
        if used_count >= maxc:
            raise xc.CouponUserError("You cannot use this coupon more")
    maxc = coupon_dict["max_use_count_global"]
    if maxc is not None:
        with Session(db.engine) as session:
            statement = select(db.Qitem.id).where(
                db.Qitem.coupon_name == qitem.coupon_name
            )
            used_count = len(list(session.exec(statement)))
        if used_count >= maxc:
            raise xc.CouponUserError(
                "Sorry, the framework for this coupon has been exhausted by customers"
            )

    params = coupon_dict["params"]
    ret = []
    for module_name, func_dict in params.items():
        for func_name, arg in func_dict.items():
            ret.append([func_name, arg])
            try:
                module = coupon_params[module_name]
                function = getattr(module, func_name)
            except (AttributeError, KeyError) as err:  # paranoia
                raise xc.CouponSystemError(
                    f"Invalid param {module_name}.{func_name} in {coupon_dict}: {params} {err}"
                ) from err
            function(
                record, arg, params
            )  # modify record in-place according to each coupon param
    return ret


def _generate_name(coupon_item: bm.CreateCoupon) -> None:
    """Update coupon_item.coupon_name in-place"""
    for _ in range(NTRIES_INSERT_RAND):
        coupon_item.coupon_name = "".join(
            random.choice(settings.coupon_alphabet)
            for _ in range(settings.coupon_name_len)
        )
        try:
            _insert(coupon_item)
            return
        except IntegrityError:
            coupon_item.coupon_name = None
    raise xc.CouponError(
        f"Could not generate coupon name in {NTRIES_INSERT_RAND} tries"
    )


def _insert(coupon_item: bm.CreateCoupon) -> None:
    """
    Called from 2 places:
    1. Predefined coupon name (die if already exists)
    2. Generating new coupon name (retry in a loop if already exists)
    """
    dic = _coupon_dict(coupon_item)
    dic["params_json"] = json.dumps(dic.pop("params"))
    rec = db.Coupon(**dic)
    with Session(db.engine) as session:
        session.add(rec)  # might raise on conflict (dup key)
        session.commit()
