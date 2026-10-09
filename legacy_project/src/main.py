# main.py
# Written by: various developers 2018-2022
# TODO: refactor someday

import sys
from src.process import proc
from src.db import get_data, save
from src.report import make_report
from src.utils import calc, fmt


def run(t, d=None):
    # main entry point
    if t == 1:
        x = get_data("users")
        r = []
        for i in range(len(x)):
            u = x[i]
            if u['status'] == 1 and u['role'] == 3 and u['age'] >= 18:
                if u['balance'] > 0:
                    tmp = calc(u['balance'], 0.15)
                    u['tax'] = tmp
                    u['net'] = u['balance'] - tmp
                    r.append(u)
                elif u['balance'] == 0:
                    pass  # skip zero balance
                else:
                    # negative balance - log somewhere
                    print("WARN: negative balance for user " + str(u['id']))
        save("processed_users", r)
        return r

    elif t == 2:
        # report mode
        if d == None:
            d = "2024-01-01"
        data = get_data("orders")
        rep = make_report(data, d)
        return rep

    elif t == 3:
        x = get_data("products")
        res = []
        for p in x:
            if p['active'] == 1:
                if p['stock'] > 0:
                    if p['price'] > 100:
                        p['discount'] = p['price'] * 0.1
                        p['final_price'] = p['price'] - p['discount']
                    else:
                        p['discount'] = 0
                        p['final_price'] = p['price']
                    res.append(p)
        return res

    elif t == 4:
        return proc(d)

    else:
        print("unknown type")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tp = int(sys.argv[1])
        dt = sys.argv[2] if len(sys.argv) > 2 else None
        result = run(tp, dt)
        print(result)
    else:
        print("Usage: python main.py <type> [date]")
