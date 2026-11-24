import pytest
from shopcore.inventory import InventoryManager
from shopcore.models import CartItem, Product


def test_negative_initial_stock_raises():
    with pytest.raises(ValueError):
        InventoryManager({"SKU1": -5})


def test_cartitem_zero_quantity_raises():
    product = Product("SKU1", "Widget", 100.0)
    with pytest.raises(ValueError):
        CartItem(product, 0)


def test_cartitem_negative_quantity_raises():
    product = Product("SKU1", "Widget", 100.0)
    with pytest.raises(ValueError):
        CartItem(product, -2)


def test_cartitem_negative_price_raises():
    product = Product("SKU1", "Widget", -50.0)
    with pytest.raises(ValueError):
        CartItem(product, 1)
