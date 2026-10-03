from dataclasses import dataclass

from database.repositories.dose_repository import DoseRepository
from database.repositories.order_repository import OrderRepository
from models.order import Order


@dataclass(slots=True)
class OrderCreateData:
    user_id: int
    dose_id: int
    weeks_count: int
    city: str
    delivery_method: str
    address: str


@dataclass(slots=True)
class OrderPreview:
    weeks_count: int
    total_price: float
    delivery_data: str


class OrderService:
    def __init__(self, order_repository: OrderRepository, dose_repository: DoseRepository) -> None:
        self.order_repository = order_repository
        self.dose_repository = dose_repository

    def get_all_orders_by_user_id(self, user_id: int) -> list[Order]:
        return self.order_repository.get_all_by_user_id(user_id)

    def get_admin_orders(self, status: str | None = None) -> list[dict]:
        return self.order_repository.get_all_by_status(status)

    def get_admin_order(self, order_id: int) -> dict | None:
        return self.order_repository.get_by_id(order_id)

    def update_status(self, order_id: int, status: str) -> bool:
        if status not in {"new", "processed", "completed"}:
            raise ValueError("Невідомий статус замовлення")
        return self.order_repository.update_status(order_id, status)

    def calculate_discount(self, weeks_count: int) -> int:
        match weeks_count:
            case 1:
                return 0
            case 2:
                return 10
            case 4:
                return 20
            case _:
                raise ValueError("Invalid weeks count")

    def calculate_total_price(self, price: float, weeks_count: int, discount: int) -> float:
        subtotal = price * weeks_count
        return subtotal * (1 - discount / 100)

    def create_order(self, data: OrderCreateData) -> int:
        dose = self.dose_repository.get_by_id(data.dose_id)

        if dose is None:
            raise ValueError("Dose not found")

        discount = self.calculate_discount(data.weeks_count)

        total_price = self.calculate_total_price(
            price=dose.price,
            weeks_count=data.weeks_count,
            discount=discount
        )

        delivery_data = self.build_delivery_data(
            city=data.city,
            method=data.delivery_method,
            address=data.address,
        )

        return self.order_repository.create(
            user_id=data.user_id,
            dose_id=data.dose_id,
            weeks_count=data.weeks_count,
            discount=discount,
            total_price=total_price,
            delivery_data=delivery_data,
            status="new",
        )

    def build_delivery_data(self, city: str, method: str, address: str) -> str:
        method_names = {
            "branch": "Відділення",
            "parcel_locker": "Поштомат",
            "courier_delivery": "Адреса",
        }

        method_name = method_names.get(method)

        if method_name is None:
            raise ValueError("Unknown delivery method")

        return (
            f"Місто: {city}\n"
            f"{method_name}: {address}"
        )

    def build_order_preview(
            self,
            dose_id: int,
            weeks_count: int,
            city: str,
            delivery_method: str,
            address: str,
    ) -> OrderPreview:
        dose = self.dose_repository.get_by_id(dose_id)

        if dose is None:
            raise ValueError("Dose not found")

        discount = self.calculate_discount(weeks_count)

        total_price = self.calculate_total_price(
            price=dose.price,
            weeks_count=weeks_count,
            discount=discount,
        )

        delivery_data = self.build_delivery_data(
            city=city,
            method=delivery_method,
            address=address,
        )

        return OrderPreview(
            weeks_count=weeks_count,
            total_price=total_price,
            delivery_data=delivery_data,
        )


