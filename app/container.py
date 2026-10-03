from dataclasses import dataclass
from app.services.user_service import UserService
from app.services.dose_service import DoseService
from app.services.therapy_service import TherapyService
from services.order_service import OrderService
from services.weight_service import WeightService


@dataclass
class Services:
    user: UserService
    dose: DoseService
    therapy: TherapyService
    weight: WeightService
    order: OrderService