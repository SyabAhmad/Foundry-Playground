from flask_sqlalchemy import SQLAlchemy

# Single database instance shared across all models
db = SQLAlchemy()

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .apikey.api import APIKey
from .conversation import Conversation
from .message.message import Message
from .aimodel.aimodel import AIModel
from .training.trainingjob import TrainingJob
from .training.trainingdataset import TrainingDataset
from .upload.upload import UploadedFile
from .rag.ragdoc import RAGDocument
from .config.configandlog import SystemConfig, AuditLog

__all__ = [
    'db',
    'User',
    'APIKey',
    'Conversation',
    'Message',
    'AIModel',
    'TrainingJob',
    'TrainingDataset',
    'UploadedFile',
    'RAGDocument',
    'SystemConfig',
    'AuditLog'
]