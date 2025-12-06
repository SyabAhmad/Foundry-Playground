from models import db
from datetime import datetime
import uuid

class RAGDocument(db.Model):
    """RAG document chunks and embeddings"""
    __tablename__ = 'rag_documents'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = db.Column(db.String(36), db.ForeignKey('uploaded_files.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=True)  # Vector embedding
    chunk_metadata = db.Column(db.JSON, nullable=True)  # Chunk metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
