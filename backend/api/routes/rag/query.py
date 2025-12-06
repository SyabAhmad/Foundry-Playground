from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, RAGDocument, UploadedFile
import numpy as np

bp = Blueprint('query_rag', __name__)

@bp.route('/query', methods=['POST'])
def query_rag():
    """Query the RAG system with a question"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        question = data.get('question')
        file_ids = data.get('file_ids', [])  # Optional: limit to specific files
        top_k = data.get('top_k', 5)
        model = data.get('model', 'default-rag-model')

        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400

        # Get relevant documents
        query_embedding = None

        # First, get embedding for the question
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://localhost:8080')
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        embed_payload = {
            'model': 'embedding-model',  # Assuming default embedding model
            'input': [question]
        }

        embed_response = requests.post(f'{foundry_url}/embeddings', json=embed_payload, headers=headers, timeout=30)

        if embed_response.status_code == 200:
            embed_result = embed_response.json()
            query_embedding = embed_result.get('data', [{}])[0].get('embedding')

        if not query_embedding:
            return jsonify({
                'success': False,
                'error': 'Failed to generate question embedding'
            }), 500

        # Find similar documents using vector similarity
        query_vec = np.array(query_embedding)

        # Get all RAG documents (or filter by file_ids)
        query = RAGDocument.query
        if file_ids:
            query = query.filter(RAGDocument.file_id.in_(file_ids))

        documents = query.all()

        similarities = []
        for doc in documents:
            if doc.embedding:
                doc_vec = np.array(doc.embedding)
                similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                similarities.append({
                    'document': doc,
                    'similarity': float(similarity)
                })

        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_documents = similarities[:top_k]

        # Prepare context from top documents
        context_parts = []
        for item in top_documents:
            doc = item['document']
            context_parts.append(f"[Similarity: {item['similarity']:.3f}] {doc.content}")

        context = "\n\n".join(context_parts)

        # Generate answer using context
        chat_payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are a helpful assistant. Use the following context to answer the question. If the context doesn\'t contain enough information, say so.\n\nContext:\n{context}'
                },
                {
                    'role': 'user',
                    'content': question
                }
            ],
            'max_tokens': 500,
            'temperature': 0.3
        }

        chat_response = requests.post(f'{foundry_url}/chat/completions', json=chat_payload, headers=headers, timeout=60)

        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            answer = chat_result.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Prepare sources information
            sources = []
            for item in top_documents:
                doc = item['document']
                uploaded_file = UploadedFile.query.get(doc.file_id)
                sources.append({
                    'file_id': doc.file_id,
                    'filename': uploaded_file.filename if uploaded_file else 'Unknown',
                    'chunk_index': doc.chunk_index,
                    'similarity': item['similarity'],
                    'content_preview': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content
                })

            return jsonify({
                'success': True,
                'answer': answer,
                'sources': sources,
                'context_used': len(top_documents),
                'usage': chat_result.get('usage', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Answer generation failed: {chat_response.status_code}',
                'message': chat_response.text
            }), chat_response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Connection error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'RAG query failed',
            'message': str(e)
        }), 500

@bp.route('/stats/<user_id>', methods=['GET'])
def get_rag_stats(user_id):
    """Get RAG statistics for a user"""
    try:
        # Count total documents
        total_files = UploadedFile.query.filter_by(
            user_id=user_id,
            content_type='document'
        ).count()

        # Count processed documents
        processed_files = UploadedFile.query.filter_by(
            user_id=user_id,
            content_type='document',
            is_processed=True
        ).count()

        # Count total chunks
        total_chunks = db.session.query(db.func.sum(
            db.func.array_length(RAGDocument.__table__.c.embedding, 1)
        )).filter(
            RAGDocument.file_id.in_(
                db.session.query(UploadedFile.id).filter_by(
                    user_id=user_id,
                    content_type='document',
                    is_processed=True
                )
            )
        ).scalar() or 0

        # Get file type distribution
        file_types = db.session.query(
            UploadedFile.file_type,
            db.func.count(UploadedFile.id)
        ).filter_by(
            user_id=user_id,
            content_type='document'
        ).group_by(UploadedFile.file_type).all()

        return jsonify({
            'success': True,
            'stats': {
                'total_files': total_files,
                'processed_files': processed_files,
                'total_chunks': total_chunks,
                'file_types': dict(file_types)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get RAG stats',
            'message': str(e)
        }), 500