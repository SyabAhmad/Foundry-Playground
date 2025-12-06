from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, UploadedFile
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

bp = Blueprint('transcribe_audio', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio file to text"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        user_id = request.form.get('user_id') or str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")

        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Create database record
        uploaded_file = UploadedFile(
            id=file_id,
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type or 'audio/wav',
            content_type='audio',
            is_processed=False,
            processing_status='uploaded'
        )

        db.session.add(uploaded_file)
        db.session.commit()

        # Call Foundry Local for transcription
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'audio_path': file_path,
            'model': request.form.get('model', 'whisper-base')
        }

        response = requests.post(f'{foundry_url}/audio/transcribe', json=payload, headers=headers, timeout=300)

        if response.status_code == 200:
            result = response.json()

            # Update file status
            uploaded_file.is_processed = True
            uploaded_file.processing_status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'transcription': result.get('text', ''),
                'language': result.get('language'),
                'duration': result.get('duration'),
                'file_id': file_id
            })
        else:
            # Processing failed
            uploaded_file.processing_status = 'failed'
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Transcription failed: {response.status_code}',
                'message': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Connection error',
            'message': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Transcription failed',
            'message': str(e)
        }), 500