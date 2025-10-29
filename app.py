import logging
import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import PORT, ENVIRONMENT, AZURE_OPENAI_ENDPOINT
from services.database_service import DatabaseService
from controllers.webhook_controller import handle_webhook, test_wati_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# --- Middleware for request logging ---
@app.before_request
def log_request():
    """Log incoming request"""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(f"[{timestamp}] {request.method} {request.path}")
    try:
        if request.json and len(request.json) > 0:
            logger.info(f"Request body: {request.json}")
    except:
        logger.info("Could not log request body")

# --- Error handlers ---
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Ruta no encontrada'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Ocurrió un error interno',
        'details': str(error) if ENVIRONMENT != 'production' else ''
    }), 500

# --- Routes ---
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Webhook de WATI está funcionando',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': ENVIRONMENT
    }), 200

@app.route('/webhook/wati', methods=['POST'])
def webhook():
    """Handle WATI webhook"""
    logger.info('🔔 Webhook WATI recibido')
    return handle_webhook()

@app.route('/test-connection', methods=['GET'])
def test_connection():
    """Test connection to WATI"""
    logger.info('🧪 Testing connection...')
    return test_wati_connection()

# --- Initialization ---
def initialize_app():
    """Initialize application"""
    try:
        logger.info("🚀 Inicializando aplicación...")
        
        # Connect to database
        DatabaseService.connect()
        logger.info("✅ Base de datos conectada")
        
        # Validate Azure OpenAI configuration
        if not AZURE_OPENAI_ENDPOINT:
            logger.warning("⚠️  Azure OpenAI endpoint not configured")
        
        logger.info(f"✅ Aplicación iniciada en modo: {ENVIRONMENT}")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando aplicación: {e}")
        raise

# --- Startup and shutdown ---
@app.before_first_request
def before_first_request():
    """Initialize app on first request"""
    initialize_app()

@app.teardown_appcontext
def teardown(error):
    """Cleanup on shutdown"""
    if error:
        logger.error(f"Error during teardown: {error}")
    DatabaseService.close_connection()

if __name__ == '__main__':
    try:
        logger.info(f"🚀 Iniciando servidor en puerto {PORT}...")
        logger.info(f"🔐 Usando Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT[:50]}..." if AZURE_OPENAI_ENDPOINT else "No Azure OpenAI endpoint configured")
        
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=(ENVIRONMENT == 'development'),
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("⏹️  Servidor detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor: {e}")
        raise
