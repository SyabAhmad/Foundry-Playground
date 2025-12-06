from models import db
from datetime import datetime
import uuid

class AIModel(db.Model):
    """AI model information and tracking"""
    __tablename__ = 'ai_models'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    model_id = db.Column(db.String(100), unique=True, nullable=False)  # Foundry model identifier
    model_type = db.Column(db.String(50), nullable=False)  # 'text', 'embedding', 'vision', etc.
    description = db.Column(db.Text, nullable=True)
    parameters = db.Column(db.JSON, nullable=True)  # Model parameters/configuration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    training_jobs = db.relationship('TrainingJob', backref='base_model', lazy=True)
