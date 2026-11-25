class OutOfStockError(Exception):
    pass


class InventoryManager:
    def __init__(self, initial_stock: dict[str, int] | None = None, low_stock_threshold: int = 5):
        # Validate that initial stock quantities are non‑negative
        if initial_stock:
            for sku, qty in initial_stock.items():
                if qty < 0:
                    raise ValueError(f"Initial stock for SKU '{sku}' cannot be negative")
        if low_stock_threshold < 0:
            raise ValueError("Low stock threshold cannot be negative")
        self._stock: dict[str, int] = dict(initial_stock or {})
        self._low_stock_threshold = low_stock_threshold
        self._history: list[dict] = []

    def get_stock(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def add_stock(self, sku: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity to add cannot be negative")
        self._stock[sku] = self.get_stock(sku) + quantity
        self._history.append({
            "sku": sku,
            "action": "add",
            "quantity": quantity,
            "balance_after": self._stock[sku]
        })

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
            self._history.append({
                "sku": sku,
                "action": "reserve",
                "quantity": quantity,
                "balance_after": self._stock[sku]
            })
        else:
            raise OutOfStockError(
                f"Insufficient stock for {sku}: requested {quantity}, available {available}"
            )

    def get_low_stock_skus(self) -> list[str]:
        return sorted([sku for sku, qty in self._stock.items() if qty <= self._low_stock_threshold])

    def get_stock_history(self, sku: str | None = None) -> list[dict]:
        if sku is None:
            return list(self._history)
        return [entry for entry in self._history if entry["sku"] == sku]
