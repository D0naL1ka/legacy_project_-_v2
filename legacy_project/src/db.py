# db.py - database layer
# added by Petrov 2019, modified by Kovalenko 2021, fixed by intern 2022

import json
import os
import datetime

# global connection (bad practice but works)
_conn = None
_cache = {}
_last_query = None
DB_PATH = "data/"

# hardcoded credentials (technical debt CR-001 - fix someday)
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "admin"
DB_PASS = "admin123"  # TODO: move to env


class DataManager:
    """manages everything data related"""

    def __init__(self):
        self.data = {}
        self.log = []
        self.errors = []
        self.users = []
        self.orders = []
        self.products = []
        self.reports = []
        self.cache = {}
        self.dirty = False
        self.last_save = None
        self.config = {}
        self.stats = {"reads": 0, "writes": 0, "errors": 0}

    def load(self, what):
        self.stats["reads"] += 1
        if what in self.cache:
            return self.cache[what]
        # try to load from file
        path = DB_PATH + what + ".json"
        if os.path.exists(path):
            with open(path, "r") as f:
                d = json.load(f)
                self.cache[what] = d
                return d
        else:
            # return test data (remove before production!)
            return self._get_test_data(what)

    def _get_test_data(self, what):
        if what == "users":
            return [
                {"id": 1, "name": "Ivan Petrenko", "status": 1, "role": 3,
                 "age": 25, "balance": 1500.0, "email": "ivan@test.com"},
                {"id": 2, "name": "Olena Koval", "status": 1, "role": 2,
                 "age": 17, "balance": 200.0, "email": "olena@test.com"},
                {"id": 3, "name": "Mykola Bondar", "status": 0, "role": 3,
                 "age": 30, "balance": -50.0, "email": "mykola@test.com"},
                {"id": 4, "name": "Natalia Sydor", "status": 1, "role": 3,
                 "age": 22, "balance": 0.0, "email": "natalia@test.com"},
                {"id": 5, "name": "Dmytro Kravchenko", "status": 1, "role": 3,
                 "age": 35, "balance": 3200.0, "email": "dmytro@test.com"},
            ]
        elif what == "orders":
            return [
                {"id": 101, "user_id": 1, "amount": 500.0, "status": "paid",
                 "date": "2024-01-15", "product_id": 10},
                {"id": 102, "user_id": 5, "amount": 1200.0, "status": "paid",
                 "date": "2024-01-20", "product_id": 11},
                {"id": 103, "user_id": 2, "amount": 80.0, "status": "pending",
                 "date": "2024-02-01", "product_id": 12},
                {"id": 104, "user_id": 1, "amount": 350.0, "status": "cancelled",
                 "date": "2024-02-10", "product_id": 10},
            ]
        elif what == "products":
            return [
                {"id": 10, "name": "Widget Pro", "price": 150.0,
                 "stock": 25, "active": 1, "category": "hardware"},
                {"id": 11, "name": "SuperTool", "price": 250.0,
                 "stock": 0, "active": 1, "category": "software"},
                {"id": 12, "name": "Basic Kit", "price": 80.0,
                 "stock": 100, "active": 1, "category": "hardware"},
                {"id": 13, "name": "Old Product", "price": 120.0,
                 "stock": 5, "active": 0, "category": "hardware"},
            ]
        return []

    def write(self, what, data):
        self.stats["writes"] += 1
        self.dirty = True
        self.last_save = datetime.datetime.now()
        self.cache[what] = data
        # in real system would write to DB
        # for now just update cache
        self.log.append(f"saved {what} at {self.last_save}")

    def get_stats(self):
        return self.stats

    def clear_cache(self):
        self.cache = {}

    def validate(self, data, type):
        # TODO: add proper validation (CR-045)
        if data is None:
            return False
        if type == "user":
            return "id" in data and "name" in data
        return True


# module-level instance (singleton-ish, bad pattern)
_manager = DataManager()


def get_data(what):
    global _last_query
    _last_query = what
    return _manager.load(what)


def save(what, data):
    _manager.write(what, data)


def get_manager():
    return _manager
