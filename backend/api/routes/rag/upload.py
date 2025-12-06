from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, UploadedFile, RAGDocument
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

bp = Blueprint('upload_rag', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'json', 'csv', 'md', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
def upload_rag_document():
    """Upload a document for RAG processing"""
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

        user_id = request.form.get('user_id') or str(uuid.uuid4())  # Temporary for demo
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")

        # Save file
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Create database record
        uploaded_file = UploadedFile(
            id=file_id,
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type or 'application/octet-stream',
            content_type='document',
            is_processed=False,
            processing_status='uploaded'
        )

        db.session.add(uploaded_file)
        db.session.commit()

        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'file_size': file_size,
            'message': 'File uploaded successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Upload failed',
            'message': str(e)
        }), 500

@bp.route('/process/<file_id>', methods=['POST'])
def process_rag_document(file_id):
    """Process an uploaded document for RAG"""
    try:
        uploaded_file = UploadedFile.query.get(file_id)

        if not uploaded_file:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        if uploaded_file.is_processed:
            return jsonify({
                'success': False,
                'error': 'File already processed'
            }), 400

        # Update processing status
        uploaded_file.processing_status = 'processing'
        db.session.commit()

        # Call Foundry Local to process the document
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'file_path': uploaded_file.file_path,
            'file_type': uploaded_file.file_type
        }

        response = requests.post(f'{foundry_url}/rag/process', json=payload, headers=headers, timeout=120)

        if response.status_code == 200:
            result = response.json()
            chunks = result.get('chunks', [])

            # Save chunks to database
            for i, chunk in enumerate(chunks):
                rag_doc = RAGDocument(
                    file_id=file_id,
                    chunk_index=i,
                    content=chunk.get('content', ''),
                    metadata=chunk.get('metadata', {}),
                    embedding=chunk.get('embedding')
                )
                db.session.add(rag_doc)

            # Update file status
            uploaded_file.is_processed = True
            uploaded_file.processing_status = 'completed'
            db.session.commit()

            return jsonify({
                'success': True,
                'file_id': file_id,
                'chunks_processed': len(chunks),
                'message': 'Document processed successfully for RAG'
            })
        else:
            # Processing failed
            uploaded_file.processing_status = 'failed'
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Processing failed: {response.status_code}',
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
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@bp.route('/files/<user_id>', methods=['GET'])
def get_user_rag_files(user_id):
    """Get all RAG files for a user"""
    try:
        files = UploadedFile.query.filter_by(
            user_id=user_id,
            content_type='document'
        ).order_by(UploadedFile.created_at.desc()).all()

        files_data = []
        for file in files:
            files_data.append({
                'file_id': file.id,
                'filename': file.filename,
                'original_filename': file.original_filename,
                'file_size': file.file_size,
                'is_processed': file.is_processed,
                'processing_status': file.processing_status,
                'created_at': file.created_at.isoformat(),
                'expires_at': file.expires_at.isoformat() if file.expires_at else None
            })

        return jsonify({
            'success': True,
            'files': files_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get user files',
            'message': str(e)
        }), 500