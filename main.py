import json
import os
import re
import time
import urllib.request

from fastapi import FastAPI

ORDERS_URL = os.environ.get("ORDERS_URL", "https://test.ooobs.ru/api/orders")
CACHE_TTL = 30

app = FastAPI(title="Orders sync")
_cache = {"ts": 0.0, "orders": None}


def fetch_orders():
    now = time.time()
    if _cache["orders"] is not None and now - _cache["ts"] < CACHE_TTL:
        return _cache["orders"]
    try:
        req = urllib.request.Request(ORDERS_URL, headers={"User-Agent": "orders-sync/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            orders = json.loads(r.read().decode("utf-8"))
        _cache.update(ts=now, orders=orders)
        return orders
    except Exception:
        if _cache["orders"] is not None:
            return _cache["orders"]  # last good copy
        raise


def normalize_phone(raw):
    digits = re.sub(r"\D", "", str(raw or ""))
    if len(digits) == 10:
        digits = "7" + digits
    elif len(digits) == 11 and digits[0] in "78":
        digits = "7" + digits[1:]
    else:
        return None
    return "+" + digits


def build_result(orders):
    best = {}  # phone -> order (insertion order = first appearance)
    invalid = 0
    for o in orders:
        phone = normalize_phone(o.get("phone"))
        if phone is None:
            invalid += 1
            continue
        amount = o.get("amount") or 0
        key = (amount, o.get("created_at") or "")
        cur = best.get(phone)
        if cur is None or key > cur[0]:
            best[phone] = (key, o)
    valid = len(orders) - invalid
    clients = [
        {
            "name": o.get("name", ""),
            "phone": phone,
            "email": o.get("email", ""),
            "amount": o.get("amount", 0),
        }
        for phone, (_, o) in best.items()
    ]
    return {
        "clients": clients,
        "stats": {
            "received": len(orders),
            "unique": len(clients),
            "duplicates_merged": valid - len(clients),
            "invalid_dropped": invalid,
        },
    }


@app.get("/")
@app.get("/result")
@app.get("/sync")
def result():
    return build_result(fetch_orders())


@app.get("/health")
def health():
    return {"ok": True}
