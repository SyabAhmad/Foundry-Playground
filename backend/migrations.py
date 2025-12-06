from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
import os
from dotenv import load_dotenv
from models import db

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/foundry_playground')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    return app

def run_migrations():
    """Run database migrations"""
    app = create_app()

    with app.app_context():
        print("Running database migrations...")
        upgrade()
        print("Migrations completed successfully!")

if __name__ == '__main__':
    run_migrations()