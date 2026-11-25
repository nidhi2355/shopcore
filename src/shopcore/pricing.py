from .models import CartItem

DEFAULT_TAX_RATE = 0.18

# Categories that are exempt from GST tax
TAX_EXEMPT_CATEGORIES = {"groceries", "books"}

COUPONS = {
    "SAVE10": {"type": "percent", "value": 10.0, "min_subtotal": 0.0, "active": True},
    "SAVE25": {"type": "percent", "value": 25.0, "min_subtotal": 2000.0, "active": True},
    "FLAT500": {"type": "flat", "value": 500.0, "min_subtotal": 0.0, "active": True},
    "EXPIRED10": {"type": "percent", "value": 10.0, "min_subtotal": 0.0, "active": False},
}


def calculate_subtotal(items: list[CartItem]) -> float:
    """Calculate the total price for all items before discounts and tax."""
    return round(sum(item.product.price * item.quantity for item in items), 2)


def calculate_taxable_subtotal(items: list[CartItem]) -> float:
    """Calculate the subtotal that is subject to GST.

    Items whose product category is in ``TAX_EXEMPT_CATEGORIES`` are ignored.
    If a product does not have a ``category`` attribute, it is treated as
    taxable (i.e., falls back to the default behaviour).
    """
    taxable_sum = 0.0
    for item in items:
        category = getattr(item.product, "category", None)
        if category is None or category not in TAX_EXEMPT_CATEGORIES:
            taxable_sum += item.product.price * item.quantity
    return round(taxable_sum, 2)


def calculate_discount(subtotal: float, coupon_code: str | None) -> float:
    if not coupon_code:
        return 0.0

    code = coupon_code.strip().upper()
    if code not in COUPONS:
        raise ValueError(f"Invalid coupon code: {coupon_code}")

    coupon = COUPONS[code]
    if not coupon["active"]:
        raise ValueError(f"Coupon {code} is inactive")
    if subtotal < coupon["min_subtotal"]:
        raise ValueError(
            f"Subtotal {subtotal} does not meet minimum {coupon['min_subtotal']} for coupon {code}"
        )

    discount_type = coupon["type"]
    value = coupon["value"]
    if discount_type == "percent":
        return round(subtotal * (value / 100.0), 2)

    # Flat discount – ensure it does not exceed the subtotal
    return round(min(value, subtotal), 2)


def calculate_tax(amount: float, tax_rate: float = DEFAULT_TAX_RATE) -> float:
    return round(amount * tax_rate, 2)
