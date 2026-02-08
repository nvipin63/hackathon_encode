from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv

# Import the existing workflow
from main import app as langgraph_app, AgentState
from langchain_core.messages import HumanMessage

load_dotenv()

# Validate API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

# Create Flask app
flask_app = Flask(__name__, static_folder='static', static_url_path='')
CORS(flask_app)  # Enable CORS for local development

@flask_app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@flask_app.route('/api/analyze', methods=['POST'])
def analyze_journal():
    """
    Analyze a journal entry using the multi-agent workflow
    
    Expected JSON body:
    {
        "journal_entry": "I've been so stressed...",
        "user_profile": {
            "name": "User",
            "diet": "Low Carb",
            "allergies": []
        },
        "health_data": {
            "glucose_trend": "Normal",
            "energy_level": "Low"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'journal_entry' not in data:
            return jsonify({
                'error': 'Missing journal_entry in request body'
            }), 400
        
        # Extract data from request
        journal_entry = data.get('journal_entry', '')
        user_profile = data.get('user_profile', {
            'name': 'User',
            'diet': 'No specific diet',
            'allergies': []
        })
        health_data = data.get('health_data', {
            'glucose_trend': 'Normal',
            'energy_level': 'Normal'
        })
        
        # Create initial state for the workflow
        initial_state = {
            "messages": [HumanMessage(content=f"Here is my journal: {journal_entry}")],
            "user_profile": user_profile,
            "health_data": health_data,
            "journal_entry": journal_entry
        }
        
        # Run the LangGraph workflow
        print(f"\n{'='*60}")
        print("Processing journal entry via API...")
        print(f"{'='*60}\n")
        
        result = langgraph_app.invoke(initial_state)
        
        # Extract results
        final_message = result['messages'][-1].content if result.get('messages') else ""
        
        response = {
            'success': True,
            'results': {
                'user_profile': result.get('user_profile', user_profile),
                'detected_triggers': result.get('detected_triggers', []),
                'final_plan': result.get('final_plan', ''),
                'complete_response': final_message
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@flask_app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Nutrition Assistant API'
    }), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Nutrition Assistant Web Server")
    print("="*60)
    print(f"\n📍 Access the app at: http://localhost:5000")
    print(f"🔧 API endpoint: http://localhost:5000/api/analyze")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    flask_app.run(host='0.0.0.0', port=5000, debug=True)
