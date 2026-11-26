import pytest
from shopcore.inventory import InventoryManager
from shopcore.models import CartItem, Product
from shopcore.order_service import OrderService
from shopcore.catalog import ProductCatalog


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


def test_create_order_from_catalog_with_coupon():
    """Create an order via the catalog helper using a valid coupon."""
    # Setup inventory and catalog
    inventory = InventoryManager({"SKU1": 10, "SKU2": 5})
    service = OrderService(inventory)
    product1 = Product("SKU1", "Widget", 100.0)
    product2 = Product("SKU2", "Gadget", 200.0)
    catalog = ProductCatalog({"SKU1": product1, "SKU2": product2})

    # Create order using catalog helper
    order = service.create_order_from_catalog({"SKU1": 2, "SKU2": 1}, catalog, coupon_code="SAVE10")

    # Verify order details
    assert order.subtotal == 2 * 100.0 + 1 * 200.0
    expected_discount = round(order.subtotal * 0.10, 2)
    assert order.discount == expected_discount
    # Tax should be calculated on taxable amount after discount (both items are taxable by default)
    taxable_subtotal = 2 * 100.0 + 1 * 200.0
    taxable_after_discount = max(taxable_subtotal - expected_discount, 0.0)
    expected_tax = round(taxable_after_discount * 0.18, 2)
    assert order.tax == expected_tax
    expected_total = round(order.subtotal - expected_discount + expected_tax, 2)
    assert order.total == expected_total
    # Inventory should be reduced accordingly
    assert inventory.stock["SKU1"] == 8
    assert inventory.stock["SKU2"] == 4


def test_create_order_from_catalog_unknown_sku_raises_and_no_stock_reserved():
    """When an unknown SKU is supplied, a KeyError is raised and no stock is reserved for any SKU."""
    inventory = InventoryManager({"SKU1": 5, "SKU2": 5})
    service = OrderService(inventory)
    product1 = Product("SKU1", "Widget", 100.0)
    catalog = ProductCatalog({"SKU1": product1})  # SKU2 is missing from catalog

    # Attempt to create order with one known and one unknown SKU
    with pytest.raises(KeyError) as exc:
        service.create_order_from_catalog({"SKU1": 2, "SKU2": 1}, catalog)
    assert "SKU2" in str(exc.value)
    # Ensure stock for the known SKU was not deducted
    assert inventory.stock["SKU1"] == 5
    # No new order should be recorded
    assert len(service._orders) == 0


def test_get_top_selling_skus_aggregation_and_limit():
    """Aggregates quantities across orders, excludes cancelled, respects limit and tie‑break ordering."""
    inventory = InventoryManager({"A": 10, "B": 10, "C": 10, "D": 10})
    service = OrderService(inventory)
    # Create catalog for convenience
    prod_a = Product("A", "Alpha", 50.0)
    prod_b = Product("B", "Beta", 60.0)
    prod_c = Product("C", "Gamma", 70.0)
    prod_d = Product("D", "Delta", 80.0)
    catalog = ProductCatalog({"A": prod_a, "B": prod_b, "C": prod_c, "D": prod_d})

    # Order 1: A x3, B x2
    service.create_order_from_catalog({"A": 3, "B": 2}, catalog)
    # Order 2: B x3, C x5
    service.create_order_from_catalog({"B": 3, "C": 5}, catalog)
    # Order 3: A x2, D x4 (will be cancelled later)
    order_to_cancel = service.create_order_from_catalog({"A": 2, "D": 4}, catalog)
    service.cancel_order(order_to_cancel.order_id)

    # At this point totals (excluding cancelled):
    # A: 3, B: 5, C: 5, D: 0
    top_3 = service.get_top_selling_skus(limit=3)
    # Expected order: B (5), C (5) – tie broken alphabetically, then A (3)
    assert top_3 == [("B", 5), ("C", 5), ("A", 3)]

    # Limit of 2 should truncate correctly
    top_2 = service.get_top_selling_skus(limit=2)
    assert top_2 == [("B", 5), ("C", 5)]

    # Request with invalid limit should raise ValueError
    with pytest.raises(ValueError):
        service.get_top_selling_skus(limit=0)


def test_create_order_from_catalog_empty_sku_quantities_raises():
    """Creating an order with an empty sku_quantities dict should raise ValueError and not affect stock."""
    inventory = InventoryManager({"SKU1": 5})
    service = OrderService(inventory)
    product = Product("SKU1", "Widget", 100.0)
    catalog = ProductCatalog({"SKU1": product})
    with pytest.raises(ValueError):
        service.create_order_from_catalog({}, catalog)
    # stock unchanged
    assert inventory.stock["SKU1"] == 5
    assert len(service._orders) == 0


def test_get_top_selling_skus_limit_exceeds_available():
    """When limit exceeds number of SKUs, all SKUs are returned sorted correctly."""
    inventory = InventoryManager({"X": 5, "Y": 5})
    service = OrderService(inventory)
    prod_x = Product("X", "ItemX", 10.0)
    prod_y = Product("Y", "ItemY", 20.0)
    catalog = ProductCatalog({"X": prod_x, "Y": prod_y})
    service.create_order_from_catalog({"X": 1}, catalog)
    service.create_order_from_catalog({"Y": 2}, catalog)
    # limit larger than distinct SKUs
    result = service.get_top_selling_skus(limit=10)
    assert result == [("Y", 2), ("X", 1)]


def test_get_top_selling_skus_no_orders_returns_empty():
    """If there are no orders, get_top_selling_skus should return an empty list."""
    inventory = InventoryManager({"A": 5})
    service = OrderService(inventory)
    assert service.get_top_selling_skus(limit=3) == []
