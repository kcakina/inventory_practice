from datetime import datetime, timezone, timedelta

from app.db import DB, Reservation, InventoryItem, Status
from app.services import cleanup_exp_reservations, reserve_item


def _make_db(reservations, inventory):
    db = DB()
    for r in reservations:
        db.reservations[r.id] = r
    for item in inventory:
        db.inventory[item.sku] = item
    return db


def test_expired_reservation_is_cancelled():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    db = _make_db(
        [Reservation("r1", "SKU1", "u1", 5, Status.RESERVED, past)],
        [InventoryItem("SKU1", available=0)],
    )

    cleanup_exp_reservations(db)

    assert db.reservations["r1"].status == Status.CANCELLED
    assert db.inventory["SKU1"].available == 5


def test_not_yet_expired_reservation_is_untouched():
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    db = _make_db(
        [Reservation("r1", "SKU1", "u1", 3, Status.RESERVED, future)],
        [InventoryItem("SKU1", available=10)],
    )

    cleanup_exp_reservations(db)

    assert db.reservations["r1"].status == Status.RESERVED
    assert db.inventory["SKU1"].available == 10


def test_non_reserved_status_is_skipped():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    db = _make_db(
        [
            Reservation("r1", "SKU1", "u1", 2, Status.CONFIRMED, past),
            Reservation("r2", "SKU1", "u2", 4, Status.CANCELLED, past),
        ],
        [InventoryItem("SKU1", available=0)],
    )

    cleanup_exp_reservations(db)

    assert db.reservations["r1"].status == Status.CONFIRMED
    assert db.reservations["r2"].status == Status.CANCELLED
    assert db.inventory["SKU1"].available == 0


def test_multiple_expired_reservations_restore_inventory():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    db = _make_db(
        [
            Reservation("r1", "SKU1", "u1", 3, Status.RESERVED, past),
            Reservation("r2", "SKU1", "u2", 7, Status.RESERVED, past),
        ],
        [InventoryItem("SKU1", available=0)],
    )

    cleanup_exp_reservations(db)

    assert db.reservations["r1"].status == Status.CANCELLED
    assert db.reservations["r2"].status == Status.CANCELLED
    assert db.inventory["SKU1"].available == 10


def test_empty_reservations():
    db = _make_db([], [InventoryItem("SKU1", available=5)])

    cleanup_exp_reservations(db)

    assert db.inventory["SKU1"].available == 5


# --- reserve_item tests ---


def test_reserve_item_happy_path():
    db = _make_db([], [InventoryItem("SKU1", available=20)])

    body, status = reserve_item(db, "SKU1", "user1", 5)

    assert status == 200
    assert "reservation_id" in body
    assert "expires_at" in body
    assert db.inventory["SKU1"].available == 15
    res = db.reservations[body["reservation_id"]]
    assert res.status == Status.RESERVED
    assert res.sku == "SKU1"
    assert res.user_id == "user1"
    assert res.qty == 5


def test_reserve_item_exact_available():
    db = _make_db([], [InventoryItem("SKU1", available=10)])

    body, status = reserve_item(db, "SKU1", "user1", 10)

    assert status == 200
    assert db.inventory["SKU1"].available == 0


def test_reserve_item_qty_zero_returns_400():
    db = _make_db([], [InventoryItem("SKU1", available=10)])

    body, status = reserve_item(db, "SKU1", "user1", 0)

    assert status == 400
    assert "error" in body
    assert db.inventory["SKU1"].available == 10


def test_reserve_item_qty_negative_returns_400():
    db = _make_db([], [InventoryItem("SKU1", available=10)])

    body, status = reserve_item(db, "SKU1", "user1", -3)

    assert status == 400
    assert "error" in body
    assert db.inventory["SKU1"].available == 10


def test_reserve_item_unknown_sku_returns_404():
    db = _make_db([], [InventoryItem("SKU1", available=10)])

    body, status = reserve_item(db, "DOESNOTEXIST", "user1", 1)

    assert status == 404
    assert "error" in body


def test_reserve_item_insufficient_inventory_returns_409():
    db = _make_db([], [InventoryItem("SKU1", available=3)])

    body, status = reserve_item(db, "SKU1", "user1", 5)

    assert status == 409
    assert "error" in body
    assert db.inventory["SKU1"].available == 3


def test_reserve_item_zero_available_returns_409():
    db = _make_db([], [InventoryItem("SKU1", available=0)])

    body, status = reserve_item(db, "SKU1", "user1", 1)

    assert status == 409
    assert "error" in body


def test_reserve_item_sets_expiry_about_two_minutes():
    db = _make_db([], [InventoryItem("SKU1", available=10)])
    before = datetime.now(timezone.utc)

    body, status = reserve_item(db, "SKU1", "user1", 1)

    after = datetime.now(timezone.utc)
    res = db.reservations[body["reservation_id"]]
    assert res.expires_at >= before + timedelta(minutes=2) - timedelta(seconds=1)
    assert res.expires_at <= after + timedelta(minutes=2) + timedelta(seconds=1)


def test_reserve_item_multiple_reserves_decrement_correctly():
    db = _make_db([], [InventoryItem("SKU1", available=20)])

    reserve_item(db, "SKU1", "user1", 5)
    reserve_item(db, "SKU1", "user2", 8)

    assert db.inventory["SKU1"].available == 7
    assert len(db.reservations) == 2