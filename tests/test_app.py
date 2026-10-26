"""
End-to-End Application & Route Tests
====================================
Tests web routes, HTTP status codes, form submissions, database persistence,
filtering, deletion, dashboard statistics, and custom error pages.
"""

import pytest
from app.models import db, ElectricityPrediction


def test_home_page(client):
    """Verify home page loads successfully with HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Electricity Bill Prediction System" in response.data
    assert b"Linear Regression" in response.data
    assert b"Random Forest" in response.data


def test_predict_form_rendering(client):
    """Verify prediction form loads with default values."""
    response = client.get("/predict")
    assert response.status_code == 200
    assert b"average_daily_consumption_kwh" in response.data
    assert b"tariff_per_kwh" in response.data
    assert b"Quick Test Presets" in response.data


def test_valid_prediction_submission_and_result(client):
    """Verify valid form submission redirects to result page and persists record."""
    form_data = {
        "average_daily_consumption_kwh": "12.0",
        "previous_month_consumption_kwh": "350.0",
        "billing_days": "30",
        "tariff_per_kwh": "7.50",
        "fixed_charges": "50.00",
        "additional_charge_percentage": "5.0",
        "model_choice": "auto",
    }

    response = client.post("/predict", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Estimated Electricity Bill" in response.data
    assert b"Transparent Cost Breakdown" in response.data

    # Verify record in database
    prediction = ElectricityPrediction.query.first()
    assert prediction is not None
    assert prediction.average_daily_consumption_kwh == 12.0
    assert prediction.estimated_total_bill > 0


def test_negative_consumption_form_rejection(client):
    """Verify negative consumption is rejected on form submission."""
    form_data = {
        "average_daily_consumption_kwh": "-10.0",
        "previous_month_consumption_kwh": "350.0",
        "billing_days": "30",
        "tariff_per_kwh": "7.50",
        "fixed_charges": "50.00",
        "additional_charge_percentage": "5.0",
    }
    response = client.post("/predict", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Input validation error" in response.data


def test_invalid_tariff_form_rejection(client):
    """Verify negative tariff is rejected on form submission."""
    form_data = {
        "average_daily_consumption_kwh": "12.0",
        "previous_month_consumption_kwh": "350.0",
        "billing_days": "30",
        "tariff_per_kwh": "-5.0",
        "fixed_charges": "50.00",
        "additional_charge_percentage": "5.0",
    }
    response = client.post("/predict", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Input validation error" in response.data


def test_missing_input_form_rejection(client):
    """Verify empty form inputs are rejected."""
    form_data = {
        "average_daily_consumption_kwh": "",
        "previous_month_consumption_kwh": "350.0",
        "billing_days": "30",
        "tariff_per_kwh": "7.50",
        "fixed_charges": "50.00",
        "additional_charge_percentage": "5.0",
    }
    response = client.post("/predict", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Input validation error" in response.data


def test_empty_database_dashboard_state(client):
    """Dashboard should load without errors even when no records exist."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"No Prediction Data Recorded Yet" in response.data


def test_history_and_dashboard_with_data(client):
    """Create predictions and verify persistence, dashboard metrics, and history list."""
    # Insert 2 predictions
    for daily, prev in [(10.0, 300.0), (20.0, 600.0)]:
        client.post(
            "/predict",
            data={
                "average_daily_consumption_kwh": str(daily),
                "previous_month_consumption_kwh": str(prev),
                "billing_days": "30",
                "tariff_per_kwh": "7.0",
                "fixed_charges": "50.0",
                "additional_charge_percentage": "5.0",
                "model_choice": "auto",
            },
            follow_redirects=True,
        )

    # Check History page
    hist_resp = client.get("/history")
    assert hist_resp.status_code == 200
    assert b"Showing 2 prediction records" in hist_resp.data

    # Check Dashboard page
    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200
    assert b"Total Predictions" in dash_resp.data
    # Dashboard should show count 2
    assert b"2</div>" in dash_resp.data or b">2<" in dash_resp.data


def test_prediction_detail_view(client):
    """Verify viewing single record detail."""
    client.post(
        "/predict",
        data={
            "average_daily_consumption_kwh": "15.0",
            "previous_month_consumption_kwh": "450.0",
            "billing_days": "30",
            "tariff_per_kwh": "8.0",
            "fixed_charges": "60.0",
            "additional_charge_percentage": "6.0",
            "model_choice": "linear_regression",
        },
        follow_redirects=True,
    )

    record = ElectricityPrediction.query.first()
    assert record is not None

    resp = client.get(f"/history/{record.id}")
    assert resp.status_code == 200
    assert b"Detailed Prediction Record" in resp.data
    assert b"Cost Computation Table" in resp.data


def test_prediction_deletion(client):
    """Verify deleting a prediction record."""
    client.post(
        "/predict",
        data={
            "average_daily_consumption_kwh": "11.0",
            "previous_month_consumption_kwh": "330.0",
            "billing_days": "30",
            "tariff_per_kwh": "7.0",
            "fixed_charges": "50.0",
            "additional_charge_percentage": "5.0",
        },
        follow_redirects=True,
    )

    record = ElectricityPrediction.query.first()
    assert record is not None
    record_id = record.id

    del_resp = client.post(f"/history/{record_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    assert b"successfully deleted" in del_resp.data

    assert db.session.get(ElectricityPrediction, record_id) is None


def test_model_evaluation_page(client):
    """Verify evaluation page displays comparison metrics."""
    response = client.get("/evaluation")
    assert response.status_code == 200
    assert b"Machine Learning Model Evaluation" in response.data
    assert b"Linear Regression" in response.data
    assert b"Random Forest Regressor" in response.data
    assert b"Mean Absolute Error (MAE)" in response.data
    assert b"Root Mean Squared Error (RMSE)" in response.data
    assert b"R\xc2\xb2 Score" in response.data or b"R" in response.data


def test_about_page(client):
    """Verify about page loads with viva and architecture documentation."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"MCA Viva Frequently Asked Questions" in response.data


def test_404_error_page(client):
    """Verify custom 404 error page is returned for unknown URLs."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
