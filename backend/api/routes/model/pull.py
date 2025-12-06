from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, AIModel

bp = Blueprint('pull_model', __name__)

@bp.route('/pull/<model_id>', methods=['POST'])
def pull_model(model_id):
    """Pull/download a model using Foundry CLI"""
    try:
        import subprocess

        # Use Foundry CLI to download/run the model
        result = subprocess.run(
            ["foundry", "model", "run", model_id],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for model download
        )

        if result.returncode == 0:
            # Update our database
            existing_model = AIModel.query.filter_by(model_id=model_id).first()
            if not existing_model:
                new_model = AIModel(
                    name=model_id,
                    model_id=model_id,
                    model_type='text',
                    description=f"Model {model_id}",
                    is_active=True
                )
                db.session.add(new_model)
            else:
                existing_model.is_active = True

            db.session.commit()

            return jsonify({
                'success': True,
                'model_id': model_id,
                'status': 'running',
                'message': f'Model {model_id} download and run triggered successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to pull model',
                'details': result.stderr,
                'stdout': result.stdout
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Timeout waiting for model download'
        }), 500
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Foundry CLI not found. Make sure Foundry is installed and in PATH'
        }), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to pull model',
            'message': str(e)
        }), 500

@bp.route('/pull', methods=['GET'])
def list_pullable_models():
    """List models available for pulling using Foundry CLI"""
    try:
        import subprocess
        import json

        # Use Foundry CLI to list available models
        result = subprocess.run(
            ["foundry", "model", "list", "--available", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                models_data = json.loads(result.stdout.strip())
                if isinstance(models_data, list):
                    models = models_data
                else:
                    models = models_data.get('models', [])
            except json.JSONDecodeError:
                # Fallback: parse as text lines
                models = [{"id": line.strip(), "name": line.strip()}
                         for line in result.stdout.splitlines() if line.strip()]

            return jsonify({
                'success': True,
                'models': models,
                'count': len(models)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to list pullable models',
                'details': result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Timeout waiting for Foundry CLI'
        }), 500
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Foundry CLI not found. Make sure Foundry is installed and in PATH'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to list pullable models',
            'message': str(e)
        }), 500