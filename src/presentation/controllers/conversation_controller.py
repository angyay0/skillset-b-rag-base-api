from flask import request, jsonify
from typing import Dict, Any
from src.application.services.conversation_service import ConversationService


class ConversationController:
    """Controller for conversation endpoints"""
    
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service
    
    def list_conversations(self) -> tuple[Dict[str, Any], int]:
        """
        GET /api/conversations
        List all conversations with optional channel filter
        
        Query Parameters:
            - limit (optional): Maximum number of conversations to return (default: 50)
            - channel (optional): Filter by channel (e.g., 'whatsapp', 'whatsapp_twilio')
            - offset (optional): Number of conversations to skip (default: 0)
            
        Returns:
            JSON response with conversations list
        """
        try:
            # Get query parameters
            limit = request.args.get('limit', default=50, type=int)
            channel = request.args.get('channel', type=str)
            offset = request.args.get('offset', default=0, type=int)
            
            # Get all conversations with optional channel filter
            conversations = self.conversation_service.list_all_conversations(
                channel=channel,
                limit=limit,
                offset=offset
            )
            
            return jsonify({
                'success': True,
                'data': conversations,
                'count': len(conversations)
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def get_conversation(self, conversation_id: int) -> tuple[Dict[str, Any], int]:
        """
        GET /api/conversations/:id
        Get a single conversation with messages (CASCADE)
        
        Path Parameters:
            - conversation_id: Conversation ID
            
        Query Parameters:
            - limit (optional): Maximum number of messages to return (default: 50)
            
        Returns:
            JSON response with conversation and nested messages
        """
        try:
            # Get query parameters
            limit = request.args.get('limit', default=50, type=int)
            
            # Get conversation with messages
            conversation = self.conversation_service.get_conversation_with_messages(
                conversation_id, 
                message_limit=limit
            )
            
            return jsonify({
                'success': True,
                'data': conversation
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def send_message(self, conversation_id: int) -> tuple[Dict[str, Any], int]:
        """
        POST /api/conversations/:id/messages
        Send a message to a conversation
        
        Path Parameters:
            - conversation_id: Conversation ID
            
        Request Body:
            {
                "user_message": "Message text",
                "metadata": {"key": "value"}  // optional
            }
            
        Returns:
            JSON response with created message including AI response
        """
        try:
            # Get request body
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            # Extract parameters
            user_message = data.get('user_message')
            metadata = data.get('metadata')
            
            # Validate required fields
            if not user_message:
                return jsonify({
                    'success': False,
                    'error': 'user_message is required'
                }), 400
            
            # Send message
            message = self.conversation_service.send_message(
                conversation_id=conversation_id,
                user_message=user_message,
                metadata=metadata
            )
            
            return jsonify({
                'success': True,
                'data': message
            }), 200
            
        except ValueError as e:
            error_msg = str(e)
            # Check if it's a not found error or validation error
            if 'not found' in error_msg.lower():
                status_code = 404
            else:
                status_code = 400
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), status_code
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def get_conversation_messages_handler(self, conversation_id: int) -> tuple[Dict[str, Any], int]:
        """
        GET /api/conversations/:id/messages
        Get messages from a conversation with advanced filtering
        
        Path Parameters:
            - conversation_id: Conversation ID
            
        Query Parameters:
            - limit (optional): Maximum messages to return (default: 50)
            - offset (optional): Number of messages to skip (default: 0)
            - order (optional): 'asc' or 'desc' (default: 'desc')
            - from_date (optional): ISO date string (YYYY-MM-DD or full ISO)
            - to_date (optional): ISO date string (YYYY-MM-DD or full ISO)
            
        Returns:
            JSON response with messages and pagination metadata
        """
        try:
            # Get query parameters
            limit = request.args.get('limit', default=50, type=int)
            offset = request.args.get('offset', default=0, type=int)
            order = request.args.get('order', default='desc', type=str)
            from_date = request.args.get('from_date', type=str)
            to_date = request.args.get('to_date', type=str)
            
            # Get messages with filtering
            result = self.conversation_service.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                offset=offset,
                order=order,
                from_date=from_date,
                to_date=to_date
            )
            
            return jsonify({
                'success': True,
                'data': result
            }), 200
            
        except ValueError as e:
            error_msg = str(e)
            # Check if it's a not found error or validation error
            if 'not found' in error_msg.lower():
                status_code = 404
            else:
                status_code = 400
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), status_code
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def create_conversation(self) -> tuple[Dict[str, Any], int]:
        """
        POST /api/conversations
        Create a new conversation
        
        Request Body:
            {
                "user_id": 1,
                "channel": "whatsapp"  // 'whatsapp', 'whatsapp_twilio', or 'voice'
            }
            
        Returns:
            JSON response with created conversation
        """
        try:
            # Get request body
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            # Extract parameters
            user_id = data.get('user_id')
            channel = data.get('channel')
            
            # Validate required fields
            if not user_id or not channel:
                return jsonify({
                    'success': False,
                    'error': 'user_id and channel are required'
                }), 400
            
            # Create conversation
            conversation = self.conversation_service.create_conversation(
                user_id=user_id,
                channel=channel
            )
            
            return jsonify({
                'success': True,
                'data': conversation
            }), 201
            
        except ValueError as e:
            error_msg = str(e)
            # Check if it's a not found error or validation error
            if 'not found' in error_msg.lower():
                status_code = 404
            else:
                status_code = 400
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), status_code
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def get_agent_conversations(self, agent_id: int) -> tuple[Dict[str, Any], int]:
        """
        GET /api/agents/:id/conversations
        List all conversations from all users of an agent
        
        Path Parameters:
            - agent_id: Agent ID
            
        Query Parameters:
            - limit (optional): Conversations per page (default: 20)
            - offset (optional): Skip N conversations (default: 0)
            
        Returns:
            JSON response with conversations and pagination metadata
        """
        try:
            # Get query parameters
            limit = request.args.get('limit', default=20, type=int)
            offset = request.args.get('offset', default=0, type=int)
            
            # Validate limit
            if limit < 1 or limit > 100:
                return jsonify({
                    'success': False,
                    'error': 'limit must be between 1 and 100'
                }), 400
            
            # Get agent conversations
            result = self.conversation_service.get_agent_conversations(
                agent_id=agent_id,
                limit=limit,
                offset=offset
            )
            
            return jsonify({
                'success': True,
                'data': result
            }), 200
            
        except ValueError as e:
            error_msg = str(e)
            # Check if it's a not found error
            if 'not found' in error_msg.lower():
                status_code = 404
            else:
                status_code = 400
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), status_code
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500

