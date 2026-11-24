class OutOfStockError(Exception):
    pass


class InventoryManager:
    def __init__(self, initial_stock: dict[str, int] | None = None):
        # Validate that initial stock quantities are non‑negative
        if initial_stock:
            for sku, qty in initial_stock.items():
                if qty < 0:
                    raise ValueError(f"Initial stock for SKU '{sku}' cannot be negative")
        self._stock: dict[str, int] = dict(initial_stock or {})

    def get_stock(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def add_stock(self, sku: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity to add cannot be negative")
        self._stock[sku] = self.get_stock(sku) + quantity

    def reserve_stock(self, sku: str, quantity: int) -> None:
        """Reserve a quantity of stock for a given SKU.

        Allows reserving the exact amount of available stock. If the requested
        quantity exceeds the available stock, an ``OutOfStockError`` is raised.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        available = self.get_stock(sku)
        # Allow reservation when the requested quantity is less than **or equal** to the available stock.
        if available >= quantity:
            self._stock[sku] = available - quantity
        else:
            raise OutOfStockError(
                f"Insufficient stock for {sku}: requested {quantity}, available {available}"
            )
