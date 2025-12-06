from flask import Blueprint, jsonify, request, current_app
import requests

bp = Blueprint('generate', __name__)

@bp.route('/generate', methods=['POST'])
def generate_text():
    """Generate text using a Foundry Local model"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        model = data.get('model')
        prompt = data.get('prompt')
        max_tokens = data.get('max_tokens', 100)
        temperature = data.get('temperature', 0.7)
        stream = data.get('stream', False)

        if not model:
            return jsonify({
                'success': False,
                'error': 'Model is required'
            }), 400

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400

        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'model': model,
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': stream
        }

        response = requests.post(f'{foundry_url}/v1/completions', json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'generated_text': result.get('text', ''),
                'model': model,
                'usage': result.get('usage', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Generation failed: {response.status_code}',
                'message': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Connection error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/embeddings', methods=['POST'])
def generate_embeddings():
    """Generate embeddings for text using a Foundry Local model"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        model = data.get('model')
        input_text = data.get('input')

        if not model:
            return jsonify({
                'success': False,
                'error': 'Model is required'
            }), 400

        if not input_text:
            return jsonify({
                'success': False,
                'error': 'Input text is required'
            }), 400

        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'model': model,
            'input': input_text
        }

        response = requests.post(f'{foundry_url}/v1/embeddings', json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'embeddings': result.get('embeddings', []),
                'model': model
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Embedding generation failed: {response.status_code}',
                'message': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Connection error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500