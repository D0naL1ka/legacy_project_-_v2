# tests/test_process.py
# Characterization + unit tests for src/process.py (reengineering, lab 8, variant 2).
# The DB layer (get_data / save) is replaced with mocks, so no data/ files are needed.

import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import process  # noqa: E402

USERS = [
    {"id": 1, "name": "Premium User", "role": 3},
    {"id": 2, "name": "Regular User", "role": 2},
    {"id": 4, "name": "Other User", "role": 4},
]
PRODUCTS = [{"id": 10, "name": "Widget"}]
ORDERS = [
    {"id": 1, "user_id": 1, "product_id": 10, "amount": 1200.0, "status": "paid", "date": "2024-01-15"},
    {"id": 2, "user_id": 1, "product_id": 10, "amount": 600.0, "status": "paid", "date": "2024-01-16"},
    {"id": 3, "user_id": 1, "product_id": 10, "amount": 400.0, "status": "paid", "date": "2024-01-17"},
    {"id": 4, "user_id": 2, "product_id": 10, "amount": 500.0, "status": "paid", "date": "2024-02-01"},
    {"id": 5, "user_id": 4, "product_id": 10, "amount": 100.0, "status": "paid", "date": "2024-02-02"},
    {"id": 6, "user_id": 2, "product_id": 10, "amount": 80.0, "status": "pending", "date": "2024-02-03"},
    {"id": 7, "user_id": 1, "product_id": 10, "amount": 350.0, "status": "cancelled", "date": "2024-02-10"},
    {"id": 8, "user_id": 1, "product_id": 10, "amount": 50.0, "status": "refunded", "date": "2024-02-11"},
    {"id": 9, "user_id": 99, "product_id": 10, "amount": 10.0, "status": "paid", "date": "2024-02-12"},
    {"id": 10, "user_id": 1, "product_id": 999, "amount": 10.0, "status": "paid", "date": "2024-02-13"},
]
TABLES = {"orders": ORDERS, "users": USERS, "products": PRODUCTS}


def run_proc(tables=None):
    tables = TABLES if tables is None else tables
    with mock.patch("src.process.get_data", side_effect=tables.get) as get_data, \
            mock.patch("src.process.save") as save:
        result = process.proc()
    return result, get_data, save


# ---------- characterization tests: behaviour of proc() must not change ----------

def test_proc_summary_totals():
    result, _, _ = run_proc()
    s = result["summary"]
    assert s["processed"] == 5
    assert s["pending"] == 1
    assert s["cancelled"] == 1
    assert s["total_revenue"] == 2272.0
    assert s["total_tax"] == 450.0


def test_proc_errors_kept_in_order():
    result, _, _ = run_proc()
    assert result["summary"]["errors"] == [
        {"order_id": 8, "error": "unknown status: refunded"},
        {"order_id": 9, "error": "user not found"},
        {"order_id": 10, "error": "product not found"},
    ]


def test_proc_paid_premium_record_shape():
    result, _, _ = run_proc()
    assert result["orders"][0] == {
        "order_id": 1, "user": "Premium User", "amount": 1200.0,
        "discount": 60.0, "tax": 180.0, "net": 960.0,
        "status": "processed", "date": "15.01.2024",
    }


def test_proc_pending_and_cancelled_records():
    result, _, _ = run_proc()
    by_id = {r["order_id"]: r for r in result["orders"]}
    assert by_id[6] == {"order_id": 6, "user": "Regular User", "amount": 80.0,
                        "status": "pending", "date": "03.02.2024"}
    assert by_id[7] == {"order_id": 7, "user": "Premium User", "amount": 0,
                        "status": "cancelled", "date": "10.02.2024"}


def test_proc_persists_results():
    result, _, save = run_proc()
    save.assert_any_call("processed_orders", result["orders"])
    save.assert_any_call("summary", result["summary"])


def test_proc_reads_three_tables():
    _, get_data, _ = run_proc()
    assert sorted(c.args[0] for c in get_data.call_args_list) == ["orders", "products", "users"]


def test_proc_empty_orders():
    result, _, _ = run_proc({"orders": [], "users": USERS, "products": PRODUCTS})
    assert result["orders"] == []
    assert result["summary"]["processed"] == 0
    assert result["summary"]["total_revenue"] == 0


def test_proc_accepts_legacy_params_argument():
    # main.py calls proc(d) - the positional argument must stay accepted
    with mock.patch("src.process.get_data", side_effect=TABLES.get), mock.patch("src.process.save"):
        assert "summary" in process.proc("2024-01-01")


# ---------- parameterized tests per user type (premium / regular / other) ----------

