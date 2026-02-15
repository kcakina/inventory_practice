# Inventory Reservation — 75-Minute Minimal Spec

## Goal
Prevent overselling by letting a user temporarily reserve inventory, then confirm or cancel it.

## Entities
### InventoryItem
- sku (string, unique)
- available (int)

### Reservation
- id (string)
- sku (string)
- user_id (string)
- qty (int)
- status (reserved | confirmed | cancelled)
- expires_at (timestamp)

> Keep it to **one SKU** at first if you want (e.g., `sku="widget"` with `available=20`).

---

## Endpoints (only 3)

### 1) POST /reserve
Body:
- sku
- user_id
- qty

Rules:
- Validate qty > 0
- If `available < qty` → **409**
- Otherwise, atomically:
  - decrement `available` by qty
  - create Reservation with status=reserved, expires_at = now + 2 minutes
Return:
- reservation_id, expires_at

---

### 2) POST /confirm/{reservation_id}
Rules:
- If not found → **404**
- If already confirmed → return **200** (idempotent)
- If cancelled → **409**
- If expired → **410**
- Else set status=confirmed, return **200**

---

### 3) POST /cancel/{reservation_id}
Rules:
- If not found → **404**
- If already cancelled → return **200** (idempotent)
- If confirmed → **409**
- Else set status=cancelled and increment `available` by reservation.qty, return **200**

---

## Expiration Rule (simple)
Before handling **any** request, run a quick cleanup:
- Find reservations with status=reserved and expires_at < now
- Mark them cancelled and return their qty to `available`

No background worker required.

---

## Must-Haves
- Correct status codes: 200/404/409/410
- No double-release of inventory (cancel/expire should only add stock back once)
- Basic input validation

## Quick Manual Test Script (mental checklist)
- Reserve qty=5 (available drops)
- Reserve qty too large → 409
- Confirm reservation → 200
- Cancel confirmed → 409
- Reserve then cancel → available returns
- Reserve then wait >2 min then confirm → 410 and available restored
