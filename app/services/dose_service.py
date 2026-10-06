from math import isfinite

from app.database.repositories.dose_repository import DoseRepository
from app.models.dose import Dose


class DoseService:
    def __init__(self, dose_repository: DoseRepository):
        self.dose = dose_repository

    def get_all_doses(self):
        return self.dose.get_all()

    def delete_dose(self, dose_id: int) -> bool:
        return self.dose.deactivate(dose_id)

    def get_active_dose(self, dose_id: int) -> Dose | None:
        return self.dose.get_active_by_id(dose_id)

    def create_dose(self, medication: str, dose_value: float, price: int) -> int:
        medication = medication.strip()
        if not 1 <= len(medication) <= 100:
            raise ValueError("Назва препарату має містити від 1 до 100 символів.")
        if not isfinite(dose_value) or dose_value <= 0:
            raise ValueError("Дозування має бути додатним числом.")
        if not isinstance(price, int) or not 0 < price <= 1_000_000_000:
            raise ValueError("Вкажіть додатну ціну в цілих гривнях, не більше 1 000 000 000.")
        return self.dose.create(medication, dose_value, price)

    def get_dose_by_dose_id(self, dose_id) -> Dose | None:
        return self.dose.get_by_id(dose_id)
