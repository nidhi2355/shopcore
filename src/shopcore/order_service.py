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

        # Pre‑validation: ensure all items have sufficient stock before any reservation
        for item in items:
            available = self.inventory.get_stock(item.product.sku)
            if available < item.quantity:
                raise OutOfStockError(
                    f"Insufficient stock for {item.product.sku}: requested {item.quantity}, available {available}"
                )

        reserved: list[tuple[str, int]] = []
        try:
            # Reserve stock for each item, tracking successful reservations
            for item in items:
                self.inventory.reserve_stock(item.product.sku, item.quantity)
                reserved.append((item.product.sku, item.quantity))

            subtotal = calculate_subtotal(items)
            discount = calculate_discount(subtotal, coupon_code)
            taxable_amount = subtotal - discount
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
        except Exception as exc:
            # Roll back any stock that was already reserved
            for sku, qty in reserved:
                # Use add_stock to return the reserved quantity
                self.inventory.add_stock(sku, qty)
            # Re‑raise the original exception
            raise exc

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)
