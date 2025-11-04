from flask import request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from src.application.services.chat_service import ChatService


class VoiceController:
    """Controller for voice call endpoints"""
    
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        self.default_language = os.getenv('DEFAULT_LANGUAGE', 'es')
        self.voice_languages = {
            'es': 'Polly.Lupe-Neural',
            'en': 'Polly.Joanna-Neural',
            'pt': 'Polly.Camila-Neural',
        }
    
    def incoming(self):
        """Handle incoming voice calls"""
        response = VoiceResponse()
        
        caller = request.values.get('From', '')
        language = request.values.get('Language', self.default_language)
        
        welcome_message = {
            'es': '¡Hola! Soy tu asistente virtual. Por favor, dime cómo puedo ayudarte.',
            'en': 'Hello! I am your virtual assistant. Please tell me how I can help you.',
            'pt': 'Olá! Sou seu assistente virtual. Por favor, me diga como posso ajudá-lo.'
        }
        
        gather = Gather(
            input='speech',
            action='/voice/process',
            method='POST',
            language=f'{language}-MX' if language == 'es' else f'{language}-US',
            speech_timeout='auto',
            timeout=5
        )
        
        gather.say(
            welcome_message.get(language, welcome_message['es']),
            voice=self.voice_languages.get(language, self.voice_languages['es']),
            language=f'{language}-MX' if language == 'es' else f'{language}-US'
        )
        
        response.append(gather)
        response.redirect('/voice/incoming')
        
        return str(response)
    
    def process(self):
        """Process speech input and generate response"""
        response = VoiceResponse()
        
        speech_result = request.values.get('SpeechResult', '')
        caller = request.values.get('From', '')
        call_sid = request.values.get('CallSid', '')
        language = request.values.get('Language', self.default_language)
        
        if not speech_result:
            no_input_message = {
                'es': 'No escuché nada. Por favor, intenta de nuevo.',
                'en': 'I did not hear anything. Please try again.',
                'pt': 'Não ouvi nada. Por favor, tente novamente.'
            }
            response.say(
                no_input_message.get(language, no_input_message['es']),
                voice=self.voice_languages.get(language, self.voice_languages['es']),
                language=f'{language}-MX' if language == 'es' else f'{language}-US'
            )
            response.redirect('/voice/incoming')
            return str(response)
        
        # Process message through service
        ai_response = self.chat_service.process_message(
            phone_number=caller,
            message_text=speech_result,
            channel='voice',
            language=language,
            metadata={'call_sid': call_sid}
        )
        
        # Speak the response
        response.say(
            ai_response,
            voice=self.voice_languages.get(language, self.voice_languages['es']),
            language=f'{language}-MX' if language == 'es' else f'{language}-US'
        )
        
        # Ask if they need more help
        continue_message = {
            'es': '¿Hay algo más en lo que pueda ayudarte?',
            'en': 'Is there anything else I can help you with?',
            'pt': 'Há mais alguma coisa que eu possa ajudá-lo?'
        }
        
        gather = Gather(
            input='speech',
            action='/voice/process',
            method='POST',
            language=f'{language}-MX' if language == 'es' else f'{language}-US',
            speech_timeout='auto',
            timeout=5
        )
        
        gather.say(
            continue_message.get(language, continue_message['es']),
            voice=self.voice_languages.get(language, self.voice_languages['es']),
            language=f'{language}-MX' if language == 'es' else f'{language}-US'
        )
        
        response.append(gather)
        
        # If no response, end the call
        goodbye_message = {
            'es': 'Gracias por llamar. ¡Hasta luego!',
            'en': 'Thank you for calling. Goodbye!',
            'pt': 'Obrigado por ligar. Até logo!'
        }
        
        response.say(
            goodbye_message.get(language, goodbye_message['es']),
            voice=self.voice_languages.get(language, self.voice_languages['es']),
            language=f'{language}-MX' if language == 'es' else f'{language}-US'
        )
        response.hangup()
        
        return str(response)
    
    def status(self):
        """Handle call status callbacks"""
        call_sid = request.values.get('CallSid', '')
        call_status = request.values.get('CallStatus', '')
        
        print(f"Call {call_sid} status: {call_status}")
        
        return jsonify({"status": "received"}), 200
