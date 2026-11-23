import pytest
from shopcore.inventory import InventoryManager, OutOfStockError
from shopcore.models import CartItem, Product
from shopcore.order_service import OrderService


def test_reserve_exact_quantity_success():
    inv = InventoryManager({"SKU1": 2})
    # Should not raise an exception when reserving the exact available quantity
    inv.reserve_stock("SKU1", 2)
    assert inv.get_stock("SKU1") == 0


def test_create_order_exact_quantity_success():
    inv = InventoryManager({"SKU1": 2})
    service = OrderService(inv)
    items = [CartItem(Product("SKU1", "Keyboard", 1500.0), 2)]
    order = service.create_order(items)
    # Verify order calculations are correct for the given items
    assert order.subtotal == 3000.0
    # After successful reservation, stock should be depleted
    assert inv.get_stock("SKU1") == 0
