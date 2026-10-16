"""Prices and starter offers shared by the menu and checkout."""
from dataclasses import dataclass


@dataclass(frozen=True)
class StarterOffer:
    title: str
    dose_value: float
    quantity: int
    price: int

    @property
    def regular_price(self) -> int:
        return int(self.dose_value * 1000 * self.quantity)


OFFERS = {
    "first": StarterOffer("🤍 Первинне дозування (2,5 мл)", 2.5, 1, 2000),
    "individual": StarterOffer("🌿 Індивідуальний курс (2 мл)", 2, 4, 6500),
    "course": StarterOffer("✨ Стартовий курс (2,5 мл)", 2.5, 4, 8500),
}


def dose_label(value: float) -> str:
    return f"{value:g}".replace(".", ",")
