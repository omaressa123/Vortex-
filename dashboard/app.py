import streamlit as st
import pandas as pd
import sys
import os
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ingestion_agent import IngestionAgent
from agents.profiling_agent import DataProfilingAgent
from agents.cleaning_agent import CleaningAgent
from agents.eda_agent import EDAAgent
from agents.visualization_agent import VisualizationAgent
from rag.rag_engine import DataRAGEngine

# Cash Flow Prediction Functions
def init_cash_flow_db():
    """Initialize cash flow database"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()
    
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

def add_financial_data(month, income, expenses):
    """Add financial data"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()
    
    profit = income - expenses
    cursor.execute('''
        INSERT OR REPLACE INTO financials (month, income, expenses, profit)
        VALUES (?, ?, ?, ?)
    ''', (month, income, expenses, profit))
    
    conn.commit()
    conn.close()

def get_financial_data():
    """Get all financial data"""
    conn = sqlite3.connect('financial_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT month, income, expenses, profit FROM financials ORDER BY month')
    data = cursor.fetchall()
    conn.close()
    
    return data

def predict_cash_flow(data):
    """Predict next month cash flow"""
    if len(data) < 2:
        return None
    
    # Get last two months
    last = data[-1]
    prev = data[-2]
    
    # Calculate growth rates
    income_growth = (last[1] - prev[1]) / prev[1] if prev[1] != 0 else 0
    expense_growth = (last[2] - prev[2]) / prev[2] if prev[2] != 0 else 0
    
    # Predict next month
    predicted_income = last[1] * (1 + income_growth)
    predicted_expenses = last[2] * (1 + expense_growth)
    predicted_profit = predicted_income - predicted_expenses
    
    return {
        'income': round(predicted_income, 2),
        'expenses': round(predicted_expenses, 2),
        'profit': round(predicted_profit, 2),
        'income_growth': round(income_growth * 100, 2),
        'expense_growth': round(expense_growth * 100, 2)
    }

def generate_financial_insight(prediction, last_month):
    """Generate financial insight"""
    income_growth = prediction.get('income_growth', 0)
    expense_growth = prediction.get('expense_growth', 0)
    
    if income_growth > expense_growth:
        return f"✅ Your business shows healthy growth with revenue increasing faster than expenses by {income_growth - expense_growth:.1f}%. Maintain this trend for improved profitability."
    elif expense_growth > income_growth:
        return f"⚠️ Expenses are growing {expense_growth - income_growth:.1f}% faster than revenue. Consider cost control measures to protect profit margins."
    else:
        return f"📊 Revenue and expenses are growing at similar rates. Focus on increasing revenue while maintaining current expense levels for better cash flow."

# Initialize database
init_cash_flow_db()

st.set_page_config(page_title="Intelligent Data System", layout="wide")


# Show Vortex logo and custom title (use st.image for clarity)
st.markdown(
    "<h1 style='color: #38bdf8; font-family: Segoe UI, Arial, sans-serif; margin-top: 18px; text-shadow: 0px 2px 4px rgba(56, 189, 248, 0.3);'>Vortex Data System</h1>",
    unsafe_allow_html=True
)

# No API keys needed - everything runs locally!
st.sidebar.header("System Status")
st.sidebar.success("Local Data Analysis Engine Active")
st.sidebar.info("No API keys required")

# Initialize local Data RAG Engine
data_rag_engine = DataRAGEngine()

# File Upload
st.header("1. Data Ingestion")
uploaded_files = st.file_uploader(
    "Upload your data files (CSV, Excel, JSON) - Multiple files supported", 
    type=['csv', 'xlsx', 'json'],
    accept_multiple_files=True,
    help="You can upload multiple files at once. They will be merged into one dataset."
)

