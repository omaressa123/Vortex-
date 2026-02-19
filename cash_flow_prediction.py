import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

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
        api_key = 'your-default-key'  # You can modify this
        
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

# Flask app for Cash Flow Prediction
app = Flask(__name__)

@app.route('/')
def home():
    """Homepage for Cash Flow Prediction API"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cash Flow Prediction API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #007bff; text-align: center; margin-bottom: 30px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { color: #28a745; font-weight: bold; }
            .url { color: #dc3545; font-family: monospace; }
            .description { color: #666; margin-top: 5px; }
            .status { text-align: center; padding: 20px; background: #d4edda; color: #155724; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Cash Flow Prediction API</h1>
            
            <div class="status">
                ✅ Server is running successfully on port 8001
            </div>
            
            <h2>📡 Available Endpoints</h2>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="url">/financial/add</span></div>
                <div class="description">Add monthly financial data (month, income, expenses)</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/financial/predict</span></div>
                <div class="description">Get next month prediction (requires 2+ months of data)</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/financial/data</span></div>
                <div class="description">Get all historical financial data</div>
            </div>
            
            <h2>🚀 Quick Test</h2>
            <div class="endpoint">
                <div>Add sample data: <span class="url">python add_sample_data.py</span></div>
                <div class="description">Run this script to add test data and see predictions</div>
            </div>
            
            <h2>📊 Integration</h2>
            <p>This API is integrated into the main dashboard. Navigate to the main application to use the Cash Flow Prediction feature with a beautiful UI.</p>
            
            <p style="text-align: center; color: #666; margin-top: 30px;">
                <strong>🎯 Ready for financial forecasting!</strong>
            </p>
        </div>
    </body>
    </html>
    '''

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

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the Flask app
    app.run(port=8001, debug=True)
