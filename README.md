# Project Coupon

## Task

### Draft

Tools to use:

- latest stable python
- fastapi
- sqlmodel
- postgres

If only a part of the whole is implemented, let it be a vertical slice.

- service layer
- model
- testing
- one endpoint is enough, but it should have coverage

Workload: max 1 weekend (or 1 day if you know the tech stack)

From end user's POV, we provide service packages

E.g. user uplads a photo of skin, we send back diagnosis and therapy plan in 2 days, user pays e.g 10kHUF.

We'd like to give users coupons that modify the package. E.g.

- discount percent (15%)
- additional discount percent for frequent buyers (not in original specs)
- discount amount: (2000 HUF)
- vip: jump to beginning of waiting queue
- reopen: allows upload even if waiting room is full

All above can be:
- combined (except percent and amount together because final price changes by the order of applying them)
- recurring coupon (any of above): usable once or N or infinite times
  - by a given user (not in original specs)
  - globally
- promo code for everyone vs. coupon for a specific user (not in original specs)

Methods to implement for a coupon:

- create
- query
- use

Methods for queue:

- create (add order)
- query (list all queue items)

### Additional details

- For one order, max one coupon can be used
- When preemting with VIP coupon, VIP users already in the queue must not be overtaken
- There is only one level of VIP (i.e. 0/1, in our case it means no/yes)
- For simplicity, uniq name is used as primary key instead of autoincrement id, except for queue where id is needed for order.

### Pending:

- Test

### Not implemented

- Logging (sry)
- User balance
- Service (price, ETA, multiple queues)
- Coupon validity time interval
- Paginating for GET /coupon and /queue
- DB locking (sry)
- Store native JSON in DB
- Exception handling for API client other than 503 (e.g. no Content-tpye: application/problem+json)
- Foreign key on delete restrict (with sa_column)
- Alerting (on e.g. ran out of free coupon names)
- Testing on separate database
- Separate requirements_test.txt
- How to put the py files under an app/ dir without breaking uvicorn :-/

## Install

```sh
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

### Database

postgres=# create user couponmaster with encrypted password 'k9u8P7o6n'; -- see db_url in config.py
postgres=# create database coupon owner couponmaster;

## Run Server

```sh
uvicorn main:app --reload   
```

## Edit

Set line length to 120

## Test

```sh
python tests/test_app.py
```

or 

```sh
pytest --cov
```

## Client Usage

```sh
curl http://localhost:8000 -X POST -d '{"what": "ever"}'
```

or from browser at http://127.0.0.1:8000/docs
