import uuid
from .inventory import InventoryManager, OutOfStockError
from .models import CartItem, Order
from .pricing import calculate_discount, calculate_subtotal, calculate_tax


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
            taxable_amount = max(subtotal - discount, 0.0)
            tax = calculate_tax(taxable_amount)
            total = round(taxable_amount + tax, 2)

            order = Order(
                order_id=str(uuid.uuid4())[:8],
                items=items,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
            )
            # Initialize status for new orders
            setattr(order, "status", "created")
            self._orders[order.order_id] = order
            return order
        except Exception:
            # Roll back reservations on any unexpected error
            for sku, qty in reserved_items:
                self.inventory.add_stock(sku, qty)
            raise

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def cancel_order(self, order_id: str) -> Order:
        """Cancel an existing order and restore its stock.

        Args:
            order_id: Identifier of the order to cancel.

        Returns:
            The updated Order instance with status set to "cancelled".

        Raises:
            KeyError: If the order does not exist.
            ValueError: If the order is already cancelled.
        """
        order = self._orders.get(order_id)
        if order is None:
            raise KeyError(f"Order with id {order_id} does not exist")

        current_status = getattr(order, "status", None)
        if current_status == "cancelled":
            raise ValueError(f"Order {order_id} is already cancelled")

        # Restore inventory for each item in the order
        for item in order.items:
            self.inventory.add_stock(item.product.sku, item.quantity)

        # Update order status
        setattr(order, "status", "cancelled")
        return order
