from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, AIModel

bp = Blueprint('stop_model', __name__)

@bp.route('/stop/<model_id>', methods=['POST'])
def stop_model(model_id):
    """Stop/unload a model from Foundry Local"""
    try:
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        from api.helpers.foundry import is_foundry_available
        ok, _ = is_foundry_available(foundry_url)
        if not ok:
            # Fallback: mark inactive in DB and return warning
            model = AIModel.query.filter_by(model_id=model_id).first()
            if model:
                model.is_active = False
                db.session.commit()
            return jsonify({
                'success': True,
                'model_id': model_id,
                'status': 'stopped-db-only',
                'warning': 'Foundry Local unreachable: model marked inactive in DB only'
            }), 200
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {'model': model_id}

        print(f"Stopping model via Foundry: url={foundry_url}/models/stop, payload={payload}")
        try:
            response = requests.post(f'{foundry_url}/models/stop', json=payload, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"Error sending stop request to Foundry: {e}")
            # Fallback to DB: mark inactive and return helpful message (200 OK with warning)
            model = AIModel.query.filter_by(model_id=model_id).first()
            if model:
                model.is_active = False
                db.session.commit()
            return jsonify({
                'success': True,
                'model_id': model_id,
                'status': 'stopped-db-only',
                'warning': 'Foundry Local unreachable: model marked inactive in DB only',
                'message': str(e)
            }), 200

        print(f"Foundry stop response status: {response.status_code}, text: {response.text[:500]}")
        if response.status_code == 200:
            result = response.json()

            # Update our database to mark as inactive
            model = AIModel.query.filter_by(model_id=model_id).first()
            if model:
                model.is_active = False
                db.session.commit()

            return jsonify({
                'success': True,
                'model_id': model_id,
                'status': result.get('status', 'stopped'),
                'message': f'Model {model_id} stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop model: {response.status_code}',
                'message': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Connection error',
            'message': str(e)
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to stop model',
            'message': str(e)
        }), 500

@bp.route('/running', methods=['GET'])
def list_running_models():
    """List currently running/loaded models in Foundry Local"""
    try:
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        response = requests.get(f'{foundry_url}/models/running', headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'models': result.get('models', []),
                'count': len(result.get('models', []))
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to get running models: {response.status_code}',
                'message': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        # Fallback: Return models from our DB where is_active=True
        db_models = AIModel.query.filter_by(is_active=True).all()
        models_response = []
        for model in db_models:
            models_response.append({
                'id': model.model_id,
                'name': model.name,
                'type': model.model_type,
                'description': model.description,
                'parameters': model.parameters,
                'last_used': model.last_used_at.isoformat() if model.last_used_at else None
            })
        return jsonify({
            'success': True,
            'models': models_response,
            'count': len(models_response),
            'warning': f'Foundry Local unreachable: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to list running models',
            'message': str(e)
        }), 500