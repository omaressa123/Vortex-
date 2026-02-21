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
    host: str = Field(default="swift-ai.p.rapidapi.com", description="RapidAPI Host")
    model: str = Field(default="gpt-5", description="Model name")
    api_url: str = Field(default="https://swift-ai.p.rapidapi.com/chat/completions", description="API Endpoint")
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
            print(f"Making API call to: {self.api_url}")
            print(f"Headers: {headers}")
            # Create a safe payload for logging (api_messages is already a dict list)
            safe_payload = {
                "model": self.model,
                "messages": api_messages
            }
            print(f"Payload: {json.dumps(safe_payload, indent=2)}")
            
            response = requests.post(
                self.api_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            print(f"Response data: {json.dumps(result, indent=2)}")
            
            # DeepSeek via RapidAPI response format
            # { "choices": [ { "message": { "content": "..." } } ] }
            if "choices" not in result or len(result["choices"]) == 0:
                raise Exception("Invalid response format: missing choices")
            
            content = result["choices"][0]["message"]["content"]
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            print(f"DeepSeek API Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise e

    @property
    def _llm_type(self) -> str:
        return "deepseek-rapidapi"
