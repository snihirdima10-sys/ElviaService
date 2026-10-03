from datetime import date, timedelta

from app.database.repositories.user_repository import UserRepository
from app.models.user import User


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_by_user_id(self, user_id: int) -> User | None:
        return self.user_repository.get_by_id(user_id)

    def get_user_by_tg_id(self, tg_id: int) -> User | None:
        user_id = self.get_user_id_by_tg_id(tg_id)
        if user_id is None:
            return None
        return self.user_repository.get_by_id(user_id)

    def get_user_id_by_tg_id(self, tg_id: int) -> int | None:
        return self.user_repository.get_user_id_by_tg_id(tg_id)

    def search_users(self, query: str) -> list:
        query = query.strip()
        if not query:
            return []

        return self.user_repository.search_by_name_or_phone(query)

    def update_current_weight_by_user_id(self, user_id: int, new_weight: float) -> int | None:
        next_weight_request_at = (date.today() + timedelta(days=7)).isoformat()
        return self.user_repository.update_current_weight_by_user_id(
            user_id=user_id,
            new_weight=new_weight,
            next_weight_request_at=next_weight_request_at
        )