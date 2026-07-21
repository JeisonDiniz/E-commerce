"""
Carregamento e engenharia de features a partir do histórico de vendas.

Duas fontes de dados são suportadas, produzindo o MESMO formato de saída
(colunas normalizadas), para que o restante do pipeline seja agnóstico à
origem dos dados:

  - `load_daily_sales_from_csv`: lê `database/seed/output/sales_history.csv`
    (gerado na Etapa 6) — usado para desenvolvimento/teste dos modelos sem
    precisar do Postgres no ar.
  - `load_daily_sales_from_db`: consulta a view `vw_daily_sales` (Postgres)
    — usado em produção, já traz `variant_id`/`category_id` reais (UUID),
    necessários para gravar as previsões com as FKs corretas.

Depois de carregado, dois agregados são construídos:
  - `build_category_series`: série diária por categoria (entrada do Prophet).
  - `build_variant_month_table`: tabela variante×mês (entrada do Random Forest).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CSV_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "database" / "seed" / "output" / "sales_history.csv"


def load_daily_sales_from_csv(path: Path | str = CSV_DEFAULT_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["sale_date"])
    return df.rename(columns={"sku": "variant_id", "category_slug": "category_id"})[
        ["variant_id", "category_id", "gender", "season", "size", "color", "price", "sale_date", "units_sold", "revenue"]
    ]


async def load_daily_sales_from_db(session: AsyncSession) -> pd.DataFrame:
    result = await session.execute(text("SELECT * FROM vw_daily_sales"))
    rows = [dict(r._mapping) for r in result]
    df = pd.DataFrame(rows)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["variant_id"] = df["variant_id"].astype(str)
    df["category_id"] = df["category_id"].astype(str)
    return df[["variant_id", "category_id", "gender", "season", "size", "color", "price", "sale_date", "units_sold", "revenue"]]


def build_category_series(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Uma série diária (ds, y) por categoria, com datas faltantes preenchidas com 0 vendas."""
    series: dict[str, pd.DataFrame] = {}
    full_range = pd.date_range(df["sale_date"].min(), df["sale_date"].max(), freq="D")

    for category_id, group in df.groupby("category_id"):
        daily = group.groupby("sale_date")["units_sold"].sum().reindex(full_range, fill_value=0)
        series[category_id] = pd.DataFrame({"ds": full_range, "y": daily.values})

    return series


def build_variant_month_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega vendas por (variante, mês-calendário). Atributos estáticos
    (categoria/gênero/estação/tamanho/cor/preço) são carregados via `first`
    pois não variam ao longo do tempo neste catálogo.
    """
    df = df.copy()
    df["month_period"] = df["sale_date"].dt.to_period("M")

    static_cols = ["category_id", "gender", "season", "size", "color", "price"]
    agg = (
        df.groupby(["variant_id", "month_period"])
        .agg(units_sold=("units_sold", "sum"), **{c: (c, "first") for c in static_cols})
        .reset_index()
    )
    agg["month_num"] = agg["month_period"].dt.month
    agg["month_sin"] = np.sin(2 * np.pi * agg["month_num"] / 12)
    agg["month_cos"] = np.cos(2 * np.pi * agg["month_num"] / 12)
    return agg


def split_train_test_by_month(monthly_df: pd.DataFrame, test_months: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split TEMPORAL (não aleatório): os últimos `test_months` meses do
    histórico viram o conjunto de teste, simulando a situação real de
    "prever demanda dos próximos meses com base nos meses anteriores" —
    evita vazamento de informação do futuro para o passado.
    """
    periods = sorted(monthly_df["month_period"].unique())
    if len(periods) <= test_months:
        raise ValueError("Histórico curto demais para separar meses de teste")

    train_periods = set(periods[:-test_months])
    train_df = monthly_df[monthly_df["month_period"].isin(train_periods)].copy()
    test_df = monthly_df[~monthly_df["month_period"].isin(train_periods)].copy()
    return train_df, test_df


def attach_historical_feature(
    train_df: pd.DataFrame, test_df: pd.DataFrame | None = None
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """
    Adiciona `historical_avg_monthly_units`: a demanda média mensal de cada
    variante, calculada SOMENTE a partir do período de treino. É a feature
    que captura a "popularidade" (relativamente estável) de cada item —
    sem essa feature, o modelo não teria como distinguir um best-seller de
    um produto parado apenas por categoria/tamanho/cor/preço.
    """
    hist = train_df.groupby("variant_id")["units_sold"].mean().rename("historical_avg_monthly_units")

    train_df = train_df.merge(hist, on="variant_id", how="left")
    train_df["historical_avg_monthly_units"] = train_df["historical_avg_monthly_units"].fillna(0)

    if test_df is not None:
        test_df = test_df.merge(hist, on="variant_id", how="left")
        test_df["historical_avg_monthly_units"] = test_df["historical_avg_monthly_units"].fillna(0)
        return train_df, test_df

    return train_df, None


def build_next_month_rows(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Uma linha por variante com os atributos mais recentes + o mês seguinte
    ao último mês observado no histórico — é o que o Random Forest treinado
    em produção usa para prever a demanda do próximo período.
    """
    last_period = monthly_df["month_period"].max()
    next_period = last_period + 1

    latest = monthly_df.sort_values("month_period").groupby("variant_id").last().reset_index()
    hist_all = monthly_df.groupby("variant_id")["units_sold"].mean().rename("historical_avg_monthly_units")

    rows = latest[["variant_id", "category_id", "gender", "season", "size", "color", "price"]].copy()
    rows = rows.merge(hist_all, on="variant_id", how="left")
    rows["historical_avg_monthly_units"] = rows["historical_avg_monthly_units"].fillna(0)
    rows["month_num"] = next_period.month
    rows["month_sin"] = np.sin(2 * np.pi * rows["month_num"] / 12)
    rows["month_cos"] = np.cos(2 * np.pi * rows["month_num"] / 12)
    rows["target_period"] = str(next_period)
    rows["target_date"] = next_period.to_timestamp()
    return rows
