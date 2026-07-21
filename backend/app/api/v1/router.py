from fastapi import APIRouter

from app.api.v1.endpoints import auth, cart, categories, inventory, orders, predictions, products, reports, users

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