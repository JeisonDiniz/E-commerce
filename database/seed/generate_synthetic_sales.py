"""
Gera um dataset sintético de vendas de roupas com sazonalidade, para treinar
e testar localmente os modelos de ML (Prophet + Random Forest) sem depender
do Postgres.

Modelo de geração (processo de Poisson não-homogêneo por variante/dia):

    lambda(variante, data) = popularidade(variante)
                            * fator_dia_da_semana(data)
                            * fator_sazonal(estacao_do_produto, mes)
                            * fator_feriado_comercial(data, categoria, genero)
                            * fator_tendencia(data)
                            * escala_global

    unidades_vendidas ~ Poisson(lambda)

Isso produz, de propósito, os padrões que os dois modelos devem aprender:
  - Prophet: sazonalidade semanal (pico fim de semana), mensal/anual
    (verão x inverno) e picos de datas comerciais (Black Friday, Natal,
    Dia das Mães, Dia dos Namorados, volta às aulas).
  - Random Forest: correlação entre categoria/tamanho/cor/preço e volume
    de demanda (produtos "populares" vendem consistentemente mais,
    produtos caros vendem consistentemente menos).

Uso:
    python generate_synthetic_sales.py --start 2024-01-01 --end 2025-12-31
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from catalog import build_flat_catalog

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Janelas de datas comerciais fixas (aproximação didática; datas móveis como
# Dia das Mães são recalculadas por ano dentro de `_holiday_multiplier`).
def _second_sunday_of_may(year: int) -> pd.Timestamp:
    first_of_may = pd.Timestamp(year=year, month=5, day=1)
    first_sunday = first_of_may + pd.Timedelta(days=(6 - first_of_may.weekday()) % 7)
    return first_sunday + pd.Timedelta(weeks=1)


def _last_friday_of_november(year: int) -> pd.Timestamp:
    last_of_nov = pd.Timestamp(year=year, month=11, day=30)
    offset = (last_of_nov.weekday() - 4) % 7
    return last_of_nov - pd.Timedelta(days=offset)


def _weekday_multiplier(dates: pd.DatetimeIndex) -> np.ndarray:
    weekday = dates.weekday.values  # Monday=0 ... Sunday=6
    return np.select(
        [weekday == 4, weekday == 5, weekday == 6],
        [1.2, 1.4, 1.15],
        default=1.0,
    )


def _season_multiplier(season: str, dates: pd.DatetimeIndex) -> np.ndarray:
    month = dates.month.values
    if season == "o_ano_todo":
        return np.ones(len(dates))

    peak_months = {
        "verao": {12, 1, 2, 3},
        "inverno": {6, 7, 8},
        "outono": {3, 4, 5},
        "primavera": {9, 10, 11},
    }[season]

    is_peak = np.isin(month, list(peak_months))
    return np.where(is_peak, 1.8, 0.65)


def _holiday_multiplier(dates: pd.DatetimeIndex, category_slug: str, gender: str) -> np.ndarray:
    mult = np.ones(len(dates))
    years = range(dates.year.min(), dates.year.max() + 1)

    for year in years:
        # Black Friday: pico geral em todas as categorias.
        bf = _last_friday_of_november(year)
        window = (dates >= bf - pd.Timedelta(days=1)) & (dates <= bf + pd.Timedelta(days=1))
        mult[window] *= 3.5

        # Natal: pico geral, janela mais longa.
        natal_start, natal_end = pd.Timestamp(year, 12, 15), pd.Timestamp(year, 12, 24)
        window = (dates >= natal_start) & (dates <= natal_end)
        mult[window] *= 2.3

        # Dia das Mães: pico forte em produtos femininos, leve nos demais.
        dia_maes = _second_sunday_of_may(year)
        window = (dates >= dia_maes - pd.Timedelta(days=3)) & (dates <= dia_maes)
        mult[window] *= 2.2 if gender == "feminino" else 1.25

        # Dia dos Namorados: pico moderado geral.
        namorados = pd.Timestamp(year, 6, 12)
        window = (dates >= namorados - pd.Timedelta(days=2)) & (dates <= namorados)
        mult[window] *= 1.6

        # Volta às aulas: leve alta em acessórios.
        if category_slug in {"bones", "acessorios", "cintos"}:
            volta_start, volta_end = pd.Timestamp(year, 1, 20), pd.Timestamp(year, 2, 10)
            window = (dates >= volta_start) & (dates <= volta_end)
            mult[window] *= 1.3

    return mult


def _trend_multiplier(dates: pd.DatetimeIndex) -> np.ndarray:
    n = len(dates)
    # Loja em crescimento moderado ao longo do período (30% no total).
    return 1.0 + 0.3 * (np.arange(n) / max(n - 1, 1))


def generate_daily_sales(start: str, end: str, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    categories, products, variants = build_flat_catalog()
    variants_df = pd.DataFrame(variants)
    products_df = pd.DataFrame(products)
    categories_df = pd.DataFrame(categories)

    dates = pd.date_range(start, end, freq="D")
    weekday_mult = _weekday_multiplier(dates)
    trend_mult = _trend_multiplier(dates)

    # Popularidade por variante: distribuição log-normal -> poucos best-sellers,
    # muitos itens medianos e alguns "parados" (baixa saída) — reproduz o
    # problema real de excesso de estoque parado citado no TCC.
    popularity = rng.lognormal(mean=0.0, sigma=0.9, size=len(variants_df))
    # Produtos mais caros tendem a vender um pouco menos (elasticidade simples).
    price_factor = (variants_df["price"].to_numpy() / variants_df["price"].mean()) ** -0.4

    records = []
    for i, variant in variants_df.iterrows():
        season_mult = _season_multiplier(variant["season"], dates)
        holiday_mult = _holiday_multiplier(dates, variant["category_slug"], variant["gender"])

        base_scale = 0.12
        lam = (
            popularity[i]
            * price_factor[i]
            * weekday_mult
            * season_mult
            * holiday_mult
            * trend_mult
            * base_scale
        )
        units = rng.poisson(lam)

        nonzero = units > 0
        if not nonzero.any():
            continue

        records.append(
            pd.DataFrame(
                {
                    "sku": variant["sku"],
                    "product_slug": variant["product_slug"],
                    "category_slug": variant["category_slug"],
                    "gender": variant["gender"],
                    "season": variant["season"],
                    "size": variant["size"],
                    "color": variant["color"],
                    "price": variant["price"],
                    "sale_date": dates[nonzero],
                    "units_sold": units[nonzero],
                }
            )
        )

    sales_df = pd.concat(records, ignore_index=True)
    sales_df["revenue"] = (sales_df["units_sold"] * sales_df["price"]).round(2)
    sales_df = sales_df.sort_values(["sale_date", "sku"]).reset_index(drop=True)

    return categories_df, products_df, variants_df, sales_df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    categories_df, products_df, variants_df, sales_df = generate_daily_sales(args.start, args.end, args.seed)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    categories_df.to_csv(OUTPUT_DIR / "categories.csv", index=False)
    products_df.to_csv(OUTPUT_DIR / "products.csv", index=False)
    variants_df.to_csv(OUTPUT_DIR / "variants.csv", index=False)
    sales_df.to_csv(OUTPUT_DIR / "sales_history.csv", index=False)

    print(f"Categorias: {len(categories_df)}")
    print(f"Produtos: {len(products_df)}")
    print(f"Variantes: {len(variants_df)}")
    print(f"Registros de venda (variante x dia): {len(sales_df):,}")
    print(f"Unidades vendidas no total: {int(sales_df['units_sold'].sum()):,}")
    print(f"Faturamento total simulado: R$ {sales_df['revenue'].sum():,.2f}")
    print(f"Período: {sales_df['sale_date'].min().date()} a {sales_df['sale_date'].max().date()}")
    print(f"\nArquivos salvos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()