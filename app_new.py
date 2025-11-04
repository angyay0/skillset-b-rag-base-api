import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from src.infrastructure.database.connection import init_db
from src.presentation.routes import register_routes

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize database
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {str(e)}")
    print("Application will continue but database operations may fail")

# Register routes
register_routes(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port)
