from models import db
from datetime import datetime
import uuid

class TrainingJob(db.Model):
    """Training/fine-tuning job tracking"""
    __tablename__ = 'training_jobs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    base_model_id = db.Column(db.String(36), db.ForeignKey('ai_models.id'), nullable=True)
    job_name = db.Column(db.String(200), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)  # 'fine-tune', 'rag', 'custom'
    status = db.Column(db.String(50), default='pending')  # 'pending', 'running', 'completed', 'failed'
    foundry_job_id = db.Column(db.String(100), nullable=True)  # ID from Foundry Local
    parameters = db.Column(db.JSON, nullable=True)
    progress = db.Column(db.Float, default=0.0)  # 0-100
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    datasets = db.relationship('TrainingDataset', backref='training_job', lazy=True)
