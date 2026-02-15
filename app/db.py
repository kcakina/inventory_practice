import threading
from datetime import datetime
from enum import Enum
from typing import Dict


class InventoryItem:
    def __init__(self, sku: str, available: int) -> None:
        self.sku: str = sku
        self.available: int = available


class Status(str, Enum):
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Reservation:
    def __init__(
        self,
        id: str,
        sku: str,
        user_id: str,
        qty: int,
        status: Status,
        expires_at: datetime,
    ) -> None:
        self.id: str = id
        self.sku: str = sku
        self.user_id: str = user_id
        self.qty: int = qty
        self.status: Status = status
        self.expires_at: datetime = expires_at


class DB:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.inventory: Dict[str, InventoryItem] = {}
        self.reservations: Dict[str, Reservation] = {}
