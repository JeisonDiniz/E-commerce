"""
Random Forest — predição de demanda por variante (categoria, tamanho, cor e
preço como features), conforme especificado no TCC. Usa Pipeline do
scikit-learn para que o mesmo objeto encapsule pré-processamento (one-hot
das categóricas) e o modelo — evitando "treinar de um jeito, servir de outro".
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

MODEL_VERSION = "random-forest-v1"

CATEGORICAL_FEATURES = ["category_id", "gender", "season", "size", "color"]
NUMERIC_FEATURES = ["price", "month_sin", "month_cos", "historical_avg_monthly_units"]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMN = "units_sold"


def _mae_mape(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    mask = y_true > 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else float("nan")
    return mae, mape


def build_pipeline(n_estimators: int = 300, max_depth: int | None = 12, random_state: int = 42) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    regressor = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", regressor)])


def train_and_evaluate(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[Pipeline, dict]:
    pipeline = build_pipeline()
    pipeline.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    predictions = np.clip(pipeline.predict(test_df[FEATURE_COLUMNS]), 0, None)
    mae, mape = _mae_mape(test_df[TARGET_COLUMN].to_numpy(), predictions)
    rmse = float(np.sqrt(np.mean((test_df[TARGET_COLUMN].to_numpy() - predictions) ** 2)))

    metrics = {"mae": mae, "mape": mape, "rmse": rmse, "n_test": len(test_df)}
    return pipeline, metrics


def fit_full(full_df: pd.DataFrame) -> Pipeline:
    pipeline = build_pipeline()
    pipeline.fit(full_df[FEATURE_COLUMNS], full_df[TARGET_COLUMN])
    return pipeline


def predict(pipeline: Pipeline, rows_df: pd.DataFrame) -> np.ndarray:
    return np.clip(pipeline.predict(rows_df[FEATURE_COLUMNS]), 0, None)
