from flask import Blueprint, jsonify, request, current_app
from models import db, Conversation, Message
from datetime import datetime
import uuid

bp = Blueprint('conversations', __name__)

@bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for a user"""
    try:
        user_id = request.args.get('user_id', 'demo-user')  # For demo purposes

        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()

        conversations_data = []
        for conv in conversations:
            # Get message count for this conversation
            message_count = Message.query.filter_by(conversation_id=conv.id).count()

            conversations_data.append({
                'id': conv.id,
                'title': conv.title,
                'model_used': conv.model_used,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': message_count
            })

        return jsonify({
            'success': True,
            'conversations': conversations_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get conversations',
            'message': str(e)
        }), 500

@bp.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        user_id = data.get('user_id', 'demo-user')  # For demo purposes
        title = data.get('title', 'New Conversation')
        model = data.get('model', 'default-model')

        conversation = Conversation(
            user_id=user_id,
            title=title,
            model_used=model
        )

        db.session.add(conversation)
        db.session.commit()

        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'model_used': conversation.model_used,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create conversation',
            'message': str(e)
        }), 500

@bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with all its messages"""
    try:
        conversation = Conversation.query.get(conversation_id)

        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404

        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()

        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'model': msg.model,
                'tokens_used': msg.tokens_used,
                'created_at': msg.created_at.isoformat()
            })

        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'model_used': conversation.model_used,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            },
            'messages': messages_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get conversation',
            'message': str(e)
        }), 500

@bp.route('/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """Update a conversation (e.g., title)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        conversation = Conversation.query.get(conversation_id)

        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404

        if 'title' in data:
            conversation.title = data['title']
            conversation.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'model_used': conversation.model_used,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update conversation',
            'message': str(e)
        }), 500

@bp.route('/conversations/<conversation_id>', methods=['DELETE'])
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

@bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
def add_message(conversation_id):
    """Add a message to a conversation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        conversation = Conversation.query.get(conversation_id)

        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404

        role = data.get('role')
        content = data.get('content')
        model = data.get('model')
        tokens_used = data.get('tokens_used')

        if not role or not content:
            return jsonify({
                'success': False,
                'error': 'Role and content are required'
            }), 400

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            tokens_used=tokens_used
        )

        db.session.add(message)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'model': message.model,
                'tokens_used': message.tokens_used,
                'created_at': message.created_at.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to add message',
            'message': str(e)
        }), 500