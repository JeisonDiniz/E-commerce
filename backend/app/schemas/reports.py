from datetime import date

from pydantic import BaseModel


class DailySalesPoint(BaseModel):
    sale_date: date
    units_sold: int
    revenue: float


class TopProduct(BaseModel):
    product_name: str
    sku: str
    units_sold: int
    revenue: float


class InventoryStatusSummary(BaseModel):
    total_variants: int
    total_units_in_stock: int
    variants_below_min: int