import os


class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    # Model configuration
    TRIAGE_MODEL = os.getenv("TRIAGE_MODEL", "google/gemini-3-flash-preview")
    CODE_MODEL = os.getenv("CODE_MODEL", "google/gemini-3-flash-preview")
    SUPPORT_MODEL = os.getenv(
        "SUPPORT_MODEL", "google/gemini-3-flash-preview"
    )  # Using free/fast model for support too

    # TokenCompany compression
    TOKENC_API_KEY = os.getenv("TOKENC_API_KEY")
    DOCS_PATH = os.getenv("DOCS_PATH", "/app/DOCS")
