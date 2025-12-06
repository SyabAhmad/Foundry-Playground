from models import db
from datetime import datetime
import uuid

class TrainingDataset(db.Model):
    """Datasets used in training jobs"""
    __tablename__ = 'training_datasets'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    training_job_id = db.Column(db.String(36), db.ForeignKey('training_jobs.id'), nullable=False)
    file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=False)
    dataset_type = db.Column(db.String(50), nullable=False)  # 'training', 'validation', 'test'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
