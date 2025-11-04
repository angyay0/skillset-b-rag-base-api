from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import hmac
import hashlib
import requests
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
from vertexai.preview.generative_models import GenerativeModel
import vertexai

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Vertex AI
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
LOCATION = os.getenv('GCP_LOCATION', 'us-central1')
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize the model
MODEL_NAME = "gemini-1.5-pro"
model = GenerativeModel(MODEL_NAME)

# WhatsApp Business API Configuration
WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Twilio Voice Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# Default language (can be configured)
DEFAULT_LANGUAGE = 'es'

# Language mapping for Twilio voices
VOICE_LANGUAGES = {
    'es': 'Polly.Lupe-Neural',  # Spanish (Latin American)
    'en': 'Polly.Joanna-Neural',  # English (US)
    'pt': 'Polly.Camila-Neural',  # Portuguese (Brazilian)
}

# Store conversation history (in-memory, consider using a database in production)
conversations = {}
call_conversations = {}

def get_vertex_ai_response(question, context=None, language=DEFAULT_LANGUAGE):
    """Get response from Vertex AI model"""
    try:
        # Add language context to the prompt
        prompt = f"""Responde en {language} de manera clara y concisa.
        Contexto: {context or 'No se proporcionó contexto específico.'}
        
        Pregunta: {question}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "Lo siento, ocurrió un error al procesar tu solicitud."

def send_whatsapp_message(phone_number, message):
    """Send message via WhatsApp Business API"""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        return None

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook for WhatsApp Business API"""
    
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Webhook verified successfully!")
            return challenge, 200
        else:
            return 'Forbidden', 403
    
    elif request.method == 'POST':
        # Handle incoming messages
        data = request.get_json()
        
        # Log incoming webhook data
        print(f"Incoming webhook: {data}")
        
        try:
            # Extract message details
            if data.get('object') == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        
                        # Check if there are messages
                        if 'messages' in value:
                            for message in value['messages']:
                                from_number = message.get('from')
                                message_type = message.get('type')
                                
                                # Handle text messages
                                if message_type == 'text':
                                    incoming_msg = message.get('text', {}).get('body', '')
                                    
                                    # Get or initialize conversation history
                                    if from_number not in conversations:
                                        conversations[from_number] = []
                                    
                                    # Get response from Vertex AI
                                    response_text = get_vertex_ai_response(incoming_msg)
                                    
                                    # Update conversation history
                                    conversations[from_number].append({
                                        'user': incoming_msg,
                                        'assistant': response_text
                                    })
                                    
                                    # Send response via WhatsApp
                                    send_whatsapp_message(from_number, response_text)
            
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "dp-base-api"}), 200

@app.route('/voice/incoming', methods=['POST'])
def voice_incoming():
    """Handle incoming voice calls"""
    response = VoiceResponse()
    
    # Get caller information
    caller = request.values.get('From', '')
    language = request.values.get('Language', DEFAULT_LANGUAGE)
    
    # Initialize call conversation
    if caller not in call_conversations:
        call_conversations[caller] = []
    
    # Welcome message
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
        voice=VOICE_LANGUAGES.get(language, VOICE_LANGUAGES['es']),
        language=f'{language}-MX' if language == 'es' else f'{language}-US'
    )
    
    response.append(gather)
    
    # If no input, redirect to the same endpoint
    response.redirect('/voice/incoming')
    
    return str(response)

@app.route('/voice/process', methods=['POST'])
def voice_process():
    """Process speech input and generate response"""
    response = VoiceResponse()
    
    # Get the transcribed speech
    speech_result = request.values.get('SpeechResult', '')
    caller = request.values.get('From', '')
    language = request.values.get('Language', DEFAULT_LANGUAGE)
    
    if not speech_result:
        # No speech detected
        no_input_message = {
            'es': 'No escuché nada. Por favor, intenta de nuevo.',
            'en': 'I did not hear anything. Please try again.',
            'pt': 'Não ouvi nada. Por favor, tente novamente.'
        }
        response.say(
            no_input_message.get(language, no_input_message['es']),
            voice=VOICE_LANGUAGES.get(language, VOICE_LANGUAGES['es']),
            language=f'{language}-MX' if language == 'es' else f'{language}-US'
        )
        response.redirect('/voice/incoming')
        return str(response)
    
    # Get AI response
    ai_response = get_vertex_ai_response(speech_result, language=language)
    
    # Store conversation
    if caller in call_conversations:
        call_conversations[caller].append({
            'user': speech_result,
            'assistant': ai_response
        })
    
    # Speak the response
    response.say(
        ai_response,
        voice=VOICE_LANGUAGES.get(language, VOICE_LANGUAGES['es']),
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
        voice=VOICE_LANGUAGES.get(language, VOICE_LANGUAGES['es']),
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
        voice=VOICE_LANGUAGES.get(language, VOICE_LANGUAGES['es']),
        language=f'{language}-MX' if language == 'es' else f'{language}-US'
    )
    response.hangup()
    
    return str(response)

@app.route('/voice/status', methods=['POST'])
def voice_status():
    """Handle call status callbacks"""
    call_sid = request.values.get('CallSid', '')
    call_status = request.values.get('CallStatus', '')
    
    print(f"Call {call_sid} status: {call_status}")
    
    return jsonify({"status": "received"}), 200

@app.route('/whatsapp/twilio', methods=['POST'])
def whatsapp_twilio():
    """Handle WhatsApp messages via Twilio API"""
    # Get message details
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    to_number = request.values.get('To', '')
    message_sid = request.values.get('MessageSid', '')
    
    # Extract language from profile or use default
    language = request.values.get('Language', DEFAULT_LANGUAGE)
    
    # Log incoming message
    print(f"Twilio WhatsApp message from {from_number}: {incoming_msg}")
    
    # Get or initialize conversation history
    if from_number not in conversations:
        conversations[from_number] = []
    
    # Get response from Vertex AI
    response_text = get_vertex_ai_response(incoming_msg, language=language)
    
    # Update conversation history
    conversations[from_number].append({
        'user': incoming_msg,
        'assistant': response_text,
        'message_sid': message_sid
    })
    
    # Create TwiML response
    resp = MessagingResponse()
    resp.message(response_text)
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5003)))
