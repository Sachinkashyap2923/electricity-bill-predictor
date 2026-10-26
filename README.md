# Electricity Bill Prediction System Using Machine Learning

An end-to-end Machine Learning web application and academic minor project for **Master of Computer Applications (MCA)** students.

This system estimates monthly electricity consumption from user inputs (daily usage, previous billing cycle, billing days) using **Linear Regression** and **Random Forest Regressor**, and transparently computes the estimated utility bill using configurable flat-rate tariffs, fixed meter charges, and surcharges.

---

## ⚡ Key Highlights

- **Dual Machine Learning Algorithms:** Trains and compares **Linear Regression** (interpretable Ordinary Least Squares) and **Random Forest Regressor** (non-linear ensemble).
- **Leakage-Free ML Pipeline:** Feature scaling (`StandardScaler`) is fitted strictly on the 80% training split. Both models are evaluated on 300 held-out test samples.
- **Empirical Metric Comparison:** Calculates and renders actual Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Coefficient of Determination ($R^2$).
- **Transparent Tariff Billing:** Decouples physical energy estimation (kWh) from local tariff policy. Computes itemized Energy Charges, Fixed Charges, and Additional Surcharges with decimal precision.
- **Out-of-Distribution Warning:** Alerts users when input values exceed the statistical boundaries of the training dataset.
- **Persistent Storage:** Stores prediction records, timestamps, and model metadata in SQLite using SQLAlchemy ORM.
- **Interactive Dashboard:** Dynamic KPI cards and Chart.js visualizations for billing trends, usage tiers (Low, Moderate, High), and algorithm comparisons.
- **Academic Disclaimer:** Explicitly documented as an academic estimation tool, not an official utility billing invoice.

---

## 📂 Project Architecture

```
d:/ML project minor/
├── app/
│   ├── __init__.py                 # Flask Application Factory pattern
│   ├── config.py                   # Environment configuration & SQLite URI resolver
│   ├── models.py                   # SQLAlchemy ElectricityPrediction model
│   ├── routes.py                   # Blueprint HTTP route handlers
│   ├── services.py                 # BillingService, PredictionService, DashboardService
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── train_models.py         # Full training pipeline (LR & RF)
│   │   ├── predict.py              # In-memory prediction engine & range checks
│   │   └── evaluate.py             # Metric loader & educational viva definitions
│   ├── templates/
│   │   ├── base.html               # Base layout, navbar, footer, CDNs
│   │   ├── index.html              # Landing page, algorithms, workflow
│   │   ├── predict.html            # Prediction form with 1-click presets & live preview
│   │   ├── result.html             # Itemized bill, usage tier, model metadata
│   │   ├── history.html            # Persistent historical table with date & model filters
│   │   ├── prediction_detail.html  # Full audit breakdown for individual prediction
│   │   ├── dashboard.html          # Dynamic KPI cards and Chart.js trend graphs
│   │   ├── model_evaluation.html   # Model comparison table & actual vs. predicted charts
│   │   ├── about.html              # System architecture, viva Q&A cheat sheet
│   │   ├── 404.html                # Custom Not Found error page
│   │   └── 500.html                # Custom Server Error page
│   └── static/
│       ├── css/
│       │   └── style.css           # Modern, responsive design system
│       └── js/
│           ├── main.js             # Form presets and live bill estimation preview
│           └── charts.js           # Chart.js renderers for dashboard & evaluation
├── datasets/
│   └── electricity_consumption.csv # 1,500 synthetic records with realistic noise
├── trained_models/
│   ├── linear_regression.joblib    # Serialized Linear Regression model
│   ├── random_forest.joblib        # Serialized Random Forest Regressor
│   ├── scaler.joblib               # Serialized StandardScaler fitted on training set
│   └── metrics.json                # Test set evaluation metrics & sample points
├── scripts/
│   └── generate_dataset.py         # Standalone synthetic dataset generator
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures and isolated in-memory DB
│   ├── test_app.py                 # HTTP routes, UI workflow, and error handlers
│   ├── test_prediction.py          # Input validation, NaNs, Inf, and model inference
│   └── test_billing.py             # Billing calculations, rounding, and usage tiers
├── instance/
│   └── electricity.db              # SQLite persistent database file
├── .env.example                    # Template environment variables
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Pinned dependencies
├── run.py                          # Application entry point and CLI runner
├── README.md                       # Windows setup instructions and documentation
└── PROJECT_REPORT.md               # Complete MCA Minor Project Report
```

---

## 🛠️ Windows PowerShell Setup Instructions

Follow these exact steps in **Windows PowerShell** to set up, train, and run the project locally.

### Step 1: Open PowerShell and Navigate to Project Directory

```powershell
cd "d:\ML project minor"
```

### Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Script Execution Policy:**  
> If PowerShell displays an error like `cannot be loaded because running scripts is disabled on this system`, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then retry activating `.venv\Scripts\Activate.ps1`.

### Step 4: Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 5: Generate the Synthetic Dataset

Generates 1,500 realistic consumption records at `datasets/electricity_consumption.csv`:

```powershell
python scripts/generate_dataset.py
```

### Step 6: Train the Machine Learning Models

Trains both Linear Regression and Random Forest Regressor on an 80/20 train/test split:

