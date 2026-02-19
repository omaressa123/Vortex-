import os
import uuid
from flask import Flask, request, jsonify, render_template, session, redirect, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd

# Import Agents
from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.mapper_agent import MapperAgent
from rag.rag_engine import RAGSystem

# Initialize database
def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()
    
    # Create financials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT UNIQUE NOT NULL,
            income REAL NOT NULL,
            expenses REAL NOT NULL,
            profit REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def predict_next_month(data):
    """
    Predict next month's financials using simple trend analysis
    data: list of dicts sorted by month
    """
    if len(data) < 2:
        return {
            "error": "Need at least 2 months of data for prediction",
            "income": 0,
            "expenses": 0,
            "profit": 0
        }
    
    # Get last two months
    last = data[-1]
    prev = data[-2]
    
    # Calculate growth rates
    income_growth = (last["income"] - prev["income"]) / prev["income"] if prev["income"] != 0 else 0
    expense_growth = (last["expenses"] - prev["expenses"]) / prev["expenses"] if prev["expenses"] != 0 else 0
    
    # Predict next month
    predicted_income = last["income"] * (1 + income_growth)
    predicted_expenses = last["expenses"] * (1 + expense_growth)
    predicted_profit = predicted_income - predicted_expenses
    
    return {
        "income": round(predicted_income, 2),
        "expenses": round(predicted_expenses, 2),
        "profit": round(predicted_profit, 2),
        "income_growth": round(income_growth * 100, 2),
        "expense_growth": round(expense_growth * 100, 2),
        "last_month": last["month"],
        "data_points": len(data)
    }

def generate_financial_insight(prediction, last_month_data):
    """Generate AI-powered financial insight using LLM"""
    try:
        from utils.deepseek_llm import ChatDeepSeekRapidAPI
        from langchain_core.messages import HumanMessage
        
        # Get API key from session or use default
        api_key = session.get('api_key', 'your-default-key')
        
        if api_key == 'your-default-key':
            # Fallback insight if no API key
            return generate_fallback_insight(prediction, last_month_data)
        
        llm = ChatDeepSeekRapidAPI(api_key=api_key)
        
        prompt = f"""
        As a financial advisor for SMEs, analyze this data:
        
        Last month performance:
        - Income: ${last_month_data.get('income', 0):,.2f}
        - Expenses: ${last_month_data.get('expenses', 0):,.2f}
        - Profit: ${last_month_data.get('profit', 0):,.2f}
        
        Next month prediction:
        - Predicted Income: ${prediction['income']:,.2f}
        - Predicted Expenses: ${prediction['expenses']:,.2f}
        - Predicted Profit: ${prediction['profit']:,.2f}
        
        Income growth rate: {prediction.get('income_growth', 0)}%
        Expense growth rate: {prediction.get('expense_growth', 0)}%
        
        Provide a short, actionable financial insight for an SME owner (max 2 sentences).
        Focus on cash flow management and profitability.
        """
        
        result = llm._generate([HumanMessage(content=prompt)])
        insight_text = str(result).strip()
        
        return insight_text
        
    except Exception as e:
        print(f"Error generating AI insight: {e}")
        return generate_fallback_insight(prediction, last_month_data)

def generate_fallback_insight(prediction, last_month_data):
    """Generate fallback insight without AI"""
    income_growth = prediction.get('income_growth', 0)
    expense_growth = prediction.get('expense_growth', 0)
    
    if income_growth > expense_growth:
        return f"Your business shows healthy growth with revenue increasing faster than expenses by {income_growth - expense_growth:.1f}%. Maintain this trend for improved profitability."
    elif expense_growth > income_growth:
        return f"ΓÜá∩╕Å Expenses are growing {expense_growth - income_growth:.1f}% faster than revenue. Consider cost control measures to protect profit margins."
    else:
        return f"Revenue and expenses are growing at similar rates. Focus on increasing revenue while maintaining current expense levels for better cash flow."

# Simple template configuration
def get_template_spec(template_name):
    """Get template specification"""
    templates = {
        'financial': {
            'name': 'Financial Dashboard',
            'components': ['date', 'amount', 'description', 'category']
        },
        'sales': {
            'name': 'Sales Dashboard', 
            'components': ['product', 'quantity', 'price', 'total']
        },
        'hr': {
            'name': 'HR Dashboard',
            'components': ['employee', 'department', 'salary', 'position']
        }
    }
    return templates.get(template_name, {})

# Import Dashboard Blueprint
from dashboard.flask_dashboard import dashboard_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, 
     origins=["*"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True)
