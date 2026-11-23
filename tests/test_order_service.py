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