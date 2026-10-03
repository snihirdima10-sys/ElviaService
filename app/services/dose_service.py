from app.database.repositories.dose_repository import DoseRepository
from models.dose import Dose


class DoseService:
    def __init__(self, dose_repository: DoseRepository):
        self.dose = dose_repository

    def get_all_doses(self):
        return self.dose.get_all()

    def get_dose_by_dose_id(self, dose_id) -> Dose | None:
        return self.dose.get_by_id(dose_id)