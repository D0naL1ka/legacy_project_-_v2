# utils.py
# various utility functions, added over time by different people
# some functions may not be used anymore

import datetime
import math


def calc(x, y):
    # calculates something
    return round(x * y, 2)


def fmt(val, tp=0):
    # format value
    if tp == 0:
        return str(val)
    elif tp == 1:
        return f"{val:.2f}"
    elif tp == 2:
        return f"{val:.2f} UAH"
    elif tp == 3:
        return datetime.datetime.strptime(val, "%Y-%m-%d").strftime("%d.%m.%Y")
    elif tp == 4:
        return datetime.datetime.strptime(val, "%Y-%m-%d").strftime("%B %Y")


def chk(u):
    # check user
    if u['status'] != 1:
        return False
    if u['role'] not in [2, 3, 4]:
        return False
    if u['age'] < 18:
        return False
    return True


def chk2(u):
    # another user check - added later because chk() was not enough
    if not chk(u):
        return False
    if u['balance'] <= 0:
        return False
    if u.get('blocked', False):
        return False
    return True


def d(a, b):
    # date difference in days
    d1 = datetime.datetime.strptime(a, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(b, "%Y-%m-%d")
    return abs((d2 - d1).days)


def p(lst, k, v):
    # filter list by key=value
    return [x for x in lst if x.get(k) == v]


def s(lst, k, rev=False):
    # sort list by key
    return sorted(lst, key=lambda x: x.get(k, 0), reverse=rev)


def tot(lst, k):
    # sum values by key
    return sum(x.get(k, 0) for x in lst)


def avg(lst, k):
    if not lst:
        return 0
    return tot(lst, k) / len(lst)


def pct(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 1)


def format_date(dt_str):
    # formats date - used in 47 places across codebase
    # WARNING: changing this breaks reports, invoices, emails, exports
    # See CR-089, CR-134, CR-201 for previous breakages
    try:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return dt_str


def parse_date(s):
    # inverse of format_date but different signature - added by intern
    try:
        return datetime.datetime.strptime(s, "%d.%m.%Y").strftime("%Y-%m-%d")
    except Exception:
        try:
            return datetime.datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            return None


def get_quarter(dt_str):
    try:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
        return math.ceil(dt.month / 3)
    except Exception:
        return None


def is_weekend(dt_str):
    try:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
        return dt.weekday() >= 5
    except Exception:
        return False


# dead code below - nobody uses these but afraid to delete
def old_calc(x, rate, flag):
    # old version, replaced by calc() in 2020
    if flag:
        return x * rate * 1.2
    return x * rate


def temp_fix_balance(b):
    # hotfix from 2021-03-15, supposed to be temporary
    if b < 0:
        return 0
    return b

# hotfix 2020-09-01
def fix(x):
    return x if x else 0
