"""
Business Logic & Service Layer
==============================
Handles bill calculation, prediction workflow, input validation,
history queries, and dashboard metric calculations.
"""

import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func

from app.models import db, ElectricityPrediction
from app.ml.predict import predict_consumption, load_ml_artifacts
from app.ml.evaluate import get_evaluation_metrics


class InputValidationError(Exception):
    """Custom exception raised when user input fails validation."""
    pass


class BillingService:
    """Encapsulates electricity bill calculation using configurable tariffs."""

    @staticmethod
    def calculate_bill(
        predicted_consumption_kwh: float,
        tariff_per_kwh: float,
        fixed_charges: float,
        additional_charge_percentage: float,
        previous_month_consumption_kwh: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculates the estimated electricity bill breakdown.

        Formula:
        Energy Charge = Predicted Monthly Consumption * Tariff per kWh
        Additional Charges = Energy Charge * Additional Charge Percentage / 100
        Estimated Total Bill = Energy Charge + Fixed Charges + Additional Charges
        """
        pred_dec = Decimal(str(round(predicted_consumption_kwh, 4)))
        tariff_dec = Decimal(str(round(tariff_per_kwh, 4)))
        fixed_dec = Decimal(str(round(fixed_charges, 4)))
        pct_dec = Decimal(str(round(additional_charge_percentage, 4)))

        # Precise calculations rounded to 2 decimal places
        energy_charge = (pred_dec * tariff_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        additional_charges = (energy_charge * (pct_dec / Decimal("100.0"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_bill = (energy_charge + fixed_dec + additional_charges).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Classification into usage tier
        if predicted_consumption_kwh < 150.0:
            usage_category = "Low"
            category_color = "success"
            category_desc = "Within energy-efficient domestic consumption range (< 150 kWh)."
        elif predicted_consumption_kwh <= 400.0:
            usage_category = "Moderate"
            category_color = "info"
            category_desc = "Typical residential household with standard appliance loads (150 - 400 kWh)."
        else:
            usage_category = "High"
            category_color = "warning"
            category_desc = "High consumption tier; likely includes multiple air-conditioners, water heaters, or commercial loads (> 400 kWh)."

        # Month-over-month comparison
        if previous_month_consumption_kwh > 0:
            diff = predicted_consumption_kwh - previous_month_consumption_kwh
            pct_change = round((diff / previous_month_consumption_kwh) * 100.0, 1)
        else:
            pct_change = 0.0

        return {
            "predicted_monthly_consumption_kwh": float(pred_dec),
            "tariff_per_kwh": float(tariff_dec),
            "fixed_charges": float(fixed_dec),
            "additional_charge_percentage": float(pct_dec),
            "energy_charge": float(energy_charge),
            "additional_charges_amount": float(additional_charges),
            "estimated_total_bill": float(total_bill),
            "usage_category": usage_category,
            "category_color": category_color,
            "category_desc": category_desc,
            "month_change_percentage": pct_change,
        }


class PredictionService:
    """Orchestrates ML prediction, bill estimation, and SQLite database persistence."""

    @staticmethod
    def validate_inputs(
        daily_kwh: Any,
        prev_month_kwh: Any,
        billing_days: Any,
        tariff_per_kwh: Any,
        fixed_charges: Any,
        additional_charge_percentage: Any,
    ) -> Dict[str, float]:
        """
        Validates raw form inputs. Rejects negative values, missing fields, NaNs, and infinity.
        """
        errors = []

        def parse_float(val, name, min_val=0.0, max_val=None, allow_zero=True):
            if val is None or str(val).strip() == "":
                errors.append(f"'{name}' is required and cannot be empty.")
                return None
            try:
                num = float(val)
            except (ValueError, TypeError):
                errors.append(f"'{name}' must be a valid numeric value.")
                return None

            if math.isnan(num) or math.isinf(num):
                errors.append(f"'{name}' cannot be NaN or infinite.")
                return None

            if not allow_zero and num <= min_val:
                errors.append(f"'{name}' must be greater than {min_val}.")
                return None

            if allow_zero and num < min_val:
                errors.append(f"'{name}' cannot be negative (minimum: {min_val}).")
                return None

            if max_val is not None and num > max_val:
                errors.append(f"'{name}' exceeds allowable maximum limit of {max_val}.")
                return None

            return num

        parsed_daily = parse_float(daily_kwh, "Average Daily Consumption", min_val=0.01, max_val=200.0, allow_zero=False)
        parsed_prev = parse_float(prev_month_kwh, "Previous Month Consumption", min_val=0.0, max_val=5000.0, allow_zero=True)
        parsed_days = parse_float(billing_days, "Billing Period (Days)", min_val=1.0, max_val=365.0, allow_zero=False)
        parsed_tariff = parse_float(tariff_per_kwh, "Tariff Rate per kWh", min_val=0.0, max_val=100.0, allow_zero=True)
        parsed_fixed = parse_float(fixed_charges, "Fixed Monthly Charges", min_val=0.0, max_val=10000.0, allow_zero=True)
        parsed_pct = parse_float(additional_charge_percentage, "Additional Charge %", min_val=0.0, max_val=100.0, allow_zero=True)

        if errors:
            raise InputValidationError(" | ".join(errors))

        # Billing days should be a positive integer
        days_int = int(round(parsed_days))
        if days_int < 1 or days_int > 365:
            raise InputValidationError("Billing period must be between 1 and 365 days.")

        return {
            "average_daily_consumption_kwh": parsed_daily,
            "previous_month_consumption_kwh": parsed_prev,
            "billing_days": days_int,
            "tariff_per_kwh": parsed_tariff,
            "fixed_charges": parsed_fixed,
            "additional_charge_percentage": parsed_pct,
        }

    @staticmethod
    def create_prediction(
        inputs: Dict[str, Any],
        model_choice: str = "auto",
        persist: bool = True,
    ) -> Tuple[ElectricityPrediction, Dict[str, Any]]:
        """
        Runs ML prediction, computes billing breakdown, and saves record to database.
        """
        # Run ML model inference
        ml_result = predict_consumption(
            daily_kwh=inputs["average_daily_consumption_kwh"],
            prev_month_kwh=inputs["previous_month_consumption_kwh"],
            billing_days=inputs["billing_days"],
            model_choice=model_choice,
        )

        pred_kwh = ml_result["predicted_consumption_kwh"]
        model_name = ml_result["model_name"]

        # Calculate bill
        bill_data = BillingService.calculate_bill(
            predicted_consumption_kwh=pred_kwh,
            tariff_per_kwh=inputs["tariff_per_kwh"],
            fixed_charges=inputs["fixed_charges"],
            additional_charge_percentage=inputs["additional_charge_percentage"],
            previous_month_consumption_kwh=inputs["previous_month_consumption_kwh"],
        )

        # Create database record
        record = ElectricityPrediction(
            average_daily_consumption_kwh=inputs["average_daily_consumption_kwh"],
            previous_month_consumption_kwh=inputs["previous_month_consumption_kwh"],
            billing_days=inputs["billing_days"],
            tariff_per_kwh=inputs["tariff_per_kwh"],
            fixed_charges=inputs["fixed_charges"],
            additional_charge_percentage=inputs["additional_charge_percentage"],
            predicted_monthly_consumption_kwh=pred_kwh,
            estimated_total_bill=bill_data["estimated_total_bill"],
            model_name=model_name,
        )

        if persist:
            db.session.add(record)
            db.session.commit()

        metadata = {
            **bill_data,
            "model_name": model_name,
            "model_key": ml_result["model_key"],
            "is_out_of_range": ml_result["is_out_of_range"],
            "warnings": ml_result["warnings"],
            "model_metrics": ml_result["model_metrics"],
        }

        return record, metadata


class DashboardService:
    """Computes real-time statistics and Chart.js datasets from database records."""

    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """
        Queries database records to compute summary KPI cards and chart series.
        Handles empty database state gracefully.
        """
        total_predictions = db.session.query(func.count(ElectricityPrediction.id)).scalar() or 0

        if total_predictions == 0:
            return {
                "total_predictions": 0,
                "average_estimated_bill": 0.0,
                "latest_predicted_bill": 0.0,
                "average_predicted_consumption": 0.0,
                "recent_predictions": [],
                "chart_labels": [],
                "chart_bills": [],
                "chart_consumptions": [],
                "category_counts": {"Low": 0, "Moderate": 0, "High": 0},
                "model_usage": {},
                "is_empty": True,
            }

        avg_bill = db.session.query(func.avg(ElectricityPrediction.estimated_total_bill)).scalar() or 0.0
        avg_kwh = db.session.query(func.avg(ElectricityPrediction.predicted_monthly_consumption_kwh)).scalar() or 0.0
        latest_record = (
            db.session.query(ElectricityPrediction)
            .order_by(ElectricityPrediction.created_at.desc(), ElectricityPrediction.id.desc())
            .first()
        )
        latest_bill = latest_record.estimated_total_bill if latest_record else 0.0

        # Recent 10 predictions for chart timeline
        recent_records = (
            db.session.query(ElectricityPrediction)
            .order_by(ElectricityPrediction.created_at.desc(), ElectricityPrediction.id.desc())
            .limit(10)
            .all()
        )
        # Reverse to chronological order for charts
        chronological_records = list(reversed(recent_records))

        chart_labels = [
            f"#{r.id} ({r.created_at.strftime('%d %b') if r.created_at else ''})"
            for r in chronological_records
        ]
        chart_bills = [round(r.estimated_total_bill, 2) for r in chronological_records]
        chart_consumptions = [round(r.predicted_monthly_consumption_kwh, 2) for r in chronological_records]

        # Category distribution across all records
        all_records = db.session.query(ElectricityPrediction).all()
        category_counts = {"Low": 0, "Moderate": 0, "High": 0}
        model_usage: Dict[str, int] = {}

        for r in all_records:
            cat = r.usage_category
            category_counts[cat] = category_counts.get(cat, 0) + 1
            model_usage[r.model_name] = model_usage.get(r.model_name, 0) + 1

        return {
            "total_predictions": total_predictions,
            "average_estimated_bill": round(float(avg_bill), 2),
            "latest_predicted_bill": round(float(latest_bill), 2),
            "average_predicted_consumption": round(float(avg_kwh), 2),
            "recent_predictions": recent_records[:5],
            "chart_labels": chart_labels,
            "chart_bills": chart_bills,
            "chart_consumptions": chart_consumptions,
            "category_counts": category_counts,
            "model_usage": model_usage,
            "is_empty": False,
        }
