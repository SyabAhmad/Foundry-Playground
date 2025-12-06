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

        if result.returncode == 0 and result.stdout.strip():
            output_lines = result.stdout.splitlines()
            all_model_aliases = []

            # First, extract all model aliases from the list
            for line in output_lines:
                line = line.strip()
                if not line or line.startswith('Alias') or line.startswith('-'):
                    continue

                parts = line.split()
                if len(parts) >= 1:
                    first_part = parts[0]
                    # If first part is not empty and not CPU/GPU, it's a model alias
                    if first_part and first_part not in ['CPU', 'GPU']:
                        all_model_aliases.append(first_part)

            print(f"Found {len(all_model_aliases)} model aliases, checking which are downloaded...")

            # Now check which models are actually downloaded by trying to get their info
            models = []
            for alias in all_model_aliases:
                try:
                    # Try to get model info - if it succeeds, the model is downloaded
                    info_result = subprocess.run(
                        ["foundry", "model", "info", alias],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if info_result.returncode == 0 and info_result.stdout.strip():
                        # Parse the info output
                        info_lines = info_result.stdout.splitlines()
                        if len(info_lines) >= 2:  # Should have at least header + data
                            # Parse the info line (similar format to list)
                            for info_line in info_lines[1:]:  # Skip header
                                info_line = info_line.strip()
                                if info_line:
                                    parts = info_line.split()
                                    if len(parts) >= 6:
                                        model_name = parts[0]
                                        device = parts[1]
                                        task = parts[2]
                                        file_size = parts[3] + ' ' + parts[4] if len(parts) > 4 else 'Unknown'
                                        license = parts[5] if len(parts) > 5 else 'Unknown'
                                        model_id = parts[-1] if len(parts) > 6 else alias

                                        models.append({
                                            "id": alias,
                                            "name": model_name,
                                            "type": "text",
                                            "device": device,
                                            "task": task,
                                            "file_size": file_size,
                                            "license": license,
                                            "model_id": model_id,
                                            "description": f"Downloaded model {model_name} ({device}) - {file_size}"
                                        })
                                        break  # Only take the first info line

                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    # Model info failed, skip this model (not downloaded)
                    continue

            print(f"Found {len(models)} downloaded models")

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

@bp.route('/<model_id>', methods=['GET'])
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