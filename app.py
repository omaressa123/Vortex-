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
from rag.rag_engine import DataRAGEngine

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
    """Generate financial insight without API"""
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

# Global Data RAG Engine (session-based in production)
data_rag_engine = DataRAGEngine()

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

# ===== Data RAG Conversation Endpoints =====

@app.route('/api/rag/status')
def rag_status():
    """Check RAG engine status"""
    has_data = data_rag_engine.df is not None
    return jsonify({
        'available': True,
        'has_data': has_data,
        'documents_count': len(data_rag_engine.data_documents),
        'message': 'Data loaded and ready for questions' if has_data else 'No data loaded. Upload a file to start.'
    })

@app.route('/api/rag/ask', methods=['POST'])
def rag_ask_question():
    """Ask a question about loaded data using the RAG engine"""
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    if data_rag_engine.df is None:
        return jsonify({
            'success': False,
            'error': 'No data loaded. Please upload a file first.'
        }), 400
    
    try:
        result = data_rag_engine.answer_question(question)
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'kpis': result['kpis']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error answering question: {str(e)}'
        }), 500

@app.route('/api/rag/summary')
def rag_data_summary():
    """Get data summary from RAG engine"""
    if data_rag_engine.df is None:
        return jsonify({
            'success': False,
            'error': 'No data loaded'
        }), 400
    
    summary = data_rag_engine.get_data_summary()
    return jsonify({
        'success': True,
        **summary
    })

# ===== Financial Endpoints =====

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
        
        # Generate insight (no API needed)
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

