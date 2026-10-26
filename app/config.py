"""
Application Configuration
=========================
Loads environment variables and configures Flask, SQLAlchemy, and paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Ensure instance directory exists
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


def get_database_uri() -> str:
    """
    Constructs a robust SQLAlchemy database URI.
    If using SQLite with a relative path, converts it to an absolute path
    so that SQLite can reliably create/access the file on Windows.
    """
    env_uri = os.getenv("DATABASE_URL")
    if not env_uri:
        default_db = (INSTANCE_DIR / "electricity.db").resolve()
        return f"sqlite:///{default_db.as_posix()}"

    if env_uri.startswith("sqlite:///") and not env_uri.startswith("sqlite:///:memory:"):
        path_part = env_uri[len("sqlite:///"):]
        # Check if already absolute (e.g., C:/ or /)
        if len(path_part) > 2 and (path_part[1] == ":" or path_part.startswith("/")):
            return env_uri
        abs_db_path = (BASE_DIR / path_part).resolve()
        abs_db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{abs_db_path.as_posix()}"

    return env_uri


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-electricity-mca-project-2026")

    INSTANCE_DIR = INSTANCE_DIR
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Machine Learning and Datasets Paths
    DATASET_PATH = BASE_DIR / "datasets" / "electricity_consumption.csv"
    TRAINED_MODELS_DIR = BASE_DIR / "trained_models"
    LINEAR_REGRESSION_MODEL_PATH = TRAINED_MODELS_DIR / "linear_regression.joblib"
    RANDOM_FOREST_MODEL_PATH = TRAINED_MODELS_DIR / "random_forest.joblib"
    SCALER_PATH = TRAINED_MODELS_DIR / "scaler.joblib"
    METRICS_PATH = TRAINED_MODELS_DIR / "metrics.json"


class TestingConfig(Config):
    """Configuration used during automated testing."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
