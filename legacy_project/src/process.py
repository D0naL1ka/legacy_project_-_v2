"""Order processing - core business logic.

Reengineered (lab 8): proc() is an orchestrator (fetch -> process -> persist),
business rules live in small single-purpose functions, tax/discount logic
exists in one place, magic numbers are replaced with Enum and named constants.
"""

from collections import Counter
from enum import Enum, IntEnum

from src.db import get_data, save
from src.utils import calc, format_date


class Role(IntEnum):
    """User roles that affect tax and discount."""
    REGULAR = 2
    PREMIUM = 3


class OrderStatus(str, Enum):
    """Order statuses known to the system."""
    PAID = "paid"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


TAX_RATE_PREMIUM = 0.15
TAX_RATE_STANDARD = 0.2
DISCOUNT_LARGE_THRESHOLD = 1000
DISCOUNT_LARGE_RATE = 0.05
DISCOUNT_MEDIUM_THRESHOLD = 500
DISCOUNT_MEDIUM_RATE = 0.03


def _index_by_id(items):
    """Build {id: item} for O(1) lookup instead of a linear search per order."""
    return {item['id']: item for item in items}


def _paid_record(order, user):
    """Record for a paid order: tax and discount depend on the user's role."""
    tax = calculate_tax(order['amount'], user['role'])
    discount = get_discount(order['amount'], user['role'])
    return {
        "order_id": order['id'],
        "user": user['name'],
        "amount": order['amount'],
        "discount": discount,
        "tax": tax,
        "net": order['amount'] - discount - tax,
        "status": "processed",
        "date": format_date(order['date']),
    }


def _pending_record(order, user):
    """Record for a pending order: logged without any calculation."""
    return {
        "order_id": order['id'],
        "user": user['name'],
        "amount": order['amount'],
        "status": "pending",
        "date": format_date(order['date']),
    }


def _cancelled_record(order, user):
    """Record for a cancelled order: amount is reported as 0."""
    return {
        "order_id": order['id'],
        "user": user['name'],
        "amount": 0,
        "status": "cancelled",
        "date": format_date(order['date']),
    }


STATUS_HANDLERS = {
    OrderStatus.PAID.value: _paid_record,
    OrderStatus.PENDING.value: _pending_record,
    OrderStatus.CANCELLED.value: _cancelled_record,
}


def _process_order(order, users_by_id, products_by_id):
    """Process one order. Returns (record, None) or (None, error)."""
    user = users_by_id.get(order['user_id'])
    if user is None:
        return None, {"order_id": order['id'], "error": "user not found"}
    if order['product_id'] not in products_by_id:
        return None, {"order_id": order['id'], "error": "product not found"}
    handler = STATUS_HANDLERS.get(order['status'])
    if handler is None:
        return None, {"order_id": order['id'],
                      "error": f"unknown status: {order['status']}"}
    return handler(order, user), None


def build_summary(records, errors):
    """Count records by status and total revenue/tax of processed orders."""
    counts = Counter(r['status'] for r in records)
    processed = [r for r in records if r['status'] == 'processed']
    return {
        "processed": counts['processed'],
        "pending": counts['pending'],
        "cancelled": counts['cancelled'],
        "total_revenue": round(sum(r['net'] for r in processed), 2),
        "total_tax": round(sum(r['tax'] for r in processed), 2),
        "errors": errors,
    }


def process_orders(orders, users, products):
    """Pure business logic: no DB access, data is passed in (easy to test)."""
    users_by_id = _index_by_id(users)
    products_by_id = _index_by_id(products)
    records, errors = [], []
    for order in orders:
        record, error = _process_order(order, users_by_id, products_by_id)
        if error:
            errors.append(error)
        else:
            records.append(record)
    return {"orders": records, "summary": build_summary(records, errors)}


def proc(params=None):
    """Orchestrator: fetch data -> process orders -> persist the result.

    ``params`` is kept for backward compatibility (main.py calls proc(d))
    and is not used.
    """
    del params  # reserved, see docstring
    result = process_orders(get_data("orders"), get_data("users"),
                            get_data("products"))
    save("processed_orders", result["orders"])
    save("summary", result["summary"])
    return result


VALID_STATUSES = frozenset(status.value for status in OrderStatus)

# (check, error message) - checked in this order, the first failing rule wins
VALIDATION_RULES = (
    (lambda o: 'amount' in o, "no amount"),
    (lambda o: o['amount'] > 0, "invalid amount"),
    (lambda o: 'user_id' in o, "no user_id"),
    (lambda o: 'product_id' in o, "no product_id"),
    (lambda o: 'status' in o, "no status"),
    (lambda o: o['status'] in VALID_STATUSES, "invalid status: {status}"),
)


def validate_order(o):
    """Validate an order dict (CR-156). Returns (True, None) or (False, reason)."""
    if not o:
        return False, "empty order"
    for check, message in VALIDATION_RULES:
        if not check(o):
            return False, message.format(**o)
    return True, None


def calculate_tax(amount, role):
    """Tax for an order amount: premium rate for premium users, standard otherwise."""
    if role == Role.PREMIUM:
        return calc(amount, TAX_RATE_PREMIUM)
    return calc(amount, TAX_RATE_STANDARD)


def get_discount(amount, role):
    """Discount for premium users by amount thresholds (single source of truth)."""
    if role != Role.PREMIUM:
        return 0
    if amount > DISCOUNT_LARGE_THRESHOLD:
        return calc(amount, DISCOUNT_LARGE_RATE)
    if amount > DISCOUNT_MEDIUM_THRESHOLD:
        return calc(amount, DISCOUNT_MEDIUM_RATE)
    return 0
