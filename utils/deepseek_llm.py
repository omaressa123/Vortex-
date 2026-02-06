from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import requests
import json
from pydantic import Field

class ChatDeepSeekRapidAPI(BaseChatModel):
    """Wrapper for DeepSeek API via RapidAPI."""
    
    api_key: str = Field(..., description="RapidAPI Key")
    host: str = Field(default="deepseek-v31.p.rapidapi.com", description="RapidAPI Host")
    model: str = Field(default="DeepSeek-V3-0324", description="Model name")
    api_url: str = Field(default="https://deepseek-v31.p.rapidapi.com/", description="API Endpoint")
    temperature: float = Field(default=0.0)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key
        }
        
        # Convert LangChain messages to API format
        api_messages = []
        for msg in messages:
            role = "user"
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            
            api_messages.append({"role": role, "content": msg.content})
            
        payload = {
            "model": self.model,
            "messages": api_messages
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # DeepSeek via RapidAPI response format
            # { "choices": [ { "message": { "content": "..." } } ] }
            content = result["choices"][0]["message"]["content"]
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
            
        except Exception as e:
            print(f"DeepSeek API Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise e

    @property
    def _llm_type(self) -> str:
        return "deepseek-rapidapi"
