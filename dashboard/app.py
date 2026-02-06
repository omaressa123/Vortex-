import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.eda_agent import EDAAgent
from agents.visualization_agent import VisualizationAgent
from agents.insight_agent import InsightAgent
from rag.rag_engine import RAGSystem

st.set_page_config(page_title="Intelligent Data System", layout="wide")

st.title("🤖 Intelligent Data Cleaning, Analysis & Dashboard System")

# Sidebar for Configuration
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Initialize RAG System
rag_system = None
if api_key:
    with st.spinner("Initializing RAG System..."):
        rag_system = RAGSystem(api_key=api_key)
        st.sidebar.success("RAG System Active")
else:
    st.sidebar.warning("RAG System Inactive (Missing API Key)")

# File Upload
st.header("1. Data Ingestion")
uploaded_file = st.file_uploader("Upload your data file (CSV, Excel, JSON)", type=['csv', 'xlsx', 'json'])

if uploaded_file is not None:
    # Ingestion
    ingestion = IngestionAgent()
    try:
        df = ingestion.load_file(uploaded_file)
        st.write(f"**Loaded Data:** {df.shape[0]} rows, {df.shape[1]} columns")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    # Profiling
    st.header("2. Data Profiling")
    profiler = DataProfilingAgent(df)
    profile = profiler.column_profile()
    quality_score = profiler.data_quality_score()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Data Quality Score", f"{quality_score['score']}/100")
    with col2:
        st.json(profiler.dataset_overview())
    
    with st.expander("Detailed Column Profile"):
        st.json(profile)

    # Cleaning
    st.header("3. Data Cleaning (Hybrid: Rule-based + LLM)")
    if st.button("Run Auto-Cleaning"):
        cleaner = CleaningAgent(rag_system=rag_system)
        with st.spinner("Cleaning data..."):
            cleaned_df = cleaner.clean_data(df, profile)
        
        st.success("Data Cleaned!")
        st.write(f"**Cleaned Data:** {cleaned_df.shape[0]} rows, {cleaned_df.shape[1]} columns")
        
        # Show comparison
        st.subheader("Changes Made")
        st.write(f"Rows removed: {len(df) - len(cleaned_df)}")
        st.write(f"Columns removed: {len(df.columns) - len(cleaned_df.columns)}")
        
        # Update df for next steps
        df = cleaned_df
        st.dataframe(df.head())

    # EDA & KPI
    st.header("4. EDA & KPI Extraction")
    eda = EDAAgent(df)
    
    tab1, tab2, tab3 = st.tabs(["Numeric Summary", "Categorical Summary", "KPIs"])
    
    with tab1:
        st.dataframe(pd.DataFrame(eda.numeric_summary()).T)
    
    with tab2:
        st.dataframe(pd.DataFrame(eda.categorical_summary()).T)
        
    with tab3:
        kpis = eda.generate_kpis()
        st.json(kpis)
        
        # Display KPIs as metrics
        cols = st.columns(len(kpis))
        for i, (k, v) in enumerate(kpis.items()):
            if isinstance(v, dict): # For column specific KPIs
                pass # Skip complex ones for simple metric view
            else:
                with cols[i % len(cols)]:
                    st.metric(k, v)

    # Visualization
    st.header("5. Visualizations")
    viz_agent = VisualizationAgent(df)
    
    viz_type = st.selectbox("Select Visualization Type", ["Auto-Generate", "Correlation Heatmap", "Distribution", "Time Series"])
    
    if viz_type == "Auto-Generate":
        figures = viz_agent.auto_visualize()
        for name, col, fig in figures:
            st.write(f"### {name.title()}: {col}")
            st.pyplot(fig)
            
    elif viz_type == "Correlation Heatmap":
        fig = viz_agent.plot_correlation()
        if fig:
            st.pyplot(fig)
        else:
            st.warning("Not enough numeric columns for correlation.")
            
    elif viz_type == "Distribution":
        col = st.selectbox("Select Column", viz_agent.numeric_cols)
        if col:
            fig = viz_agent.plot_numeric_distribution(col)
            st.pyplot(fig)

    # Insights
    st.header("6. Insights (LLM + RAG)")
    if rag_system:
        insight_agent = InsightAgent(df, rag_system)
        if st.button("Generate AI Insights"):
            with st.spinner("Generating insights..."):
                insights = insight_agent.generate_insights()
                for insight in insights:
                    st.write(insight)
    else:
        st.info("Enable RAG System (add API Key) to generate AI insights.")

    # Conversational RAG
    st.header("7. Conversational RAG")
    if rag_system:
        user_question = st.text_input("Ask a question about your data:")
        if user_question:
            # Schema-aware RAG answer
            schema_info = str(df.dtypes.to_dict())
            with st.spinner("Thinking..."):
                answer = rag_system.analyze_schema(schema_info + "\nSample Data:\n" + df.head().to_string(), user_question)
                st.write(answer)
                
                # Explainability check
                st.write("---")
                st.write("**Why this answer?** (Checking rules...)")
                rule_check = rag_system.retrieve_rules(user_question)
                st.write(f"Relevant Rules found: {rule_check}")
    else:
        st.info("Enable RAG System to chat with your data.")
