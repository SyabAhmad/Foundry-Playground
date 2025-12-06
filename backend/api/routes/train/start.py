from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, TrainingJob, TrainingDataset, UploadedFile, AIModel
from datetime import datetime
import uuid

bp = Blueprint('start_training', __name__)

@bp.route('', methods=['POST'])
def start_training():
    """Start a new training/fine-tuning job"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        user_id = data.get('user_id')  # In real app, from authentication
        job_name = data.get('job_name', f'Training Job {datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        job_type = data.get('job_type', 'fine-tune')
        base_model_id = data.get('base_model')
        dataset_files = data.get('dataset_files', [])  # List of file_ids
        parameters = data.get('parameters', {})

        if not base_model_id:
            return jsonify({
                'success': False,
                'error': 'Base model is required'
            }), 400

        if not dataset_files:
            return jsonify({
                'success': False,
                'error': 'Dataset files are required'
            }), 400

        # Verify base model exists
        base_model = AIModel.query.filter_by(model_id=base_model_id, is_active=True).first()
        if not base_model:
            return jsonify({
                'success': False,
                'error': 'Base model not found or not active'
            }), 404

        # Verify all dataset files exist
        for file_id in dataset_files:
            uploaded_file = UploadedFile.query.filter_by(id=file_id, is_processed=True).first()
            if not uploaded_file:
                return jsonify({
                    'success': False,
                    'error': f'Dataset file {file_id} not found or not processed'
                }), 404

        # Create training job record
        training_job = TrainingJob(
            user_id=user_id or str(uuid.uuid4()),  # Temporary for demo
            base_model_id=base_model.id,
            job_name=job_name,
            job_type=job_type,
            status='pending',
            parameters=parameters
        )

        db.session.add(training_job)
        db.session.flush()  # Get the job ID

        # Create training dataset records
        for file_id in dataset_files:
            dataset_record = TrainingDataset(
                training_job_id=training_job.id,
                file_id=file_id,
                dataset_type='training'  # Could be expanded for validation/test splits
            )
            db.session.add(dataset_record)

        # Call Foundry Local training API
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        foundry_payload = {
            'model': base_model_id,
            'training_files': dataset_files,
            'job_type': job_type,
            'parameters': parameters
        }

        response = requests.post(f'{foundry_url}/train', json=foundry_payload, headers=headers, timeout=60)

        if response.status_code in [200, 201]:
            result = response.json()

            # Update job with Foundry job ID and mark as started
            training_job.foundry_job_id = result.get('job_id')
            training_job.status = 'running'
            training_job.started_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'success': True,
                'job_id': training_job.id,
                'foundry_job_id': training_job.foundry_job_id,
                'status': 'running',
                'message': 'Training job started successfully'
            })
        else:
            # Training failed to start, mark as failed
            training_job.status = 'failed'
            training_job.error_message = response.text
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Failed to start training: {response.status_code}',
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
            'error': 'Failed to start training',
            'message': str(e)
        }), 500