# ===== Dashboard & Upload Endpoints =====

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard_main.html')

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
    
    return jsonify({
        'success': True,
        'files': files,
        'message': f'{len(files)} files uploaded successfully'
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a single file and initialize RAG"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1]
        saved_filename = f"{file_id}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(file_path)
        
        # Load data
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Initialize RAG with the data
        rag_result = data_rag_engine.load_data(df)
        
        # Store file info in session
        session['current_file'] = {
            'filename': saved_filename,
            'original_name': file.filename,
            'file_path': file_path,
            'file_id': file_id,
            'shape': list(df.shape),
            'columns': df.columns.tolist()
        }
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': saved_filename,
            'original_name': file.filename,
            'shape': list(df.shape),
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'preview': df.head(10).to_dict('records'),
            'rag_documents': rag_result['documents_created'],
            'kpis': _serialize_kpis(rag_result.get('kpis', {}))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/process', methods=['POST'])
def process_file():
    """Process uploaded file: profiling, cleaning, and analysis"""
    data = request.json
    file_id = data.get('file_id')
    
    # Get cleaning method options from request
    cleaning_methods = data.get('cleaning_methods', {
        'handle_missing': True,
        'remove_duplicates': True,
        'knn_impute': True,
        'isolation_forest': True,
        'linear_regression_outliers': False,
        'statistical_outliers': True,
        'z_score_threshold': 3.0,
        'iqr_multiplier': 1.5,
        'isolation_contamination': 0.01
    })
    
    try:
        # Find uploaded file
        file_path = None
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            if f.startswith(file_id):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                break
        
        if not file_path:
            return jsonify({'error': 'File not found'}), 404
        
        # Load data
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # 1. Profiling
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        quality_score = profiler.data_quality_score()
        overview = profiler.dataset_overview()
        
        # 2. Cleaning (Methods-based, no API key needed)
        cleaner = CleaningAgent()
        cleaned_df = cleaner.clean_data(df, profile, methods=cleaning_methods)
        cleaning_report = cleaner.get_cleaning_report()
        
        # Save cleaned data
        cleaned_filename = f"cleaned_{os.path.basename(file_path)}"
        cleaned_path = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
        cleaned_df.to_csv(cleaned_path, index=False)
        
        # 3. Update RAG with cleaned data
        rag_result = data_rag_engine.load_data(cleaned_df)
        
        # 4. Store cleaned file info
        session['current_file'] = session.get('current_file', {})
        session['current_file']['cleaned_path'] = cleaned_path
        session['current_file']['cleaned_filename'] = cleaned_filename
        session['current_file']['cleaned_shape'] = list(cleaned_df.shape)
        
        return jsonify({
            'success': True,
            'profiling': {
                'overview': overview,
                'quality_score': quality_score,
                'column_profile': profile
            },
            'cleaning': {
                'original_shape': list(df.shape),
                'cleaned_shape': list(cleaned_df.shape),
                'report': cleaning_report,
                'cleaned_filename': cleaned_filename,
                'preview': cleaned_df.head(10).to_dict('records')
            },
            'rag': {
                'documents': rag_result['documents_created'],
                'kpis': _serialize_kpis(rag_result.get('kpis', {}))
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _serialize_kpis(kpis):
    """Convert KPIs to JSON-serializable format"""
    serialized = {}
    for key, value in kpis.items():
        if isinstance(value, dict):
            serialized[key] = {}
            for k, v in value.items():
                if hasattr(v, 'item'):  # numpy types
                    serialized[key][k] = v.item()
                else:
                    serialized[key][k] = v
        else:
            if hasattr(value, 'item'):
                serialized[key] = value.item()
            else:
                serialized[key] = value
    return serialized

# ===== Heuristic Mapping (No LLM Required) =====

def heuristic_mapping(df, template_spec):
    """Map data columns to template without using LLM"""
    mapping = {}
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    # Also check string columns that look like dates
    for col in cat_cols[:]:
        try:
            pd.to_datetime(df[col].head(5))
            date_cols.append(col)
            cat_cols.remove(col)
        except (ValueError, TypeError):
            pass
    
    kpi_count = 0
    chart_count = 0
    
    # Map KPIs from numeric columns
    for col in num_cols[:4]:
        kpi_count += 1
        mapping[f'kpi_{kpi_count}'] = {
            'column': col,
            'aggregation': 'sum'
        }
    
    # Map charts
    if date_cols and num_cols:
        chart_count += 1
        mapping[f'chart_{chart_count}'] = {
            'x': date_cols[0],
            'y': num_cols[0],
            'type': 'line'
        }
    
    if cat_cols and num_cols:
        chart_count += 1
        y_col = num_cols[1] if len(num_cols) > 1 else num_cols[0]
        mapping[f'chart_{chart_count}'] = {
            'x': cat_cols[0],
            'y': y_col,
            'type': 'bar'
        }
    
    return mapping

def generate_simple_data(df, mapping):
    """Generate dashboard data from mapping without LLM"""
    data = {}
    
    for comp_id, config in mapping.items():
        try:
            if 'aggregation' in config:
                col = config.get('column')
                agg = config.get('aggregation', 'sum')
                
                if col and col in df.columns:
                    if agg == 'sum':
                        val = df[col].sum()
                    elif agg == 'avg':
                        val = df[col].mean()
                    elif agg == 'count':
                        val = df[col].count()
                    else:
                        val = df[col].sum()
                    
                    if isinstance(val, (int, float)):
                        if val > 1000000:
                            val_str = f"{val/1000000:.1f}M"
                        elif val > 1000:
                            val_str = f"{val/1000:.1f}K"
                        else:
                            val_str = f"{val:.1f}"
                    else:
                        val_str = str(val)
                    
                    data[comp_id] = {'value': val_str, 'label': f"Total {col}"}
                    
            elif 'x' in config and 'y' in config:
                x_col = config.get('x')
                y_col = config.get('y')
                chart_type = config.get('type', 'bar')
                
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    if chart_type == 'line':
                        try:
                            df[x_col] = pd.to_datetime(df[x_col])
                            chart_df = df.groupby(x_col)[y_col].sum().reset_index().sort_values(x_col)
                            chart_df[x_col] = chart_df[x_col].dt.strftime('%Y-%m-%d')
                        except Exception:
                            chart_df = df.groupby(x_col)[y_col].sum().reset_index().head(20)
                    else:
                        chart_df = df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(10)
                    
                    data[comp_id] = {
                        'type': chart_type,
                        'labels': chart_df[x_col].tolist(),
                        'datasets': [{
                            'label': y_col,
                            'data': chart_df[y_col].tolist()
                        }]
                    }
        except Exception as e:
            print(f"Error generating data for {comp_id}: {e}")
            data[comp_id] = {'error': str(e)}
    
    return data

# Initialize database on startup
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
