"""
Endpoints de relatórios gerenciais (dashboard).

Consultam diretamente a view `vw_daily_sales` (criada em database/schema.sql,
que já filtra pedidos cancelados e agrega por dia/variante) via SQL textual —
não há um model ORM para uma view somente-leitura usada apenas em agregações.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.schemas.reports import DailySalesPoint, InventoryStatusSummary, TopProduct

router = APIRouter(
    prefix="/reports",
    tags=["Relatórios"],
    dependencies=[Depends(require_roles(UserRole.staff, UserRole.manager, UserRole.admin))],
)


@router.get("/sales-summary", response_model=list[DailySalesPoint])
async def sales_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[DailySalesPoint]:
    # Casts explícitos (::date) nos parâmetros: sem eles, quando start_date/
    # end_date são None (nenhum filtro informado — o caso mais comum, usado
    # pelo dashboard), o asyncpg não consegue inferir o tipo de um parâmetro
    # NULL isolado e falha com "AmbiguousParameterError" antes mesmo de
    # rodar a query.
    stmt = text(
        """
        SELECT sale_date, SUM(units_sold) AS units_sold, SUM(revenue) AS revenue
        FROM vw_daily_sales
        WHERE (CAST(:start_date AS DATE) IS NULL OR sale_date >= CAST(:start_date AS DATE))
          AND (CAST(:end_date AS DATE) IS NULL OR sale_date <= CAST(:end_date AS DATE))
        GROUP BY sale_date
        ORDER BY sale_date
        """
    )
    result = await db.execute(stmt, {"start_date": start_date, "end_date": end_date})
    return [DailySalesPoint(**row._mapping) for row in result]


@router.get("/top-products", response_model=list[TopProduct])
async def top_products(limit: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> list[TopProduct]:
    stmt = text(
        """
        SELECT p.name AS product_name, ds.sku, SUM(ds.units_sold) AS units_sold, SUM(ds.revenue) AS revenue
        FROM vw_daily_sales ds
        JOIN product_variants pv ON pv.id = ds.variant_id
        JOIN products p ON p.id = pv.product_id
        GROUP BY p.name, ds.sku
        ORDER BY units_sold DESC
        LIMIT :limit
        """
    )
    result = await db.execute(stmt, {"limit": limit})
    return [TopProduct(**row._mapping) for row in result]


@router.get("/inventory-status", response_model=InventoryStatusSummary)
async def inventory_status(db: AsyncSession = Depends(get_db)) -> InventoryStatusSummary:
    stmt = text(
        """
        SELECT
            COUNT(*) AS total_variants,
            COALESCE(SUM(quantity), 0) AS total_units_in_stock,
            COUNT(*) FILTER (WHERE quantity <= min_quantity) AS variants_below_min
        FROM inventory
        """
    )
    result = await db.execute(stmt)
    return InventoryStatusSummary(**result.one()._mapping)