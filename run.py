"""
Application Entrypoint
======================
Runs the Flask development server and provides CLI commands for database
initialization, dataset generation, and model training.
"""

import sys
import os
from app import create_app
from app.models import db
from app.ml.train_models import train_and_evaluate_models
from scripts.generate_dataset import generate_electricity_dataset

app = create_app()


def init_database():
    """Initializes the database tables."""
    with app.app_context():
        db.create_all()
        print("[SUCCESS] Database initialized successfully (SQLite instance created).")


if __name__ == "__main__":
    # Handle custom CLI arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command in ["init-db", "--init-db"]:
            init_database()
            sys.exit(0)
        elif command in ["train-models", "--train"]:
            train_and_evaluate_models()
            sys.exit(0)
        elif command in ["generate-dataset", "--generate"]:
            generate_electricity_dataset()
            sys.exit(0)
        elif command in ["setup", "--setup"]:
            print("[INFO] Running complete project setup...")
            generate_electricity_dataset()
            train_and_evaluate_models()
            init_database()
            print("[SUCCESS] Project setup completed!")
            sys.exit(0)

    # By default, ensure database exists
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")

    print(f"\n============================================================")
    print(f" Electricity Bill Prediction System (MCA Minor Project)")
    print(f" Running at: http://{host}:{port}/")
    print(f" Press Ctrl+C to stop the server.")
    print(f"============================================================\n")

    app.run(host=host, port=port, debug=debug)
