import requests
import json

# Sample financial data for testing
sample_data = [
    {
        "month": "2024-01",
        "income": 50000,
        "expenses": 35000
    },
    {
        "month": "2024-02", 
        "income": 55000,
        "expenses": 38000
    },
    {
        "month": "2024-03",
        "income": 52000,
        "expenses": 36000
    },
    {
        "month": "2024-04",
        "income": 58000,
        "expenses": 40000
    }
]

def add_sample_data():
    """Add sample financial data to test the prediction system"""
    base_url = "http://localhost:8001"
    
    for data in sample_data:
        try:
            response = requests.post(
                f"{base_url}/financial/add",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Added data for {data['month']}: {result['message']}")
            else:
                print(f"❌ Error adding data for {data['month']}: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    # Test prediction
    try:
        response = requests.get(f"{base_url}/financial/predict")
        if response.status_code == 200:
            result = response.json()
            print("\n📈 Prediction Results:")
            print(f"Predicted Income: ${result['prediction']['income']:,.2f}")
            print(f"Predicted Expenses: ${result['prediction']['expenses']:,.2f}")
            print(f"Predicted Profit: ${result['prediction']['profit']:,.2f}")
            print(f"Income Growth: {result['prediction']['income_growth']:.2f}%")
            print(f"Expense Growth: {result['prediction']['expense_growth']:.2f}%")
            print(f"\n🤖 AI Insight: {result['insight']}")
        else:
            print(f"❌ Error getting prediction: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🚀 Adding sample financial data...")
    add_sample_data()
    print("\n✅ Sample data added successfully!")
    print("💡 Now you can test the Cash Flow Prediction feature in the dashboard!")
