from __future__ import annotations

from typing import List, Optional

from .models import Product


class ProductCatalog:
    """In‑memory catalog for registering and searching products.

    The catalog stores :class:`~shopcore.models.Product` instances keyed by their SKU.
    It provides lookup by SKU, case‑insensitive search by category or name, and
    listing utilities with optional price sorting.
    """

    def __init__(self, initial_products: dict[str, Product] | None = None) -> None:
        """Initialize the catalog, optionally with a pre‑populated mapping of SKU to Product."""
        self._products: dict[str, Product] = dict(initial_products) if initial_products is not None else {}

    def register_product(self, product: Product) -> None:
        """Register a new product.

        Args:
            product: The :class:`Product` instance to register.

        Raises:
            ValueError: If a product with the same SKU is already registered.
        """
        if product.sku in self._products:
            raise ValueError(f"Product with SKU '{product.sku}' is already registered")
        self._products[product.sku] = product

    def get_product(self, sku: str) -> Optional[Product]:
        """Return the product matching *sku* or ``None`` if not found."""
        return self._products.get(sku)

    def search_by_category(self, category: str) -> List[Product]:
        """Return products whose ``category`` matches *category* case‑insensitively.

        Results are sorted alphabetically by SKU.
        """
        lowered = category.lower()
        matches = [p for p in self._products.values()
                   if getattr(p, "category", "").lower() == lowered]
        return sorted(matches, key=lambda p: p.sku)

    def search_by_name(self, query: str) -> List[Product]:
        """Return products whose ``name`` contains *query* case‑insensitively.

        Results are sorted alphabetically by SKU.
        """
        lowered = query.lower()
        matches = [p for p in self._products.values()
                   if lowered in p.name.lower()]
        return sorted(matches, key=lambda p: p.sku)

    def list_products(self, sort_by_price: bool = False) -> List[Product]:
        """List all registered products.

        If *sort_by_price* is ``True`` the list is sorted by price (ascending) and
        then by SKU to provide a deterministic order. Otherwise the list is
        sorted solely by SKU.
        """
        products = list(self._products.values())
        if sort_by_price:
            return sorted(products, key=lambda p: (p.price, p.sku))
        return sorted(products, key=lambda p: p.sku)
