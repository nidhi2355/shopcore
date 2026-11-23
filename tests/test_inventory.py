import pytest
from shopcore.inventory import InventoryManager
from shopcore.models import CartItem, Product


def test_inventory_negative_initial_stock():
    with pytest.raises(ValueError):
        InventoryManager({"SKU1": -5})


def test_cartitem_zero_quantity():
    product = Product("SKU1", "Widget", 100.0)
    with pytest.raises(ValueError):
        CartItem(product, 0)


def test_cartitem_negative_quantity():
    product = Product("SKU1", "Widget", 100.0)
    with pytest.raises(ValueError):
        CartItem(product, -2)


def test_cartitem_negative_price():
    product = Product("SKU1", "Widget", -10.0)
    with pytest.raises(ValueError):
        CartItem(product, 1)
