# Blinky Base API

A Flask-based chatbot built with **Clean Architecture** that integrates with Vertex AI, WhatsApp, and Twilio to provide answers in Spanish (configurable to other languages).

## Architecture

This project follows Clean Architecture principles with clear separation between:
- **Domain Layer**: Business entities and repository interfaces
- **Application Layer**: Business logic and use cases
- **Infrastructure Layer**: Database, AI services, external APIs
- **Presentation Layer**: Controllers and routes

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed documentation.

## Features

- Integration with Vertex AI's Gemini 2.5 Lite model
- **Dual WhatsApp Integration**:
  - Direct WhatsApp Business API (Meta)
  - Twilio WhatsApp API (alternative/sandbox)
- Voice call integration via Twilio
- Speech-to-text and text-to-speech capabilities
- Multi-language support (default: Spanish, English, Portuguese)
- Docker containerization
- Health check endpoint
- Webhook verification for Meta
- **PostgreSQL database** for persistent storage
- Database migrations with Alembic
- **User management system** with validity periods
- Access control and subscription management
- User and conversation management

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or GCP Cloud SQL)
- Docker (for containerization)
- GCP Project with Vertex AI API enabled
- Meta Business Account
- WhatsApp Business API access (via Meta Business Platform)
- Twilio Account (for voice calls)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL database:
   ```bash
   # Local PostgreSQL
   createdb blinky_db
   
   # Or use GCP Cloud SQL (see Database Setup section)
   ```
4. Copy `.env.example` to `.env` and update with your credentials
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Add users to the database:
   ```bash
   # Add a user with 30 days validity
   python scripts/add_user.py add +1234567890 --name "John Doe" --validity 30
   
   # List all users
   python scripts/add_user.py list
   ```
7. Set up authentication for Google Cloud:
   ```bash
   gcloud auth application-default login
   ```

## Running Locally

```bash
# Using the new clean architecture app
python app_new.py

# Or with gunicorn
gunicorn app_new:app --bind 0.0.0.0:5003
```

## Building with Docker

```bash
docker build -t blinky-base-api .
docker run -p 5003:5003 --env-file .env blinky-base-api
```

## Environment Variables

- `GCP_PROJECT_ID`: Your GCP Project ID
- `GCP_LOCATION`: GCP region (default: us-central1)
- `WHATSAPP_ACCESS_TOKEN`: Your WhatsApp Business API access token
- `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp phone number ID
- `WHATSAPP_VERIFY_TOKEN`: Custom token for webhook verification
- `TWILIO_ACCOUNT_SID`: Twilio Account SID (for voice calls)
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token (for voice calls)
- `DEFAULT_LANGUAGE`: Default language for responses (default: es)

## API Endpoints

### WhatsApp
- `GET /webhook`: Webhook verification endpoint for Meta (Direct WhatsApp Business API)
- `POST /webhook`: Receives WhatsApp messages from Meta (Direct WhatsApp Business API)
- `POST /whatsapp/twilio`: Receives WhatsApp messages via Twilio API

### Voice Calls
- `POST /voice/incoming`: Handles incoming voice calls
- `POST /voice/process`: Processes speech input and generates responses
- `POST /voice/status`: Receives call status callbacks

### General
- `GET /health`: Health check endpoint

## Database Setup

### Local PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or apt-get install postgresql  # Ubuntu

# Create database
createdb blinky_db

# Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost:5432/blinky_db
```

### GCP Cloud SQL (PostgreSQL)

1. **Create Cloud SQL instance**:
   ```bash
   gcloud sql instances create blinky-db \
     --database-version=POSTGRES_14 \
     --tier=db-f1-micro \
     --region=us-central1
   ```

2. **Create database**:
   ```bash
   gcloud sql databases create blinky_db --instance=blinky-db
   ```

3. **Create user**:
   ```bash
   gcloud sql users create appuser \
     --instance=blinky-db \
     --password=your-secure-password
   ```

4. **Set DATABASE_URL** for Cloud SQL:
   ```
   # For Cloud Run with Unix socket
   DATABASE_URL=postgresql://appuser:password@/blinky_db?host=/cloudsql/PROJECT_ID:REGION:blinky-db
   
   # For external connection
   DATABASE_URL=postgresql://appuser:password@INSTANCE_IP:5432/blinky_db
   ```

5. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

## Deployment

### Google Cloud Run

