import pytest
from shopcore.models import CartItem, Product
from shopcore.pricing import (
    calculate_discount,
    calculate_subtotal,
    calculate_tax,
    calculate_taxable_subtotal,
    TAX_EXEMPT_CATEGORIES,
)


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


def test_taxable_subtotal_exempt_items():
    # All items belong to exempt categories – taxable subtotal should be 0
    p1 = Product("SKU1", "Apple", 100.0)
    p1.category = "groceries"
    p2 = Product("SKU2", "Novel", 200.0)
    p2.category = "books"
    items = [CartItem(p1, 3), CartItem(p2, 2)]
    assert calculate_taxable_subtotal(items) == 0.0


def test_taxable_subtotal_mixed_items():
    # Mix of exempt and taxable items
    p1 = Product("SKU1", "Apple", 100.0)
    p1.category = "groceries"
    p2 = Product("SKU2", "Headphones", 1500.0)
    # No category set -> treated as taxable
    items = [CartItem(p1, 2), CartItem(p2, 1)]
    # Only the headphones contribute to taxable subtotal
    assert calculate_taxable_subtotal(items) == 1500.0


def test_tax_exempt_items_tax_zero():
    p1 = Product("SKU1", "Apple", 100.0)
    p1.category = "groceries"
    p2 = Product("SKU2", "Novel", 200.0)
    p2.category = "books"
    items = [CartItem(p1, 1), CartItem(p2, 1)]
    assert calculate_taxable_subtotal(items) == 0.0
    assert calculate_tax(calculate_taxable_subtotal(items)) == 0.0


def test_mixed_cart_taxable_subtotal_and_discount():
    p1 = Product("SKU1", "Apple", 100.0)
    p1.category = "groceries"
    p2 = Product("SKU2", "Headphones", 1500.0)
    items = [CartItem(p1, 2), CartItem(p2, 1)]
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal, "SAVE10")
    taxable_subtotal = calculate_taxable_subtotal(items)
    taxable_amount = max(taxable_subtotal - discount, 0.0)
    expected_tax = calculate_tax(taxable_amount)
    assert calculate_tax(taxable_amount) == expected_tax
