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
        return f"⚠️ Expenses are growing {expense_growth - income_growth:.1f}% faster than revenue. Consider cost control measures to protect profit margins."
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

# Register blueprint
app.register_blueprint(dashboard_bp)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# API Key Configuration - Users can modify these
API_CONFIG = {
    'openai': {
        'key': os.environ.get('OPENAI_API_KEY', 'sk-your-openai-key-here'),
        'base_url': 'https://api.openai.com/v1',
        'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
    },
    'deepseek': {
        'key': os.environ.get('DEEPSEEK_API_KEY', 'your-deepseek-key-here'),
        'base_url': 'https://swift-ai.p.rapidapi.com',
        'models': ['gpt-5', 'deepseek-coder', 'deepseek-chat'],
        'rapidapi_host': 'swift-ai.p.rapidapi.com'
    },
    'anthropic': {
        'key': os.environ.get('ANTHROPIC_API_KEY', 'sk-ant-your-key-here'),
        'base_url': 'https://api.anthropic.com/v1',
        'models': ['claude-3-sonnet', 'claude-3-opus']
    },
    'google': {
        'key': os.environ.get('GOOGLE_API_KEY', 'your-google-key-here'),
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'models': ['gemini-pro', 'gemini-pro-vision']
    }
}

# Global RAG System (initialized per request or globally if key is constant)
# In a real app, manage this per user/session
rag_system = None

def get_api_key(provider='openai', custom_key=None):
    """Get API key from configuration or custom input"""
    if custom_key:
        return custom_key
    
    config = API_CONFIG.get(provider, {})
    return config.get('key')

def get_available_providers():
    """Get list of available API providers"""
    return list(API_CONFIG.keys())

def validate_api_key(api_key, provider='openai'):
    """Validate if API key is properly formatted"""
    if not api_key:
        return False
    
    # Basic validation based on provider
    if provider == 'openai':
        return api_key.startswith('sk-') and len(api_key) > 20
    elif provider == 'deepseek':
        return len(api_key) > 10  # Basic check for RapidAPI keys
    elif provider == 'anthropic':
        return api_key.startswith('sk-ant-') and len(api_key) > 20
    elif provider == 'google':
        return len(api_key) > 10  # Basic check
    else:
        return len(api_key) > 5  # Generic check

def get_rag_system(api_key=None, provider='openai', use_local=False, local_model='llama3'):
    """Initialize RAG system with configurable API key, provider, or local LLM"""
    global rag_system
    
    if use_local:
        # Use local LLM - NO API KEY NEEDED!
        if not rag_system or rag_system.api_key != 'local':
            rag_system = RAGSystem(use_local=True, local_model=local_model)
        return rag_system
    
    # Get API key from custom input, environment, or config
    key = api_key or get_api_key(provider)
    
    if key and validate_api_key(key, provider):
        # Create unique cache key based on provider and key
        cache_key = f"{provider}_{key[:10]}"
        
        if not rag_system or rag_system.api_key != key:
            rag_system = RAGSystem(api_key=key)
        return rag_system
    return None

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
        # Test with RAG system
        rag = get_rag_system(api_key, provider)
        if rag:
            return jsonify({
                'success': True,
                'provider': provider,
                'message': f'{provider.title()} API key is working'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to initialize RAG system'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/user-status')
def user_status():
    """Check user authentication status"""
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'email': session['user']
        })
    else:
        return jsonify({
            'authenticated': False
        }), 401

