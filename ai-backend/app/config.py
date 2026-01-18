import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Model configuration
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "mistralai/devstral-2512:free")
    CODE_MODEL = os.getenv("CODE_MODEL", "mistralai/devstral-2512:free")
    SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "mistralai/devstral-2512:free") # Using free/fast model for support too
