from flask import Blueprint, jsonify, request, current_app
from models import db, AIModel

bp = Blueprint('pull_model_clean', __name__)


def _run_foundry_cmd(args, timeout=600):
    import subprocess
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)


@bp.route('/pull/<model_id>', methods=['POST'])
def pull_model(model_id):
    try:
        result = _run_foundry_cmd(["foundry", "model", "run", model_id], timeout=600)
        if result.returncode == 0:
            existing = AIModel.query.filter_by(model_id=model_id).first()
            if not existing:
                newm = AIModel(name=model_id, model_id=model_id, model_type='text', description=f"Model {model_id}", is_active=True)
                db.session.add(newm)
            else:
                existing.is_active = True
            db.session.commit()
            return jsonify({'success': True, 'model_id': model_id, 'status': 'running'})
        return jsonify({'success': False, 'error': 'CLI failed', 'details': result.stderr, 'stdout': result.stdout}), 500
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'Foundry CLI missing'}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('pull_model error')
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/pull', methods=['GET'])
def list_pullable_models():
    try:
        import json
        res = _run_foundry_cmd(["foundry", "model", "list", "--available", "--json"], timeout=30)
        if res.returncode == 0 and res.stdout and res.stdout.strip():
            try:
                models = json.loads(res.stdout.strip())
            except json.JSONDecodeError:
                models = [{"id": l.strip(), "name": l.strip()} for l in res.stdout.splitlines() if l.strip()]
            # Improved: Add validation and structured response
            if not isinstance(models, list):
                return jsonify({'success': False, 'error': 'Invalid model data format'}), 500
            model_count = len(models)
            response_data = {
                'success': True,
                'models': models,
                'count': model_count
            }
            return jsonify(response_data)
        fallback = _run_foundry_cmd(["foundry", "model", "list"], timeout=30)
        if fallback.returncode == 0 and fallback.stdout and fallback.stdout.strip():
            parsed = []
            for line in [l.strip() for l in fallback.stdout.splitlines() if l.strip()]:
                if line.lower().startswith('alias') or '---' in line or 'file size' in line.lower():
                    continue
                parts = line.split()
                if not parts:
                    continue
                parsed.append({"id": parts[-1].replace(':', '-'), "name": parts[-1].replace(':', '-')})
            # Improved: Consistent response format
            if not isinstance(parsed, list):
                return jsonify({'success': False, 'error': 'Invalid parsed model data'}), 500
            model_count = len(parsed)
            response_data = {
                'success': True,
                'models': parsed,
                'count': model_count
            }
            return jsonify(response_data)
        return jsonify({'success': False, 'error': 'Failed to list pullable models', 'details': res.stderr}), 500
    except Exception as e:
        current_app.logger.exception('list_pullable_models error')
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/all', methods=['GET'])
def list_all_models():
    try:
        res = _run_foundry_cmd(["foundry", "model", "list"], timeout=30)
        if res.returncode == 0 and res.stdout and res.stdout.strip():
            parsed = []
            for line in [l.strip() for l in res.stdout.splitlines() if l.strip()]:
                if line.lower().startswith('alias') or '---' in line:
                    continue
                parts = line.split()
                if not parts:
                    continue
                parsed.append({"id": parts[-1].replace(':', '-'), "name": parts[-1].replace(':', '-')})
            return jsonify({'success': True, 'models': parsed})
        return jsonify({'success': False, 'error': 'Failed to list all models', 'details': res.stderr}), 500
    except Exception as e:
        current_app.logger.exception('list_all_models error')
        return jsonify({'success': False, 'error': str(e)}), 500
