from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, AIModel
import numpy as np

bp = Blueprint('embeddings', __name__)

@bp.route('/embeddings', methods=['POST'])
def create_embeddings():
    """Create embeddings for input text"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        model = data.get('model', 'default-embedding-model')
        input_text = data.get('input')
        user_id = data.get('user_id')  # For tracking usage

        if not input_text:
            return jsonify({
                'success': False,
                'error': 'Input text is required'
            }), 400

        # Validate input types
        if isinstance(input_text, str):
            input_texts = [input_text]
        elif isinstance(input_text, list):
            input_texts = input_text
        else:
            return jsonify({
                'success': False,
                'error': 'Input must be a string or array of strings'
            }), 400

        # Check model exists in our database
        ai_model = AIModel.query.filter_by(model_id=model, model_type='embedding').first()
        if not ai_model:
            # Create model record if it doesn't exist
            ai_model = AIModel(
                name=f"Embedding Model {model}",
                model_id=model,
                model_type='embedding',
                description=f"Embedding model {model}"
            )
            db.session.add(ai_model)
            db.session.commit()

        # Call Foundry Local API
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'model': model,
            'input': input_texts
        }

        response = requests.post(f'{foundry_url}/v1/embeddings', json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()

            # Update model usage
            ai_model.last_used_at = db.func.now()
            db.session.commit()

            return jsonify({
                'success': True,
                'data': result.get('data', []),
                'model': model,
                'usage': result.get('usage', {})
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
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/embeddings/similarity', methods=['POST'])
def calculate_similarity():
    """Calculate similarity between embeddings"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        embedding1 = data.get('embedding1')
        embedding2 = data.get('embedding2')
        metric = data.get('metric', 'cosine')  # cosine, euclidean, dot_product

        if not embedding1 or not embedding2:
            return jsonify({
                'success': False,
                'error': 'Both embeddings are required'
            }), 400

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        if metric == 'cosine':
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        elif metric == 'euclidean':
            # Euclidean distance (convert to similarity)
            distance = np.linalg.norm(vec1 - vec2)
            similarity = 1 / (1 + distance)  # Convert distance to similarity
        elif metric == 'dot_product':
            similarity = np.dot(vec1, vec2)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported metric: {metric}'
            }), 400

        return jsonify({
            'success': True,
            'similarity': float(similarity),
            'metric': metric
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Similarity calculation failed',
            'message': str(e)
        }), 500

@bp.route('/embeddings/search', methods=['POST'])
def search_similar():
    """Search for similar embeddings (simplified version)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        query_embedding = data.get('query_embedding')
        embeddings = data.get('embeddings', [])
        top_k = data.get('top_k', 5)
        metric = data.get('metric', 'cosine')

        if not query_embedding or not embeddings:
            return jsonify({
                'success': False,
                'error': 'Query embedding and embeddings array are required'
            }), 400

        query_vec = np.array(query_embedding)
        similarities = []

        for i, emb in enumerate(embeddings):
            emb_vec = np.array(emb)

            if metric == 'cosine':
                similarity = np.dot(query_vec, emb_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(emb_vec))
            elif metric == 'euclidean':
                distance = np.linalg.norm(query_vec - emb_vec)
                similarity = 1 / (1 + distance)
            elif metric == 'dot_product':
                similarity = np.dot(query_vec, emb_vec)
            else:
                continue

            similarities.append({
                'index': i,
                'similarity': float(similarity)
            })

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return jsonify({
            'success': True,
            'results': similarities[:top_k],
            'metric': metric
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500