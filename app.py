from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import pandas as pd
import os
import uuid
import json
from werkzeug.utils import secure_filename

# Import Agents
from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.mapper_agent import MapperAgent
from rag.rag_engine import RAGSystem
from templates_config import get_template_spec

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

# Global RAG System (initialized per request or globally if key is constant)
# In a real app, manage this per user/session
rag_system = None

def get_rag_system(api_key=None):
    global rag_system
    # Prioritize passed key, then env, then DeepSeek
    key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if key:
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

@app.route('/test-api', methods=['POST'])
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
