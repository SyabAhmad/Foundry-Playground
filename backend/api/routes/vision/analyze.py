from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, UploadedFile
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

bp = Blueprint('analyze_image', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/analyze', methods=['POST'])
def analyze_image():
    """Analyze image content using vision models"""
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
        prompt = request.form.get('prompt', 'Describe this image in detail')
        model = request.form.get('model', 'clip-vit-base-patch32')

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
            file_type=file.content_type or 'image/jpeg',
            content_type='image',
            is_processed=False,
            processing_status='uploaded'
        )

        db.session.add(uploaded_file)
        db.session.commit()

        # Call Foundry Local for image analysis
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'image_path': file_path,
            'prompt': prompt,
            'model': model
        }

        response = requests.post(f'{foundry_url}/vision/analyze', json=payload, headers=headers, timeout=120)

        if response.status_code == 200:
            result = response.json()

            # Update file status
            uploaded_file.is_processed = True
            uploaded_file.processing_status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'analysis': result.get('description', ''),
                'objects': result.get('objects', []),
                'text': result.get('text', []),
                'colors': result.get('colors', []),
                'file_id': file_id
            })
        else:
            # Processing failed
            uploaded_file.processing_status = 'failed'
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Analysis failed: {response.status_code}',
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
            'error': 'Analysis failed',
            'message': str(e)
        }), 500

@bp.route('/caption', methods=['POST'])
def generate_caption():
    """Generate a caption for an image"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        model = request.form.get('model', 'blip-image-captioning-base')

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
            file_type=file.content_type or 'image/jpeg',
            content_type='image',
            is_processed=False,
            processing_status='uploaded'
        )

        db.session.add(uploaded_file)
        db.session.commit()

        # Call Foundry Local for caption generation
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'image_path': file_path,
            'model': model
        }

        response = requests.post(f'{foundry_url}/vision/caption', json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()

            # Update file status
            uploaded_file.is_processed = True
            uploaded_file.processing_status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'caption': result.get('caption', ''),
                'confidence': result.get('confidence'),
                'file_id': file_id
            })
        else:
            # Processing failed
            uploaded_file.processing_status = 'failed'
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Caption generation failed: {response.status_code}',
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
            'error': 'Caption generation failed',
            'message': str(e)
        }), 500