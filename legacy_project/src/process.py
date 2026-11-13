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


def proc(params=None):
    """process orders - main business flow"""
    orders = get_data("orders")
    users = get_data("users")
    products = get_data("products")

    result = []
    errors = []
    total_revenue = 0
    total_tax = 0

    for o in orders:
        # find user
        u = None
        for usr in users:
            if usr['id'] == o['user_id']:
                u = usr
                break

        if u is None:
            errors.append({"order_id": o['id'], "error": "user not found"})
            continue

        # find product
        pr = None
        for prod in products:
            if prod['id'] == o['product_id']:
                pr = prod
                break

        if pr is None:
            errors.append({"order_id": o['id'], "error": "product not found"})
            continue

        # process based on status
        if o['status'] == OrderStatus.PAID:
            if u['role'] == Role.PREMIUM:
                # premium user
                tax = calc(o['amount'], TAX_RATE_PREMIUM)
                discount = 0
                if o['amount'] > DISCOUNT_LARGE_THRESHOLD:
                    discount = calc(o['amount'], DISCOUNT_LARGE_RATE)
                elif o['amount'] > DISCOUNT_MEDIUM_THRESHOLD:
                    discount = calc(o['amount'], DISCOUNT_MEDIUM_RATE)
                net = o['amount'] - discount - tax
                total_revenue += net
                total_tax += tax
                result.append({
                    "order_id": o['id'],
                    "user": u['name'],
                    "amount": o['amount'],
                    "discount": discount,
                    "tax": tax,
                    "net": net,
                    "status": "processed",
                    "date": format_date(o['date'])
                })
            elif u['role'] == Role.REGULAR:
                # regular user
                tax = calc(o['amount'], TAX_RATE_STANDARD)
                net = o['amount'] - tax
                total_revenue += net
                total_tax += tax
                result.append({
                    "order_id": o['id'],
                    "user": u['name'],
                    "amount": o['amount'],
                    "discount": 0,
                    "tax": tax,
                    "net": net,
                    "status": "processed",
                    "date": format_date(o['date'])
                })
            else:
                # other roles - no discount, standard tax
                tax = calc(o['amount'], TAX_RATE_STANDARD)
                net = o['amount'] - tax
                total_revenue += net
                total_tax += tax
                result.append({
                    "order_id": o['id'],
                    "user": u['name'],
                    "amount": o['amount'],
                    "discount": 0,
                    "tax": tax,
                    "net": net,
                    "status": "processed",
                    "date": format_date(o['date'])
                })

        elif o['status'] == OrderStatus.PENDING:
            # pending orders - just log
            result.append({
                "order_id": o['id'],
                "user": u['name'],
                "amount": o['amount'],
                "status": "pending",
                "date": format_date(o['date'])
            })

        elif o['status'] == OrderStatus.CANCELLED:
            # cancelled - skip but log
            result.append({
                "order_id": o['id'],
                "user": u['name'],
                "amount": 0,
                "status": "cancelled",
                "date": format_date(o['date'])
            })

        else:
            errors.append({
                "order_id": o['id'],
                "error": f"unknown status: {o['status']}"
            })

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
    # duplicated from proc() - should be unified (CR-212, low priority)
    if role == Role.PREMIUM:
        return calc(amount, TAX_RATE_PREMIUM)
    return calc(amount, TAX_RATE_STANDARD)


def get_discount(amount, role):
    # same logic as in proc() - also duplicated
    if role != Role.PREMIUM:
        return 0
    if amount > DISCOUNT_LARGE_THRESHOLD:
        return calc(amount, DISCOUNT_LARGE_RATE)
    if amount > DISCOUNT_MEDIUM_THRESHOLD:
        return calc(amount, DISCOUNT_MEDIUM_RATE)
    return 0

# CR-156 validation
