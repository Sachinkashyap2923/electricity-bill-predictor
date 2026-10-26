"""
Tests for Prediction Engine & Input Validation
==============================================
Verifies validation rules (negative values, missing fields, NaNs, infinity)
and model inference correctness.
"""

import math
import pytest
from app.services import PredictionService, InputValidationError
from app.ml.predict import predict_consumption, load_ml_artifacts


def test_valid_input_validation():
    """Ensure standard positive inputs validate cleanly."""
    valid = PredictionService.validate_inputs(
        daily_kwh="12.5",
        prev_month_kwh="350.0",
        billing_days="30",
        tariff_per_kwh="7.5",
        fixed_charges="50.0",
        additional_charge_percentage="5.0",
    )
    assert valid["average_daily_consumption_kwh"] == 12.5
    assert valid["previous_month_consumption_kwh"] == 350.0
    assert valid["billing_days"] == 30
    assert valid["tariff_per_kwh"] == 7.5
    assert valid["fixed_charges"] == 50.0
    assert valid["additional_charge_percentage"] == 5.0


def test_negative_consumption_rejected():
    """Negative consumption values must be strictly rejected."""
    with pytest.raises(InputValidationError, match="greater than 0.01"):
        PredictionService.validate_inputs(
            daily_kwh="-5.0",
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_zero_daily_consumption_rejected():
    """Zero daily consumption must be rejected because power must be consumed."""
    with pytest.raises(InputValidationError, match="greater than 0.01"):
        PredictionService.validate_inputs(
            daily_kwh="0.0",
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_invalid_billing_period_rejected():
    """Billing period must be positive and within 1-365 days."""
    with pytest.raises(InputValidationError):
        PredictionService.validate_inputs(
            daily_kwh="10.0",
            prev_month_kwh="300.0",
            billing_days="0",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )

    with pytest.raises(InputValidationError):
        PredictionService.validate_inputs(
            daily_kwh="10.0",
            prev_month_kwh="300.0",
            billing_days="400",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_negative_tariff_rejected():
    """Negative tariff must be rejected."""
    with pytest.raises(InputValidationError, match="cannot be negative"):
        PredictionService.validate_inputs(
            daily_kwh="10.0",
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="-2.5",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_missing_input_handled():
    """Empty or missing fields must raise validation errors."""
    with pytest.raises(InputValidationError, match="required"):
        PredictionService.validate_inputs(
            daily_kwh="",
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_nan_and_infinite_values_rejected():
    """NaN and Inf must be rejected."""
    with pytest.raises(InputValidationError, match="cannot be NaN or infinite"):
        PredictionService.validate_inputs(
            daily_kwh=float("nan"),
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )

    with pytest.raises(InputValidationError, match="cannot be NaN or infinite"):
        PredictionService.validate_inputs(
            daily_kwh=float("inf"),
            prev_month_kwh="300.0",
            billing_days="30",
            tariff_per_kwh="7.0",
            fixed_charges="50.0",
            additional_charge_percentage="5.0",
        )


def test_ml_model_artifacts_loading():
    """Verify that models, scalers, and metrics load into memory cleanly."""
    artifacts = load_ml_artifacts()
    assert artifacts["loaded"] is True
    assert "linear_regression" in artifacts
    assert "random_forest" in artifacts
    assert "scaler" in artifacts
    assert "metrics" in artifacts


def test_model_prediction_inference():
    """Verify prediction outputs for linear regression, random forest, and auto."""
    # Test Linear Regression
    lr_res = predict_consumption(10.0, 300.0, 30, model_choice="linear_regression")
    assert lr_res["predicted_consumption_kwh"] > 0
    assert lr_res["model_name"] == "Linear Regression"

    # Test Random Forest
    rf_res = predict_consumption(10.0, 300.0, 30, model_choice="random_forest")
    assert rf_res["predicted_consumption_kwh"] > 0
    assert rf_res["model_name"] == "Random Forest Regressor"

    # Test Auto Model
    auto_res = predict_consumption(10.0, 300.0, 30, model_choice="auto")
    assert auto_res["predicted_consumption_kwh"] > 0
    assert auto_res["model_name"] in ["Linear Regression", "Random Forest Regressor"]


def test_out_of_range_boundary_detection():
    """Extrapolated inputs outside training ranges must trigger warning flags."""
    # Daily usage 65.0 kWh is way above maximum training value (~35 kWh)
    res = predict_consumption(65.0, 300.0, 30, model_choice="auto")
    assert res["is_out_of_range"] is True
    assert len(res["warnings"]) > 0
    assert "outside the training data range" in res["warnings"][0]
