"""
Pytest Fixtures & Configuration
================================
Provides application client and in-memory test database fixtures.
"""

import os
import pytest
from app import create_app
from app.config import TestingConfig
from app.models import db
from app.ml.train_models import train_and_evaluate_models
from scripts.generate_dataset import generate_electricity_dataset


@pytest.fixture(scope="session", autouse=True)
def ensure_dataset_and_models():
    """Ensure dataset and model artifacts exist before executing tests."""
    dataset_file = "datasets/electricity_consumption.csv"
    metrics_file = "trained_models/metrics.json"

    if not os.path.exists(dataset_file):
        generate_electricity_dataset(output_path=dataset_file, num_samples=1500)

    if not os.path.exists(metrics_file):
        train_and_evaluate_models(dataset_path=dataset_file)


@pytest.fixture
def app():
    """Create Flask application configured for isolated in-memory testing."""
    test_app = create_app(config_class=TestingConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()
