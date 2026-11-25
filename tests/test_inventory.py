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


def test_negative_low_stock_threshold_raises():
    with pytest.raises(ValueError):
        InventoryManager(low_stock_threshold=-1)


def test_low_stock_reporting():
    inv = InventoryManager({"SKU1": 3, "SKU2": 10, "SKU3": 5})
    # Default threshold is 5
    low_stock = inv.get_low_stock_skus()
    assert low_stock == ["SKU1", "SKU3"]

    # Reserve some stock to push SKU2 below threshold
    inv.reserve_stock("SKU2", 6)
    low_stock = inv.get_low_stock_skus()
    assert low_stock == ["SKU1", "SKU2", "SKU3"]


def test_stock_history():
    inv = InventoryManager({"SKU1": 10})
    inv.add_stock("SKU1", 5)
    inv.reserve_stock("SKU1", 3)
    
    history = inv.get_stock_history()
    assert len(history) == 2
    assert history[0] == {"sku": "SKU1", "action": "add", "quantity": 5, "balance_after": 15}
    assert history[1] == {"sku": "SKU1", "action": "reserve", "quantity": 3, "balance_after": 12}

    # Filter by SKU
    filtered = inv.get_stock_history("SKU1")
    assert len(filtered) == 2
    
    # Filter by non-existent SKU
    empty = inv.get_stock_history("SKU2")
    assert empty == []
