"""Application for project Coupon"""
import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import base_model as bm
import coupon
import exception as xc
import queue_item

app_dir = os.path.join(os.path.dirname(__file__))
sys.path.append(app_dir)

app = FastAPI()


@app.exception_handler(xc.Coupon404)
async def exception_handler_404(_: Request, err: xc.Coupon404) -> JSONResponse:
    """Catch Not Found ("no such") errors"""
    return JSONResponse(
        status_code=404,
        content={"message": " ".join(err.args)},
    )


@app.exception_handler(xc.CouponUserError)
async def exception_handler_400(_: Request, err: xc.CouponUserError) -> JSONResponse:
    """Catch user errors"""
    return JSONResponse(
        status_code=400,
        content={"message": " ".join(err.args)},
    )


@app.exception_handler(xc.CouponSystemError)
async def exception_handler_500(_: Request, err: xc.CouponSystemError) -> JSONResponse:
    """Catch app's own errors"""
    return JSONResponse(
        status_code=500,
        content={"message": " ".join(err.args)},
    )


@app.exception_handler(Exception)
async def exception_handler_503(_: Request, err: Exception) -> JSONResponse:
    """Catch all other (runtime) errors"""
    return JSONResponse(
        status_code=503,
        content={"message": " ".join(err.args)},
    )


@app.post("/coupon")
async def create_coupon(coupon_item: bm.CreateCoupon):
    """create coupon"""
    return coupon.create(coupon_item)


@app.get("/coupon")
async def list_coupons():
    """list all coupons"""
    return coupon.get_all()


@app.get("/coupon/{coupon_name}")
async def get_coupon(coupon_name: str):
    """read coupon"""
    return coupon.get_by_name(coupon_name)


@app.post("/queue")
async def create_qitem(qitem: bm.CreateQitem):
    """create queue (order), optionally using a coupon"""
    return queue_item.create(qitem)


@app.get("/queue")
async def list_qitems():
    """list all items in queue"""
    return queue_item.get_all()


@app.get("/queue/len")
async def get_qlen():
    """ "Return the number of not completed items in the queue"""
    return queue_item.get_len()


@app.put("/queue/shift/{count}")
async def shift_qitems(count: int):
    """shift {count} queue items, for testing only to consume from the queue"""
    return queue_item.shift(count)
