"""
Configuration management for the RAG system.
Loads settings from environment variables.
NOW WITH GEMINI SUPPORT!
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for RAG system"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    # Model Settings
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-1.5-flash')
    
    # Vector Database
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './data/chroma_db')
    
    # Document Processing
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
    
    # Search Settings
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 5))
    
    # Directories
    DOCUMENTS_DIR = './documents'
    
    @classmethod
    def validate(cls):
        """Validate that required settings are present"""
        if cls.LLM_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")
        if cls.LLM_PROVIDER == 'anthropic' and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic")
        if cls.LLM_PROVIDER == 'gemini' and not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when using Gemini")
        if cls.LLM_PROVIDER == 'groq' and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq")
        return True