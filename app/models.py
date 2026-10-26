"""
Database Models
===============
Defines the SQLAlchemy database models for electricity bill predictions.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ElectricityPrediction(db.Model):
    """
    Stores individual electricity bill predictions and user inputs.
    """
    __tablename__ = "electricity_predictions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # User input features
    average_daily_consumption_kwh = db.Column(db.Float, nullable=False)
    previous_month_consumption_kwh = db.Column(db.Float, nullable=False)
    billing_days = db.Column(db.Integer, nullable=False)

    # Tariff and charge settings
    tariff_per_kwh = db.Column(db.Float, nullable=False)
    fixed_charges = db.Column(db.Float, nullable=False)
    additional_charge_percentage = db.Column(db.Float, nullable=False)

    # Prediction outputs
    predicted_monthly_consumption_kwh = db.Column(db.Float, nullable=False)
    estimated_total_bill = db.Column(db.Float, nullable=False)
    model_name = db.Column(db.String(100), nullable=False)

    @property
    def energy_charge(self) -> float:
        """Energy Charge = Predicted Consumption * Tariff per kWh"""
        return round(self.predicted_monthly_consumption_kwh * self.tariff_per_kwh, 2)

    @property
    def additional_charges_amount(self) -> float:
        """Additional Charges = Energy Charge * Additional Charge Percentage / 100"""
        return round(self.energy_charge * (self.additional_charge_percentage / 100.0), 2)

    @property
    def usage_category(self) -> str:
        """
        Usage classification based on standard residential thresholds:
        - Low: < 150 kWh
        - Moderate: 150 to 400 kWh
        - High: > 400 kWh
        """
        val = self.predicted_monthly_consumption_kwh
        if val < 150.0:
            return "Low"
        elif val <= 400.0:
            return "Moderate"
        else:
            return "High"

    @property
    def month_change_percentage(self) -> float:
        """Percentage change compared to previous month."""
        if self.previous_month_consumption_kwh and self.previous_month_consumption_kwh > 0:
            diff = self.predicted_monthly_consumption_kwh - self.previous_month_consumption_kwh
            return round((diff / self.previous_month_consumption_kwh) * 100.0, 1)
        return 0.0

    def to_dict(self) -> dict:
        """Serialize prediction record to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "average_daily_consumption_kwh": self.average_daily_consumption_kwh,
            "previous_month_consumption_kwh": self.previous_month_consumption_kwh,
            "billing_days": self.billing_days,
            "tariff_per_kwh": self.tariff_per_kwh,
            "fixed_charges": self.fixed_charges,
            "additional_charge_percentage": self.additional_charge_percentage,
            "predicted_monthly_consumption_kwh": self.predicted_monthly_consumption_kwh,
            "energy_charge": self.energy_charge,
            "additional_charges_amount": self.additional_charges_amount,
            "estimated_total_bill": self.estimated_total_bill,
            "model_name": self.model_name,
            "usage_category": self.usage_category,
            "month_change_percentage": self.month_change_percentage,
        }

    def __repr__(self):
        return f"<ElectricityPrediction id={self.id} bill={self.estimated_total_bill} model='{self.model_name}'>"
