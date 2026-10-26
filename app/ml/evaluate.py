"""
Model Evaluation and Metric Explanations
=========================================
Loads saved test metrics and formats educational explanations for viva and reporting.
"""

import os
import json
from typing import Dict, Any


def get_evaluation_metrics(metrics_path: str = "trained_models/metrics.json") -> Dict[str, Any]:
    """
    Reads model evaluation metrics calculated strictly on the held-out test set.
    """
    if not os.path.exists(metrics_path):
        return {
            "available": False,
            "error": "Metrics file not found. Please train models using: python -m app.ml.train_models",
        }

    try:
        with open(metrics_path, "r") as f:
            data = json.load(f)
            data["available"] = True
            return data
    except Exception as e:
        return {
            "available": False,
            "error": f"Error loading evaluation metrics: {str(e)}",
        }


def get_metric_definitions() -> Dict[str, Dict[str, str]]:
    """
    Returns educational descriptions of each evaluation metric for MCA viva defense.
    """
    return {
        "MAE": {
            "title": "Mean Absolute Error (MAE)",
            "unit": "kWh",
            "formula": "MAE = (1/n) * Σ |y_actual - y_predicted|",
            "explanation": (
                "Measures the average magnitude of prediction errors in the original units (kWh). "
                "Because errors are not squared, MAE treats all deviations equally and is robust to outliers."
            ),
            "ideal": "Lower is better (0 represents a perfect fit).",
        },
        "RMSE": {
            "title": "Root Mean Squared Error (RMSE)",
            "unit": "kWh",
            "formula": "RMSE = √[(1/n) * Σ (y_actual - y_predicted)²]",
            "explanation": (
                "Square root of the average squared errors. Because errors are squared before averaging, "
                "RMSE penalizes larger prediction mistakes more severely than MAE, making it critical for utility budgeting."
            ),
            "ideal": "Lower is better.",
        },
        "R2": {
            "title": "Coefficient of Determination (R² Score)",
            "unit": "Dimensionless (scale: -∞ to 1.0)",
            "formula": "R² = 1 - (SS_res / SS_tot)",
            "explanation": (
                "Represents the proportion of variance in monthly electricity consumption that is explained "
                "by the model's independent input features. An R² of 1.0 indicates perfect fit, while 0.0 means the model "
                "performs no better than predicting the simple mean."
            ),
            "ideal": "Higher is better (closest to 1.0).",
        },
    }