app.secret_key = 'super_secret_key'

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# API Key Configuration - Users can modify these
API_CONFIG = {
    'openai': {
        'key': os.environ.get('OPENAI_API_KEY', 'sk-your-openai-key-here'),
        'url': 'https://api.openai.com/v1/chat/completions'
    },
    'deepseek': {
        'key': os.environ.get('DEEPSEEK_API_KEY', 'sk-your-deepseek-key-here'),
        'url': 'https://api.deepseek.com/v1/chat/completions'
    }
}

def validate_api_key(api_key, provider='openai'):
    """Validate if API key is properly formatted"""
    if not api_key:
        return False
    
    # Basic validation based on provider
    if provider == 'openai':
        return api_key.startswith('sk-') and len(api_key) > 20
    elif provider == 'deepseek':
        return api_key.startswith('sk-') and len(api_key) > 20
    else:
        return len(api_key) > 10

def get_api_key(provider='openai', custom_key=None):
    """Get API key from configuration or custom input"""
    if custom_key:
        return custom_key
    
    config = API_CONFIG.get(provider, {})
    return config.get('key')

def get_available_providers():
    """Get list of available API providers"""
    return list(API_CONFIG.keys())

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return send_from_directory('static', 'login.html')
    
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Simple authentication (in production, use proper password hashing and database)
    if email and password:
        session['user'] = email
        return jsonify({'success': True, 'message': 'Login successful'})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return send_from_directory('static', 'signin.html')
    
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    # Simple registration (in production, use proper password hashing and database)
    if name and email and password:
        session['user'] = email
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return jsonify({'success': False, 'error': 'Missing required fields'}), 400

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/local-llm/status')
def local_llm_status():
    """Check local LLM status"""
    try:
        from utils.local_llm import check_ollama_available, get_available_models
        is_available = check_ollama_available()
        models = get_available_models() if is_available else []
        
        return jsonify({
            'available': is_available,
            'models': models,
            'message': 'Ollama is running' if is_available else 'Ollama not running. Start with: ollama serve'
        })
    except ImportError:
        return jsonify({
            'available': False,
            'models': [],
            'message': 'Local LLM not available. Install with: pip install requests'
        })

@app.route('/api/local-llm/setup')
def local_llm_setup():
    """Get setup instructions for local LLM"""
    try:
        from utils.local_llm import setup_ollama
        instructions = setup_ollama()
        return jsonify({
            'instructions': instructions
        })
    except ImportError:
        return jsonify({
            'instructions': 'Local LLM not available. Install with: pip install requests'
        })

@app.route('/api/local-llm/pull', methods=['POST'])
def pull_local_model():
    """Pull a model from Ollama"""
    try:
        from utils.local_llm import pull_model
        
        data = request.json
        model_name = data.get('model', 'llama3')
        
        if pull_model(model_name):
            return jsonify({
                'success': True,
                'message': f'Successfully pulled {model_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to pull {model_name}'
            }), 500
            
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Local LLM not available'
        }), 500

@app.route('/api/providers')
def get_api_providers():
    """Get available API providers and their configurations"""
    return jsonify({
        'providers': get_available_providers(),
        'config': {k: {
            'models': v.get('models', []),
            'base_url': v.get('base_url', ''),
            'has_key': bool(v.get('key') and v.get('key') not in ['sk-your-openai-key-here', 'your-deepseek-key-here', 'sk-ant-your-key-here', 'your-google-key-here'])
        } for k, v in API_CONFIG.items()}
    })

@app.route('/api/test-provider', methods=['POST'])
def test_api_provider():
    """Test API key for specific provider"""
    data = request.json
    provider = data.get('provider', 'openai')
    api_key = data.get('api_key')
    
    if not api_key:
        # Use configured key if no custom key provided
        api_key = get_api_key(provider)
    
    if not validate_api_key(api_key, provider):
        return jsonify({
            'success': False,
            'error': f'Invalid API key format for {provider}'
        }), 400
    
    try:
        # Test the API key
        if provider == 'openai':
            from utils.openai_llm import ChatOpenAI
            llm = ChatOpenAI(api_key=api_key)
        elif provider == 'deepseek':
            from utils.deepseek_llm import ChatDeepSeekRapidAPI
            llm = ChatDeepSeekRapidAPI(api_key=api_key)
        else:
            return jsonify({
                'success': False,
                'error': f'Provider {provider} not supported'
            }), 400
        
        # Simple test
        from langchain_core.messages import HumanMessage
        result = llm._generate([HumanMessage(content="Hello")])
        
        return jsonify({
            'success': True,
            'message': f'API key for {provider} is valid',
            'response': str(result)[:100] + '...' if len(str(result)) > 100 else str(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Register blueprint
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    # Run the Flask app
    app.run(port=8000, debug=True)
