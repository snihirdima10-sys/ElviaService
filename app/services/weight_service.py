class WeightService:
    def __init__(self, weight_repository):
        self.weight_repository = weight_repository

    def add_weight_by_user_id(self, user_id: int, weight: float) -> int:
        return self.weight_repository.add_weight_by_user_id(user_id, weight)