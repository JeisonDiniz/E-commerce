"""
Popula o Postgres (schema criado por database/schema.sql) com o catálogo e
o histórico de vendas sintéticos gerados em database/seed/.

Requisitos antes de rodar:
  1. Postgres no ar, com o schema já aplicado:
         psql "$DATABASE_URL" -f ../database/schema.sql
  2. .env configurado (ver backend/.env.example).

Uso (a partir da pasta backend/, com o venv ativado):
    python -m scripts.seed_database                # popula (idempotente só se banco vazio)
    python -m scripts.seed_database --reset         # apaga tudo antes de popular de novo
    python -m scripts.seed_database --start 2024-01-01 --end 2025-12-31

Decisões importantes:
  - `orders.created_at` / `order_items.created_at` são gravados com a DATA
    HISTÓRICA da venda simulada (não com o instante da execução do script),
    porque é exatamente essa coluna que alimenta a view `vw_daily_sales`
    usada pelo módulo de ML (Prophet precisa de histórico real ao longo do
    tempo para aprender sazonalidade).
  - O nível de estoque atual (`inventory.quantity`) é definido de forma
    independente do replay dos movimentos históricos: os SKUs mais vendidos
    recebem estoque baixo (simulando risco de RUPTURA) e os menos vendidos
    recebem estoque alto (simulando excesso de produto PARADO) — os dois
    problemas centrais que motivam este TCC (ver docs/er-diagram.md).
"""
import argparse
import asyncio
import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "database" / "seed"))
from catalog import build_flat_catalog  # noqa: E402
from generate_synthetic_sales import generate_daily_sales  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.catalog import Category, Product, ProductVariant  # noqa: E402
from app.models.commerce import Order, OrderItem, Payment  # noqa: E402
from app.models.enums import (  # noqa: E402
    GenderType,
    MovementType,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    SeasonType,
    SizeType,
    UserRole,
)
from app.models.inventory import Inventory, InventoryMovement, PriceLog  # noqa: E402
from app.models.user import Address, User  # noqa: E402

DEMO_PASSWORD = "Senha@123"
CHUNK_SIZE = 2000

CUSTOMER_FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Fábio", "Gabriela", "Hugo",
    "Isabela", "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia",
    "Paulo", "Queila", "Rafael", "Sabrina", "Thiago", "Vanessa", "Wesley",
]
CUSTOMER_LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Pereira", "Costa", "Rodrigues",
    "Almeida", "Nascimento", "Lima", "Araújo", "Fernandes", "Carvalho",
]
CITIES = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
    ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
]


async def reset_database(session: AsyncSession) -> None:
    print("Apagando dados existentes (--reset)...")
    await session.execute(
        text(
            """
            TRUNCATE TABLE
                restock_suggestions, ml_predictions, ml_model_metrics,
                price_logs, inventory_movements, payments, order_items,
                orders, cart_items, carts, inventory, product_variants,
                products, categories, addresses, users
            RESTART IDENTITY CASCADE
            """
        )
    )
    await session.commit()


async def seed_users(session: AsyncSession, n_customers: int, rng: np.random.Generator) -> dict:
    users = [
        {"id": uuid.uuid4(), "name": "Administrador", "email": "admin@loja.com",
         "password_hash": hash_password(DEMO_PASSWORD), "role": UserRole.admin},
        {"id": uuid.uuid4(), "name": "Gestora de Estoque", "email": "gestor@loja.com",
         "password_hash": hash_password(DEMO_PASSWORD), "role": UserRole.manager},
        {"id": uuid.uuid4(), "name": "Operador de Estoque", "email": "estoque@loja.com",
         "password_hash": hash_password(DEMO_PASSWORD), "role": UserRole.staff},
    ]

    customer_ids = []
    for i in range(n_customers):
        first = CUSTOMER_FIRST_NAMES[i % len(CUSTOMER_FIRST_NAMES)]
        last = CUSTOMER_LAST_NAMES[(i * 3) % len(CUSTOMER_LAST_NAMES)]
        user_id = uuid.uuid4()
        customer_ids.append(user_id)
        users.append(
            {
                "id": user_id,
                "name": f"{first} {last}",
                "email": f"cliente{i+1}@exemplo.com",
                "password_hash": hash_password(DEMO_PASSWORD),
                "role": UserRole.customer,
            }
        )

    await session.execute(insert(User), users)

    addresses = []
    address_by_customer = {}
    for user_id in customer_ids:
        city, state = CITIES[rng.integers(0, len(CITIES))]
        address_id = uuid.uuid4()
        address_by_customer[user_id] = address_id
        addresses.append(
            {
                "id": address_id,
                "user_id": user_id,
                "street": "Rua das Flores",
                "number": str(rng.integers(10, 999)),
                "complement": None,
                "neighborhood": "Centro",
                "city": city,
                "state": state,
                "zip_code": f"{rng.integers(10000, 99999)}-{rng.integers(100, 999)}",
                "is_default": True,
            }
        )
    await session.execute(insert(Address), addresses)
    await session.commit()

    return {
        "admin_id": users[0]["id"],
        "manager_id": users[1]["id"],
        "staff_id": users[2]["id"],
        "customer_ids": customer_ids,
        "address_by_customer": address_by_customer,
    }


