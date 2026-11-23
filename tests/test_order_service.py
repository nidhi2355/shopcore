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


def test_create_order_flat_coupon_exceeds_subtotal():
    inv = InventoryManager({"SKU1": 5})
    service = OrderService(inv)
    items = [CartItem(Product("SKU1", "Item", 300.0), 1)]

    order = service.create_order(items, coupon_code="FLAT500")

    assert order.subtotal == 300.0
    assert order.discount == 300.0
    assert order.tax == 0.0
    assert order.total == 0.0
    assert inv.get_stock("SKU1") == 4


def test_atomic_stock_reservation_on_failure():
    """Ensure that stock is not deducted when an order fails due to insufficient stock.

    The first item can be reserved, but the second triggers an OutOfStockError.
    After the exception, inventory levels should remain unchanged.
    """
    inv = InventoryManager({"SKU1": 5, "SKU2": 1})
    service = OrderService(inv)
    items = [
        CartItem(Product("SKU1", "Keyboard", 1500.0), 2),
        CartItem(Product("SKU2", "Mouse", 500.0), 3),
    ]

    with pytest.raises(OutOfStockError):
        service.create_order(items)

    # Stock should be unchanged for both SKUs
    assert inv.get_stock("SKU1") == 5
    assert inv.get_stock("SKU2") == 1


def test_create_order_duplicate_skus_exceed_stock():
    """Duplicate line items for the same SKU should be aggregated for stock validation.
    When total quantity exceeds available stock, an OutOfStockError is raised and stock remains unchanged.
    """
    inv = InventoryManager({"SKU1": 5})
    service = OrderService(inv)
    items = [
        CartItem(Product("SKU1", "Keyboard", 1500.0), 3),
        CartItem(Product("SKU1", "Keyboard", 1500.0), 3),
    ]

    with pytest.raises(OutOfStockError):
        service.create_order(items)

    assert inv.get_stock("SKU1") == 5


def test_create_order_duplicate_skus_within_stock():
    """Duplicate line items that together fit within stock should succeed.
    Stock should be correctly decremented by the total quantity.
    """
    inv = InventoryManager({"SKU1": 6})
    service = OrderService(inv)
    items = [
        CartItem(Product("SKU1", "Keyboard", 1500.0), 3),
        CartItem(Product("SKU1", "Keyboard", 1500.0), 3),
    ]

    order = service.create_order(items)

    # Subtotal = 6 * 1500 = 9000
    assert order.subtotal == 9000.0
    # No discount applied
    assert order.discount == 0.0
    # Tax rate is 18% (as inferred from other tests)
    assert order.tax == 1620.0
    # Total = subtotal + tax
    assert order.total == 10620.0
    # Stock should be fully depleted
    assert inv.get_stock("SKU1") == 0
