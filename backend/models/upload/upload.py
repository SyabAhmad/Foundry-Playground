from models import db
from datetime import datetime
import uuid

class UploadedFile(db.Model):
    """File upload tracking"""
    __tablename__ = 'uploaded_files'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)  # MIME type
    content_type = db.Column(db.String(50), nullable=False)  # 'document', 'image', 'audio', etc.
    checksum = db.Column(db.String(128), nullable=True)  # File hash for integrity
    is_processed = db.Column(db.Boolean, default=False)
    processing_status = db.Column(db.String(50), default='pending')
    file_metadata = db.Column(db.JSON, nullable=True)  # Additional file metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # For temporary files
