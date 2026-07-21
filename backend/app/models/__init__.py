"""
Importa todos os models para que o mapper registry do SQLAlchemy resolva
corretamente as relationships declaradas por string (ex: Mapped["Order"]),
independentemente da ordem de import de cada módulo individual.
"""
from app.models.base import Base
from app.models.user import Address, PasswordResetToken, User
from app.models.catalog import Category, Product, ProductVariant
from app.models.inventory import Inventory, InventoryMovement, PriceLog
from app.models.commerce import Cart, CartItem, Order, OrderItem, Payment
from app.models.ml import MLModelMetric, MLPrediction, RestockSuggestion

__all__ = [
    "Base",
    "User",
    "Address",
    "PasswordResetToken",
    "Category",
    "Product",
    "ProductVariant",
    "Inventory",
    "InventoryMovement",
    "PriceLog",
    "Cart",
    "CartItem",
    "Order",
    "OrderItem",
    "Payment",
    "MLPrediction",
    "MLModelMetric",
    "RestockSuggestion",
]