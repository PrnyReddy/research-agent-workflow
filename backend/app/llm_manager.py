import os
from typing import Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    """
    Manages LLM providers.
    Primarily supports Google Gemini with fallback options.
    """
    
    def __init__(self, default_provider: str = "gemini"):
        self.default_provider = default_provider
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers based on environment variables."""
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            self.providers["gemini"] = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=google_api_key
            )
            
            self.providers["gemini-pro"] = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0,
                google_api_key=google_api_key
            )
            
        
            self.providers["gemini-flash"] = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0,
                google_api_key=google_api_key
            )
    
    def get_llm(self, provider: Optional[str] = None) -> Any:
        """
        Get LLM instance for specified provider or fallback to available ones.
        
        Args:
            provider: Preferred provider name ("gemini", "gemini-pro", "gemini-flash")
            
        Returns:
            LangChain LLM instance
        """
        if provider and provider in self.providers:
            return self.providers[provider]
        
        # Fallback chain: specified -> default -> first available
        if self.default_provider in self.providers:
            return self.providers[self.default_provider]
        
        if self.providers:
            return list(self.providers.values())[0]
        
        raise ValueError("No LLM providers available. Please check your GOOGLE_API_KEY.")
    
    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def invoke_with_fallback(self, prompt: str, preferred_provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke LLM with automatic fallback if the preferred provider fails.
        
        Args:
            prompt: The prompt to send to the LLM
            preferred_provider: Preferred provider name
            
        Returns:
            Dict with response and provider used
        """
        providers_to_try = []
        
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        # Add other providers as fallbacks
        for provider in self.providers:
            if provider not in providers_to_try:
                providers_to_try.append(provider)
        
        for provider in providers_to_try:
            try:
                llm = self.providers[provider]
                response = llm.invoke(prompt)
                return {
                    "response": response,
                    "provider": provider,
                    "success": True
                }
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        return {
            "response": "All LLM providers failed",
            "provider": None,
            "success": False,
            "error": "No available LLM providers"
        }

# Global instance
llm_manager = LLMManager() 