```bash
gcloud run deploy blinky-base-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$GCP_PROJECT_ID" \
  --set-env-vars="GCP_LOCATION=us-central1" \
  --set-env-vars="WHATSAPP_ACCESS_TOKEN=$WHATSAPP_ACCESS_TOKEN" \
  --set-env-vars="WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID" \
  --set-env-vars="WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN" \
  --set-env-vars="TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID" \
  --set-env-vars="TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN"
```

## WhatsApp Business API Setup

1. **Create a Meta Business Account** at https://business.facebook.com
2. **Set up WhatsApp Business API**:
   - Go to Meta for Developers (https://developers.facebook.com)
   - Create a new app or use an existing one
   - Add WhatsApp product to your app
3. **Get your credentials**:
   - Access Token: Found in App Dashboard -> WhatsApp -> API Setup
   - Phone Number ID: Found in the same section
   - Create a custom Verify Token (any string you choose)
4. **Configure Webhook**:
   - In WhatsApp -> Configuration
   - Set Callback URL to: `https://your-deployed-url/webhook`
   - Set Verify Token to match your `WHATSAPP_VERIFY_TOKEN`
   - Subscribe to `messages` webhook field
5. **Test the integration** by sending a message to your WhatsApp number

## Twilio WhatsApp Setup (Alternative to Direct API)

1. **Get a Twilio Account** at https://www.twilio.com
2. **Set up WhatsApp Sandbox** (for testing):
   - Go to Messaging -> Try it out -> Send a WhatsApp message
   - Follow instructions to join the sandbox
3. **Configure WhatsApp Webhook**:
   - In the WhatsApp Sandbox Settings
   - Set "WHEN A MESSAGE COMES IN" webhook to: `https://your-deployed-url/whatsapp/twilio`
   - Set HTTP method to POST
4. **For Production** (requires approval):
   - Apply for WhatsApp Business API access through Twilio
   - Configure your approved WhatsApp number with the same webhook
5. **Test the integration** by sending a WhatsApp message to your Twilio number

## Twilio Voice Setup

1. **Get a Twilio Account** at https://www.twilio.com (if not already done)
2. **Purchase a phone number**:
   - Go to Phone Numbers -> Buy a Number
   - Select a number with Voice capabilities
3. **Get your credentials**:
   - Account SID: Found in Twilio Console Dashboard
   - Auth Token: Found in the same section
4. **Configure Voice Webhook**:
   - Go to Phone Numbers -> Manage -> Active Numbers
   - Select your phone number
   - Under Voice Configuration:
     - Set "A CALL COMES IN" webhook to: `https://your-deployed-url/voice/incoming`
     - Set HTTP method to POST
   - Under Status Callback:
     - Set URL to: `https://your-deployed-url/voice/status`
5. **Test the integration** by calling your Twilio phone number

## User Management

### Access Control

Users must be registered in the database before they can use the service. Each user has:
- **Validity Period**: Default 30 days from creation
- **Language Preference**: Spanish, English, or Portuguese
- **Active Status**: Can be manually deactivated

### Managing Users

```bash
# Add a new user
python scripts/add_user.py add +1234567890 --name "John Doe" --validity 30

# List all users
python scripts/add_user.py list

# Update user validity
python scripts/add_user.py update +1234567890 --validity 60

# Deactivate a user
python scripts/add_user.py deactivate +1234567890
```

### User Messages

When a user tries to access without permission:
- **Not registered**: "Lo sentimos, no tienes acceso a este servicio. Por favor, contacta a tu administrador para obtener acceso."
- **Expired**: "Tu período de servicio ha expirado. Tu acceso venció el [date]. Por favor, contacta a tu administrador para renovar tu suscripción."

See [docs/USER_MANAGEMENT.md](docs/USER_MANAGEMENT.md) for detailed documentation.

## Supported Languages

The chatbot supports multiple languages with appropriate voice synthesis:

- **Spanish (es)**: Default language, uses Polly.Lupe-Neural voice
- **English (en)**: Uses Polly.Joanna-Neural voice
- **Portuguese (pt)**: Uses Polly.Camila-Neural voice

You can configure the default language by setting the `DEFAULT_LANGUAGE` environment variable.

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Clean architecture design and patterns
- **[USER_MANAGEMENT.md](docs/USER_MANAGEMENT.md)** - Complete user management guide
- **[USER_VALIDATION_CHANGES.md](docs/USER_VALIDATION_CHANGES.md)** - User validation system changes
- **[MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** - Migration from monolithic to clean architecture
- **[REFACTORING_SUMMARY.md](docs/REFACTORING_SUMMARY.md)** - Complete refactoring overview

## License

MIT
