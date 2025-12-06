from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, AIModel

bp = Blueprint('models', __name__)

# This route has been moved to api/routes/model/list.py to use Foundry CLI

@bp.route('/models/<model_id>', methods=['GET'])
def get_model_details(model_id):
    """Get detailed information about a specific model"""
    try:
        # Check our database first
        model = AIModel.query.filter_by(model_id=model_id, is_active=True).first()

        if model:
            # Try to get additional details from Foundry Local
            foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
            headers = {}
            api_key = current_app.config.get('FOUNDRY_API_KEY')
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            try:
                response = requests.get(f'{foundry_url}/models/{model_id}', headers=headers, timeout=10)
                if response.status_code == 200:
                    foundry_details = response.json()
                    # Merge foundry details with our database info
                    model_info = {
                        'id': model.model_id,
                        'name': model.name,
                        'type': model.model_type,
                        'description': model.description,
                        'parameters': model.parameters,
                        'database_info': {
                            'created_at': model.created_at.isoformat(),
                            'last_used': model.last_used_at.isoformat() if model.last_used_at else None,
                            'is_active': model.is_active
                        },
                        'foundry_details': foundry_details
                    }
                else:
                    model_info = {
                        'id': model.model_id,
                        'name': model.name,
                        'type': model.model_type,
                        'description': model.description,
                        'parameters': model.parameters,
                        'database_info': {
                            'created_at': model.created_at.isoformat(),
                            'last_used': model.last_used_at.isoformat() if model.last_used_at else None,
                            'is_active': model.is_active
                        }
                    }
            except:
                # Foundry unreachable, return database info only
                model_info = {
                    'id': model.model_id,
                    'name': model.name,
                    'type': model.model_type,
                    'description': model.description,
                    'parameters': model.parameters,
                    'database_info': {
                        'created_at': model.created_at.isoformat(),
                        'last_used': model.last_used_at.isoformat() if model.last_used_at else None,
                        'is_active': model.is_active
                    }
                }

            return jsonify({
                'success': True,
                'model': model_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Model not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get model details',
            'message': str(e)
        }), 500