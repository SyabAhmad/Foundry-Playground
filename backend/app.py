from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
import requests
import os
from dotenv import load_dotenv
from models import db
from api.routes import models, generate, chat, embeddings, conversations
from api.routes.model.list import bp as list_models
from api.routes.model.pull import bp as pull_model
from api.routes.model.stop import bp as stop_model
from api.routes.train.start import bp as start_training
from api.routes.train.status import bp as training_status
from api.routes.rag.upload import bp as upload_rag
from api.routes.rag.query import bp as query_rag
from api.routes.audio.transcribe import bp as transcribe_audio
from api.routes.vision.analyze import bp as analyze_image

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///foundry_playground.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Foundry Local configuration
app.config['FOUNDRY_BASE_URL'] = os.getenv('FOUNDRY_BASE_URL', 'http://127.0.0.1:56831')
app.config['FOUNDRY_API_KEY'] = os.getenv('FOUNDRY_API_KEY', '')

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(models.bp, url_prefix='/api')
app.register_blueprint(generate.bp, url_prefix='/api')
app.register_blueprint(chat.bp, url_prefix='/api')
app.register_blueprint(embeddings.bp, url_prefix='/api')
app.register_blueprint(conversations.bp, url_prefix='/api')
app.register_blueprint(list_models, url_prefix='/api')
app.register_blueprint(pull_model, url_prefix='/api/models')
app.register_blueprint(stop_model, url_prefix='/api/models')
app.register_blueprint(start_training, url_prefix='/api/train')
app.register_blueprint(training_status, url_prefix='/api/train')
app.register_blueprint(upload_rag, url_prefix='/api/rag')
app.register_blueprint(query_rag, url_prefix='/api/rag')
app.register_blueprint(transcribe_audio, url_prefix='/api/audio')
app.register_blueprint(analyze_image, url_prefix='/api/vision')

@app.route('/')
def index():
    return jsonify({
        'message': 'Foundry Playground API',
        'version': '1.0.0',
        'description': 'Community-driven API layer for Microsoft Foundry Local',
        'endpoints': {
            'models': '/api/models',
            'generate': '/api/generate',
            'train': '/api/train'
        }
    })

@app.route('/health')
def health():
    try:
        # Check if Foundry Local is running
        response = requests.get(f'{FOUNDRY_BASE_URL}/health', timeout=5)
        return jsonify({
            'status': 'healthy',
            'foundry_status': response.json() if response.status_code == 200 else 'unknown'
        })
    except:
        return jsonify({
            'status': 'healthy',
            'foundry_status': 'unreachable'
        }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)