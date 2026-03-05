import os
import logging
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Load environment variables
load_dotenv()

# Configure logging - FIX #1: Define logger at module level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
TIER4_URL = os.getenv('TIER4_URL', 'https://seekreap-tier4-tif2gmgi4q-uc.a.run.app')

def get_db():
    return psycopg2.connect(DATABASE_URL)

# FIX #4: Single health endpoint (remove duplicate)
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logger.info("Health check called")
    return jsonify({
        'status': 'healthy',
        'tier': 5,
        'timestamp': datetime.now().isoformat()
    }), 200

# FIX #1 & #5: Forward endpoint with proper logger
@app.route('/api/forward/health', methods=['GET'])
def forward_health():
    """Forward health check to Tier-4 Orchestrator"""
    logger.info(f"Forwarding health check to Tier-4: {TIER4_URL}")
    
    try:
        response = requests.get(f"{TIER4_URL}/health", timeout=5)
        
        # Try to parse JSON response, fallback to text
        try:
            response_data = response.json()
        except:
            response_data = response.text
            
        return jsonify({
            "status": "connected",
            "tier": 5,
            "tier4_status": response.status_code,
            "tier4_response": response_data
        }), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error("Timeout connecting to Tier-4")
        return jsonify({"error": "Connection to Tier-4 timed out"}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to Tier-4")
        return jsonify({"error": "Could not connect to Tier-4"}), 503
    except Exception as e:
        logger.error(f"Error connecting to Tier-4: {str(e)}")
        return jsonify({"error": str(e)}), 500

# FIX #2: Submissions endpoint - POST method
@app.route('/api/submissions', methods=['POST'])
def create_submission():
    """Create a new content submission"""
    try:
        data = request.json
        logger.info(f"Received submission: {data}")
        
        creator_id = data.get('creator_id')
        title = data.get('title')
        content_type = data.get('content_type')
        content_url = data.get('content_url')
        
        if not all([creator_id, title, content_type, content_url]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Mock successful submission for now
        return jsonify({
            "id": str(uuid.uuid4()),
            "status": "pending",
            "message": "Submission received",
            "creator_id": creator_id,
            "timestamp": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating submission: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Upload endpoint (from original)
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        # Simplified upload logic
        return jsonify({"status": "success", "message": "Upload received"}), 200
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Tasks endpoint (from original)
@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.json
        logger.info(f"Task created: {data}")
        task_id = str(uuid.uuid4())
        return jsonify({"status": "success", "task_id": task_id}), 201
    except Exception as e:
        logger.error(f"Task creation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Tier-5 Backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
