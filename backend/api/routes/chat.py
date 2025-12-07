from flask import Blueprint, jsonify, request, current_app
import requests
from models import db, Conversation, Message, User
from datetime import datetime
import uuid

bp = Blueprint('chat', __name__)

@bp.route('/chat', methods=['POST'])
def create_chat():
    """Create a new chat conversation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        user_id = data.get('user_id')  # In a real app, this would come from authentication
        title = data.get('title', 'New Conversation')
        model = data.get('model', 'default-model')

        if not user_id:
            # For demo purposes, create a temporary user
            user_id = str(uuid.uuid4())

        conversation = Conversation(
            user_id=user_id,
            title=title,
            model_used=model
        )

        db.session.add(conversation)
        db.session.commit()

        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'message': 'Conversation created successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create conversation',
            'message': str(e)
        }), 500

@bp.route('/chat/<conversation_id>', methods=['POST'])
def send_message(conversation_id):
    """Send a message in a conversation and get AI response"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Handle both single message and OpenAI messages array format
        messages = data.get('messages')
        model = data.get('model', 'default-model')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 500)

        if messages:
            # OpenAI format - extract the last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content')
                    break
        else:
            # Legacy single message format
            user_message = data.get('message')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400

        # Get conversation - if it doesn't exist, create it
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            # Try to create the conversation if it doesn't exist
            conversation = Conversation(
                id=conversation_id,
                user_id=data.get('user_id', 'demo-user'),
                title='Chat Conversation',
                model_used=model
            )
            db.session.add(conversation)
            db.session.commit()

        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            role='user',
            content=user_message,
            model=model
        )
        db.session.add(user_msg)
        db.session.commit()  # persist the user message before calling Foundry

        # Get conversation history for context
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages[-10:]  # Last 10 messages for context
        ]

        # Call Foundry Local API using OpenAI-compatible endpoint
        foundry_url = current_app.config.get('FOUNDRY_BASE_URL', 'http://127.0.0.1:56831')
        from api.helpers.foundry import is_foundry_available
        ok, _ = is_foundry_available(foundry_url)
        if not ok:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Foundry Local unreachable',
                'message': 'Foundry Local is not accessible at the configured FOUNDRY_BASE_URL'
            }), 503
        headers = {'Content-Type': 'application/json'}
        api_key = current_app.config.get('FOUNDRY_API_KEY')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = {
            'model': model,
            'messages': conversation_history,
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        print('Sending payload to Foundry chat:', payload)
        try:
            response = requests.post(f'{foundry_url}/v1/chat/completions', json=payload, headers=headers, timeout=60)
        except requests.exceptions.RequestException as e:
            print(f'Error contacting Foundry chat endpoint: {e}')
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Foundry Local unreachable',
                'message': str(e)
            }), 503

        # Robustly parse JSON result - Foundry instances sometimes return non-JSON or error text
        result = None
        print(f'Foundry chat response status: {response.status_code}, text: {response.text[:1200]}')
        if response.status_code == 200:
            try:
                result = response.json()
            except Exception as parse_err:
                # Log parse error and return a helpful response
                print(f"Failed to parse Foundry response JSON: {parse_err}")
                print(f"Foundry stdout/text: {response.text[:1000]}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': 'Foundry response parse error',
                    'message': str(parse_err),
                    'foundry_text': response.text
                }), 500
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Save AI response
            ai_msg = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_response,
                model=model,
                tokens_used=result.get('usage', {}).get('total_tokens')
            )
            db.session.add(ai_msg)
            db.session.commit()

            return jsonify({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation_id,
                'usage': result.get('usage', {})
            })
        else:
            # Preserve response text for debugging
            db.session.rollback()
            print(f"Foundry returned error status {response.status_code}: {response.text[:1000]}")
            return jsonify({
                'success': False,
                'error': f'AI response failed: {response.status_code}',
                'message': response.text
            }), response.status_code

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/chat/<conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    """Get all messages in a conversation"""
    try:
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()

        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'messages': [{
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'model': msg.model,
                'tokens_used': msg.tokens_used,
                'created_at': msg.created_at.isoformat()
            } for msg in messages]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve messages',
            'message': str(e)
        }), 500

@bp.route('/chat/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages"""
    try:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404

        # Delete all messages first
        Message.query.filter_by(conversation_id=conversation_id).delete()

        # Delete conversation
        db.session.delete(conversation)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Conversation deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete conversation',
            'message': str(e)
        }), 500