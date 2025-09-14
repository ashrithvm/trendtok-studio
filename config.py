import os
from typing import Optional


class Config:
    """Configuration class for environment variables and settings."""
    
    @staticmethod
    def get_env_var(var_name: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default."""
        value = os.getenv(var_name, default)
        if value is None:
            raise ValueError(f"Environment variable {var_name} is required but not set")
        return value
    
    # API Configuration
    LLAMA_API_KEY = get_env_var.__func__('LLAMA_API_KEY')
    
    # Google Drive Configuration  
    GOOGLE_SERVICE_ACCOUNT_FILE = get_env_var.__func__('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
    
    # Flask Configuration
    FLASK_SECRET_KEY = get_env_var.__func__('FLASK_SECRET_KEY')
    
    # Model Configuration
    MUSICGEN_MODEL = "facebook/musicgen-small"
    STABLE_DIFFUSION_MODEL = "runwayml/stable-diffusion-v1-5"
