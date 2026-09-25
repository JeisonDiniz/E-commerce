from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    cart,
    categories,
    inventory,
    orders,
    payments,
    predictions,
    products,
    reports,
    shipping,
    users,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(reports.router)
api_router.include_router(predictions.router)
api_router.include_router(shipping.router)
api_router.include_router(payments.router)
api_router.include_router(webhooks.router)