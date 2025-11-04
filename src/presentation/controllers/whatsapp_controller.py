from flask import request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from src.application.services.chat_service import ChatService


class WhatsAppController:
    """Controller for WhatsApp endpoints"""
    
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        self.whatsapp_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.whatsapp_phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        self.whatsapp_api_url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_number_id}/messages"
    
    def webhook_meta(self):
        """Handle WhatsApp Business API webhook (Meta)"""
        if request.method == 'GET':
            return self._verify_webhook()
        elif request.method == 'POST':
            return self._handle_meta_message()
    
    def _verify_webhook(self):
        """Verify webhook for Meta"""
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == self.verify_token:
            print("Webhook verified successfully!")
            return challenge, 200
        else:
            return 'Forbidden', 403
    
    def _handle_meta_message(self):
        """Handle incoming messages from Meta WhatsApp API"""
        data = request.get_json()
        print(f"Incoming webhook: {data}")
        
        try:
            if data.get('object') == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        
                        if 'messages' in value:
                            for message in value['messages']:
                                from_number = message.get('from')
                                message_type = message.get('type')
                                
                                if message_type == 'text':
                                    incoming_msg = message.get('text', {}).get('body', '')
                                    
                                    # Process message through service
                                    response_text = self.chat_service.process_message(
                                        phone_number=from_number,
                                        message_text=incoming_msg,
                                        channel='whatsapp',
                                        language=os.getenv('DEFAULT_LANGUAGE', 'es')
                                    )
                                    
                                    # Send response
                                    self._send_whatsapp_message(from_number, response_text)
            
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    def _send_whatsapp_message(self, phone_number: str, message: str):
        """Send message via WhatsApp Business API"""
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(self.whatsapp_api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return None
    
    def webhook_twilio(self):
        """Handle WhatsApp messages via Twilio API"""
        try:
            incoming_msg = request.values.get('Body', '').strip()
            from_number = request.values.get('From', '')
            message_sid = request.values.get('MessageSid', '')
            language = request.values.get('Language', os.getenv('DEFAULT_LANGUAGE', 'es'))
            
            print(f"Twilio WhatsApp message from {from_number}: {incoming_msg}")
            
            # Validate inputs
            if not incoming_msg or not from_number:
                print("Error: Missing required fields (Body or From)")
                resp = MessagingResponse()
                resp.message("Error: Invalid request")
                return str(resp), 200, {'Content-Type': 'text/xml'}
            
            # Process message through service with error handling
            try:
                response_text = self.chat_service.process_message(
                    phone_number=from_number[-10:],
                    message_text=incoming_msg,
                    channel='whatsapp_twilio',
                    language=language,
                    metadata={'message_sid': message_sid}
                )
            except Exception as process_error:
                print(f"Error processing message: {str(process_error)}")
                # Return user-friendly error message
                error_messages = {
                    'es': 'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo en unos momentos.',
                    'en': 'Sorry, an error occurred while processing your message. Please try again in a few moments.',
                    'pt': 'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente em alguns instantes.'
                }
                response_text = error_messages.get(language, error_messages['es'])
            
            # Create TwiML response
            resp = MessagingResponse()
            resp.message(response_text)
            
            return str(resp), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            # Catch-all error handler
            print(f"Critical error in webhook_twilio: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Return minimal valid TwiML response
            resp = MessagingResponse()
            resp.message("Service temporarily unavailable. Please try again later.")
            return str(resp), 200, {'Content-Type': 'text/xml'}
