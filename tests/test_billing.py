"""
Tests for Billing Service Calculations
======================================
Verifies mathematical accuracy, decimal precision, tier assignment,
and month-over-month consumption changes.
"""

import pytest
from app.services import BillingService


def test_basic_bill_calculation():
    """Verify formula: Energy Charge + Fixed Charges + Surcharges."""
    # 300 kWh * 7.00/unit = 2100.00 energy charge
    # Fixed charges = 50.00
    # Additional charge (5%) = 2100 * 0.05 = 105.00
    # Total = 2100 + 50 + 105 = 2255.00
    result = BillingService.calculate_bill(
        predicted_consumption_kwh=300.0,
        tariff_per_kwh=7.0,
        fixed_charges=50.0,
        additional_charge_percentage=5.0,
        previous_month_consumption_kwh=280.0,
    )

    assert result["energy_charge"] == 2100.00
    assert result["fixed_charges"] == 50.00
    assert result["additional_charges_amount"] == 105.00
    assert result["estimated_total_bill"] == 2255.00
    assert result["usage_category"] == "Moderate"


def test_zero_additional_charges():
    """Verify calculation when surcharges percentage is 0%."""
    result = BillingService.calculate_bill(
        predicted_consumption_kwh=200.0,
        tariff_per_kwh=6.5,
        fixed_charges=30.0,
        additional_charge_percentage=0.0,
        previous_month_consumption_kwh=200.0,
    )

    assert result["energy_charge"] == 1300.00
    assert result["additional_charges_amount"] == 0.00
    assert result["estimated_total_bill"] == 1330.00


def test_rounding_precision():
    """Ensure monetary calculations round to two decimal places without floating-point artifacts."""
    result = BillingService.calculate_bill(
        predicted_consumption_kwh=333.33,
        tariff_per_kwh=7.77,
        fixed_charges=45.55,
        additional_charge_percentage=5.5,
        previous_month_consumption_kwh=300.0,
    )

    # 333.33 * 7.77 = 2589.9741 -> 2589.97
    # 2589.97 * 0.055 = 142.44835 -> 142.45
    # Total = 2589.97 + 45.55 + 142.45 = 2777.97
    assert result["energy_charge"] == 2589.97
    assert result["additional_charges_amount"] == 142.45
    assert result["estimated_total_bill"] == 2777.97


def test_usage_category_thresholds():
    """Verify tier assignment: Low (<150), Moderate (150-400), High (>400)."""
    low_res = BillingService.calculate_bill(120.0, 6.0, 20.0, 0.0)
    assert low_res["usage_category"] == "Low"

    mod_res_boundary = BillingService.calculate_bill(150.0, 6.0, 20.0, 0.0)
    assert mod_res_boundary["usage_category"] == "Moderate"

    mod_res = BillingService.calculate_bill(350.0, 6.0, 20.0, 0.0)
    assert mod_res["usage_category"] == "Moderate"

    high_res_boundary = BillingService.calculate_bill(400.1, 6.0, 20.0, 0.0)
    assert high_res_boundary["usage_category"] == "High"

    high_res = BillingService.calculate_bill(650.0, 6.0, 20.0, 0.0)
    assert high_res["usage_category"] == "High"



def test_month_over_month_percentage():
    """Verify month-over-month percentage change calculation."""
    # 330 vs 300 = +10.0%
    increase_res = BillingService.calculate_bill(
        predicted_consumption_kwh=330.0,
        tariff_per_kwh=7.0,
        fixed_charges=50.0,
        additional_charge_percentage=5.0,
        previous_month_consumption_kwh=300.0,
    )
    assert increase_res["month_change_percentage"] == 10.0

    # 240 vs 300 = -20.0%
    decrease_res = BillingService.calculate_bill(
        predicted_consumption_kwh=240.0,
        tariff_per_kwh=7.0,
        fixed_charges=50.0,
        additional_charge_percentage=5.0,
        previous_month_consumption_kwh=300.0,
    )
    assert decrease_res["month_change_percentage"] == -20.0
