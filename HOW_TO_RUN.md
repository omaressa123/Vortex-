# 🚀 How to Run the AI-Powered Data Cleaning & Dashboard System

## **Option 1: Flask Dashboard (Recommended)**

### **Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Run Flask App**
```bash
python app.py
```

### **Step 3: Access Dashboard**
- **Main App**: http://127.0.0.1:8000
- **Dashboard**: http://127.0.0.1:8000/dashboard/

---

## **Option 2: Streamlit Dashboard (Original)**

### **Step 1: Run Streamlit**
```bash
streamlit run dashboard/app.py
```

### **Step 2: Access Dashboard**
- **Streamlit**: http://localhost:8501

---

## **🔹 Local LLM Setup (Optional - No API Keys!)**

### **Install Ollama**
```bash
# Windows: Download from https://ollama.ai/download
# Mac: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
```

### **Start Ollama**
```bash
ollama serve
```

### **Pull Models**
```bash
ollama pull llama3          # Recommended
ollama pull mistral         # Fast
ollama pull phi-3           # Lightweight
```

### **Use in Dashboard**
1. Go to http://127.0.0.1:8000/dashboard/
2. Select "Local LLM (Ollama)"
3. Choose your model
4. No API keys needed!

---

## **🔑 Cloud API Setup (Optional)**

### **Set Environment Variables**
```bash
# OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# DeepSeek (RapidAPI)
export DEEPSEEK_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Google Gemini
export GOOGLE_API_KEY="your-key-here"
```

### **Or Copy Configuration File**
```bash
cp api_keys.env.example .env
# Edit .env with your actual API keys
```

---

## **📁 Project Structure**

```
📦 AI-Powered Data Cleaning, Analysis & Dashboard System
├── 🚀 app.py                    # Main Flask application
├── 📊 dashboard/
│   ├── 📈 flask_dashboard.py     # Flask dashboard blueprint
│   └── 📋 app.py               # Original Streamlit app
├── 🧠 rag/
│   └── 🤖 rag_engine.py         # RAG system with local/cloud support
├── 🔧 utils/
│   ├── 🦙 local_llm.py          # Local LLM (Ollama) integration
│   └── 🌐 deepseek_llm.py       # DeepSeek API integration
├── 🎨 templates/
│   └── 📄 dashboard_main.html   # Dashboard UI
├── 💻 static/
│   ├── 🎯 dashboard_main.js     # Dashboard JavaScript
│   └── 🎨 style.css            # Styling
└── 📚 rag/knowledge_base/       # RAG knowledge base
```

---

## **🎯 Features Available**

### **Flask Dashboard Features**
- ✅ **Data Upload & Preview**
- ✅ **Data Profiling & Quality Analysis**
- ✅ **Data Cleaning with AI**
- ✅ **Exploratory Data Analysis (EDA)**
- ✅ **Data Visualization**
- ✅ **AI-Powered Insights**
- ✅ **Conversational RAG Q&A**
- ✅ **Multiple Dashboard Templates**
- ✅ **Local LLM Support (Ollama)**
- ✅ **Cloud API Support (OpenAI, DeepSeek, Anthropic, Google)**
- ✅ **User Authentication**

### **Local LLM Benefits**
- 🔒 **100% Privacy** - Data never leaves your computer
- 💰 **No Costs** - No API usage fees
- 🚀 **Fast Response** - No network latency
- 🎛️ **Full Control** - Your models, your rules

### **Cloud API Benefits**
- 🌐 **More Powerful Models**
- 📈 **Higher Accuracy**
- 🔧 **Easy Setup** - Just add API key

---

## **🐛 Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Install missing packages
pip install langchain-community sentence-transformers requests
```

#### **2. Local LLM Not Working**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

#### **3. Port Already in Use**
```bash
# Kill existing process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
python app.py --port 8001
```

#### **4. API Key Issues**
- Check environment variables are set
- Verify API key format
- Test API key in dashboard

---

## **🎨 Dashboard Usage**

### **1. Upload Data**
- Supported formats: CSV, Excel, JSON
- Click "Upload & Generate Dashboard"

### **2. Configure AI**
- **Local LLM**: Select "Local LLM (Ollama)" → Choose model
- **Cloud API**: Select provider → Enter API key → Test

### **3. Analyze Data**
- **Profile**: Data quality analysis
- **Clean**: AI-powered data cleaning
- **EDA**: Exploratory data analysis
- **Visualize**: Charts and graphs
- **Insights**: AI-generated insights
- **Q&A**: Ask questions about your data

### **4. Customize**
- **Themes**: 6 color themes
- **Templates**: Multiple dashboard layouts
- **Export**: Download results

---

## **🚀 Production Deployment**

### **Docker (Recommended)**
```bash
docker build -t vortex-dashboard .
docker run -p 8000:8000 vortex-dashboard
```

### **Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## **📞 Support**

### **Documentation**
- 📚 **GitHub**: https://github.com/omaressa123/Vortex-
- 📖 **Wiki**: Setup guides and tutorials

### **Issues**
- 🐛 **Report**: Create GitHub issue
- 💬 **Discuss**: GitHub discussions

---

**🎉 Your AI-Powered Data Dashboard is ready!**

**Start with**: `python app.py` → **Visit**: http://127.0.0.1:8000
