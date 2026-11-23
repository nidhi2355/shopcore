from .models import CartItem

DEFAULT_TAX_RATE = 0.18

COUPONS = {
    "SAVE10": ("percent", 10.0),
    "SAVE25": ("percent", 25.0),
    "FLAT500": ("flat", 500.0),
}


def calculate_subtotal(items: list[CartItem]) -> float:
    return round(sum(item.product.price * item.quantity for item in items), 2)


def calculate_discount(subtotal: float, coupon_code: str | None) -> float:
    if not coupon_code:
        return 0.0

    code = coupon_code.strip().upper()
    if code not in COUPONS:
        raise ValueError(f"Invalid coupon code: {coupon_code}")

    discount_type, value = COUPONS[code]
    if discount_type == "percent":
        return round(subtotal * (value / 100.0), 2)

    # Flat discount – ensure it does not exceed the subtotal
    return round(min(value, subtotal), 2)


def calculate_tax(amount: float, tax_rate: float = DEFAULT_TAX_RATE) -> float:
    return round(amount * tax_rate, 2)