```powershell
python -m app.ml.train_models
```

### Step 7: Initialize the SQLite Database

Creates all tables in the `instance/electricity.db` SQLite database:

```powershell
python run.py init-db
```

*(Alternatively, run `python run.py setup` to execute dataset generation, training, and database setup in one command).*

### Step 8: Run Automated Tests

Execute the automated test suite with pytest:

```powershell
python -m pytest -v
```

*(All 28 tests must pass with 0 failures).*

### Step 9: Start the Application

Launch the Flask development server:

```powershell
python run.py
```

Open your web browser and navigate to:  
👉 **`http://127.0.0.1:5000/`**

---

## 📊 Live Model Evaluation Metrics

Evaluated on 300 held-out test samples (80% training / 20% testing split, seed=42):

| Metric | Linear Regression | Random Forest Regressor | Preferred Model |
| :--- | :---: | :---: | :---: |
| **Mean Absolute Error (MAE)** | **10.852 kWh** | 11.960 kWh | **Linear Regression** |
| **Root Mean Squared Error (RMSE)** | **13.660 kWh** | 15.107 kWh | **Linear Regression** |
| **$R^2$ Score (Variance Explained)** | **0.9931** | 0.9916 | **Linear Regression** |

*Rationale:* Physical power consumption is proportional to average daily load multiplied by billing cycle days ($kWh = Daily \times Days$). Linear Regression captures this linear hyper-plane with fewer parameters and lower test variance, avoiding the minor step-function discretization errors of tree-based ensembles.

---

## 🌐 Application Workflow & URL Sitemap

| Page | URL Route | Description |
| :--- | :--- | :--- |
| **Home Page** | `/` | Project overview, algorithms summary, workflow pipeline, and academic disclaimer. |
| **Prediction Form** | `/predict` | Inputs for daily usage, previous cycle, days, tariff, and fixed fees. Includes 1-click test presets and live bill estimation preview. |
| **Prediction Result** | `/result/<id>` | Itemized bill estimate, energy charge, surcharges, usage category (Low/Moderate/High), and out-of-range warnings. |
| **Prediction History** | `/history` | Filterable table of past predictions with date range and model filters, modal delete actions. |
| **Prediction Detail** | `/history/<id>` | Full itemized audit breakdown of a saved historical record. |
| **Analytics Dashboard**| `/dashboard` | Real-time KPI summary cards and Chart.js graphs (billing trend line chart, usage category doughnut chart). |
| **Model Evaluation** | `/evaluation` | Real MAE, RMSE, and $R^2$ comparisons, error bar charts, actual-vs-predicted curves, and MCA viva definitions. |
| **About & Documentation**| `/about` | Technical architecture, mathematical formulations, and viva Q&A defense cheat sheet. |

---

## 🧮 Bill Calculation Formula

The application uses transparent, decimal-safe monetary arithmetic:

$$\text{Energy Charge} = \text{Predicted Monthly Consumption (kWh)} \times \text{Tariff Rate per kWh}$$

$$\text{Additional Surcharges} = \text{Energy Charge} \times \left(\frac{\text{Additional Surcharge Percentage}}{100}\right)$$

$$\text{Estimated Total Bill} = \text{Energy Charge} + \text{Fixed Monthly Charges} + \text{Additional Surcharges}$$

---

## 🔧 Common Troubleshooting & FAQs

### 1. `ModuleNotFoundError: No module named 'app'`
**Cause:** Running a sub-script directly without setting the Python module path.  
**Solution:** Always execute modules using the `-m` switch from the project root:
```powershell
python -m app.ml.train_models
```

### 2. `FileNotFoundError: Model artifacts not found`
**Cause:** Attempting to run predictions before training models.  
**Solution:** Run the dataset generator and ML training pipeline:
```powershell
python scripts/generate_dataset.py
python -m app.ml.train_models
```

### 3. `Port 5000 is already in use`
**Cause:** Another application (or background Flask instance) is occupying port 5000.  
**Solution:** Specify an alternate port via environment variable:
```powershell
$env:PORT="5050"; python run.py
```

### 4. `sqlite3.OperationalError: unable to open database file`
**Cause:** The `instance/` folder does not exist or relative path cannot be resolved.  
**Solution:** The application automatically resolves relative SQLite paths against `BASE_DIR`. You can also manually create the folder:
```powershell
mkdir instance
python run.py init-db
```

### 5. Replacing the Synthetic Dataset with Real Utility Data
To use real utility billing records or smart-meter data:
1. Export a CSV file with columns: `average_daily_consumption_kwh`, `previous_month_consumption_kwh`, `billing_days`, and `monthly_consumption_kwh`.
2. Save it at `datasets/electricity_consumption.csv`.
3. Retrain models via `python -m app.ml.train_models`.
4. The web application will immediately reflect updated coefficients, feature ranges, and evaluation metrics without restarting.

---

## 📜 Academic Project Information

- **Degree Program:** Master of Computer Applications (MCA)
- **Course:** Minor Project
- **Project Title:** Electricity Bill Prediction System Using Machine Learning
- **Author:** MCA Student
- **Supervisor:** Faculty Project Guide
- **Academic Year:** 2026
