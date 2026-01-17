import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Model configuration
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "mistralai/mistral-7b-instruct:free")
    CODE_MODEL = os.getenv("CODE_MODEL", "anthropic/claude-3-sonnet")
    SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "mistralai/mistral-7b-instruct:free") # Using free/fast model for support too
