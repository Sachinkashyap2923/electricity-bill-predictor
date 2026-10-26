"""
Flask Application Routes & HTTP Handlers
========================================
Implements web endpoints for Home, Predict, Result, History,
Dashboard, Model Evaluation, About, and Error Pages.
"""

from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app,
)
from app.models import db, ElectricityPrediction
from app.services import (
    PredictionService,
    BillingService,
    DashboardService,
    InputValidationError,
)
from app.ml.evaluate import get_evaluation_metrics, get_metric_definitions
from app.ml.predict import check_feature_boundaries, load_ml_artifacts

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page featuring project overview, algorithms, and key highlights."""
    metrics_data = get_evaluation_metrics()
    selected_model = metrics_data.get("comparison", {}).get(
        "selected_model", "Random Forest Regressor"
    )
    return render_template(
        "index.html",
        selected_model=selected_model,
        metrics_available=metrics_data.get("available", False),
    )


@main_bp.route("/predict", methods=["GET", "POST"])
def predict():
    """
    Handles electricity bill prediction form display and submission.
    Validates input on both client and server side.
    """
    if request.method == "POST":
        raw_daily = request.form.get("average_daily_consumption_kwh")
        raw_prev = request.form.get("previous_month_consumption_kwh")
        raw_days = request.form.get("billing_days")
        raw_tariff = request.form.get("tariff_per_kwh")
        raw_fixed = request.form.get("fixed_charges")
        raw_pct = request.form.get("additional_charge_percentage")
        model_choice = request.form.get("model_choice", "auto")

        try:
            validated = PredictionService.validate_inputs(
                daily_kwh=raw_daily,
                prev_month_kwh=raw_prev,
                billing_days=raw_days,
                tariff_per_kwh=raw_tariff,
                fixed_charges=raw_fixed,
                additional_charge_percentage=raw_pct,
            )

            prediction_record, _ = PredictionService.create_prediction(
                inputs=validated,
                model_choice=model_choice,
                persist=True,
            )

            flash("Electricity bill prediction generated successfully!", "success")
            return redirect(url_for("main.prediction_result", prediction_id=prediction_record.id))

        except InputValidationError as e:
            flash(f"Input validation error: {str(e)}", "danger")
        except FileNotFoundError as e:
            flash(f"ML Model Error: {str(e)}", "warning")
        except Exception as e:
            flash(f"An unexpected error occurred during prediction: {str(e)}", "danger")

    # Default initial values for form
    default_values = {
        "average_daily_consumption_kwh": 12.5,
        "previous_month_consumption_kwh": 360.0,
        "billing_days": 30,
        "tariff_per_kwh": 7.50,
        "fixed_charges": 50.00,
        "additional_charge_percentage": 5.0,
        "model_choice": "auto",
    }
    return render_template("predict.html", defaults=default_values)


@main_bp.route("/result/<int:prediction_id>")
def prediction_result(prediction_id: int):
    """Displays detailed bill estimate, consumption category, and model information."""
    record = db.session.get(ElectricityPrediction, prediction_id)
    if not record:
        flash(f"Prediction record #{prediction_id} not found.", "warning")
        return redirect(url_for("main.history"))

    # Recalculate transparent breakdown for display
    bill_data = BillingService.calculate_bill(
        predicted_consumption_kwh=record.predicted_monthly_consumption_kwh,
        tariff_per_kwh=record.tariff_per_kwh,
        fixed_charges=record.fixed_charges,
        additional_charge_percentage=record.additional_charge_percentage,
        previous_month_consumption_kwh=record.previous_month_consumption_kwh,
    )

    # Check boundaries against training set
    try:
        artifacts = load_ml_artifacts()
        is_out_of_range, warnings = check_feature_boundaries(
            record.average_daily_consumption_kwh,
            record.previous_month_consumption_kwh,
            record.billing_days,
            artifacts.get("feature_ranges", {}),
        )
    except Exception:
        is_out_of_range, warnings = False, []

    return render_template(
        "result.html",
        record=record,
        bill=bill_data,
        is_out_of_range=is_out_of_range,
        warnings=warnings,
    )


@main_bp.route("/history")
def history():
    """
    Displays historical predictions with search, date filtering, and model filtering.
    """
    model_filter = request.args.get("model", "").strip()
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    query = db.session.query(ElectricityPrediction)

    if model_filter:
        query = query.filter(ElectricityPrediction.model_name.ilike(f"%{model_filter}%"))

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.filter(ElectricityPrediction.created_at >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            query = query.filter(ElectricityPrediction.created_at <= end_date)
        except ValueError:
            pass

    predictions = query.order_by(
        ElectricityPrediction.created_at.desc(), ElectricityPrediction.id.desc()
    ).all()

    return render_template(
        "history.html",
        predictions=predictions,
        selected_model=model_filter,
        start_date=start_date_str,
        end_date=end_date_str,
    )


@main_bp.route("/history/<int:prediction_id>")
def prediction_detail(prediction_id: int):
    """View full detailed record of an individual saved prediction."""
    record = db.session.get(ElectricityPrediction, prediction_id)
    if not record:
        flash(f"Prediction record #{prediction_id} was not found.", "warning")
        return redirect(url_for("main.history"))

    bill_data = BillingService.calculate_bill(
        predicted_consumption_kwh=record.predicted_monthly_consumption_kwh,
        tariff_per_kwh=record.tariff_per_kwh,
        fixed_charges=record.fixed_charges,
        additional_charge_percentage=record.additional_charge_percentage,
        previous_month_consumption_kwh=record.previous_month_consumption_kwh,
    )

    return render_template("prediction_detail.html", record=record, bill=bill_data)


@main_bp.route("/history/<int:prediction_id>/delete", methods=["POST"])
def delete_prediction(prediction_id: int):
    """Deletes a historical prediction record."""
    record = db.session.get(ElectricityPrediction, prediction_id)
    if record:
        db.session.delete(record)
        db.session.commit()
        flash(f"Prediction record #{prediction_id} was successfully deleted.", "info")
    else:
        flash(f"Record #{prediction_id} not found.", "warning")

    return redirect(url_for("main.history"))


@main_bp.route("/dashboard")
def dashboard():
    """Analytical dashboard displaying summary KPI cards and Chart.js trend charts."""
    dash_data = DashboardService.get_dashboard_data()
    metrics_data = get_evaluation_metrics()
    return render_template(
        "dashboard.html",
        dash=dash_data,
        metrics=metrics_data,
    )


@main_bp.route("/evaluation")
def model_evaluation():
    """
    Renders the model evaluation page comparing Linear Regression and Random Forest
    on MAE, RMSE, and R2 calculated from the held-out test set.
    """
    metrics = get_evaluation_metrics()
    metric_defs = get_metric_definitions()
    return render_template(
        "model_evaluation.html",
        metrics=metrics,
        metric_defs=metric_defs,
    )


@main_bp.route("/about")
def about():
    """Information page describing project objectives, ML algorithms, and MCA viva notes."""
    metrics = get_evaluation_metrics()
    return render_template("about.html", metrics=metrics)


@main_bp.app_errorhandler(404)
def not_found_error(error):
    """Custom 404 page."""
    return render_template("404.html"), 404


@main_bp.app_errorhandler(500)
def internal_error(error):
    """Custom 500 page."""
    db.session.rollback()
    return render_template("500.html"), 500
