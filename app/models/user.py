from dataclasses import dataclass
from datetime import date


@dataclass
class User:
    id: int
    tg_id: int
    full_name: str
    phone: str
    height: float
    start_weight: float
    current_weight: float
    target_weight: float
    next_weight_request_at: date
    created_at: date
