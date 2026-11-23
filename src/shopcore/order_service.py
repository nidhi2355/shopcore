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
            total = round(taxable_amount + tax, 2)

            order = Order(
                order_id=str(uuid.uuid4())[:8],
                items=items,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
            )
            self._orders[order.order_id] = order
            return order
        except Exception:
            # If any calculation fails, roll back reserved stock
            for sku, qty in reserved_items:
                self.inventory.add_stock(sku, qty)
            raise
        
