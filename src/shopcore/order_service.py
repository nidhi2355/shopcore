import uuid
from .inventory import InventoryManager, OutOfStockError
from .models import CartItem, Order
from .pricing import (
    calculate_discount,
    calculate_subtotal,
    calculate_tax,
    calculate_taxable_subtotal,
)


class OrderService:
    def __init__(self, inventory: InventoryManager):
        self.inventory = inventory
        self._orders: dict[str, Order] = {}

    def create_order(
        self, items: list[CartItem], coupon_code: str | None = None
    ) -> Order:
        if not items:
            raise ValueError("Cannot create an order with an empty cart")

        # Aggregate quantities per SKU to ensure total requested quantity does not exceed stock
        aggregated: dict[str, int] = {}
        for item in items:
            sku = item.product.sku
            aggregated[sku] = aggregated.get(sku, 0) + item.quantity

        # Reserve stock for each aggregated SKU, tracking successful reservations
        reserved_items: list[tuple[str, int]] = []
        try:
            for sku, total_qty in aggregated.items():
                self.inventory.reserve_stock(sku, total_qty)
                reserved_items.append((sku, total_qty))
        except OutOfStockError:
            # Roll back any stock that was already reserved before re‑raising
            for sku, qty in reserved_items:
                self.inventory.add_stock(sku, qty)
            raise

        # Perform pricing calculations; ensure any failure rolls back reservations
        try:
            subtotal = calculate_subtotal(items)
            discount = calculate_discount(subtotal, coupon_code)
            # Tax is calculated only on taxable items after discount
            taxable_subtotal = calculate_taxable_subtotal(items)
            taxable_amount = max(taxable_subtotal - discount, 0.0)
            tax = calculate_tax(taxable_amount)
            total = round(subtotal - discount + tax, 2)

            order = Order(
                order_id=str(uuid.uuid4())[:8],
                items=items,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
            )
            # Default status for a newly created order
            order.status = "confirmed"
            self._orders[order.order_id] = order
            return order
        except Exception:
            # If any calculation fails, roll back reserved stock
            for sku, qty in reserved_items:
                self.inventory.add_stock(sku, qty)
            raise

    def cancel_order(self, order_id: str) -> None:
        """Cancel an existing order.

        Restores the reserved stock and marks the order as cancelled.
        """
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"Order with id {order_id} does not exist")
        if getattr(order, "status", None) == "cancelled":
            raise ValueError(f"Order {order_id} is already cancelled")

        # Restore stock for each item in the order
        for item in order.items:
            self.inventory.add_stock(item.product.sku, item.quantity)
        # Mark the order as cancelled
        order.status = "cancelled"

    def list_orders(self, status: str | None = None) -> list[Order]:
        """Return all orders or only those matching the given status.

        If *status* is ``None`` the full list of orders is returned.
        Otherwise only orders whose ``status`` attribute equals the supplied
        value are returned.
        """
        if status is None:
            return list(self._orders.values())
        return [order for order in self._orders.values() if getattr(order, "status", None) == status]

    def get_total_revenue(self) -> float:
        """Calculate net revenue from non‑cancelled orders.

        The revenue is the sum of ``order.total`` for every order whose
        ``status`` is not ``"cancelled"``. The result is rounded to two decimal
        places.
        """
        revenue = sum(
            order.total for order in self._orders.values() if getattr(order, "status", None) != "cancelled"
        )
        return round(revenue, 2)
