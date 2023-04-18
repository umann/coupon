"""Modify admission and position into queue according to queing params of Coupon"""


def vip(record: dict, value: int, _dummy_params) -> None:
    """Upgrade queue item to vip"""
    record["vip"] = value


def reopen(record: dict, value: bool, _dummy_params) -> None:
    """Allow insert to queue even if waiting room is full (i.e. reopen door)"""
    record["_check_queue_len"] = not value
