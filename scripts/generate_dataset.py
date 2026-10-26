"""
Synthetic Dataset Generator for Electricity Consumption Prediction
===================================================================
MCA Minor Project Demonstration Dataset

NOTE: This dataset is synthetically generated for academic and demonstration
purposes. It does NOT contain actual utility customer records. In a production
environment, this synthetic dataset should be replaced with verified smart-meter
or utility billing records (e.g., CSV export from a distribution company or open
energy data repositories like Pecan Street or Open Power System Data).
"""

import os
import numpy as np
import pandas as pd


def generate_electricity_dataset(
    output_path: str = "datasets/electricity_consumption.csv",
    num_samples: int = 1500,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates a realistic synthetic dataset for electricity consumption prediction.

    Features:
    - average_daily_consumption_kwh: Average daily usage in kilowatt-hours (e.g., 3.0 to 30.0 kWh)
    - previous_month_consumption_kwh: Previous month total usage in kWh
    - billing_days: Number of days in the billing cycle (e.g., 28 to 33 days)
    
    Target:
    - monthly_consumption_kwh: Estimated monthly consumption in kWh
    """
    np.random.seed(random_seed)

    # 1. Billing cycle days (mostly 29-32 days, typical for residential/commercial utility cycles)
    billing_days = np.random.choice([28, 29, 30, 31, 32, 33], size=num_samples, p=[0.05, 0.15, 0.50, 0.20, 0.07, 0.03])

    # 2. Average daily consumption in kWh (residential to light commercial: 3 kWh/day to 30 kWh/day)
    # Using a mixture of normal and gamma to simulate small apartments, medium homes, and larger households
    daily_base = np.random.gamma(shape=3.5, scale=2.8, size=num_samples) + 2.5
    # Clip between 2.5 and 35.0 kWh/day
    daily_kwh = np.clip(daily_base, 2.5, 35.0)

    # 3. Previous month consumption (correlated with daily consumption * 30 with realistic variation)
    prev_noise = np.random.normal(loc=0.0, scale=18.0, size=num_samples)
    previous_month_kwh = np.clip((daily_kwh * 30.0) + prev_noise, 45.0, 1100.0)

    # 4. Target: Actual monthly consumption (kWh)
    # Core relationship: daily * billing_days
    expected_kwh = daily_kwh * billing_days

    # Autoregressive component: household habits persist (slight pull towards previous month)
    habit_inertia = 0.08 * (previous_month_kwh - (daily_kwh * 30.0))

    # Nonlinear interaction: heavy consumers (high daily load > 18 kWh) have slight load surge due to HVAC/appliance heat
    nonlinear_surge = np.where(daily_kwh > 18.0, (daily_kwh - 18.0) * 1.5, 0.0)

    # Realistic random noise (fluctuation in weather, appliances, occupancy)
    noise = np.random.normal(loc=0.0, scale=12.0, size=num_samples)

    # Combined target
    monthly_kwh = expected_kwh + habit_inertia + nonlinear_surge + noise
    monthly_kwh = np.clip(monthly_kwh, 40.0, 1250.0)

    # Build DataFrame with clean rounded values
    df = pd.DataFrame(
        {
            "average_daily_consumption_kwh": np.round(daily_kwh, 2),
            "previous_month_consumption_kwh": np.round(previous_month_kwh, 2),
            "billing_days": billing_days.astype(int),
            "monthly_consumption_kwh": np.round(monthly_kwh, 2),
        }
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"[SUCCESS] Synthetic dataset generated with {len(df)} records at: {output_path}")
    print("\nDataset Summary Statistics:")
    print(df.describe().to_string())
    return df


if __name__ == "__main__":
    generate_electricity_dataset()
