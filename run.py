"""
Entry point for running the Flask application.

Usage:
    python run.py
"""

from src.web.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
