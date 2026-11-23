import pytest
from shopcore.inventory import InventoryManager, OutOfStockError
from shopcore.models import CartItem, Product
from shopcore.order_service import OrderService


def test_create_order_success():
    inv = InventoryManager({"SKU1": 10})
    service = OrderService(inv)
    items = [CartItem(Product("SKU1", "Headphones", 2000.0), 2)]

    order = service.create_order(items, coupon_code="SAVE10")

    assert order.subtotal == 4000.0
    assert order.discount == 400.0
    assert order.tax == 648.0
    assert order.total == 4248.0
    assert inv.get_stock("SKU1") == 8


def test_create_order_insufficient_stock():
    inv = InventoryManager({"SKU1": 1})
    service = OrderService(inv)
    items = [CartItem(Product("SKU1", "Headphones", 2000.0), 5)]

    with pytest.raises(OutOfStockError):
        service.create_order(items)