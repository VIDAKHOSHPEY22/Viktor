# vikibot_api.py
import os
import sys
import time
import logging
from functools import wraps
from flask import Flask, request, jsonify
from llama_cpp import Llama
from werkzeug.serving import WSGIRequestHandler
from werkzeug.middleware.proxy_fix import ProxyFix

# ======================
# Configuration
# ======================
class Config:
    # Model configuration
    MODEL_PATH = os.path.normpath(r"E:\viktor\models\tinyllama\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    MODEL_CONFIG = {
        "n_ctx": 2048,
        "n_threads": min(6, os.cpu_count() or 1),
        "n_gpu_layers": 20 if os.environ.get('USE_GPU') else 0,
        "verbose": False
    }
    
    # Server configuration
    HOST = '0.0.0.0'
    PORT = 5000
    MAX_CONTENT_LENGTH = 16 * 1024  # 16KB max request size
    
    # Security
    API_KEYS = {
        os.getenv('API_KEY', 'default-secret-key'): 'telegram-bot'
    }

# ======================
# Initialization
# ======================
def configure_logging():
    """Configure logging with proper encoding handling"""
    class ASCIIFilter(logging.Filter):
        def filter(self, record):
            record.msg = record.msg.encode('ascii', 'ignore').decode('ascii')
            return True

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('vikibot_api.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.addFilter(ASCIIFilter())
    return logger

logger = configure_logging()

# ======================
# Flask Application
# ======================
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# ======================
# Authentication
# ======================
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if api_key in Config.API_KEYS:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid API key"}), 401
    return decorated

# ======================
# Model Loading
# ======================
def load_model():
    """Load and initialize the LLM model"""
    try:
        logger.info("Loading the LLM model...")
        start_time = time.time()
        
        if not os.path.exists(Config.MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {Config.MODEL_PATH}")
        
        llm = Llama(model_path=Config.MODEL_PATH, **Config.MODEL_CONFIG)
        
        logger.info(f"Model loaded in {time.time() - start_time:.2f} seconds")
        logger.info(f"Model context size: {Config.MODEL_CONFIG['n_ctx']} tokens")
        logger.info(f"Using {Config.MODEL_CONFIG['n_threads']} CPU threads")
        
        return llm
    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        raise

llm = load_model()

# ======================
# API Endpoints
# ======================
@app.route("/chat", methods=["POST"])
@require_api_key
def chat():
    """Main chat endpoint"""
    try:
        # Validate input
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        if "message" not in data:
            return jsonify({"error": "Message field is required"}), 400
            
        user_input = data["message"]
        if not isinstance(user_input, str) or not user_input.strip():
            return jsonify({"error": "Message must be a non-empty string"}), 400
            
        logger.info(f"Processing message: {user_input[:100]}...")
        
        # Generate response
        start_time = time.time()
        response = llm.create_chat_completion(
            messages=[{"role": "user", "content": user_input}],
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>", "[INST]", "[/INST]"],
        )
        processing_time = time.time() - start_time
        
        output = response["choices"][0]["message"]["content"].strip()
        tokens_used = response["usage"]["total_tokens"]
        
        logger.info(f"Generated response in {processing_time:.2f}s ({tokens_used} tokens)")
        
        return jsonify({
            "response": output,
            "processing_time": processing_time,
            "tokens_used": tokens_used
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": "tinyllama-1.1b-chat",
        "context_size": Config.MODEL_CONFIG["n_ctx"],
        "uptime": time.time() - app.start_time
    })

@app.route("/")
def home():
    """Homepage with API documentation"""
    return """
    <h1>Viktor AI Boyfriend API</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><strong>POST /chat</strong> - Send messages to your AI boyfriend</li>
        <li><strong>GET /health</strong> - Check API status</li>
    </ul>
    <p>Include <code>X-API-KEY</code> header for authenticated endpoints.</p>
    """

@app.route("/favicon.ico")
def favicon():
    """Favicon endpoint"""
    return "", 204

# ======================
# Error Handlers
# ======================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "Request payload too large"}), 413

# ======================
# Main Execution
# ======================
if __name__ == "__main__":
    app.start_time = time.time()
    
    # Configure server
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    
    # Run with Werkzeug
    from werkzeug.serving import run_simple
    logger.info(f"Starting server on {Config.HOST}:{Config.PORT}")
    run_simple(
        hostname=Config.HOST,
        port=Config.PORT,
        application=app,
        threaded=True,
        use_reloader=False
    )
