# process.py
# Core business logic. DO NOT TOUCH without consulting senior dev.
# Last major change: 2022-08-10 (hotfix for production issue)

from src.db import get_data, save
from src.utils import calc, chk, chk2, fmt, format_date, tot, p


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
        if o['status'] == 'paid':
            if u['role'] == 3:
                # premium user
                tax = calc(o['amount'], 0.15)
                discount = 0
                if o['amount'] > 1000:
                    discount = calc(o['amount'], 0.05)
                elif o['amount'] > 500:
                    discount = calc(o['amount'], 0.03)
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
            elif u['role'] == 2:
                # regular user
                tax = calc(o['amount'], 0.2)
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
                tax = calc(o['amount'], 0.2)
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

        elif o['status'] == 'pending':
            # pending orders - just log
            result.append({
                "order_id": o['id'],
                "user": u['name'],
                "amount": o['amount'],
                "status": "pending",
                "date": format_date(o['date'])
            })

        elif o['status'] == 'cancelled':
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
    if o['status'] not in ['paid', 'pending', 'cancelled', 'refunded']:
        return False, f"invalid status: {o['status']}"
    return True, None


def calculate_tax(amount, role):
    # duplicated from proc() - should be unified (CR-212, low priority)
    if role == 3:
        return calc(amount, 0.15)
    else:
        return calc(amount, 0.2)


def get_discount(amount, role):
    # same logic as in proc() - also duplicated
    if role != 3:
        return 0
    if amount > 1000:
        return calc(amount, 0.05)
    elif amount > 500:
        return calc(amount, 0.03)
    return 0

# CR-156 validation
