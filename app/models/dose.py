from dataclasses import dataclass


@dataclass
class Dose:
    id: int
    medication: str
    dose_value: float
    price: int