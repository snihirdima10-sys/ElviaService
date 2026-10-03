from datetime import date

from app.database.repositories.therapy_repository import TherapyRepository
from app.database.repositories.user_repository import UserRepository
from app.database.repositories.dose_repository import DoseRepository
from models import therapy
from models.therapy import Therapy


class TherapyService:
    def __init__(self,
                 therapy_repository: TherapyRepository,
                 user_repository: UserRepository,
                 dose_repository: DoseRepository
                 ):

        self.therapy = therapy_repository
        self.user = user_repository
        self.dose = dose_repository

    def get_active_therapy_by_user_id(self, user_id: int) -> Therapy | None:
        return self.therapy.get_active_by_user_id(user_id)

    def get_planned_therapy_by_user_id(self, user_id: int) -> Therapy | None:
        return self.therapy.get_planned_by_user_id(user_id)

    def get_history_therapy_by_user_id(self, user_id):
        return self.therapy.get_history_by_user_id(user_id)

    def get_first_therapy_start_date_by_user_id(self, user_id) -> date | None:
        first_therapy = self.therapy.get_first_by_user_id(user_id)
        return first_therapy.start_date if first_therapy else None

    def create_therapy(self, user_id: int, dose_id: int, start_date: date):
        # 1. Перевіряємо пацієнта
        user = self.user.get_by_id(user_id)
        if user is None:
            raise ValueError("Пацієнта не знайдено")

        # 2. Перевіряємо дозування
        dose = self.dose.get_by_id(dose_id)
        if dose is None:
            raise ValueError("Дозування не знайдено")

        # 3. Визначаємо статус
        if start_date == date.today():
            status = "active"
        else:
            status = "planned"

        # 4. Перевіряємо існуючі терапії
        if status == "active":
            active = self.therapy.get_active_by_user_id(user_id)
            if active is not None:
                self.therapy.set_status_by_therapy_id(active["id"], "completed")

         # 5. Створюємо
        therapy_id = self.therapy.create_therapy(
            user_id=user_id,
            dose_id=dose_id,
            start_date=start_date.isoformat(),
            start_weight=user["current_weight"],
            status=status,
            )

        return therapy_id








