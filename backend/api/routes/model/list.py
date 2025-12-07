from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, AIModel

bp = Blueprint('list_models', __name__)

@bp.route('/models', methods=['GET'])
def list_available_models():
    """List all available models using Foundry CLI"""
    print("list_available_models function called!")
    try:
        import subprocess
        import json

        # Use Foundry CLI to list downloaded models (those with CPU/GPU indicators)
        print("Calling Foundry CLI...")
        result = subprocess.run(
            ["foundry", "model", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(f"CLI return code: {result.returncode}")
        print(f"CLI stdout: {result.stdout[:200]}...")
        print(f"CLI stderr: {result.stderr[:200]}...")

        if result.returncode == 0:
            # Instead of parsing the CLI output, check the actual cache directory
            import os
            import platform

            # Get the Foundry cache directory - models are in cache/models/Microsoft/
            home_dir = os.path.expanduser('~')
            if platform.system() == 'Windows':
                cache_dir = os.path.join(home_dir, '.foundry', 'cache', 'models', 'Microsoft')
            else:
                cache_dir = os.path.join(home_dir, '.foundry', 'cache', 'models', 'Microsoft')

            print(f"Checking cache directory: {cache_dir}")

            models = []
            if os.path.exists(cache_dir):
                try:
                    # List all subdirectories in cache/models/Microsoft (these are downloaded models)
                        for item in os.listdir(cache_dir):
                            item_path = os.path.join(cache_dir, item)
                            if not os.path.isdir(item_path):
                                continue
                            # Check if this looks like a model directory (has files)
                            try:
                                if not os.listdir(item_path):
                                    # empty directory - skip
                                    continue
                            except PermissionError:
                                # Skip directories we can't read
                                continue

                            model_id = item  # Preserve the directory name as the model id
                            print(f"Processing cached model: {model_id}")
                            try:
                                # Parse model info from directory name
                                # Format: model-name-generic-device-version
                                if '-generic-' in model_id:
                                    parts = model_id.split('-generic-')
                                    model_base = parts[0]
                                    device_version = parts[1]  # e.g., "cpu-4"

                                    device_parts = device_version.split('-')
                                    device = device_parts[0].upper() if device_parts else "CPU"

                                    models.append({
                                        # Use the full directory name for ID (keeps device/version): e.g. qwen2.5-1.5b-instruct-generic-cpu-4
                                        "id": model_id,
                                        # use model base for display name
                                        "name": model_base,
                                        "type": "text",
                                        "device": device,
                                        "task": "chat",
                                        "file_size": "Cached",
                                        "description": f"Cached model {model_base} ({device})"
                                    })
                                    print(f"Added cached model: {model_id} (base {model_base})")
                                else:
                                    # Fallback: use the full directory name
                                    models.append({
                                        # keep ID same as directory name
                                        "id": model_id,
                                        "name": model_id,
                                        "type": "text",
                                        "device": "CPU",
                                        "task": "chat",
                                        "file_size": "Cached",
                                        "description": f"Cached model {model_id}"
                                    })
                                    print(f"Added cached model (fallback): {model_id}")

                            except Exception as e:
                                print(f"Error processing cached model {model_id}: {e}")
                                import traceback
                                traceback.print_exc()

                except Exception as e:
                    print(f"Error checking cache directory: {e}")

            print(f"Found {len(models)} cached/downloaded models")

            # Update our database with foundry models
            for model_data in models:
                model_id = model_data.get('id') or model_data.get('name')
                if model_id:
                    existing_model = AIModel.query.filter_by(model_id=model_id).first()

                    if not existing_model:
                        # Create new model record
                        new_model = AIModel(
                            name=model_data.get('name', model_id),
                            model_id=model_id,
                            model_type='text',  # Default to text
                            description=f'Model {model_id}',
                            parameters={},
                            is_active=True
                        )
                        db.session.add(new_model)

            db.session.commit()

            return jsonify({
                'success': True,
                'models': models,
                'count': len(models),
                'source': 'foundry_cli'
            })
        else:
            print(f"Foundry CLI failed: {result.stderr}")
            return jsonify({
                'success': False,
                'error': 'Failed to list models from Foundry CLI',
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
        print(f"Error listing models: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list models',
            'details': str(e)
        }), 500

    except requests.exceptions.RequestException as e:
        # If Foundry is unreachable, return models from database
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
            'source': 'database',
            'warning': f'Foundry Local unreachable: {str(e)}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to list models',
            'message': str(e)
        }), 500

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