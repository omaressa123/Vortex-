from flask import Blueprint, render_template, request, jsonify, session
import pandas as pd
import json
import os
from werkzeug.utils import secure_filename

# Add parent directory to path to allow imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.eda_agent import EDAAgent
from agents.visualization_agent import VisualizationAgent
from rag.rag_engine import DataRAGEngine

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Dashboard-specific RAG engine instance
_dashboard_rag = DataRAGEngine()

@dashboard_bp.route('/')
def dashboard_home():
    """Main dashboard page with data analysis capabilities"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    return render_template('dashboard_main.html')

@dashboard_bp.route('/upload-data', methods=['POST'])
def upload_data():
    """Handle data upload for dashboard analysis"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        # Load and analyze data
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Initialize RAG with data
        rag_result = _dashboard_rag.load_data(df)
        
        # Store file info in session
        session['current_file'] = {
            'filename': filename,
            'file_path': file_path,
            'shape': list(df.shape),
            'columns': df.columns.tolist()
        }
        
        return jsonify({
            'success': True,
            'data_preview': df.head().to_dict('records'),
            'shape': list(df.shape),
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'rag_documents': rag_result['documents_created']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@dashboard_bp.route('/profile-data', methods=['POST'])
def profile_data():
    """Generate data profile"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'current_file' not in session:
        return jsonify({'error': 'No file loaded'}), 400
    
    try:
        file_path = session['current_file']['file_path']
        print(f"🔍 Profiling file: {file_path}")
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        print(f"📊 Data loaded: {df.shape}")
        
        profiler = DataProfilingAgent(df)
        print("🔍 Generating profile...")
        profile = profiler.column_profile()
        print("🔍 Calculating quality score...")
        quality_score = profiler.data_quality_score()
        print("🔍 Getting overview...")
        overview = profiler.dataset_overview()
        
        print(f"✅ Profile generated successfully")
        
        return jsonify({
            'success': True,
            'profile': profile,
            'quality_score': quality_score,
            'overview': overview
        })
        
    except Exception as e:
        print(f"❌ Error profiling data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error profiling data: {str(e)}'}), 500

@dashboard_bp.route('/clean-data', methods=['POST'])
def clean_data():
    """Clean data using methods-based approach"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'current_file' not in session:
        return jsonify({'error': 'No file loaded'}), 400
    
    try:
        file_path = session['current_file']['file_path']
        
        # Get cleaning method options from request
        data = request.json or {}
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
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Get profile first
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        
        # Clean data 
        cleaner = CleaningAgent()
        cleaned_df = cleaner.clean_data(df, profile, methods=cleaning_methods)
        cleaning_report = cleaner.get_cleaning_report()
        
        # Save cleaned data
        cleaned_filename = f"cleaned_{session['current_file']['filename']}"
        cleaned_path = os.path.join('uploads', cleaned_filename)
        cleaned_df.to_csv(cleaned_path, index=False)
        
        # Update RAG with cleaned data
        _dashboard_rag.load_data(cleaned_df)
        
        # Update session
        session['current_file']['cleaned_filename'] = cleaned_filename
        session['current_file']['cleaned_path'] = cleaned_path
        session['current_file']['cleaned_shape'] = list(cleaned_df.shape)
        
        return jsonify({
            'success': True,
            'cleaned_data_preview': cleaned_df.head().to_dict('records'),
            'original_shape': list(df.shape),
            'cleaned_shape': list(cleaned_df.shape),
            'rows_removed': len(df) - len(cleaned_df),
            'columns_removed': len(df.columns) - len(cleaned_df.columns),
            'cleaned_filename': cleaned_filename,
            'cleaning_report': cleaning_report
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error cleaning data: {str(e)}'}), 500

@dashboard_bp.route('/generate-eda', methods=['POST'])
def generate_eda():
    """Generate Exploratory Data Analysis"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'current_file' not in session:
        return jsonify({'error': 'No file loaded'}), 400
    
    try:
        file_path = session['current_file'].get('cleaned_path') or session['current_file']['file_path']
        print(f"🔍 EDA for file: {file_path}")
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        eda = EDAAgent(df)
        numeric_summary = eda.numeric_summary()
        categorical_summary = eda.categorical_summary()
        kpis = eda.generate_kpis()
        
        return jsonify({
            'success': True,
            'numeric_summary': numeric_summary,
            'categorical_summary': categorical_summary,
            'kpis': kpis
        })
        
    except Exception as e:
        print(f"❌ Error generating EDA: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating EDA: {str(e)}'}), 500

@dashboard_bp.route('/generate-visualization', methods=['POST'])
def generate_visualization():
    """Generate data visualizations"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'current_file' not in session:
        return jsonify({'error': 'No file loaded'}), 400
    
    try:
        viz_type = request.json.get('viz_type', 'auto')
        column = request.json.get('column')
        file_path = session['current_file'].get('cleaned_path') or session['current_file']['file_path']
        
        print(f"🔍 Generating {viz_type} visualization for column: {column}")
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        viz_agent = VisualizationAgent(df)
        
        if viz_type == 'auto':
            figures = viz_agent.auto_visualize()
            # Convert tuples to dicts for frontend compatibility
            figures_dict = [
                {'type': t, 'name': n, 'img': img} for (t, n, img) in figures
            ]
            print(f"✅ Auto visualization generated: {len(figures_dict) if figures_dict else 0} figures")
            return jsonify({'success': True, 'figures': figures_dict})
        elif viz_type == 'correlation':
            fig = viz_agent.plot_correlation()
            print(f"✅ Correlation plot generated")
            return jsonify({'success': True, 'figure': fig})
        elif viz_type == 'distribution' and column:
            fig = viz_agent.plot_numeric_distribution(column)
            print(f"✅ Distribution plot generated for {column}")
            return jsonify({'success': True, 'figure': fig})
        elif viz_type == 'categorical' and column:
            fig = viz_agent.plot_categorical(column)
            print(f"✅ Categorical plot generated for {column}")
            return jsonify({'success': True, 'figure': fig})
        elif viz_type == 'time_series' and column:
            date_col = request.json.get('date_column')
            if not date_col:
                return jsonify({'error': 'Date column required for time series'}), 400
            fig = viz_agent.plot_time_series(date_col, column)
            print(f"✅ Time series plot generated for {column}")
            return jsonify({'success': True, 'figure': fig})
        else:
            return jsonify({'error': 'Invalid visualization type or missing column'}), 400
        
    except Exception as e:
        print(f"❌ Error generating visualization: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error generating visualization: {str(e)}'}), 500

@dashboard_bp.route('/ask-question', methods=['POST'])
def ask_question():
    """Answer questions about data using Data RAG"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question required'}), 400
    
    try:
        # Load data if RAG doesn't have it
        if _dashboard_rag.df is None:
            if 'current_file' not in session:
                return jsonify({'error': 'No data loaded. Upload a file first.'}), 400
            
            file_path = session['current_file'].get('cleaned_path') or session['current_file']['file_path']
            ingestion = IngestionAgent()
            df = ingestion.load_file(file_path)
            _dashboard_rag.load_data(df)
        
        # Answer the question
        result = _dashboard_rag.answer_question(question)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'kpis': _serialize_kpis(result.get('kpis', {}))
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

def _serialize_kpis(kpis):
    """Convert KPIs to JSON-serializable format"""
    serialized = {}
    for key, value in kpis.items():
        if isinstance(value, dict):
            serialized[key] = {}
            for k, v in value.items():
                if hasattr(v, 'item'):
                    serialized[key][k] = v.item()
                else:
                    serialized[key][k] = v
        else:
            if hasattr(value, 'item'):
                serialized[key] = value.item()
            else:
                serialized[key] = value
    return serialized
