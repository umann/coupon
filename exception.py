"""Exception classes for project Coupon"""
from typing import Type


class CouponError(Exception):
    """Our base exception"""


class CouponUserError(CouponError):
    """HTTP 4xx"""


class Coupon404(CouponUserError):
    """HTTP 404"""


class CouponSystemError(CouponError):
    """HTTP 5xx"""


def raiser(err: Type[Exception]):
    """
    To be able to use "command() or raiser()"
    https://mail.python.org/pipermail/python-ideas/2014-November/029921.html"""
    raise err
