import importlib
import inspect
import os
import re

import pytest

from src import shipping

ROOT = os.path.join(os.path.dirname(__file__), "..")
ENV_KEYS = ("NP_API_KEY", "UP_LOGIN", "UP_PASSWORD", "COURIER_TOKEN")


def _reload_shipping(monkeypatch, env=None):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    if env:
        for key, value in env.items():
            monkeypatch.setenv(key, value)

    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: None)

    return importlib.reload(shipping)


@pytest.fixture(autouse=True)
def _restore_shipping_module():
    yield
    importlib.reload(shipping)

def test_credentials_not_hardcoded():
    source = inspect.getsource(shipping)
    assert "a9cdf3b2" not in source, "API key still hardcoded!"
    assert "UkrPoshta#2019" not in source, "Password still hardcoded!"
    assert "company_shipper_2019" not in source, "Login still hardcoded!"
    assert "internal_courier_prod" not in source, "Courier token still hardcoded!"


def test_credentials_read_from_environment(monkeypatch):
    mod = _reload_shipping(monkeypatch, {
        "NP_API_KEY": "test-np-key", "UP_LOGIN": "test-login",
        "UP_PASSWORD": "test-pass", "COURIER_TOKEN": "Bearer test-token",
    })
    assert mod.NP_API_KEY == "test-np-key"
    assert mod.UP_LOGIN == "test-login"
    assert mod.UP_PASSWORD == "test-pass"
    assert mod.COURIER_TOKEN == "Bearer test-token"


def test_module_imports_without_env(monkeypatch):
    mod = _reload_shipping(monkeypatch)      # no .env, no variables
    assert mod.NP_API_KEY == "" and mod.UP_PASSWORD == ""
    assert mod.UP_LOGIN == "" and mod.COURIER_TOKEN == ""


def test_public_urls_unchanged(monkeypatch):
    mod = _reload_shipping(monkeypatch)
    assert mod.NP_API_URL == "https://api.novaposhta.ua/v2.0/json/"
    assert mod.UP_API_URL == "https://www.ukrposhta.ua/ecom/0.0.1/"


def test_env_file_is_gitignored():
    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    assert ".env" in lines


def test_env_example_has_no_real_values():
    with open(os.path.join(ROOT, ".env.example"), encoding="utf-8") as f:
        content = f.read()
    for key in ENV_KEYS:
        assert re.search(rf"^{key}=\s*$", content, re.MULTILINE), key


@pytest.mark.parametrize("weight,distance,method,fragile,expected", [
    (0.4, 100, 1, False, 45),
    (3, 400, 1, False, 88.0),
    (1, 600, 2, False, 132.0),
    (5, 20, 3, False, 125.0),
    (1, 100, 4, False, 500),
    (1, 100, 1, True, 71.5),
])
def test_shipping_cost_unchanged(monkeypatch, weight, distance, method, fragile, expected):
    mod = _reload_shipping(monkeypatch)
    assert mod.calculate_shipping_cost(weight, distance, method, fragile) == expected


def test_create_shipment_still_works(monkeypatch):
    mod = _reload_shipping(monkeypatch)
    result = mod.create_shipment(42, 1, "Kyiv", 1)
    assert result["order_id"] == 42
    assert result["tracking"].startswith("TRK42")
    assert result["carrier_response"]["success"] is True