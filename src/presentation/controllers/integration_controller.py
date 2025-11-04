from flask import request, jsonify
import requests
import os
import hmac
import hashlib
import json
from src.application.services.chat_service import ChatService
from src.application.services.agent_service import AgentService


class IntegrationController:
    """Controller for Slack and Teams integration endpoints"""
    
    def __init__(self, chat_service: ChatService, agent_service: AgentService):
        self.chat_service = chat_service
        self.agent_service = agent_service
    
    # ==================== SLACK ENDPOINTS ====================
    
    def slack_webhook(self, agent_id: int):
        """Handle Slack webhook events for a specific agent
        
        POST /api/integrations/<agent_id>/slack/webhook
        """
        # Verify the agent exists
        agent = self.agent_service.get_agent_by_id(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Handle Slack URL verification challenge
        if request.content_type == 'application/json':
            data = request.get_json()
            if data.get('type') == 'url_verification':
                return jsonify({'challenge': data.get('challenge')}), 200
        
        # Verify Slack signature
        if not self._verify_slack_signature(agent_id):
            return jsonify({'error': 'Invalid signature'}), 403
        
        try:
            data = request.get_json()
            event_type = data.get('type')
            
            if event_type == 'event_callback':
                event = data.get('event', {})
                return self._handle_slack_event(agent_id, agent, event)
            
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            print(f"Error processing Slack webhook: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    def _verify_slack_signature(self, agent_id: int) -> bool:
        """Verify the Slack request signature"""
        # Get signing secret from agent config or env
        signing_secret = os.getenv(f'SLACK_SIGNING_SECRET_{agent_id}') or os.getenv('SLACK_SIGNING_SECRET')
        if not signing_secret:
            return True  # Skip verification if no secret configured
        
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        if not timestamp or not signature:
            return False
        
        # Create base string
        sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
        
        # Calculate expected signature
        my_signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(my_signature, signature)
    
    def _handle_slack_event(self, agent_id: int, agent: dict, event: dict):
        """Handle Slack event callbacks"""
        event_type = event.get('type')
        
        # Ignore bot messages to prevent loops
        if event.get('bot_id') or event.get('subtype') == 'bot_message':
            return jsonify({'status': 'ignored', 'reason': 'bot_message'}), 200
        
        if event_type == 'message' or event_type == 'app_mention':
            return self._handle_slack_message(agent_id, agent, event)
        
        return jsonify({'status': 'ok'}), 200
    
    def _handle_slack_message(self, agent_id: int, agent: dict, event: dict):
        """Handle incoming Slack messages"""
        user_id = event.get('user')
        text = event.get('text', '')
        channel = event.get('channel')
        thread_ts = event.get('thread_ts') or event.get('ts')
        
        # Remove bot mention from text if present
        text = self._clean_slack_mention(text)
        
        if not text.strip():
            return jsonify({'status': 'ignored', 'reason': 'empty_message'}), 200
        
        # Get agent configuration for AI parameters
        agent_config = agent.get('configuration') or {}
        language = agent_config.get('language', 'es')
        
        # Process message through chat service
        response_text = self.chat_service.process_message(
            phone_number=f"slack_{user_id}",
            message_text=text,
            channel='slack',
            language=language,
            agent_id=agent_id,
            metadata={
                'slack_channel': channel,
                'slack_user': user_id,
                'thread_ts': thread_ts
            }
        )
        
        # Send response back to Slack
        self._send_slack_message(agent_id, channel, response_text, thread_ts)
        
        return jsonify({'status': 'success'}), 200
    
    def _clean_slack_mention(self, text: str) -> str:
        """Remove bot mention from message text"""
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    def _send_slack_message(self, agent_id: int, channel: str, message: str, thread_ts: str = None):
        """Send message to Slack channel"""
        bot_token = os.getenv(f'SLACK_BOT_TOKEN_{agent_id}') or os.getenv('SLACK_BOT_TOKEN')
        if not bot_token:
            print(f"No Slack bot token configured for agent {agent_id}")
            return None
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": channel,
            "text": message
        }
        
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending Slack message: {str(e)}")
            return None
    
    def slack_oauth_callback(self, agent_id: int):
        """Handle Slack OAuth callback for app installation
        
        GET /api/integrations/<agent_id>/slack/oauth
        """
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        client_id = os.getenv('SLACK_CLIENT_ID')
        client_secret = os.getenv('SLACK_CLIENT_SECRET')
        redirect_uri = os.getenv('SLACK_REDIRECT_URI')
        
        if not all([client_id, client_secret]):
            return jsonify({'error': 'Slack OAuth not configured'}), 500
        
        try:
            response = requests.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            data = response.json()
            
            if data.get('ok'):
                # Store tokens in agent configuration
                return jsonify({
                    'status': 'success',
                    'message': 'Slack app installed successfully',
                    'team': data.get('team', {}).get('name'),
                    'agent_id': agent_id
                }), 200
            else:
                return jsonify({'error': data.get('error', 'OAuth failed')}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== MICROSOFT TEAMS ENDPOINTS ====================
    
    def teams_webhook(self, agent_id: int):
        """Handle Microsoft Teams webhook events for a specific agent
        
        POST /api/integrations/<agent_id>/teams/webhook
        """
        # Verify the agent exists
        agent = self.agent_service.get_agent_by_id(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        try:
            data = request.get_json()
            activity_type = data.get('type')
            
            if activity_type == 'message':
                return self._handle_teams_message(agent_id, agent, data)
            elif activity_type == 'conversationUpdate':
                return self._handle_teams_conversation_update(agent_id, data)
            
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            print(f"Error processing Teams webhook: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    def _handle_teams_message(self, agent_id: int, agent: dict, activity: dict):
        """Handle incoming Teams messages"""
        # Extract message details
        from_user = activity.get('from', {})
        user_id = from_user.get('id', '')
        user_name = from_user.get('name', '')
        text = activity.get('text', '')
        conversation = activity.get('conversation', {})
        conversation_id = conversation.get('id', '')
        service_url = activity.get('serviceUrl', '')
        
        # Remove bot mention from text
        text = self._clean_teams_mention(text, activity)
        
        if not text.strip():
            return jsonify({'status': 'ignored', 'reason': 'empty_message'}), 200
        
        # Get agent configuration for AI parameters
        agent_config = agent.get('configuration') or {}
        language = agent_config.get('language', 'es')
        
        # Process message through chat service
        response_text = self.chat_service.process_message(
            phone_number=f"teams_{user_id}",
            message_text=text,
            channel='teams',
            language=language,
            agent_id=agent_id,
            metadata={
                'teams_conversation_id': conversation_id,
                'teams_user_id': user_id,
                'teams_user_name': user_name,
                'service_url': service_url
            }
        )
        
        # Send response back to Teams
        self._send_teams_message(agent_id, activity, response_text)
        
        return jsonify({'status': 'success'}), 200
    
    def _clean_teams_mention(self, text: str, activity: dict) -> str:
        """Remove bot mention from message text"""
        entities = activity.get('entities', [])
        for entity in entities:
            if entity.get('type') == 'mention':
                mentioned = entity.get('mentioned', {})
                if mentioned.get('id') == activity.get('recipient', {}).get('id'):
                    mention_text = entity.get('text', '')
                    text = text.replace(mention_text, '').strip()
        return text
    
    def _handle_teams_conversation_update(self, agent_id: int, activity: dict):
        """Handle Teams conversation updates (bot added/removed)"""
        members_added = activity.get('membersAdded', [])
        recipient_id = activity.get('recipient', {}).get('id', '')
        
        for member in members_added:
            if member.get('id') == recipient_id:
                # Bot was added to conversation
                welcome_message = "Hello! I'm DP, your AI assistant. How can I help you today?"
                self._send_teams_message(agent_id, activity, welcome_message)
                break
        
        return jsonify({'status': 'ok'}), 200
    
    def _send_teams_message(self, agent_id: int, activity: dict, message: str):
        """Send message to Teams conversation"""
        service_url = activity.get('serviceUrl', '').rstrip('/')
        conversation_id = activity.get('conversation', {}).get('id', '')
        
        if not service_url or not conversation_id:
            print(f"Missing service URL or conversation ID for Teams message")
            return None
        
        # Get bot credentials
        app_id = os.getenv(f'TEAMS_APP_ID_{agent_id}') or os.getenv('TEAMS_APP_ID')
        app_password = os.getenv(f'TEAMS_APP_PASSWORD_{agent_id}') or os.getenv('TEAMS_APP_PASSWORD')
        
        if not app_id or not app_password:
            print(f"No Teams credentials configured for agent {agent_id}")
            return None
        
        # Get access token
        token = self._get_teams_token(app_id, app_password)
        if not token:
            return None
        
        url = f"{service_url}/v3/conversations/{conversation_id}/activities"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "type": "message",
            "text": message,
            "from": activity.get('recipient'),
            "conversation": activity.get('conversation'),
            "recipient": activity.get('from')
        }
        
        # Reply to specific message if available
        if activity.get('id'):
            payload["replyToId"] = activity.get('id')
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending Teams message: {str(e)}")
            return None
    
    def _get_teams_token(self, app_id: str, app_password: str) -> str:
        """Get Microsoft Bot Framework access token"""
        token_url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        
        try:
            response = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": app_id,
                    "client_secret": app_password,
                    "scope": "https://api.botframework.com/.default"
                }
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"Error getting Teams token: {str(e)}")
            return None
    
    # ==================== STATUS ENDPOINTS ====================
    
    def get_integration_status(self, agent_id: int):
        """Get integration status for an agent
        
        GET /api/integrations/<agent_id>/status
        """
        agent = self.agent_service.get_agent_by_id(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Check Slack configuration
        slack_configured = bool(
            os.getenv(f'SLACK_BOT_TOKEN_{agent_id}') or os.getenv('SLACK_BOT_TOKEN')
        )
        
        # Check Teams configuration
        teams_configured = bool(
            (os.getenv(f'TEAMS_APP_ID_{agent_id}') or os.getenv('TEAMS_APP_ID')) and
            (os.getenv(f'TEAMS_APP_PASSWORD_{agent_id}') or os.getenv('TEAMS_APP_PASSWORD'))
        )
        
        return jsonify({
            'agent_id': agent_id,
            'agent_name': agent.get('name'),
            'integrations': {
                'slack': {
                    'configured': slack_configured,
                    'webhook_url': f"/api/integrations/{agent_id}/slack/webhook"
                },
                'teams': {
                    'configured': teams_configured,
                    'webhook_url': f"/api/integrations/{agent_id}/teams/webhook"
                }
            }
        }), 200
