import pytest
from shopcore.inventory import InventoryManager
from shopcore.models import CartItem, Product
from shopcore.order_service import OrderService


def test_order_listing_and_revenue():
    # Setup inventory with sufficient stock for two orders
    inventory = InventoryManager({"SKU1": 5, "SKU2": 5})
    service = OrderService(inventory)

    # Create first order (1 unit of SKU1 at $100 each)
    product1 = Product("SKU1", "Widget", 100.0)
    item1 = CartItem(product1, 1)
    order1 = service.create_order([item1])

    # Create second order (2 units of SKU2 at $150 each)
    product2 = Product("SKU2", "Gadget", 150.0)
    item2 = CartItem(product2, 2)
    order2 = service.create_order([item2])

    # Verify that both orders are listed when no status filter is applied
    all_orders = service.list_orders()
    assert len(all_orders) == 2
    assert {o.order_id for o in all_orders} == {order1.order_id, order2.order_id}

    # Cancel the second order
    service.cancel_order(order2.order_id)

    # Filter by cancelled status – should return only the cancelled order
    cancelled = service.list_orders(status="cancelled")
    assert len(cancelled) == 1
    assert cancelled[0].order_id == order2.order_id

    # Filter by confirmed status – should return only the non‑cancelled order
    confirmed = service.list_orders(status="confirmed")
    assert len(confirmed) == 1
    assert confirmed[0].order_id


def test_tax_exempt_only():
    """All items are in tax‑exempt categories; tax should be 0.0."""
    inventory = InventoryManager({"SKU1": 10, "SKU2": 10})
    service = OrderService(inventory)

    prod_groceries = Product("SKU1", "Apple", 100.0)
    prod_groceries.category = "groceries"
    prod_books = Product("SKU2", "Novel", 200.0)
    prod_books.category = "books"

    items = [CartItem(prod_groceries, 3), CartItem(prod_books, 2)]
    order = service.create_order(items)
    assert order.tax == 0.0
    # Total should equal subtotal since no tax and no discount
    assert order.total == order.subtotal


def test_mixed_cart_tax():
    """Cart with both exempt and taxable items; tax applied only to taxable portion."""
    inventory = InventoryManager({"SKU1": 5, "SKU2": 5})
    service = OrderService(inventory)

    prod_groceries = Product("SKU1", "Apple", 100.0)
    prod_groceries.category = "groceries"
    prod_headphones = Product("SKU2", "Headphones", 1500.0)  # default category "general"

    items = [CartItem(prod_groceries, 2), CartItem(prod_headphones, 1)]
    order = service.create_order(items)

    # Expected calculations
    expected_subtotal = 2 * 100.0 + 1 * 1500.0
    expected_taxable = 1500.0  # only headphones
    expected_tax = round(expected_taxable * 0.18, 2)
    expected_total = round(expected_subtotal + expected_tax, 2)  # no discount

    assert order.subtotal == expected_subtotal
    assert order.tax == expected_tax
    assert order.total == expected_total


def test_mixed_cart_with_discount():
    """Mixed cart with a percent coupon; tax calculated after discount on taxable amount."""
    inventory = InventoryManager({"SKU1": 5, "SKU2": 5})
    service = OrderService(inventory)

    prod_groceries = Product("SKU1", "Apple", 100.0)
    prod_groceries.category = "groceries"
    prod_headphones = Product("SKU2", "Headphones", 1500.0)

    items = [CartItem(prod_groceries, 2), CartItem(prod_headphones, 1)]
    # Apply 10% discount on subtotal
    order = service.create_order(items, coupon_code="SAVE10")

    expected_subtotal = 2 * 100.0 + 1 * 1500.0
    expected_discount = round(expected_subtotal * 0.10, 2)
    expected_taxable = 1500.0
    taxable_after_discount = max(expected_taxable - expected_discount, 0.0)
    expected_tax = round(taxable_after_discount * 0.18, 2)
    expected_total = round(expected_subtotal - expected_discount + expected_tax, 2)

    assert order.subtotal == expected_subtotal
    assert order.discount == expected_discount
    assert order.tax == expected_tax
    assert order.total == expected_total


def test_order_creation_coupon_failure_rolls_back_stock():
    inventory = InventoryManager({"SKU1": 5})
    service = OrderService(inventory)
    product = Product("SKU1", "Widget", 100.0)
    item = CartItem(product, 2)  # subtotal 200.0
    with pytest.raises(ValueError):
        service.create_order([item], coupon_code="EXPIRED10")
    # Stock should remain unchanged after failure
    assert inventory.stock["SKU1"] == 5


def test_order_creation_coupon_min_subtotal_failure_rolls_back_stock():
    inventory = InventoryManager({"SKU1": 5})
    service = OrderService(inventory)
    product = Product("SKU1", "Widget", 500.0)
    item = CartItem(product, 3)  # subtotal 1500.0, below SAVE25 min_subtotal
    with pytest.raises(ValueError):
        service.create_order([item], coupon_code="SAVE25")
    # Stock should remain unchanged after failure
    assert inventory.stock["SKU1"] == 5
