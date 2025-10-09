"""
Configuration for BalanceIQ Baggage Demo Frontend
"""
import os

class Config:
    """Frontend configuration"""
    
    # Backend API configuration
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000')
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'demo-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:8000').split(',')
    
    @staticmethod
    def get_api_endpoint(path: str) -> str:
        """Get full API endpoint URL"""
        base_url = Config.BACKEND_API_URL.rstrip('/')
        path = path.lstrip('/')
        return f"{base_url}/{path}"