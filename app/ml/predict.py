"""
Prediction Engine
=================
Loads pre-trained models from disk (cached in memory) and generates consumption predictions.
Includes input boundary checks against training data distributions.
"""

import os
import json
from typing import Dict, Any, Tuple
import joblib
import numpy as np

# Cache loaded artifacts in memory so we do not read from disk on every HTTP request
_MODEL_CACHE: Dict[str, Any] = {}


def load_ml_artifacts(models_dir: str = "trained_models") -> Dict[str, Any]:
    """
    Loads trained models, scaler, and evaluation metrics.
    Caches artifacts in memory.
    """
    global _MODEL_CACHE
    if "loaded" in _MODEL_CACHE and _MODEL_CACHE["loaded"]:
        return _MODEL_CACHE

    metrics_path = os.path.join(models_dir, "metrics.json")
    scaler_path = os.path.join(models_dir, "scaler.joblib")
    lr_path = os.path.join(models_dir, "linear_regression.joblib")
    rf_path = os.path.join(models_dir, "random_forest.joblib")

    if not all(os.path.exists(p) for p in [metrics_path, scaler_path, lr_path, rf_path]):
        raise FileNotFoundError(
            "Model artifacts not found. Please train models first using: python -m app.ml.train_models"
        )

    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    scaler = joblib.load(scaler_path)
    lr_model = joblib.load(lr_path)
    rf_model = joblib.load(rf_path)

    _MODEL_CACHE = {
        "loaded": True,
        "metrics": metrics,
        "scaler": scaler,
        "linear_regression": lr_model,
        "random_forest": rf_model,
        "selected_model_key": metrics.get("comparison", {}).get("selected_model_key", "random_forest"),
        "feature_ranges": metrics.get("dataset", {}).get("feature_ranges", {}),
    }

    return _MODEL_CACHE


def check_feature_boundaries(
    daily_kwh: float, prev_month_kwh: float, billing_days: int, feature_ranges: Dict[str, Any]
) -> Tuple[bool, list]:
    """
    Validates if user inputs are within the training data distribution.
    Returns (is_out_of_range, warning_messages).
    """
    warnings = []

    if feature_ranges:
        daily_range = feature_ranges.get("average_daily_consumption_kwh", {})
        if daily_range and (daily_kwh < daily_range.get("min", 0) or daily_kwh > daily_range.get("max", 100)):
            warnings.append(
                f"Average daily consumption ({daily_kwh:.2f} kWh) is outside the training data range "
                f"({daily_range.get('min'):.2f} - {daily_range.get('max'):.2f} kWh). Prediction may have higher uncertainty."
            )

        prev_range = feature_ranges.get("previous_month_consumption_kwh", {})
        if prev_range and (prev_month_kwh < prev_range.get("min", 0) or prev_month_kwh > prev_range.get("max", 2000)):
            warnings.append(
                f"Previous month consumption ({prev_month_kwh:.2f} kWh) is outside the training range "
                f"({prev_range.get('min'):.2f} - {prev_range.get('max'):.2f} kWh)."
            )

        days_range = feature_ranges.get("billing_days", {})
        if days_range and (billing_days < days_range.get("min", 25) or billing_days > days_range.get("max", 40)):
            warnings.append(
                f"Billing period ({billing_days} days) deviates from typical billing cycles "
                f"({int(days_range.get('min', 28))} - {int(days_range.get('max', 35))} days)."
            )

    return (len(warnings) > 0, warnings)


def predict_consumption(
    daily_kwh: float,
    prev_month_kwh: float,
    billing_days: int,
    model_choice: str = "auto",
    models_dir: str = "trained_models",
) -> Dict[str, Any]:
    """
    Predicts monthly electricity consumption in kWh.

    Parameters:
    - daily_kwh: Average daily electricity consumption in kWh
    - prev_month_kwh: Previous month electricity consumption in kWh
    - billing_days: Current billing period in days
    - model_choice: 'auto', 'linear_regression', or 'random_forest'
    - models_dir: Directory where trained artifacts are stored

    Returns dictionary containing predicted consumption, model metadata, and boundary warnings.
    """
    artifacts = load_ml_artifacts(models_dir)
    scaler = artifacts["scaler"]
    feature_ranges = artifacts["feature_ranges"]

    # Resolve model selection
    if model_choice == "linear_regression":
        model = artifacts["linear_regression"]
        model_name = "Linear Regression"
        model_key = "linear_regression"
    elif model_choice == "random_forest":
        model = artifacts["random_forest"]
        model_name = "Random Forest Regressor"
        model_key = "random_forest"
    else:  # 'auto' or default
        model_key = artifacts["selected_model_key"]
        model = artifacts[model_key]
        model_name = artifacts["metrics"]["models"][model_key]["name"]

    # Input validation checks
    is_out_of_range, warnings = check_feature_boundaries(
        daily_kwh, prev_month_kwh, billing_days, feature_ranges
    )

    # Prepare features and scale using exact column names
    import pandas as pd
    feature_cols = [
        "average_daily_consumption_kwh",
        "previous_month_consumption_kwh",
        "billing_days",
    ]
    input_df = pd.DataFrame(
        [[float(daily_kwh), float(prev_month_kwh), float(billing_days)]],
        columns=feature_cols,
    )
    scaled_features = scaler.transform(input_df)

    # Predict
    predicted_val = float(model.predict(scaled_features)[0])

    # Ensure non-negative prediction
    predicted_kwh = max(1.0, round(predicted_val, 2))

    return {
        "predicted_consumption_kwh": predicted_kwh,
        "model_name": model_name,
        "model_key": model_key,
        "is_out_of_range": is_out_of_range,
        "warnings": warnings,
        "model_metrics": artifacts["metrics"]["models"].get(model_key, {}),
    }
