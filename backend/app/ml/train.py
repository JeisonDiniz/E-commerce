"""
Orquestra o treinamento dos dois modelos, avalia contra os critérios de
aceitação do TCC e (opcionalmente) grava previsões/métricas no Postgres.

Uso (a partir de backend/, com o venv ativado):

    # Modo offline: só calcula métricas com o CSV da Etapa 6, não toca no banco.
    python -m app.ml.train --source csv

    # Modo produção: lê a view vw_daily_sales do Postgres e grava
    # ml_model_metrics + ml_predictions + restock_suggestions.
    python -m app.ml.train --source db

Critérios de aceitação (definidos no projeto de pesquisa do TCC):
    Prophet:       MAE < 5.0 unidades  | MAPE < 7.00%
    Random Forest: MAE < 3.0 unidades  | MAPE < 5.00%
"""
import argparse
import asyncio
import math
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.ml import features, prophet_model, random_forest_model
from app.ml.holidays import build_brazilian_retail_holidays
from app.models.enums import ModelType, SuggestionStatus
from app.models.inventory import Inventory
from app.models.ml import MLModelMetric, MLPrediction, RestockSuggestion

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

ACCEPTANCE_THRESHOLDS = {
    ModelType.prophet: {"mae": 5.0, "mape": 7.0},
    ModelType.random_forest: {"mae": 3.0, "mape": 5.0},
}

# Margem de segurança aplicada sobre a demanda prevista para decidir se vale
# a pena sugerir reposição (cobre a incerteza da previsão + tempo de reposição).
RESTOCK_SAFETY_FACTOR = 1.3


def _print_metric_report(model_name: str, model_type: ModelType, metrics: dict) -> None:
    thresholds = ACCEPTANCE_THRESHOLDS[model_type]
    mae_ok = metrics["mae"] < thresholds["mae"]
    mape_ok = metrics["mape"] < thresholds["mape"]
    status = "OK" if (mae_ok and mape_ok) else "ABAIXO DO ESPERADO"
    print(
        f"[{model_name}] MAE={metrics['mae']:.3f} (limite {thresholds['mae']}) | "
        f"MAPE={metrics['mape']:.2f}% (limite {thresholds['mape']}%) | "
        f"n_test={metrics['n_test']} -> {status}"
    )


async def run_prophet(
    df: pd.DataFrame, forecast_periods: int
) -> tuple[dict, dict[str, pd.DataFrame]]:
    holidays_df = build_brazilian_retail_holidays(
        range(df["sale_date"].dt.year.min(), df["sale_date"].dt.year.max() + 1)
    )
    category_series = features.build_category_series(df)

    per_category_metrics = []
    forecasts: dict[str, pd.DataFrame] = {}

    for category_id, series in category_series.items():
        eval_metrics = prophet_model.train_and_evaluate(series, holidays_df)
        if eval_metrics is not None:
            per_category_metrics.append(eval_metrics)

        full_model = prophet_model.fit_full(series, holidays_df)
        forecasts[category_id] = prophet_model.forecast_future(
            full_model, last_history_date=series["ds"].max(), periods=forecast_periods
        )
        joblib.dump(full_model, ARTIFACTS_DIR / f"prophet_{category_id}.joblib")

    n_total = sum(m["n_test"] for m in per_category_metrics)
    aggregate = {
        "mae": float(np.average([m["mae"] for m in per_category_metrics], weights=[m["n_test"] for m in per_category_metrics])),
        "mape": float(np.average([m["mape"] for m in per_category_metrics], weights=[m["n_test"] for m in per_category_metrics])),
        "n_test": n_total,
        "n_categories": len(per_category_metrics),
    }
    return aggregate, forecasts


def run_random_forest(df: pd.DataFrame) -> tuple[dict, np.ndarray, pd.DataFrame]:
    monthly_df = features.build_variant_month_table(df)
    train_df, test_df = features.split_train_test_by_month(monthly_df, test_months=4)
    train_df, test_df = features.attach_historical_feature(train_df, test_df)

    _, eval_metrics = random_forest_model.train_and_evaluate(train_df, test_df)

    # Reajusta com TODO o histórico para gerar a previsão do próximo mês real.
    full_df, _ = features.attach_historical_feature(monthly_df)
    full_pipeline = random_forest_model.fit_full(full_df)
    joblib.dump(full_pipeline, ARTIFACTS_DIR / "random_forest.joblib")

    next_month_rows = features.build_next_month_rows(monthly_df)
    predictions = random_forest_model.predict(full_pipeline, next_month_rows)

    return eval_metrics, predictions, next_month_rows