@pytest.mark.parametrize("role, amount, tax, discount, net", [
    (3, 1200.0, 180.0, 60.0, 960.0),    # premium, > 1000 -> 5 %
    (3, 1000.0, 150.0, 30.0, 820.0),    # premium, exactly 1000 -> 3 %
    (3, 600.0, 90.0, 18.0, 492.0),      # premium, > 500 -> 3 %
    (3, 500.0, 75.0, 0, 425.0),         # premium, exactly 500 -> no discount
    (2, 1200.0, 240.0, 0, 960.0),       # regular - standard tax, no discount
    (4, 1200.0, 240.0, 0, 960.0),       # other role - same as regular
])
def test_proc_paid_order_by_user_type(role, amount, tax, discount, net):
    tables = {
        "orders": [{"id": 1, "user_id": 1, "product_id": 10, "amount": amount,
                    "status": "paid", "date": "2024-03-01"}],
        "users": [{"id": 1, "name": "U", "role": role}],
        "products": PRODUCTS,
    }
    result, _, _ = run_proc(tables)
    rec = result["orders"][0]
    assert (rec["tax"], rec["discount"], rec["net"]) == (tax, discount, net)
    assert result["summary"]["total_tax"] == tax


@pytest.mark.parametrize("role, amount, expected", [
    (3, 100.0, 15.0), (2, 100.0, 20.0), (4, 100.0, 20.0), (1, 100.0, 20.0),
])
def test_calculate_tax(role, amount, expected):
    assert process.calculate_tax(amount, role) == expected


@pytest.mark.parametrize("role, amount, expected", [
    (3, 1000.01, 50.0), (3, 1000.0, 30.0), (3, 500.01, 15.0),
    (3, 500.0, 0), (3, 0, 0), (2, 5000.0, 0), (4, 5000.0, 0),
])
def test_get_discount(role, amount, expected):
    assert process.get_discount(amount, role) == expected


# ---------- validate_order(): boundary cases ----------

VALID = {"amount": 10.0, "user_id": 1, "product_id": 10, "status": "paid"}


def without(key):
    return {k: v for k, v in VALID.items() if k != key}


@pytest.mark.parametrize("order, expected", [
    (VALID, (True, None)),
    (None, (False, "empty order")),
    ({}, (False, "empty order")),
    (without("amount"), (False, "no amount")),
    ({**VALID, "amount": 0}, (False, "invalid amount")),
    ({**VALID, "amount": -1}, (False, "invalid amount")),
    ({**VALID, "amount": 0.01}, (True, None)),
    (without("user_id"), (False, "no user_id")),
    (without("product_id"), (False, "no product_id")),
    (without("status"), (False, "no status")),
    ({**VALID, "status": "shipped"}, (False, "invalid status: shipped")),
    ({**VALID, "status": "pending"}, (True, None)),
    ({**VALID, "status": "cancelled"}, (True, None)),
    ({**VALID, "status": "refunded"}, (True, None)),
    # order of checks is part of the contract: amount is checked before user_id
    ({"amount": -5, "product_id": 10, "status": "paid"}, (False, "invalid amount")),
])
def test_validate_order(order, expected):
    assert process.validate_order(order) == expected


# ---------- unit tests for extracted helpers (iteration 3) ----------

def test_index_by_id():
    assert process._index_by_id(USERS)[2]["name"] == "Regular User"
    assert process._index_by_id([]) == {}


@pytest.mark.parametrize("order_id, expected_status", [(1, "processed"), (6, "pending"), (7, "cancelled")])
def test_process_order_dispatches_by_status(order_id, expected_status):
    order = next(o for o in ORDERS if o["id"] == order_id)
    record, error = process._process_order(order, process._index_by_id(USERS),
                                           process._index_by_id(PRODUCTS))
    assert error is None
    assert record["status"] == expected_status


def test_process_order_unknown_status_is_error():
    order = {**ORDERS[0], "status": "refunded"}
    record, error = process._process_order(order, process._index_by_id(USERS),
                                           process._index_by_id(PRODUCTS))
    assert record is None
    assert error == {"order_id": 1, "error": "unknown status: refunded"}


# ---------- process_orders() / build_summary(): no DB, no mocks (iteration 4) ----------

def test_process_orders_is_pure():
    with mock.patch("src.process.get_data") as get_data, mock.patch("src.process.save") as save:
        result = process.process_orders(ORDERS, USERS, PRODUCTS)
    get_data.assert_not_called()
    save.assert_not_called()
    assert result["summary"]["total_revenue"] == 2272.0


def test_build_summary_counts_and_totals():
    records = [
        {"status": "processed", "net": 80.0, "tax": 20.0},
        {"status": "processed", "net": 0.1, "tax": 0.2},
        {"status": "pending"},
        {"status": "cancelled"},
    ]
    s = process.build_summary(records, [{"order_id": 1, "error": "x"}])
    assert (s["processed"], s["pending"], s["cancelled"]) == (2, 1, 1)
    assert s["total_revenue"] == 80.1
    assert s["total_tax"] == 20.2
    assert len(s["errors"]) == 1


def test_build_summary_empty():
    assert process.build_summary([], []) == {
        "processed": 0, "pending": 0, "cancelled": 0,
        "total_revenue": 0, "total_tax": 0, "errors": []}