async def seed_catalog(session: AsyncSession):
    categories, products, variants = build_flat_catalog()

    category_ids: dict[str, uuid.UUID] = {slug: uuid.uuid4() for slug in [c["slug"] for c in categories]}
    category_rows = [
        {
            "id": category_ids[c["slug"]],
            "name": c["name"],
            "slug": c["slug"],
            "parent_id": category_ids[c["parent_slug"]] if c["parent_slug"] else None,
        }
        for c in categories
    ]
    await session.execute(insert(Category), category_rows)

    product_ids: dict[str, uuid.UUID] = {p["slug"]: uuid.uuid4() for p in products}
    product_rows = [
        {
            "id": product_ids[p["slug"]],
            "category_id": category_ids[p["category_slug"]],
            "name": p["name"],
            "description": p["description"],
            "brand": p["brand"],
            "gender": GenderType(p["gender"]),
            "season": SeasonType(p["season"]),
            "base_price": p["base_price"],
            "active": True,
        }
        for p in products
    ]
    await session.execute(insert(Product), product_rows)

    variant_ids: dict[str, uuid.UUID] = {v["sku"]: uuid.uuid4() for v in variants}
    variant_rows = [
        {
            "id": variant_ids[v["sku"]],
            "product_id": product_ids[v["product_slug"]],
            "sku": v["sku"],
            "size": SizeType(v["size"]),
            "color": v["color"],
            "price": v["price"],
            "cost_price": v["cost_price"],
            "active": True,
        }
        for v in variants
    ]
    await session.execute(insert(ProductVariant), variant_rows)
    await session.commit()

    return category_ids, product_ids, variant_ids, variants


async def seed_inventory(session: AsyncSession, variant_ids: dict, sales_df: pd.DataFrame, rng: np.random.Generator):
    """
    Define o saldo ATUAL de estoque por variante (independente do replay do
    histórico de vendas) de forma proposital: best-sellers ficam com estoque
    baixo (risco de ruptura) e itens de baixa saída ficam com estoque alto
    (excesso parado) — evidenciando os dois problemas citados na introdução
    do TCC diretamente nos dados de demonstração.
    """
    total_sold = sales_df.groupby("sku")["units_sold"].sum()

    rows = []
    for sku, variant_id in variant_ids.items():
        sold = int(total_sold.get(sku, 0))
        rows.append({"sku": sku, "variant_id": variant_id, "sold": sold})

    df = pd.DataFrame(rows).sort_values("sold")
    n = len(df)
    low_cutoff = int(n * 0.2)
    high_cutoff = int(n * 0.8)

    inventory_rows = []
    for i, row in enumerate(df.itertuples()):
        if i < low_cutoff:
            # Pouca saída histórica -> deixamos estoque alto (produto parado).
            quantity = int(rng.integers(150, 300))
            min_q, max_q = 10, 300
        elif i >= high_cutoff:
            # Muita saída histórica -> deixamos estoque baixo (risco de ruptura).
            quantity = int(rng.integers(0, 5))
            min_q, max_q = 15, 200
        else:
            quantity = int(rng.integers(20, 60))
            min_q, max_q = 10, 150

        inventory_rows.append(
            {
                "id": uuid.uuid4(),
                "variant_id": row.variant_id,
                "quantity": quantity,
                "min_quantity": min_q,
                "max_quantity": max_q,
            }
        )

    await session.execute(insert(Inventory), inventory_rows)
    await session.commit()


async def _execute_chunked(session: AsyncSession, table, rows: list[dict]) -> None:
    for start in range(0, len(rows), CHUNK_SIZE):
        await session.execute(insert(table), rows[start : start + CHUNK_SIZE])
    await session.commit()


