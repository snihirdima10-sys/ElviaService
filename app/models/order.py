from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from models.dose import Dose


class OrderStatus(StrEnum):
    NEW = 'new'
    PROCESSED = 'processed'
    COMPLETED = 'completed'

@dataclass
class Order:
    id: int
    user_id: int
    dose: Dose
    weeks_count: int
    discount: int
    total_price : float
    delivery_data: str
    status: OrderStatus
    created_at: date
