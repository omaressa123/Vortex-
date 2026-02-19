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
from agents.insight_agent import InsightAgent
from rag.rag_engine import RAGSystem

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
        return f"Γ£à Your business shows healthy growth with revenue increasing faster than expenses by {income_growth - expense_growth:.1f}%. Maintain this trend for improved profitability."
    elif expense_growth > income_growth:
        return f"ΓÜá∩╕Å Expenses are growing {expense_growth - income_growth:.1f}% faster than revenue. Consider cost control measures to protect profit margins."
    else:
        return f"≡ƒôè Revenue and expenses are growing at similar rates. Focus on increasing revenue while maintaining current expense levels for better cash flow."

# Initialize database
init_cash_flow_db()

st.set_page_config(page_title="Intelligent Data System", layout="wide")


# Show Vortex logo and custom title (use st.image for clarity)
st.markdown("<h1 style='color: #ff2d2d; font-family: Arial, sans-serif; margin-top: 18px;'>Vortex Data System</h1>", unsafe_allow_html=True)

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


# 5. Visualizations
# ==============================

st.markdown("<h2 style='color:#ff2d2d;'>5. Analytics Dashboard</h2>", unsafe_allow_html=True)

# Dark Theme Styling
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.power-card {
    background-color: #111111;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 20px rgba(255,45,45,0.15);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# Check if df exists and has data
if 'df' in locals() and not df.empty:
    numeric_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()

    if len(numeric_cols) > 0:

        # KPI CARDS
        st.subheader("≡ƒôè Key Metrics")
        kpi_cols = st.columns(min(4, len(numeric_cols)))

        for i, col in enumerate(numeric_cols[:4]):
            with kpi_cols[i]:
                st.metric(
                    label=col,
                    value=f"{df[col].sum():,.2f}"
                )

        st.markdown("---")

        # Interactive Filters
        selected_column = st.selectbox("Select Numeric Column", numeric_cols)

        col1, col2 = st.columns(2)

        # Distribution Chart
        with col1:
            fig_dist = px.histogram(
                df,
                x=selected_column,
                nbins=30,
                template="plotly_dark",
                title=f"Distribution of {selected_column}"
            )
            fig_dist.update_layout(
                title_font_color="#ff2d2d",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117"
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        # Box Plot
        with col2:
            fig_box = px.box(
                df,
                y=selected_column,
                template="plotly_dark",
                title=f"Box Plot of {selected_column}"
            )
            fig_box.update_layout(
                title_font_color="#ff2d2d",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117"
            )
            st.plotly_chart(fig_box, use_container_width=True)

        # Correlation Heatmap
        if len(numeric_cols) > 1:
            st.subheader("≡ƒöù Correlation Heatmap")

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
                plot_bgcolor="#0e1117"
            )

            st.plotly_chart(fig_heatmap, use_container_width=True)

    else:
        st.warning("No numeric columns available for visualization.")
else:
    st.info("≡ƒôï Please upload data first to see visualizations.")

# Check if df exists before showing RAG sections
if 'df' in locals() and not df.empty:
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

    # Cash Flow Prediction Section
    st.markdown("---")
    st.markdown("<h2 style='color:#ff2d2d;'>8. ≡ƒÆ░ Cash Flow Prediction</h2>", unsafe_allow_html=True)
    
    # Input section with Power BI style
    st.markdown('<div class="power-card">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        month = st.text_input("Month (e.g., 2024-01)", key="cash_month_input")
    with col2:
        income = st.number_input("Income ($)", min_value=0.0, key="cash_income_input")
    with col3:
        expenses = st.number_input("Expenses ($)", min_value=0.0, key="cash_expenses_input")
    with col4:
        st.write("")  # Spacer
        if st.button("Add Data", key="cash_add_data_button", type="primary"):
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
        st.subheader("≡ƒôè Historical Data")
        
        df_financial = pd.DataFrame(financial_data, columns=['Month', 'Income', 'Expenses', 'Profit'])
        df_financial['Income'] = df_financial['Income'].apply(lambda x: f"${x:,.2f}")
        df_financial['Expenses'] = df_financial['Expenses'].apply(lambda x: f"${x:,.2f}")
        df_financial['Profit'] = df_financial['Profit'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(df_financial, use_container_width=True)
        
        # Prediction section
        if len(financial_data) >= 2:
            prediction = predict_cash_flow(financial_data)
            
            if prediction:
                st.subheader("≡ƒôê Next Month Prediction")
                
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
                st.subheader("≡ƒôê Financial Trend")
                
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
            st.info(" Add at least 2 months of data to enable predictions")
    else:
        st.info(" No financial data available. Add your first month's data above to get started!")

