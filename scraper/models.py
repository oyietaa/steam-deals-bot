from dataclasses import dataclass


@dataclass(frozen=True)
class Deal:
    app_id: int
    name: str
    normal_price: int
    final_price: int
    discount_pct: int
    url: str
