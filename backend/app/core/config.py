import json
from typing import Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Although Pydantic's BaseSettings can load from .env automatically,
# calling load_dotenv() ensures it works consistently across all environments.
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables using Pydantic.
    This provides type validation and automatic parsing for complex data types.
    """
    # --- Database Configuration ---
    MONGODB_URL: str
    REDIS_URL: str
    REDIS_TOKEN: str
    
    # --- Google AI Configuration ---
    GOOGLE_API_KEY: str
    
    # --- Pinecone Configuration ---
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    
    # --- Multi-Index and Collection Mapping ---
    # Pydantic automatically parses the JSON strings from the .env file
    # into Python dictionaries because of the Dict[str, str] type hint.
    PINECONE_INDEX_MAP: Dict[str, str]
    MONGO_COLLECTION_MAP: Dict[str, str]
    
    # --- Application Configuration ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SESSION_SECRET_KEY: str

    class Config:
        # Specifies the .env file to load variables from.
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"

# Create a single, globally accessible instance of the settings.
settings = Settings()

# Example of how to access the settings from other parts of your app:
# from backend.app.core.config import settings
#
# print("Pinecone Index Map:", settings.PINECONE_INDEX_MAP)
# print("Mongo Collection Map:", settings.MONGO_COLLECTION_MAP)
# print("Google API Key:", settings.GOOGLE_API_KEY)
