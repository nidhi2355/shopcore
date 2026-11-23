from dataclasses import dataclass


@dataclass
class Product:
    sku: str
    name: str
    price: float
    category: str = ""


@dataclass
class CartItem:
    product: Product
    quantity: int

    def __post_init__(self) -> None:
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
