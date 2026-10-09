# report.py
# Report generation module
# TODO: split into multiple files - this file is getting too big

import datetime
from src.utils import fmt, format_date, tot, avg, pct, get_quarter


def make_report(data, start_date, end_date=None, tp=0):
    """
    generates report
    tp: 0=summary, 1=detailed, 2=quarterly
    """
    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # filter by date
    filtered = []
    for item in data:
        item_date = item.get('date', '')
        if item_date >= start_date and item_date <= end_date:
            filtered.append(item)

    if tp == 0:
        return _make_summary(filtered)
    elif tp == 1:
        return _make_detailed(filtered)
    elif tp == 2:
        return _make_quarterly(filtered)
    else:
        return _make_summary(filtered)


def _make_summary(data):
    paid = [x for x in data if x.get('status') == 'paid']
    pending = [x for x in data if x.get('status') == 'pending']
    cancelled = [x for x in data if x.get('status') == 'cancelled']

    total = tot(paid, 'amount')
    avg_order = avg(paid, 'amount')

    return {
        "type": "summary",
        "total_orders": len(data),
        "paid": len(paid),
        "pending": len(pending),
        "cancelled": len(cancelled),
        "total_revenue": round(total, 2),
        "avg_order": round(avg_order, 2),
        "paid_pct": pct(len(paid), len(data)),
    }


def _make_detailed(data):
    rows = []
    for item in data:
        rows.append({
            "order_id": item.get('id'),
            "date": format_date(item.get('date', '')),
            "amount": fmt(item.get('amount', 0), 2),
            "status": item.get('status'),
            "user_id": item.get('user_id'),
        })
    return {
        "type": "detailed",
        "count": len(rows),
        "rows": rows
    }


def _make_quarterly(data):
    quarters = {1: [], 2: [], 3: [], 4: []}
    for item in data:
        q = get_quarter(item.get('date', ''))
        if q:
            quarters[q].append(item)

    result = {}
    for q, items in quarters.items():
        paid = [x for x in items if x.get('status') == 'paid']
        result[f"Q{q}"] = {
            "orders": len(items),
            "paid": len(paid),
            "revenue": round(tot(paid, 'amount'), 2),
            "avg": round(avg(paid, 'amount'), 2),
        }
    return {"type": "quarterly", "quarters": result}


def export_csv(data, filename):
    # added by Ivanov 2022 - quick export feature
    # format: id,date,amount,status
    lines = ["id,date,amount,status,user_id"]
    for item in data:
        line = ",".join([
            str(item.get('id', '')),
            item.get('date', ''),
            str(item.get('amount', '')),
            item.get('status', ''),
            str(item.get('user_id', ''))
        ])
        lines.append(line)
    # TODO: actually write to file (CR-178 - low priority)
    return "\n".join(lines)


def send_report_email(report, email):
    # stub - not implemented yet (CR-089)
    # was supposed to be done in Q3 2022
    print(f"TODO: send report to {email}")
    return False
