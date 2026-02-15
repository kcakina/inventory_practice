from app.db import DB, Reservation, InventoryItem, Status
from datetime import datetime, timezone, timedelta
import uuid

def cleanup_exp_reservations(db: DB) -> None:
    now = datetime.now(timezone.utc)

    for res in db.reservations.values():
        if res.status != Status.RESERVED:
            continue

        if res.expires_at < now:
            res.status = Status.CANCELLED
            db.inventory[res.sku].available += res.qty

def reserve_item(db: DB, sku: str, user_id: str, qty: int) -> tuple[dict, int]:
    if qty <= 0:
        return {"error": "qty must be greater than 0"}, 400

    with db.lock:
        cleanup_exp_reservations(db)

        item = db.inventory.get(sku)
        if item is None:
            return {"error": "sku not found"}, 404

        if item.available < qty:
            return {"error": "insufficient inventory"}, 409

        item.available -= qty

        reservation_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)
        reservation = Reservation(
            id=reservation_id,
            sku=sku,
            user_id=user_id,
            qty=qty,
            status=Status.RESERVED,
            expires_at=expires_at,
        )
        db.reservations[reservation_id] = reservation

    return {"reservation_id": reservation_id, "expires_at": expires_at.isoformat()}, 200
