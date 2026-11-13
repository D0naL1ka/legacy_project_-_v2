# process.py
# Core business logic. DO NOT TOUCH without consulting senior dev.
# Last major change: 2022-08-10 (hotfix for production issue)

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


def proc(params=None):
    """process orders - main business flow"""
    orders = get_data("orders")
    users_by_id = _index_by_id(get_data("users"))
    products_by_id = _index_by_id(get_data("products"))

    result = []
    errors = []
    total_revenue = 0
    total_tax = 0

    for o in orders:
        record, error = _process_order(o, users_by_id, products_by_id)
        if error:
            errors.append(error)
            continue
        if record['status'] == 'processed':
            total_revenue += record['net']
            total_tax += record['tax']
        result.append(record)

    summary = {
        "processed": len([r for r in result if r['status'] == 'processed']),
        "pending": len([r for r in result if r['status'] == 'pending']),
        "cancelled": len([r for r in result if r['status'] == 'cancelled']),
        "total_revenue": round(total_revenue, 2),
        "total_tax": round(total_tax, 2),
        "errors": errors
    }

    save("processed_orders", result)
    save("summary", summary)

    return {"orders": result, "summary": summary}


def validate_order(o):
    # added in CR-156 - should have been here from start
    if not o:
        return False, "empty order"
    if 'amount' not in o:
        return False, "no amount"
    if o.get('amount', 0) <= 0:
        return False, "invalid amount"
    if 'user_id' not in o:
        return False, "no user_id"
    if 'product_id' not in o:
        return False, "no product_id"
    if 'status' not in o:
        return False, "no status"
    if o['status'] not in [st.value for st in OrderStatus]:
        return False, f"invalid status: {o['status']}"
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

# CR-156 validation