if uploaded_files and len(uploaded_files) > 0:
    # Ingestion
    ingestion = IngestionAgent()
    try:
        all_dfs = []
        total_rows = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            df_single = ingestion.load_file(uploaded_file)
            all_dfs.append(df_single)
            total_rows += df_single.shape[0]
            
            st.write(f"**File {i+1}:** {uploaded_file.name} - {df_single.shape[0]} rows, {df_single.shape[1]} columns")
        
        # Merge all dataframes
        if len(all_dfs) > 1:
            df = pd.concat(all_dfs, ignore_index=True)
            st.success(f"Successfully merged {len(uploaded_files)} files into one dataset!")
        else:
            df = all_dfs[0]
            st.success(f" Successfully loaded {uploaded_files[0].name}!")
        
        st.write(f"**Total Dataset:** {df.shape[0]} rows, {df.shape[1]} columns")
        st.dataframe(df.head())
        
        # Show file summary
        with st.expander("📋 File Upload Summary"):
            for i, uploaded_file in enumerate(uploaded_files):
                st.write(f"**File {i+1}:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
                
    except Exception as e:
        st.error(f"Error loading files: {e}")
        st.stop()

    # MAIN TABS STRUCTURE - All sections in clickable tabs
    
    # Create main tabs for all sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📥 Data Ingestion",
        "📊 Data Profiling", 
        "🧹 Data Cleaning",
        "📈 EDA & KPIs",
        "📉 Analytics Dashboard",
        "💡 Insights",
        "💬 Conversational RAG",
        "💰 Cash Flow"
    ])
    
    # TAB 1: Data Ingestion (already shown above, can add more here)
    with tab1:
        st.subheader("Upload Your Data")
        st.write("Upload CSV, Excel, or JSON files to get started.")
        st.write(f"**Currently loaded:** {df.shape[0]} rows, {df.shape[1]} columns")
        st.dataframe(df.head(10), use_container_width=True)
    
    # TAB 2: Data Profiling
    with tab2:
        st.subheader("Data Profiling")
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
    
    # TAB 3: Data Cleaning
    with tab3:
        st.subheader("Data Cleaning (Methods-based - No API Key Needed)")
        if st.button("Run Auto-Cleaning", key="clean_btn"):
            cleaner = CleaningAgent()
            with st.spinner("Cleaning data..."):
                cleaned_df = cleaner.clean_data(df, profile)
                cleaning_report = cleaner.get_cleaning_report()
            
            st.success("Data Cleaned!")
            st.write(f"**Cleaned Data:** {cleaned_df.shape[0]} rows, {cleaned_df.shape[1]} columns")
            
            # Show comparison
            st.subheader("Changes Made")
            st.write(f"Rows removed: {len(df) - len(cleaned_df)}")
            st.write(f"Columns removed: {len(df.columns) - len(cleaned_df.columns)}")
            
            if cleaning_report and 'steps' in cleaning_report:
                with st.expander("Cleaning Report Details"):
                    for step in cleaning_report['steps']:
                        st.write(f"**{step.get('method', 'N/A')}** - Rows removed: {step.get('rows_removed', 0)}")
            
            # Update df and RAG
            df = cleaned_df
            data_rag_engine.load_data(df)
            st.dataframe(df.head())
    
    # ============================================================
    # TAB 4: EDA & KPI Extraction
    # ============================================================
    with tab4:
        st.subheader("EDA & KPI Extraction")
        eda = EDAAgent(df)
        
        # Create sub-tabs for EDA sections
        eda_tab1, eda_tab2, eda_tab3 = st.tabs(["Numeric Summary", "Categorical Summary", "KPIs"])
        
        with eda_tab1:
            st.dataframe(pd.DataFrame(eda.numeric_summary()).T)
        
        with eda_tab2:
            st.dataframe(pd.DataFrame(eda.categorical_summary()).T)
            
        with eda_tab3:
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
    
    # ============================================================
    # TAB 5: Analytics Dashboard - ALL IN ONE SQUARE/RECTANGLE
    # ============================================================
    with tab5:
        # Eye-Friendly Dark Theme Styling with soft colors
        st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
        }
        .dashboard-rectangle {
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            padding: 25px;
            border-radius: 20px;
            border: 2px solid #38bdf8;
            box-shadow: 0px 8px 32px rgba(56, 189, 248, 0.15), inset 0px 1px 0px rgba(255,255,255,0.05);
            margin-bottom: 20px;
        }
        .power-card {
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #38bdf8;
            box-shadow: 0px 4px 20px rgba(56, 189, 248, 0.1);
            margin-bottom: 20px;
        }
        /* Smooth tab transitions */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 24px;
            background-color: #1e293b;
            border-radius: 10px 10px 0px 0px;
            color: #94a3b8;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #38bdf8;
            color: #0f172a;
        }
        /* Smooth scrolling */
        .stApp {
            scroll-behavior: smooth;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="dashboard-rectangle">', unsafe_allow_html=True)
        st.markdown("""
        <h3 style='color:#38bdf8; text-align:center; font-family: Helvetica, Arial, sans-serif; font-size: 28px; font-weight: 600; letter-spacing: 0.5px;'>
            📊 Complete Analytics Dashboard
        </h3>
        """, unsafe_allow_html=True)
        
        numeric_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()

        if len(numeric_cols) > 0:
            # Column selector
            selected_column = st.selectbox("Select Numeric Column to Analyze", numeric_cols, key="dash_col_select")
            
            # KPI CARDS ROW
            st.markdown("### 📈 Key Metrics")
            kpi_cols = st.columns(min(4, len(numeric_cols)))

            for i, col in enumerate(numeric_cols[:4]):
                with kpi_cols[i]:
                    st.metric(
                        label=col,
                        value=f"{df[col].sum():,.2f}"
                    )
            
            st.markdown("---")
            
            # ALL VISUALIZATIONS IN ONE GRID (2x2)
            st.markdown("### 📊 Data Visualizations")
            
            # Create a 2x2 grid for all charts
            col_left, col_right = st.columns(2)
            
            # Top Left - Distribution Chart
            with col_left:
                st.markdown("**Distribution**")
                fig_dist = px.histogram(
                    df,
                    x=selected_column,
                    nbins=30,
                    template="plotly_dark",
                    title=f"Distribution of {selected_column}"
                )
                fig_dist.update_layout(
                    title_font_color="#38bdf8",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    height=300
                )
                st.plotly_chart(fig_dist, use_container_width=True)

            # Top Right - Box Plot
            with col_right:
                st.markdown("**Box Plot**")
                fig_box = px.box(
                    df,
                    y=selected_column,
                    template="plotly_dark",
                    title=f"Box Plot of {selected_column}"
                )
                fig_box.update_layout(
                    title_font_color="#38bdf8",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#0e1117",
                    height=300
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Bottom Left - Scatter Plot (if there's another column)
            with col_left:
                if len(numeric_cols) >= 2:
                    other_cols = [c for c in numeric_cols if c != selected_column]
                    if other_cols:
                        scatter_col = st.selectbox("Select second column for scatter", other_cols, key="scatter_col")
                        st.markdown("**Scatter Plot**")
                        fig_scatter = px.scatter(
                            df,
                            x=selected_column,
                            y=scatter_col,
                            template="plotly_dark",
                            title=f"{selected_column} vs {scatter_col}"
                        )
                        fig_scatter.update_layout(
                            title_font_color="#ff2d2d",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                            height=300
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Bottom Right - Correlation Heatmap
            with col_right:
                if len(numeric_cols) > 1:
                    st.markdown("**Correlation Heatmap**")
                    corr = df[numeric_cols].corr()

                    fig_heatmap = go.Figure(
                        data=go.Heatmap(
                            z=corr.values,
                            x=corr.columns,
                            y=corr.columns,
                            colorscale="Reds"
                        )
                    )

                    fig_heatmap.update_layout(
                        template="plotly_dark",
                        title="Correlation Matrix",
                        title_font_color="#ff2d2d",
                        paper_bgcolor="#0e1117",
                        plot_bgcolor="#0e1117",
                        height=300
                    )

                    st.plotly_chart(fig_heatmap, use_container_width=True)
                else:
                    st.info("Need at least 2 numeric columns for correlation heatmap")
            
            # Additional: Data Table
            st.markdown("---")
            st.markdown("### 📋 Data Preview")
            st.dataframe(df.head(20), use_container_width=True)
            
        else:
            st.warning("No numeric columns available for visualization.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ============================================================
    # TAB 6: Data Insights (Local Analysis)
    # ============================================================
    with tab6:
        st.subheader("Data Insights (No API Key Needed)")
        if st.button("Generate Insights", key="insight_btn"):
            with st.spinner("Analyzing data..."):
                data_rag_engine.load_data(df)
                summary = data_rag_engine.get_data_summary()
                
                st.write("**Dataset Summary:**")
                st.write(f"Rows: {summary.get('rows', 'N/A')}, Columns: {summary.get('columns', 'N/A')}")
                
                if 'kpis' in summary:
                    st.write("**KPIs:**")
                    st.json(summary['kpis'])
                
                # Basic statistical insights
                desc = df.describe().to_string()
                st.write(f"**Statistical Summary:**")
                st.text(desc)
    
    # ============================================================
    # TAB 7: Conversational Data RAG (Local)
    # ============================================================
    with tab7:
        st.subheader("Ask About Your Data (No API Key Needed)")
        st.info("This uses local data analysis - no API keys required!")
        
        # Ensure RAG has data
        if data_rag_engine.df is None:
            data_rag_engine.load_data(df)
        
        user_question = st.text_input("Ask a question about your data:", key="rag_question")
        if user_question:
            with st.spinner("Analyzing..."):
                result = data_rag_engine.answer_question(user_question)
                st.write(result['answer'])
                
                if result.get('sources'):
                    st.write("---")
                    st.write("**Sources:**")
                    for source in result['sources']:
                        st.write(f"- {source.get('title', 'Unknown')}")
    
    # ============================================================
    # TAB 8: Cash Flow Prediction
    # ============================================================
    with tab8:
        st.subheader("💰 Cash Flow Prediction")
        
        # Input section with Power BI style
        st.markdown('<div class="power-card">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            month = st.text_input("Month (e.g., 2024-01)", key="cash_month_input_tab")
        with col2:
            income = st.number_input("Income ($)", min_value=0.0, key="cash_income_input_tab")
        with col3:
            expenses = st.number_input("Expenses ($)", min_value=0.0, key="cash_expenses_input_tab")
        with col4:
            st.write("")  # Spacer
            if st.button("Add Data", key="cash_add_data_button_tab", type="primary"):
                if month and income > 0 and expenses > 0:
                    add_financial_data(month, income, expenses)
                    st.success(f"Added data for {month}")
                    st.rerun()
                else:
                    st.error("Please fill all fields with valid values")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display financial data
        financial_data = get_financial_data()
        
        if financial_data:
            # Historical data table
            st.markdown("### 📊 Historical Data")
            
            df_financial = pd.DataFrame(financial_data, columns=['Month', 'Income', 'Expenses', 'Profit'])
            df_financial['Income'] = df_financial['Income'].apply(lambda x: f"${x:,.2f}")
            df_financial['Expenses'] = df_financial['Expenses'].apply(lambda x: f"${x:,.2f}")
            df_financial['Profit'] = df_financial['Profit'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_financial, use_container_width=True)
            
            # Prediction section
            if len(financial_data) >= 2:
                prediction = predict_cash_flow(financial_data)
                
                if prediction:
                    st.markdown("### 📈 Next Month Prediction")
                    
                    # Prediction cards
                    pred_col1, pred_col2, pred_col3 = st.columns(3)
                    
                    with pred_col1:
                        st.metric(
                            "Predicted Income",
                            f"${prediction['income']:,.2f}",
                            f"{prediction['income_growth']:+.1f}%"
                        )
                    
                    with pred_col2:
                        st.metric(
                            "Predicted Expenses",
                            f"${prediction['expenses']:,.2f}",
                            f"{prediction['expense_growth']:+.1f}%"
                        )
                    
                    with pred_col3:
                        st.metric(
                            "Predicted Profit",
                            f"${prediction['profit']:,.2f}",
                            f"{((prediction['profit'] / prediction['income']) * 100):+.1f}%"
                        )
                    
                    # AI Insight
                    insight = generate_financial_insight(prediction, financial_data[-1])
                    st.info(insight)
                    
                    # Simple chart
                    st.markdown("### 📈 Financial Trend")
                    
                    # Prepare data for chart
                    chart_data = []
                    for item in financial_data:
                        chart_data.append({
                            'Month': item[0],
                            'Income': item[1],
                            'Expenses': item[2],
                            'Profit': item[3]
                        })
                    
                    # Add prediction
                    last_month = financial_data[-1][0]
                    next_month = f"Predicted {last_month}"
                    chart_data.append({
                        'Month': next_month,
                        'Income': prediction['income'],
                        'Expenses': prediction['expenses'],
                        'Profit': prediction['profit']
                    })
                    
                    df_chart = pd.DataFrame(chart_data)
                    st.line_chart(df_chart.set_index('Month')[['Income', 'Expenses', 'Profit']])
                    
            else:
                st.info("Add at least 2 months of data to enable predictions")
        else:
            st.info("No financial data available. Add your first month's data above to get started!")

else:
    # No file uploaded yet - show welcome message
    st.info("👆 Please upload a data file to get started!")
    st.markdown("""
    ### Welcome to Vortex Data System
    
    Upload a CSV, Excel, or JSON file to:
    - **Data Ingestion**: Load and preview your data
    - **Data Profiling**: Analyze data quality and structure
    - **Data Cleaning**: Clean your data with AI assistance
    - **EDA & KPIs**: Explore data and extract key metrics
    - **Analytics Dashboard**: View all visualizations in one place
    - **Insights**: Get AI-powered insights
    - **Conversational RAG**: Chat with your data
    - **Cash Flow Prediction**: Predict future cash flows
    """)
