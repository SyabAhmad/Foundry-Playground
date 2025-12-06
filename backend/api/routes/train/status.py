from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, TrainingJob
from datetime import datetime

bp = Blueprint('training_status', __name__)

@bp.route('/<job_id>', methods=['GET'])
def get_training_status(job_id):
    """Get the status of a training job"""
    try:
        training_job = TrainingJob.query.get(job_id)

        if not training_job:
            return jsonify({
                'success': False,
                'error': 'Training job not found'
            }), 404

        # If we have a Foundry job ID, try to get updated status from Foundry
        if training_job.foundry_job_id:
            foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
            headers = {}
            api_key = current_app.config.get('FOUNDRY_API_KEY')
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            try:
                response = requests.get(f'{foundry_url}/train/{training_job.foundry_job_id}', headers=headers, timeout=10)

                if response.status_code == 200:
                    foundry_status = response.json()

                    # Update our database with latest status
                    training_job.status = foundry_status.get('status', training_job.status)
                    training_job.progress = foundry_status.get('progress', training_job.progress)

                    if training_job.status == 'completed':
                        training_job.completed_at = datetime.utcnow()
                    elif training_job.status == 'failed':
                        training_job.error_message = foundry_status.get('error', '')

                    db.session.commit()
            except requests.exceptions.RequestException:
                # Foundry unreachable, return cached status
                pass

        # Return job status
        response_data = {
            'success': True,
            'job_id': training_job.id,
            'job_name': training_job.job_name,
            'job_type': training_job.job_type,
            'status': training_job.status,
            'progress': training_job.progress,
            'foundry_job_id': training_job.foundry_job_id,
            'parameters': training_job.parameters,
            'created_at': training_job.created_at.isoformat(),
            'started_at': training_job.started_at.isoformat() if training_job.started_at else None,
            'completed_at': training_job.completed_at.isoformat() if training_job.completed_at else None,
            'error_message': training_job.error_message
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get training status',
            'message': str(e)
        }), 500

@bp.route('/user/<user_id>', methods=['GET'])
def get_user_training_jobs(user_id):
    """Get all training jobs for a user"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status_filter = request.args.get('status')

        query = TrainingJob.query.filter_by(user_id=user_id)

        if status_filter:
            query = query.filter_by(status=status_filter)

        jobs = query.order_by(TrainingJob.created_at.desc()).paginate(page=page, per_page=per_page)

        jobs_data = []
        for job in jobs.items:
            jobs_data.append({
                'job_id': job.id,
                'job_name': job.job_name,
                'job_type': job.job_type,
                'status': job.status,
                'progress': job.progress,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            })

        return jsonify({
            'success': True,
            'jobs': jobs_data,
            'pagination': {
                'page': jobs.page,
                'per_page': jobs.per_page,
                'total': jobs.total,
                'pages': jobs.pages
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get user training jobs',
            'message': str(e)
        }), 500

@bp.route('/<job_id>/cancel', methods=['POST'])
def cancel_training_job(job_id):
    """Cancel a training job"""
    try:
        training_job = TrainingJob.query.get(job_id)

        if not training_job:
            return jsonify({
                'success': False,
                'error': 'Training job not found'
            }), 404

        if training_job.status not in ['pending', 'running']:
            return jsonify({
                'success': False,
                'error': f'Cannot cancel job with status: {training_job.status}'
            }), 400

        # Try to cancel on Foundry Local
        if training_job.foundry_job_id:
            foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
            headers = {'Content-Type': 'application/json'}
            api_key = current_app.config.get('FOUNDRY_API_KEY')
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            try:
                response = requests.post(f'{foundry_url}/train/{training_job.foundry_job_id}/cancel',
                                       headers=headers, timeout=10)
                if response.status_code == 200:
                    training_job.status = 'cancelled'
                    training_job.completed_at = datetime.utcnow()
                    db.session.commit()

                    return jsonify({
                        'success': True,
                        'message': 'Training job cancelled successfully'
                    })
            except requests.exceptions.RequestException:
                pass

        # If Foundry cancel failed or no foundry job ID, just mark as cancelled locally
        training_job.status = 'cancelled'
        training_job.completed_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Training job marked as cancelled'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to cancel training job',
            'message': str(e)
        }), 500