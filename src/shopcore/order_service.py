import uuid
from .inventory import InventoryManager
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

        for item in items:
            self.inventory.reserve_stock(item.product.sku, item.quantity)

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
        self._orders[order.order_id] = order
        return order

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)
