"""
Prophet — análise macro de série temporal por categoria.

Objetivo (conforme o TCC): capturar sazonalidade semanal, mensal/anual e de
datas comerciais para indicar os melhores períodos de venda por categoria,
apoiando decisões de compra antecipada (ex: comprar casacos antes do inverno).
"""
import logging

import numpy as np
import pandas as pd
from prophet import Prophet

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

MODEL_VERSION = "prophet-v1"


def _mae_mape(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    # MAPE só é estável para vendas > 0 (evita divisão por zero em dias sem venda).
    mask = y_true > 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else float("nan")
    return mae, mape


def _build_model(holidays_df: pd.DataFrame) -> Prophet:
    return Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        holidays=holidays_df,
        interval_width=0.8,
    )


def train_and_evaluate(daily_df: pd.DataFrame, holidays_df: pd.DataFrame, test_days: int = 90) -> dict | None:
    """Treina em (total - test_days) dias e avalia nos últimos `test_days` (holdout temporal)."""
    daily_df = daily_df.sort_values("ds").reset_index(drop=True)
    if len(daily_df) < test_days * 2:
        return None  # histórico curto demais para uma avaliação confiável

    split_date = daily_df["ds"].max() - pd.Timedelta(days=test_days)
    train = daily_df[daily_df["ds"] <= split_date]
    test = daily_df[daily_df["ds"] > split_date]

    model = _build_model(holidays_df)
    model.fit(train[["ds", "y"]])

    forecast = model.predict(test[["ds"]])
    merged = test.merge(forecast[["ds", "yhat"]], on="ds")
    mae, mape = _mae_mape(merged["y"].to_numpy(), np.clip(merged["yhat"].to_numpy(), 0, None))

    return {"mae": mae, "mape": mape, "n_test": len(merged)}


def fit_full(daily_df: pd.DataFrame, holidays_df: pd.DataFrame) -> Prophet:
    """Reajusta o modelo com TODO o histórico — versão usada para prever o futuro real."""
    model = _build_model(holidays_df)
    model.fit(daily_df[["ds", "y"]])
    return model


def forecast_future(model: Prophet, last_history_date: pd.Timestamp, periods: int = 30) -> pd.DataFrame:
    """Retorna apenas as linhas de previsão POSTERIORES ao histórico conhecido."""
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    forecast = forecast[forecast["ds"] > last_history_date]
    for col in ("yhat", "yhat_lower", "yhat_upper"):
        forecast[col] = forecast[col].clip(lower=0)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)
