import pytest

from shopcore.catalog import ProductCatalog
from shopcore.models import Product


def _make_product(sku: str, name: str, price: float, category: str | None = None) -> Product:
    prod = Product(sku, name, price)
    if category:
        prod.category = category
    return prod


def test_duplicate_sku_raises():
    catalog = ProductCatalog()
    p1 = _make_product("SKU1", "Widget", 100.0)
    catalog.register_product(p1)
    p2 = _make_product("SKU1", "Gadget", 150.0)
    with pytest.raises(ValueError):
        catalog.register_product(p2)


def test_get_product_and_missing():
    catalog = ProductCatalog()
    p = _make_product("SKU2", "Gizmo", 200.0)
    catalog.register_product(p)
    assert catalog.get_product("SKU2") is p
    assert catalog.get_product("UNKNOWN") is None


def test_search_by_category_case_insensitive():
    catalog = ProductCatalog()
    p1 = _make_product("A1", "Item1", 10.0, category="Electronics")
    p2 = _make_product("A2", "Item2", 20.0, category="electronics")
    p3 = _make_product("B1", "Item3", 30.0, category="Home")
    for p in (p1, p2, p3):
        catalog.register_product(p)
    results = catalog.search_by_category("eLeCtRoNiCs")
    assert [p.sku for p in results] == ["A1", "A2"]


def test_search_by_name_substring_case_insensitive():
    catalog = ProductCatalog()
    p1 = _make_product("C1", "SuperWidget", 50.0)
    p2 = _make_product("C2", "widget pro", 60.0)
    p3 = _make_product("C3", "Gadget", 70.0)
    for p in (p1, p2, p3):
        catalog.register_product(p)
    results = catalog.search_by_name("WIDGET")
    assert [p.sku for p in results] == ["C1", "C2"]


def test_list_products_default_and_price_sort():
    catalog = ProductCatalog()
    p1 = _make_product("D2", "ItemA", 200.0)
    p2 = _make_product("D1", "ItemB", 100.0)
    p3 = _make_product("D3", "ItemC", 100.0)
    for p in (p1, p2, p3):
        catalog.register_product(p)
    # Default sorting by SKU
    default_sorted = catalog.list_products()
    assert [p.sku for p in default_sorted] == ["D1", "D2", "D3"]
    # Sorting by price then SKU
    price_sorted = catalog.list_products(sort_by_price=True)
    assert [p.sku for p in price_sorted] == ["D1", "D3", "D2"]


def test_update_price_success():
    catalog = ProductCatalog()
    product = _make_product("SKU10", "Gizmo", 10.123)
    catalog.register_product(product)
    updated = catalog.update_price("SKU10", 15.567)
    assert updated.price == round(15.567, 2)
    # Ensure the catalog reflects the updated price
    assert catalog.get_product("SKU10").price == round(15.567, 2)


def test_update_price_negative_raises():
    catalog = ProductCatalog()
    product = _make_product("SKU11", "Widget", 20.0)
    catalog.register_product(product)
    with pytest.raises(ValueError):
        catalog.update_price("SKU11", -5.0)
    # Price should remain unchanged
    assert catalog.get_product("SKU11").price == 20.0


def test_update_price_unknown_sku_raises():
    catalog = ProductCatalog()
    with pytest.raises(KeyError):
        catalog.update_price("UNKNOWN", 10.0)


def test_remove_product_success():
    catalog = ProductCatalog()
    product = _make_product("SKU12", "Gadget", 30.0)
    catalog.register_product(product)
    removed = catalog.remove_product("SKU12")
    assert removed is product
    assert catalog.get_product("SKU12") is None


def test_remove_product_unknown_sku_raises():
    catalog = ProductCatalog()
    with pytest.raises(KeyError):
        catalog.remove_product("NONEXISTENT")