async def seed_sales_history(
    session: AsyncSession,
    variant_ids: dict,
    sales_df: pd.DataFrame,
    customer_ids: list[uuid.UUID],
    address_by_customer: dict,
    rng: np.random.Generator,
) -> None:
    """Materializa cada linha (sku, data, quantidade) como um pedido histórico completo."""
    payment_methods = list(PaymentMethod)

    order_rows, item_rows, payment_rows, movement_rows = [], [], [], []

    customer_idx = rng.integers(0, len(customer_ids), size=len(sales_df))

    for row_i, sale in enumerate(sales_df.itertuples(index=False)):
        variant_id = variant_ids[sale.sku]
        customer_id = customer_ids[customer_idx[row_i]]
        address_id = address_by_customer[customer_id]

        order_id = uuid.uuid4()
        created_at = pd.Timestamp(sale.sale_date).to_pydatetime()
        total = float(sale.revenue)

        order_rows.append(
            {
                "id": order_id,
                "user_id": customer_id,
                "shipping_address_id": address_id,
                "status": OrderStatus.entregue,
                "total_amount": total,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        item_rows.append(
            {
                "id": uuid.uuid4(),
                "order_id": order_id,
                "variant_id": variant_id,
                "quantity": int(sale.units_sold),
                "unit_price": float(sale.price),
                "created_at": created_at,
            }
        )
        payment_rows.append(
            {
                "id": uuid.uuid4(),
                "order_id": order_id,
                "method": payment_methods[rng.integers(0, len(payment_methods))],
                "status": PaymentStatus.aprovado,
                "amount": total,
                "paid_at": created_at,
                "created_at": created_at,
            }
        )
        movement_rows.append(
            {
                "id": uuid.uuid4(),
                "variant_id": variant_id,
                "movement_type": MovementType.saida,
                "quantity": int(sale.units_sold),
                "reason": "venda",
                "reference_order_id": order_id,
                "created_by": None,
                "created_at": created_at,
            }
        )

    print(f"Inserindo {len(order_rows):,} pedidos históricos (isso pode levar alguns minutos)...")
    await _execute_chunked(session, Order.__table__, order_rows)
    await _execute_chunked(session, OrderItem.__table__, item_rows)
    await _execute_chunked(session, Payment.__table__, payment_rows)
    await _execute_chunked(session, InventoryMovement.__table__, movement_rows)


async def seed_monthly_restocks(
    session: AsyncSession, variant_ids: dict, start: str, end: str, manager_id: uuid.UUID, rng: np.random.Generator
) -> None:
    """Movimentos de 'entrada' mensais por variante, para popular o livro-razão de estoque."""
    months = pd.date_range(start, end, freq="MS")
    rows = []
    for variant_id in variant_ids.values():
        for month_start in months:
            entry_date = (month_start + pd.Timedelta(days=int(rng.integers(0, 5)))).to_pydatetime()
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "variant_id": variant_id,
                    "movement_type": MovementType.entrada,
                    "quantity": int(rng.integers(20, 80)),
                    "reason": "reposicao_mensal",
                    "reference_order_id": None,
                    "created_by": manager_id,
                    "created_at": entry_date,
                }
            )

    print(f"Inserindo {len(rows):,} movimentos de reposição mensal...")
    await _execute_chunked(session, InventoryMovement.__table__, rows)


async def seed_price_logs(
    session: AsyncSession, variants: list[dict], variant_ids: dict, manager_id: uuid.UUID, rng: np.random.Generator
) -> None:
    """Registra um reajuste de preço histórico para ~15% das variantes (audita o preço vigente)."""
    sample = rng.choice(variants, size=max(1, int(len(variants) * 0.15)), replace=False)
    rows = []
    for v in sample:
        new_price = float(v["price"])
        old_price = round(new_price / 1.08, 2)
        rows.append(
            {
                "id": uuid.uuid4(),
                "variant_id": variant_ids[v["sku"]],
                "old_price": old_price,
                "new_price": new_price,
                "changed_by": manager_id,
                "changed_at": pd.Timestamp.now() - pd.Timedelta(days=270),
            }
        )
    await _execute_chunked(session, PriceLog.__table__, rows)


async def run(start: str, end: str, seed: int, reset: bool) -> None:
    rng = np.random.default_rng(seed)

    async with AsyncSessionLocal() as session:
        if reset:
            await reset_database(session)

        existing = await session.execute(select(Category.id).limit(1))
        if existing.scalar_one_or_none() is not None and not reset:
            print("O banco já contém dados. Rode novamente com --reset para recriar do zero.")
            return

        print("Gerando dataset sintético (pandas/numpy)...")
        _, _, variants, sales_df = generate_daily_sales(start, end, seed)

        print("Semeando usuários e endereços...")
        identities = await seed_users(session, n_customers=40, rng=rng)

        print("Semeando catálogo (categorias, produtos, variantes)...")
        _, _, variant_ids, variant_records = await seed_catalog(session)

        print("Semeando estoque atual (com casos propositais de ruptura/excesso)...")
        await seed_inventory(session, variant_ids, sales_df, rng)

        await seed_sales_history(
            session, variant_ids, sales_df, identities["customer_ids"], identities["address_by_customer"], rng
        )

        await seed_monthly_restocks(session, variant_ids, start, end, identities["manager_id"], rng)

        print("Semeando histórico de reajustes de preço...")
        await seed_price_logs(session, variant_records, variant_ids, identities["manager_id"], rng)

    await engine.dispose()
    print("\nSeed concluído com sucesso.")
    print(f"Login de demonstração -> admin@loja.com / gestor@loja.com / estoque@loja.com (senha: {DEMO_PASSWORD})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true", help="Apaga todos os dados antes de semear novamente")
    args = parser.parse_args()

    asyncio.run(run(args.start, args.end, args.seed, args.reset))


if __name__ == "__main__":
    main()