async def persist_results(
    session: AsyncSession,
    prophet_metrics: dict,
    prophet_forecasts: dict[str, pd.DataFrame],
    rf_metrics: dict,
    rf_predictions: np.ndarray,
    rf_rows: pd.DataFrame,
) -> None:
    now = datetime.now(timezone.utc)

    await session.execute(
        insert(MLModelMetric),
        [
            {
                "id": uuid.uuid4(),
                "model_type": ModelType.prophet,
                "model_version": prophet_model.MODEL_VERSION,
                "mae": prophet_metrics["mae"],
                "mape": prophet_metrics["mape"],
                "rmse": None,
                "training_samples": prophet_metrics["n_test"],
                "trained_at": now,
                "notes": f"Média ponderada entre {prophet_metrics['n_categories']} categorias (holdout temporal).",
            },
            {
                "id": uuid.uuid4(),
                "model_type": ModelType.random_forest,
                "model_version": random_forest_model.MODEL_VERSION,
                "mae": rf_metrics["mae"],
                "mape": rf_metrics["mape"],
                "rmse": rf_metrics["rmse"],
                "training_samples": rf_metrics["n_test"],
                "trained_at": now,
                "notes": "Holdout dos últimos 4 meses (split temporal por variante/mês).",
            },
        ],
    )

    # --- Previsões Prophet (macro, por categoria) ---
    prophet_rows = []
    for category_id, forecast_df in prophet_forecasts.items():
        for _, r in forecast_df.iterrows():
            prophet_rows.append(
                {
                    "id": uuid.uuid4(),
                    "model_type": ModelType.prophet,
                    "variant_id": None,
                    "category_id": category_id,
                    "prediction_date": r["ds"].date(),
                    "predicted_quantity": round(float(r["yhat"]), 2),
                    "confidence_lower": round(float(r["yhat_lower"]), 2),
                    "confidence_upper": round(float(r["yhat_upper"]), 2),
                    "model_version": prophet_model.MODEL_VERSION,
                    "generated_at": now,
                }
            )
    if prophet_rows:
        await session.execute(insert(MLPrediction), prophet_rows)

    # --- Previsões Random Forest (por variante, próximo mês) ---
    rf_rows = rf_rows.copy()
    rf_rows["predicted_quantity"] = rf_predictions
    rf_prediction_rows = []
    prediction_id_by_variant = {}
    for _, r in rf_rows.iterrows():
        prediction_id = uuid.uuid4()
        prediction_id_by_variant[r["variant_id"]] = (prediction_id, float(r["predicted_quantity"]))
        rf_prediction_rows.append(
            {
                "id": prediction_id,
                "model_type": ModelType.random_forest,
                "variant_id": r["variant_id"],
                "category_id": None,
                "prediction_date": r["target_date"].date(),
                "predicted_quantity": round(float(r["predicted_quantity"]), 2),
                "confidence_lower": None,
                "confidence_upper": None,
                "model_version": random_forest_model.MODEL_VERSION,
                "generated_at": now,
            }
        )
    if rf_prediction_rows:
        await session.execute(insert(MLPrediction), rf_prediction_rows)

    await session.commit()

    # --- Sugestões de reposição (apenas sugestão — aprovação humana obrigatória) ---
    inventory_result = await session.execute(select(Inventory.variant_id, Inventory.quantity))
    current_stock = {str(variant_id): qty for variant_id, qty in inventory_result.all()}

    suggestion_rows = []
    for variant_id_str, (prediction_id, predicted_qty) in prediction_id_by_variant.items():
        on_hand = current_stock.get(str(variant_id_str), 0)
        required = predicted_qty * RESTOCK_SAFETY_FACTOR
        if required > on_hand:
            suggestion_rows.append(
                {
                    "id": uuid.uuid4(),
                    "variant_id": variant_id_str,
                    "based_on_prediction_id": prediction_id,
                    "suggested_quantity": max(1, math.ceil(required - on_hand)),
                    "status": SuggestionStatus.pendente,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "created_at": now,
                }
            )

    if suggestion_rows:
        await session.execute(insert(RestockSuggestion), suggestion_rows)
        await session.commit()

    print(f"\n{len(prophet_rows)} previsões Prophet + {len(rf_prediction_rows)} previsões Random Forest gravadas.")
    print(f"{len(suggestion_rows)} sugestões de reposição criadas (status: pendente, aguardando aprovação humana).")


async def main(source: str, forecast_periods: int) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    session: AsyncSession | None = None
    if source == "csv":
        print("Carregando histórico de vendas do CSV sintético (modo offline, sem gravação no banco)...")
        df = features.load_daily_sales_from_csv()
    else:
        print("Carregando histórico de vendas de vw_daily_sales (Postgres)...")
        session = AsyncSessionLocal()
        df = await features.load_daily_sales_from_db(session)

    print(f"{len(df):,} registros de venda carregados ({df['sale_date'].min().date()} a {df['sale_date'].max().date()})\n")

    print("Treinando Prophet (uma série por categoria)...")
    prophet_metrics, prophet_forecasts = await run_prophet(df, forecast_periods)
    _print_metric_report("Prophet", ModelType.prophet, prophet_metrics)

    print("\nTreinando Random Forest (demanda por variante/mês)...")
    rf_metrics, rf_predictions, rf_rows = run_random_forest(df)
    _print_metric_report("Random Forest", ModelType.random_forest, rf_metrics)

    if session is not None:
        print("\nGravando métricas, previsões e sugestões de reposição no Postgres...")
        await persist_results(session, prophet_metrics, prophet_forecasts, rf_metrics, rf_predictions, rf_rows)
        await session.close()
        await engine.dispose()
    else:
        print("\nModo offline (--source csv): nada foi gravado no banco. Rode com --source db para persistir.")


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["csv", "db"], default="csv")
    parser.add_argument("--forecast-periods", type=int, default=30, help="Dias de previsão futura do Prophet")
    args = parser.parse_args()
    asyncio.run(main(args.source, args.forecast_periods))


if __name__ == "__main__":
    cli()