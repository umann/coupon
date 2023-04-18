"""Database schema definition and functions for project Coupon"""

import datetime
import sys
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, create_engine, select

import exception as xc
from config import settings

db = sys.modules[__name__]  # ~import sql_model (self) as db


class User(SQLModel, table=True):
    """No user management in this project, we assume users exist and are already auth'd/authz'd"""

    user_name: str = Field(nullable=False, primary_key=True)


class Coupon(SQLModel, table=True):
    """Table coupon"""

    coupon_name: str = Field(nullable=False, primary_key=True)  # ?
    params_json: str = Field(nullable=False, default="{}")
    max_use_count_per_user: int = Field(nullable=True, default=None)  #!!!1
    max_use_count_global: int = Field(nullable=True, default=None)  # unlimited
    user_name: Optional[str] = Field(foreign_key="user.user_name", default=None)


class Qitem(SQLModel, table=True):
    """Table qitem for queue items"""

    # must keep autoincrement id for queue order
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime.datetime] = Field(
        default_factory=datetime.datetime.utcnow, nullable=False
    )
    # actually, a level of VIPness, we use 0 and 1 only.
    vip: int = Field(default=0, nullable=False)
    user_name: str = Field(nullable=False, foreign_key="user.user_name")
    order_id: str = Field(nullable=False)
    coupon_name: Optional[str] = Field(default=None, foreign_key="coupon.coupon_name")
    final_price: int = Field(nullable=False)
    # None if waiting in queue
    completed_at: Optional[datetime.datetime] = Field(default=None)


def class_of_table_name(table_name: str) -> SQLModel:
    """SQLModel class of table"""
    return globals()[table_name.title()]  # Poor Man's ucfirst


def get_one_record(
    table_name: str, column: str, value: str | None, strict: bool = False
):
    """Get one record from a table"""
    if value is None:
        if strict:
            raise xc.CouponUserError(f"Undefined {column}")
        return None
    cls = class_of_table_name(table_name)
    statement = select(cls).where(getattr(cls, column) == value)
    with Session(db.engine) as session:
        return session.exec(statement).first() or xc.raiser(
            xc.Coupon404(f"No such {column}")
        )


def add_one_record(
    table_name: str, record: dict | SQLModel, session: Session = None
) -> None:
    """Add one record to a table"""

    cls = class_of_table_name(table_name)
    if not isinstance(record, SQLModel):
        record = cls(**record)
    if session is None:
        with Session(db.engine) as session:
            session.add(record)
            session.commit()
    else:  #
        session.add(record)


def init():
    """Create tables"""
    with Session(db.engine) as session:
        try:
            for table_name, records in settings.init_db_records.items():
                cls = class_of_table_name(table_name)
                for record in records:  # add_all
                    session.add(cls(**record))
            session.commit()
        except IntegrityError:
            pass  # If any of them already exists, assume init has been run before


def drop_all():
    """Drop tables, for test only"""
    SQLModel.metadata.drop_all(db.engine)


def delete_from_variable_tables():
    """Delete all from tables that are modified (i.e. NOT constant tables user and coupon), for test only
    i.e Delete all Coupons and Queue Items
    https://github.com/tiangolo/sqlmodel/issues/181#issuecomment-992416067
    "now I can see only single object-level deletes"
    """
    with Session(db.engine) as session:
        for cls in [db.Qitem, db.Coupon]:  # order is important
            statement = select(cls)
            results = session.exec(statement)
            for record in results:
                session.delete(record)
        session.commit()


def XXdelete_from_variable_tables():
    """Delete all from tables that are modified (i.e. NOT constant tables user and coupon), for test only
    i.e Delete all Coupons and Queue Items
    """
    with Session(db.engine) as session:
        for cls in [db.Qitem, db.Coupon]:  # order is important
            delete_results(session, session.exec(select(cls)))
        session.commit()


def delete_results(session, results) -> None:
    """
     https://github.com/tiangolo/sqlmodel/issues/181#issuecomment-992416067
    "now I can see only single object-level deletes"
    """
    for record in results:
        session.delete(record)


engine = create_engine(settings.db_url)
SQLModel.metadata.create_all(db.engine)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--drop":
    drop_all()
else:
    init()
