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

        # Use Foundry CLI to list available models. Try JSON option first, then fallback to table parser
        result = subprocess.run(
            ["foundry", "model", "list", "--available", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        models = []
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
            # If the CLI returned unrecognized argument (old foundry CLI), fallback to `foundry model list`
            # and parse the tabular output
            stderr = result.stderr or ''
            if 'Unrecognized command or argument' in stderr or '--available' in stderr:
                fallback = subprocess.run(
                    ["foundry", "model", "list"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if fallback.returncode == 0 and fallback.stdout.strip():
                    # parse fallback tabular output
                    lines = [l.strip() for l in fallback.stdout.splitlines() if l.strip()]
                    parsed_models = []
                    for line in lines:
                        # Skip header or separator lines
                        if line.lower().startswith('alias') or '---' in line or 'file size' in line.lower():
                            continue
                        # Extract the last whitespace-delimited token as model id
                        parts = line.split()
                        if not parts:
                            continue
                        model_id = parts[-1]
                        # Normalize IDs: foundry CLI uses '...cpu:4' suffix; cache folder uses '...cpu-4'
                        model_id = model_id.replace(':', '-')
                        parsed_models.append({"id": model_id, "name": model_id})
                    models = parsed_models
                    return jsonify({
                        'success': True,
                        'models': models,
                        'count': len(models)
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to list pullable models (fallback)',
                        'details': fallback.stderr
                    }), 500
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


@bp.route('/all', methods=['GET'])
def list_all_models():
    """List all models present in Foundry's catalog via CLI (full list)
    This is a more general listing which returns all models (not filtered to available only).
    """
    try:
        import subprocess

        result = subprocess.run(
            ["foundry", "model", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            models = []
            for line in lines:
                # Skip header/separator lines
                low = line.lower()
                if low.startswith('alias') or '---' in line:
                    continue
                parts = line.split()
                if not parts:
                    continue
                model_id = parts[-1]
                # Normalize ID like 'qwen:...' -> 'qwen-...'
                model_id = model_id.replace(':', '-')
                # Determine device from the second token if possible
                device = parts[1] if len(parts) > 1 and parts[1].upper() in ('GPU', 'CPU') else 'CPU'
                # Derive display name from model_id base
                if '-generic-' in model_id:
                    model_name = model_id.split('-generic-')[0]
                else:
                    model_name = model_id

                # Attempt to extract file size by heuristic position
                file_size = parts[3] if len(parts) > 3 else ''

                models.append({
                    'id': model_id,
                    'name': model_name,
                    'device': device,
                    'file_size': file_size,
                    'raw_line': line
                })

            return jsonify({
                'success': True,
                'models': models,
                'count': len(models)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to list all models',
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
            'error': 'Failed to list all models',
            'message': str(e)
        }), 500