@app.route('/test-api-multiple', methods=['POST'])
def test_api_multiple():
    """Test API key and process multiple files"""
    if not request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 400
    
    try:
        # Test API key first
        from utils.deepseek_llm import ChatDeepSeekRapidAPI
        llm = ChatDeepSeekRapidAPI(api_key=api_key)
        
        from langchain_core.messages import HumanMessage
        result = llm._generate([HumanMessage(content="Hello, respond with 'API working'")])
        
        # Process uploaded files
        files = []
        for key in request.files:
            file = request.files[key]
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                ext = os.path.splitext(filename)[1]
                saved_filename = f"{file_id}{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(file_path)
                
                files.append({
                    'file_id': file_id,
                    'filename': saved_filename,
                    'original_name': file.filename
                })
        
        # Generate dashboard from all files (combine data)
        if files:
            from agents.ingestion_agent import IngestionAgent
            from agents.profiling_agent import ProfilingAgent
            from agents.cleaning_agent import CleaningAgent
            from agents.mapping_agent import MappingAgent
            import pandas as pd
            
            # Initialize agents
            ingestion_agent = IngestionAgent()
            profiling_agent = ProfilingAgent()
            cleaning_agent = CleaningAgent()
            mapping_agent = MappingAgent()
            
            # Process and combine all files
            all_data = []
            combined_profile = None
            
            for file_info in files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_info['filename'])
                
                try:
                    # Ingest data from each file
                    data = ingestion_agent.ingest(file_path)
                    
                    if data is not None and len(data) > 0:
                        # Add source file info to each row
                        if isinstance(data, pd.DataFrame):
                            data['source_file'] = file_info['original_name']
                            all_data.append(data)
                        else:
                            # Convert to DataFrame if not already
                            df = pd.DataFrame(data)
                            df['source_file'] = file_info['original_name']
                            all_data.append(df)
                            
                        print(f"✅ Processed {file_info['original_name']}: {len(data)} rows")
                    else:
                        print(f"⚠️ No data in {file_info['original_name']}")
                        
                except Exception as e:
                    print(f"❌ Error processing {file_info['original_name']}: {e}")
                    continue
            
            # Combine all data
            if all_data:
                try:
                    # Concatenate all DataFrames
                    combined_data = pd.concat(all_data, ignore_index=True)
                    print(f"📊 Combined data: {len(combined_data)} rows from {len(all_data)} files")
                    
                    # Profile combined data
                    combined_profile = profiling_agent.profile(combined_data)
                    
                    # Clean combined data
                    cleaned_data = cleaning_agent.clean(combined_data, combined_profile)
                    
                    # Map to dashboard format
                    dashboard_data = mapping_agent.map_to_dashboard(cleaned_data, combined_profile)
                    
                    # Add file summary info
                    dashboard_data['file_summary'] = {
                        'total_files': len(files),
                        'processed_files': len(all_data),
                        'total_rows': len(combined_data),
                        'files': [f['original_name'] for f in files]
                    }
                    
                    return jsonify({
                        'success': True,
                        'api_test': {'response': str(result)},
                        'files_processed': len(all_data),
                        'total_files': len(files),
                        'total_rows': len(combined_data),
                        'files': files,
                        'dashboard': dashboard_data
                    })
                    
                except Exception as e:
                    print(f"❌ Error combining data: {e}")
                    # Fallback to first file if combining fails
                    first_file = files[0]
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], first_file['filename'])
                    
                    data = ingestion_agent.ingest(file_path)
                    profile = profiling_agent.profile(data)
                    cleaned_data = cleaning_agent.clean(data, profile)
                    dashboard_data = mapping_agent.map_to_dashboard(cleaned_data, profile)
                    
                    return jsonify({
                        'success': True,
                        'api_test': {'response': str(result)},
                        'files_processed': 1,
                        'total_files': len(files),
                        'fallback_used': True,
                        'files': files,
                        'dashboard': dashboard_data
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No valid data found in any uploaded files'
                }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'API key test failed'
        }), 500

