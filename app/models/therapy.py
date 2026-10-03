from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.models.dose import Dose


class TherapyStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"

@dataclass(slots=True)
class Therapy:
    id: int
    user_id: int
    dose: Dose
    start_date: date
    end_date: date | None
    start_weight: float
    end_weight: float | None
    status: TherapyStatus
