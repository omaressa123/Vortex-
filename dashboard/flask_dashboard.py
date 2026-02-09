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
from agents.insight_agent import InsightAgent
from rag.rag_engine import RAGSystem

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

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
        
        # Store file info in session
        session['current_file'] = {
            'filename': filename,
            'file_path': file_path,
            'shape': df.shape,
            'columns': df.columns.tolist()
        }
        
        return jsonify({
            'success': True,
            'data_preview': df.head().to_dict('records'),
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict()
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
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        quality_score = profiler.data_quality_score()
        
        return jsonify({
            'success': True,
            'profile': profile,
            'quality_score': quality_score,
            'overview': profiler.dataset_overview()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error profiling data: {str(e)}'}), 500

@dashboard_bp.route('/clean-data', methods=['POST'])
def clean_data():
    """Clean data using hybrid approach"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'current_file' not in session:
        return jsonify({'error': 'No file loaded'}), 400
    
    try:
        api_key = request.json.get('api_key')
        file_path = session['current_file']['file_path']
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Get profile first
        profiler = DataProfilingAgent(df)
        profile = profiler.column_profile()
        
        # Initialize RAG if API key provided
        rag_system = None
        if api_key:
            rag_system = RAGSystem(api_key=api_key)
        
        # Clean data
        cleaner = CleaningAgent(rag_system=rag_system)
        cleaned_df = cleaner.clean_data(df, profile)
        
        # Save cleaned data
        cleaned_filename = f"cleaned_{session['current_file']['filename']}"
        cleaned_path = os.path.join('uploads', cleaned_filename)
        cleaned_df.to_csv(cleaned_path, index=False)
        
        # Update session
        session['current_file']['cleaned_filename'] = cleaned_filename
        session['current_file']['cleaned_path'] = cleaned_path
        session['current_file']['cleaned_shape'] = cleaned_df.shape
        
        return jsonify({
            'success': True,
            'cleaned_data_preview': cleaned_df.head().to_dict('records'),
            'original_shape': df.shape,
            'cleaned_shape': cleaned_df.shape,
            'rows_removed': len(df) - len(cleaned_df),
            'columns_removed': len(df.columns) - len(cleaned_df.columns),
            'cleaned_filename': cleaned_filename
        })
        
    except Exception as e:
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
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        eda = EDAAgent(df)
        
        return jsonify({
            'success': True,
            'numeric_summary': eda.numeric_summary(),
            'categorical_summary': eda.categorical_summary(),
            'kpis': eda.generate_kpis()
        })
        
    except Exception as e:
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
        
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        viz_agent = VisualizationAgent(df)
        
        if viz_type == 'auto':
            figures = viz_agent.auto_visualize()
            return jsonify({'success': True, 'figures': figures})
        elif viz_type == 'correlation':
            fig = viz_agent.plot_correlation()
            return jsonify({'success': True, 'figure': fig})
        elif viz_type == 'distribution' and column:
            fig = viz_agent.plot_numeric_distribution(column)
            return jsonify({'success': True, 'figure': fig})
        elif viz_type == 'time_series' and column:
            fig = viz_agent.plot_time_series(column)
            return jsonify({'success': True, 'figure': fig})
        else:
            return jsonify({'error': 'Invalid visualization type or missing column'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error generating visualization: {str(e)}'}), 500

@dashboard_bp.route('/generate-insights', methods=['POST'])
def generate_insights():
    """Generate AI insights using Local RAG"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    local_model = data.get('local_model', 'llama3')
    
    try:
        file_path = session['current_file'].get('cleaned_path') or session['current_file']['file_path']
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Use local LLM - NO API KEY NEEDED!
        rag_system = RAGSystem(use_local=True, local_model=local_model)
        
        if not rag_system or not rag_system.llm:
            return jsonify({'error': 'Failed to initialize local RAG system. Make sure Ollama is running.'}), 500
        
        # Generate insights
        insight_agent = InsightAgent(df, rag_system)
        insights = insight_agent.generate_insights()
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating insights: {str(e)}'}), 500

@dashboard_bp.route('/ask-question', methods=['POST'])
def ask_question():
    """Answer questions about data using conversational Local RAG"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    local_model = data.get('local_model', 'llama3')
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question required'}), 400
    
    try:
        file_path = session['current_file'].get('cleaned_path') or session['current_file']['file_path']
        ingestion = IngestionAgent()
        df = ingestion.load_file(file_path)
        
        # Use local LLM - NO API KEY NEEDED!
        rag_system = RAGSystem(use_local=True, local_model=local_model)
        
        if not rag_system or not rag_system.llm:
            return jsonify({'error': 'Failed to initialize local RAG system. Make sure Ollama is running.'}), 500
        
        # Get schema information and sample data
        schema_info = str(df.dtypes.to_dict())
        sample_data = df.head().to_string()
        
        # Generate answer
        answer = rag_system.analyze_schema(
            schema_info + "\nSample Data:\n" + sample_data, 
            question
        )
        
        # Get relevant rules
        rules = rag_system.retrieve_rules(question)
        
        return jsonify({
            'success': True,
            'answer': answer,
            'relevant_rules': rules
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500
