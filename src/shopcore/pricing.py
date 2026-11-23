from .models import CartItem

DEFAULT_TAX_RATE = 0.18

# Categories that are exempt from GST tax
TAX_EXEMPT_CATEGORIES = {"groceries", "books"}

COUPONS = {
    "SAVE10": ("percent", 10.0),
    "SAVE25": ("percent", 25.0),
    "FLAT500": ("flat", 500.0),
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

    discount_type, value = COUPONS[code]
    if discount_type == "percent":
        return round(subtotal * (value / 100.0), 2)

    # Flat discount – ensure it does not exceed the subtotal
    return round(min(value, subtotal), 2)


def calculate_tax(amount: float, tax_rate: float = DEFAULT_TAX_RATE) -> float:
    return round(amount * tax_rate, 2)
