import requests
import json
import os
from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import Field

class LocalOllamaLLM(BaseChatModel):
    """Local LLM using Ollama - No API keys required!"""
    
    model: str = Field(default="llama3", description="Ollama model name")
    base_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    temperature: float = Field(default=0.0)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        
        # Convert LangChain messages to Ollama format
        ollama_messages = []
        for msg in messages:
            role = "user"
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            
            ollama_messages.append({"role": role, "content": msg.content})
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result["message"]["content"]
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
            
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama not running. Please start Ollama with: 'ollama serve'")
        except Exception as e:
            raise Exception(f"Local LLM Error: {str(e)}")

    @property
    def _llm_type(self) -> str:
        return "local_ollama"

def check_ollama_available():
    """Check if Ollama is running and available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except:
        return []

def pull_model(model_name: str):
    """Pull a model from Ollama"""
    try:
        response = requests.post(
            f"http://localhost:11434/api/pull",
            json={"name": model_name},
            timeout=300  # 5 minutes timeout for large models
        )
        return response.status_code == 200
    except:
        return False

def setup_ollama():
    """Setup instructions for Ollama"""
    instructions = """
🔹 SETUP LOCAL LLM WITH OLLAMA (No API Keys Required!)

1️⃣ Install Ollama:
   - Windows: Download from https://ollama.ai/download
   - Mac: brew install ollama
   - Linux: curl -fsSL https://ollama.ai/install.sh | sh

2️⃣ Start Ollama Server:
   ollama serve

3️⃣ Pull a Model (Choose one):
   ollama pull llama3          # 8B parameters
   ollama pull mistral         # 7B parameters  
   ollama pull phi-3           # 3.8B parameters
   ollama pull qwen2           # 7B parameters
   ollama pull codellama       # 7B parameters (for coding)

4️⃣ Verify Installation:
   - Check models: ollama list
   - Check server: http://localhost:11434

📌 Popular Models:
• llama3 (8B) - All-around good performance
• mistral (7B) - Fast and efficient  
• phi-3 (3.8B) - Lightweight, good for CPU
• qwen2 (7B) - Multilingual support
• codellama (7B) - Specialized for code

✅ Once Ollama is running, the dashboard will use it automatically!
"""
    return instructions
