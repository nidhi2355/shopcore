from dataclasses import dataclass, field


@dataclass
class Product:
    sku: str
    name: str
    price: float
    category: str = "general"


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("CartItem quantity must be positive")
        if self.product.price < 0:
            raise ValueError("Product price cannot be negative")


@dataclass
class Order:
    order_id: str
    items: list[CartItem]
    subtotal: float
    discount: float
    tax: float
    total: float
    status: str = "confirmed"
    metadata: dict = field(default_factory=dict)