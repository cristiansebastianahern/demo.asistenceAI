"""
LLM client wrapper for Ollama integration.
"""
from typing import Optional
import ollama
from .exceptions import LLMConnectionError

class OllamaClient:
    """
    Wrapper for Ollama LLM service.
    
    Provides a clean interface for generating text completions
    with error handling and availability checks.
    """
    
    def __init__(self, model_name: str = "qwen2.5-coder:latest"):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use.
                       Default: "qwen2.5-coder:latest"
                       Alternatives: "llama3.2", "mistral", etc.
        """
        self.model_name = model_name
    
    def is_available(self) -> bool:
        """
        Check if the Ollama service is available.
        
        Returns:
            True if Ollama is running and the model is available, False otherwise.
        """
        try:
            # Try to list available models
            ollama.list()
            return True
        except Exception:
            return False
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate a text completion using the configured model.
        
        Args:
            prompt: The input prompt for the LLM.
            temperature: Sampling temperature (0.0 to 1.0).
                        Lower values make output more deterministic.
        
        Returns:
            Generated text response.
            
        Raises:
            LLMConnectionError: If Ollama service is unavailable or generation fails.
            
        Example:
            >>> client = OllamaClient()
            >>> response = client.generate("¿Dónde está la cafetería?")
            >>> print(response)
        """
        if not self.is_available():
            raise LLMConnectionError(
                f"Ollama service is not available. "
                f"Please ensure Ollama is running and model '{self.model_name}' is installed."
            )
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": temperature
                }
            )
            return response['response']
        except Exception as e:
            raise LLMConnectionError(f"Failed to generate response: {e}")
    
    def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        """
        Generate a chat completion using conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Example: [{"role": "user", "content": "Hello"}]
            temperature: Sampling temperature (0.0 to 1.0).
        
        Returns:
            Generated text response.
            
        Raises:
            LLMConnectionError: If Ollama service is unavailable or generation fails.
        """
        if not self.is_available():
            raise LLMConnectionError(
                f"Ollama service is not available. "
                f"Please ensure Ollama is running and model '{self.model_name}' is installed."
            )
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature
                }
            )
            return response['message']['content']
        except Exception as e:
            raise LLMConnectionError(f"Failed to generate chat response: {e}")
