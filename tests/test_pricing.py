import pytest
from shopcore.models import CartItem, Product
from shopcore.pricing import calculate_discount, calculate_subtotal, calculate_tax


def test_calculate_subtotal():
    items = [
        CartItem(Product("SKU1", "Keyboard", 1500.0), 2),
        CartItem(Product("SKU2", "Mouse", 500.0), 1),
    ]
    assert calculate_subtotal(items) == 3500.0


def test_percent_coupon():
    assert calculate_discount(1000.0, "SAVE10") == 100.0


def test_invalid_coupon_raises():
    with pytest.raises(ValueError):
        calculate_discount(1000.0, "FAKECODE")


def test_calculate_tax():
    assert calculate_tax(1000.0) == 180.0


def test_flat_coupon_exceeds_subtotal():
    # Discount should be capped at the subtotal
    assert calculate_discount(300.0, "FLAT500") == 300.0


def test_flat_coupon_normal():
    # When subtotal exceeds flat discount, full discount applies
    assert calculate_discount(800.0, "FLAT500") == 500.0
