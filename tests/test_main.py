"""Unit test for project Coupon"""
import os
import sys
import unittest
from fastapi.testclient import TestClient

test_dir = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(test_dir, ".."))

import db  # pylint: disable=wrong-import-position  # why should it go to top? Too nice coupon_name?
from main import app  # pylint: disable=import-error,wrong-import-position
from config import settings  # pylint: disable=wrong-import-position  # why should it go to top? Too nice coupon_name?

client = TestClient(app)

# For json's sake:
null = None # pylint: disable=invalid-name
true = True # pylint: disable=invalid-name
false = False # pylint: disable=invalid-name

class TestApi(unittest.TestCase):
    """Test class"""

    def setUp(self):
        """Delete all Coupons and Queue Items"""
        db.delete_from_variable_tables()

    def tearDown(self):
        pass # don't do anything so we can examine records inserted by last test afterwards

    def test_basic_oks(self):
        """Test basic OK's"""
        response = client.get("/queue")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(),  {'queue_items': []})

    def test_basic_errors(self):
        """Test basic errors"""

        response = client.get("/items/foo", headers={"X-Token": "coneofsilence"})
        self.assertEqual(response.status_code, 404, "You came to the wrong neighborhood")

        response = client.post("/coupon", json={
            "params": {},
            "coupon_name": "whatever",
            "user_name": "Nessuno",
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.status_code, 404,)
        self.assertEqual(response.json(), {
              "message": "No such user_name"
        })

    def test_max_queue_len(self):
        """Test for queue length check"""
        self.maxDiff = None # pylint: disable=invalid-name
        response = client.post("/coupon", json={
            "params": {"queuing": {"vip": 1}},
            "coupon_name": "VIP pub ~ ~",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "VIP pub ~ ~"
        })
        response = client.post("/coupon", json={
            "params": {"queuing": {"reopen": True}},
            "coupon_name": "VIP+Reopen pub ~ ~",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name":  "VIP+Reopen pub ~ ~"
        })

        # Fill the queue
        for _ in range(settings.max_queue_len):
            response = client.post("/queue", json={
                "user_name": "john_smith",
                "coupon_name": "VIP pub ~ ~",
                "list_price": 20000,
                "order_id": "RDR1/" + str(_)
            },)
            self.assertIn("final_price", response.json(), _)

        # Fail to add to full queue with no-Reopen coupon
        for _ in range(3):
            response = client.post("/queue", json={
                "user_name": "john_smith",
                "coupon_name": "VIP pub ~ ~",
                "list_price": 20000,
                "order_id": "RDR2/" + str(_)
            },)
            self.assertEqual(response.json(), {
                "message": "Sorry, the waiting room is full. Please try again later"
            })

        # Fail to add to full queue without coupon
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": null,
            "list_price": 20000,
            "order_id": "RDR44"
        },)
        self.assertEqual(response.json(), {
            "message": "Sorry, the waiting room is full. Please try again later"
        })

        # Succees to overbook full queue with Reopen coupon
        for _ in range(3):
            response = client.post("/queue", json={
                "user_name": "john_smith",
                "coupon_name": "VIP+Reopen pub ~ ~",
                "list_price": 20000,
                "order_id":  "RDR3/" + str(_)
            },)
            self.assertIn("final_price", response.json())


    def test_max_use_count_per_user(self):
        """Test max_use_count_per_user"""

        response = client.post("/coupon", json={
            "params": {"queuing": {"vip": 1}},
            "coupon_name": "VIP pub 1 ~",
            "user_name": null,
            "max_use_count_per_user": 1,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "VIP pub 1 ~"
        })

        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub 1 ~",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertIn("final_price", response.json())

        # 2nd add fails for same user
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub 1 ~",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertEqual(response.json(), {
            "message": "You cannot use this coupon more"
        })

        # One add succeeds for another user
        response = client.post("/queue", json={
            "user_name": "maria_de_silva",
            "coupon_name": "VIP pub 1 ~",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertIn("final_price", response.json())


    def test_max_use_count_global(self):
        """Test max_use_count_global"""

        response = client.post("/coupon", json={
            "params": {"queuing": {"vip": 1}},
            "coupon_name": "VIP pub ~ 1",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": 1
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "VIP pub ~ 1"
        })

        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub ~ 1",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertIn("final_price", response.json())

        # 2nd add fails for same user
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub ~ 1",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertEqual(response.json(), {
            "message": "Sorry, the framework for this coupon has been exhausted by customers"
        })

        # One add fails for another user
        response = client.post("/queue", json={
            "user_name": "maria_de_silva",
            "coupon_name": "VIP pub ~ 1",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertEqual(response.json(), {
            "message": "Sorry, the framework for this coupon has been exhausted by customers"
        })

    def test_pricing_percent(self):
        """Test discount by percentage"""

        response = client.post("/coupon", json={
            "params": {"pricing": {"percent": -15}},
            "coupon_name": "-15% pub ~ ~",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "-15% pub ~ ~"
        })

        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "-15% pub ~ ~",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertEqual(response.json()["final_price"], 17000)


    def test_pricing_amount(self):
        """Test discount by amount"""

        response = client.post("/coupon", json={
            "params": {"pricing": {"amount": -2000}},
            "coupon_name": "-2000HUF pub ~ ~",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "-2000HUF pub ~ ~"
        })

        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "-2000HUF pub ~ ~",
            "list_price": 20000,
            "order_id": "RDR42"
        },)
        self.assertEqual(response.json()["final_price"], 18000)


    def test_vip(self):
        """Test VIP (overtake queue)"""

        response = client.post("/coupon", json={
            "params": {"queuing": {"vip": 1}},
            "coupon_name": "VIP pub ~ ~",
            "user_name": null,
            "max_use_count_per_user": null,
            "max_use_count_global": null
        },)
        self.assertEqual(response.json(), {
              "coupon_name": "VIP pub ~ ~"
        })

        # Add a non-VIP order
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": null,
            "list_price": 20000,
            "order_id": "1st non-VIP"
        },)
        self.assertIn("final_price", response.json())

        # Add a VIP order
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub ~ ~",
            "list_price": 20000,
            "order_id": "1st VIP"
        },)
        self.assertIn("final_price", response.json())

        # Add another VIP order
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": "VIP pub ~ ~",
            "list_price": 20000,
            "order_id": "2nd VIP"
        },)

        # Add another non-VIP order
        response = client.post("/queue", json={
            "user_name": "john_smith",
            "coupon_name": null,
            "list_price": 20000,
            "order_id": "1st non-VIP"
        },)
        self.assertIn("final_price", response.json())
        response = client.get("/queue")
        order_ids = [q["order_id"] for q in  response.json()["queue_items"]]
        self.assertEqual(order_ids, ["1st VIP", "2nd VIP", "1st non-VIP", "1st non-VIP"])


if __name__ == "__main__":
    unittest.main()
