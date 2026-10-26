"""
Machine Learning Model Training Pipeline
=========================================
Trains Linear Regression and Random Forest Regressor models on electricity consumption dataset.
Evaluates both models fairly on a held-out test set, saves the model artifacts using joblib,
and stores evaluation metrics in trained_models/metrics.json.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


FEATURE_COLUMNS = [
    "average_daily_consumption_kwh",
    "previous_month_consumption_kwh",
    "billing_days",
]
TARGET_COLUMN = "monthly_consumption_kwh"


def calculate_rmse(y_true, y_pred):
    """Calculate Root Mean Squared Error safely across scikit-learn versions."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def validate_dataset(df: pd.DataFrame):
    """
    Validates dataset integrity:
    - Presence of required columns
    - Absence of nulls, NaNs, and infinite values
    - Plausible positive numeric ranges
    """
    required_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Dataset missing required column: '{col}'")

    if df[required_cols].isnull().any().any():
        raise ValueError("Dataset contains null or NaN values.")

    # Check for infinite numbers
    if np.isinf(df[required_cols].values).any():
        raise ValueError("Dataset contains infinite numbers.")

    # Check for negative values
    if (df[required_cols] < 0).any().any():
        raise ValueError("Dataset contains unexpected negative consumption or billing values.")


def train_and_evaluate_models(
    dataset_path: str = "datasets/electricity_consumption.csv",
    output_dir: str = "trained_models",
    test_size: float = 0.20,
    random_seed: int = 42,
):
    """
    Full training and evaluation pipeline:
    1. Loads and validates dataset
    2. Splits data into train and test sets (80/20)
    3. Fits StandardScaler strictly on training set (no target leakage)
    4. Trains Linear Regression and Random Forest Regressor
    5. Calculates MAE, RMSE, and R2 on test set
    6. Selects superior model based on test evaluation
    7. Saves models, scaler, and metrics.json
    """
    print(f"[INFO] Starting ML training pipeline using dataset: {dataset_path}")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset not found at '{dataset_path}'. Please run 'python scripts/generate_dataset.py' first."
        )

    df = pd.read_csv(dataset_path)
    validate_dataset(df)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Compute training distribution boundaries for out-of-range warnings
    feature_ranges = {}
    for col in FEATURE_COLUMNS:
        feature_ranges[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
        }

    # 80/20 train/test split with reproducible seed
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_seed
    )

    print(f"[INFO] Dataset split: {len(X_train)} training samples, {len(X_test)} test samples.")

    # Fit scaler strictly on training set to avoid data leakage
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Train Linear Regression
    print("[INFO] Training Model 1: Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)

    lr_mae = float(mean_absolute_error(y_test, lr_preds))
    lr_rmse = calculate_rmse(y_test, lr_preds)
    lr_r2 = float(r2_score(y_test, lr_preds))

    # 2. Train Random Forest Regressor
    print("[INFO] Training Model 2: Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=random_seed,
        n_jobs=-1,
    )
    # Random Forest can use unscaled or scaled; using scaled provides consistent feature pipeline
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)

    rf_mae = float(mean_absolute_error(y_test, rf_preds))
    rf_rmse = calculate_rmse(y_test, rf_preds)
    rf_r2 = float(r2_score(y_test, rf_preds))

    # Determine preferred model fairly based on test set RMSE (lower is better) and R2 (higher is better)
    if rf_rmse < lr_rmse and rf_r2 > lr_r2:
        best_model_name = "Random Forest Regressor"
        best_model_key = "random_forest"
        rationale = (
            f"Random Forest Regressor achieved higher explanatory power (R² = {rf_r2:.4f}) "
            f"and lower prediction error (RMSE = {rf_rmse:.2f} kWh vs {lr_rmse:.2f} kWh for Linear Regression) "
            "by capturing nonlinear appliance efficiency losses and threshold consumption effects."
        )
    elif lr_rmse < rf_rmse and lr_r2 > rf_r2:
        best_model_name = "Linear Regression"
        best_model_key = "linear_regression"
        rationale = (
            f"Linear Regression achieved superior generalization on the test set "
            f"(RMSE = {lr_rmse:.2f} kWh, R² = {lr_r2:.4f}) with lower variance and fewer parameters."
        )
    else:
        # Tie breaker / slight trade-off
        best_model_name = "Random Forest Regressor" if rf_r2 >= lr_r2 else "Linear Regression"
        best_model_key = "random_forest" if rf_r2 >= lr_r2 else "linear_regression"
        rationale = f"{best_model_name} selected based on overall balanced predictive accuracy."

    # Prepare a representative sample of 25 test points for Chart.js visualization
    chart_sample_indices = list(range(min(25, len(y_test))))
    test_actuals = [round(float(y_test.iloc[i]), 2) for i in chart_sample_indices]
    lr_sample_preds = [round(float(lr_preds[i]), 2) for i in chart_sample_indices]
    rf_sample_preds = [round(float(rf_preds[i]), 2) for i in chart_sample_indices]

    metrics_data = {
        "dataset": {
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "test_ratio": test_size,
            "feature_ranges": feature_ranges,
        },
        "models": {
            "linear_regression": {
                "name": "Linear Regression",
                "mae": round(lr_mae, 4),
                "rmse": round(lr_rmse, 4),
                "r2_score": round(lr_r2, 4),
                "coefficients": {
                    col: round(float(coef), 4)
                    for col, coef in zip(FEATURE_COLUMNS, lr_model.coef_)
                },
                "intercept": round(float(lr_model.intercept_), 4),
            },
            "random_forest": {
                "name": "Random Forest Regressor",
                "mae": round(rf_mae, 4),
                "rmse": round(rf_rmse, 4),
                "r2_score": round(rf_r2, 4),
                "n_estimators": 100,
                "max_depth": 12,
                "feature_importances": {
                    col: round(float(imp), 4)
                    for col, imp in zip(FEATURE_COLUMNS, rf_model.feature_importances_)
                },
            },
        },
        "comparison": {
            "selected_model": best_model_name,
            "selected_model_key": best_model_key,
            "rationale": rationale,
        },
        "sample_evaluations": {
            "indices": [f"Sample #{i+1}" for i in range(len(test_actuals))],
            "actual": test_actuals,
            "linear_regression": lr_sample_preds,
            "random_forest": rf_sample_preds,
        },
    }

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save models and scaler using joblib
    joblib.dump(scaler, os.path.join(output_dir, "scaler.joblib"))
    joblib.dump(lr_model, os.path.join(output_dir, "linear_regression.joblib"))
    joblib.dump(rf_model, os.path.join(output_dir, "random_forest.joblib"))

    # Save metrics JSON
    metrics_file = os.path.join(output_dir, "metrics.json")
    with open(metrics_file, "w") as f:
        json.dump(metrics_data, f, indent=4)

    print("\n" + "=" * 60)
    print("MODEL TRAINING & EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Linear Regression:       MAE = {lr_mae:.3f} kWh | RMSE = {lr_rmse:.3f} kWh | R² = {lr_r2:.4f}")
    print(f"Random Forest Regressor: MAE = {rf_mae:.3f} kWh | RMSE = {rf_rmse:.3f} kWh | R² = {rf_r2:.4f}")
    print(f"Selected Model:          {best_model_name}")
    print(f"Artifacts saved in:      {output_dir}")
    print("=" * 60 + "\n")

    return metrics_data


if __name__ == "__main__":
    train_and_evaluate_models()