@app.route('/financial/add', methods=['POST'])
def add_financial_data():
    """Add monthly financial data"""
    try:
        data = request.json
        month = data.get('month')
        income = float(data.get('income', 0))
        expenses = float(data.get('expenses', 0))
        profit = income - expenses
        
        conn = sqlite3.connect('financial_data.db')
        cursor = conn.cursor()
        
        # Insert or update financial data
        cursor.execute('''
            INSERT OR REPLACE INTO financials (month, income, expenses, profit)
            VALUES (?, ?, ?, ?)
        ''', (month, income, expenses, profit))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Financial data for {month} saved successfully',
            'data': {
                'month': month,
                'income': income,
                'expenses': expenses,
                'profit': profit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/financial/predict', methods=['GET'])
def predict_cash_flow():
    """Predict next month's cash flow"""
    try:
        conn = sqlite3.connect('financial_data.db')
        cursor = conn.cursor()
        
        # Get all financial data ordered by month
        cursor.execute('SELECT month, income, expenses, profit FROM financials ORDER BY month')
        data = cursor.fetchall()
        conn.close()
        
        if len(data) < 2:
            return jsonify({
                'success': False,
                'error': 'Need at least 2 months of data for prediction',
                'data_points': len(data)
            }), 400
        
        # Convert to list of dicts
        financial_data = []
        for row in data:
            financial_data.append({
                'month': row[0],
                'income': row[1],
                'expenses': row[2],
                'profit': row[3]
            })
        
        # Get prediction
        prediction = predict_next_month(financial_data)
        
        # Generate AI insight
        last_month_data = financial_data[-1]
        insight = generate_financial_insight(prediction, last_month_data)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'insight': insight,
            'historical_data': financial_data,
            'data_points': len(financial_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/financial/data', methods=['GET'])
def get_financial_data():
    """Get all financial data"""
    try:
        conn = sqlite3.connect('financial_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT month, income, expenses, profit, created_at FROM financials ORDER BY month')
        data = cursor.fetchall()
        conn.close()
        
        financial_data = []
        for row in data:
            financial_data.append({
                'month': row[0],
                'income': row[1],
                'expenses': row[2],
                'profit': row[3],
                'created_at': row[4]
            })
        
        return jsonify({
            'success': True,
            'data': financial_data,
            'count': len(financial_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/test-api', methods=['POST'])
def test_api():
    """Test API key connectivity and proceed with dashboard generation"""
    data = request.json
    api_key = data.get('api_key')
    file_id = data.get('file_id')
    template_image = data.get('template_image')
    
    if not api_key:
        return jsonify({'error': 'API key required'}), 400
    
    try:
        # Test with DeepSeek API
        from utils.deepseek_llm import ChatDeepSeekRapidAPI
        llm = ChatDeepSeekRapidAPI(api_key=api_key)
        
        # Simple test message
        from langchain_core.messages import HumanMessage
        result = llm._generate([HumanMessage(content="Hello, respond with 'API working'")])
        
        response_text = result.generations[0].message.content
        
        # If file_id and template_image provided, proceed with dashboard generation
        if file_id and template_image:
            try:
                # Load Data
                file_path = None
                for f in os.listdir(app.config['UPLOAD_FOLDER']):
                    if f.startswith(file_id):
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                        break
                        
                if not file_path:
                    return jsonify({'success': False, 'error': 'File not found'}), 404

                # Ingestion
                ingestion = IngestionAgent()
                df = ingestion.load_file(file_path)
                
                # Initialize RAG
                rag = get_rag_system(api_key)
                
                # Profiling & Cleaning
                profiler = DataProfilingAgent(df)
                profile = profiler.column_profile()
                
                cleaner = CleaningAgent(rag_system=rag)
                cleaned_df = cleaner.clean_data(df, profile)
                
                # Get Template Spec
                template_spec = get_template_spec(os.path.basename(template_image))
                
                # AI Mapping
                if rag:
                    try:
                        mapper = MapperAgent(cleaned_df, api_key=rag.api_key)
                        mapping = mapper.map_columns(template_spec)
                        if not mapping:
                            mapping = heuristic_mapping(cleaned_df, template_spec)
                    except Exception:
                        mapping = heuristic_mapping(cleaned_df, template_spec)
                else:
                    mapping = heuristic_mapping(cleaned_df, template_spec)
                    
                # Generate Dashboard Data
                if rag:
                    try:
                        dashboard_data = mapper.generate_dashboard_data(mapping)
                    except Exception:
                        dashboard_data = generate_simple_data(cleaned_df, mapping)
                else:
                    dashboard_data = generate_simple_data(cleaned_df, mapping)
                
                return jsonify({
                    'success': True,
                    'api_test': {
                        'response': response_text,
                        'message': 'API key is working'
                    },
                    'dashboard': {
                        'status': 'success',
                        'template': template_spec,
                        'mapping': mapping,
                        'data': dashboard_data
                    }
                })
                
            except Exception as e:
                return jsonify({
                    'success': True,
                    'api_test': {
                        'response': response_text,
                        'message': 'API key is working but dashboard generation failed'
                    },
                    'error': f'Dashboard generation failed: {str(e)}'
                }), 500
        
        # Just API test without dashboard generation
        return jsonify({
            'success': True,
            'response': response_text,
            'message': 'API key is working'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'API key test failed'
        }), 500

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return send_from_directory('static', 'dashboard.html')

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Upload multiple files at once"""
    if not request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = []
    uploaded_files = []
    
    # Get all uploaded files
    for key in request.files:
        file = request.files[key]
        if file and file.filename != '':
            files.append(file)
    
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    # Process each file
    for file in files:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        # Preserve extension
        ext = os.path.splitext(filename)[1]
        saved_filename = f"{file_id}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        uploaded_files.append({
            'file_id': file_id,
            'filename': saved_filename,
            'original_name': file.filename
        })
    
    return jsonify({
        'message': f'{len(uploaded_files)} files uploaded successfully',
        'files': uploaded_files
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        # Preserve extension
        ext = os.path.splitext(filename)[1]
        saved_filename = f"{file_id}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        return jsonify({
            'message': 'File uploaded successfully', 
            'file_id': file_id,
            'filename': saved_filename
        })

@app.route('/generate-dashboard', methods=['POST'])
def generate_dashboard():
    data = request.json
    file_id = data.get('file_id')
    template_image = data.get('template_image') # e.g., "1.jpeg"
    api_key = data.get('api_key') # Optional: receive API key from frontend
    
    if not file_id or not template_image:
        return jsonify({'error': 'Missing file_id or template_image'}), 400

    # 1. Load Data
    # Find file with any extension
    file_path = None
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.startswith(file_id):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
            break
            
    if not file_path:
        return jsonify({'error': 'File not found'}), 404

    try:
        # Ingestion
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # 2. Initialize RAG
        rag = get_rag_system(api_key)
        
        # 3. Profiling & Cleaning
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        
        cleaner = CleaningAgent(rag_system=rag)
        cleaned_df = cleaner.clean_data(df, profile)
        
        # 4. Get Template Spec
        template_spec = get_template_spec(os.path.basename(template_image))
        
        # 5. AI Mapping (The "Brain")
        if rag:
            try:
                mapper = MapperAgent(cleaned_df, api_key=rag.api_key)
                mapping = mapper.map_columns(template_spec)
                if not mapping:
                    mapping = heuristic_mapping(cleaned_df, template_spec)
            except Exception:
                mapping = heuristic_mapping(cleaned_df, template_spec)
        else:
            mapping = heuristic_mapping(cleaned_df, template_spec)
            
        # 6. Generate Data for Frontend
        if rag:
            try:
                dashboard_data = mapper.generate_dashboard_data(mapping)
            except Exception:
                dashboard_data = generate_simple_data(cleaned_df, mapping)
        else:
            dashboard_data = generate_simple_data(cleaned_df, mapping)
            
        return jsonify({
            'status': 'success',
            'template': template_spec,
            'mapping': mapping,
            'data': dashboard_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def heuristic_mapping(df, template_spec):
    """
    Simple fallback if no LLM is available.
    """
    mapping = {}
    nums = df.select_dtypes(include=['number']).columns.tolist()
    cats = df.select_dtypes(include=['object', 'category']).columns.tolist()
    dates = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Try to convert object cols to date if they look like it
    if not dates:
        for col in cats:
            if 'date' in col.lower() or 'time' in col.lower():
                dates.append(col)

    for comp in template_spec['components']:
        cid = comp['id']
        ctype = comp['type']
        
        if ctype == 'kpi':
            if nums:
                mapping[cid] = {"column": nums[0], "aggregation": "sum"}
                # Rotate
                nums.append(nums.pop(0))
            else:
                mapping[cid] = {"column": None, "aggregation": "count"}
                
        elif ctype in ('line', 'line_chart'):
            if dates and nums:
                mapping[cid] = {"x": dates[0], "y": nums[0], "type": "line"}
            elif len(nums) >= 2:
                 mapping[cid] = {"x": nums[0], "y": nums[1], "type": "line"}
            else:
                mapping[cid] = None
                
        elif ctype in ('bar', 'bar_chart'):
            if cats and nums:
                mapping[cid] = {"x": cats[0], "y": nums[0], "type": "bar"}
            else:
                mapping[cid] = None
                
    return mapping

def generate_simple_data(df, mapping):
    # Re-use the logic from MapperAgent but without the class overhead for fallback
    # Actually, MapperAgent logic is pure python mostly, so we can reuse it if we instantiated it with None
    # But let's just duplicate a simple version or instantiate MapperAgent with None
    
    # We can instantiate MapperAgent with None key if we modify it to handle it
    # But let's just implement a basic version here for safety
    data = {}
    for comp_id, config in mapping.items():
        if not config:
             data[comp_id] = {"value": "N/A", "label": "No Data"}
             continue
             
        if "aggregation" in config:
             col = config["column"]
             if col and col in df.columns:
                 val = df[col].sum() if config["aggregation"] == "sum" else df[col].count()
                 data[comp_id] = {"value": str(round(val, 2)), "label": col}
             else:
                 data[comp_id] = {"value": str(len(df)), "label": "Count"}
        elif "x" in config:
             # Charts
             x = config["x"]
             y = config["y"]
             if x in df.columns and y in df.columns:
                 grp = df.groupby(x)[y].sum().head(10)
                 data[comp_id] = {
                     "type": config.get("type", "bar"),
                     "labels": grp.index.astype(str).tolist(),
                     "datasets": [{"label": y, "data": grp.values.tolist()}]
                 }
    return data

if __name__ == '__main__':
    app.run(port=8000, debug=True)
