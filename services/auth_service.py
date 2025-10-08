from typing import Dict, Any, Optional
import httpx
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import os

class AuthService:
    def __init__(self):
        self.pingfederate_url = os.getenv("PINGFEDERATE_URL", "https://auth.airline.com")
        self.client_id = os.getenv("OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET")
        self.introspection_endpoint = f"{self.pingfederate_url}/as/introspect.oauth2"
        
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token via PingFederate introspection"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.introspection_endpoint,
                auth=(self.client_id, self.client_secret),
                data={"token": token}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed"
                )
            
            token_info = response.json()
            
            if not token_info.get("active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not active"
                )
            
            return token_info
    
    async def get_user_permissions(self, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user permissions from token"""
        scopes = token_info.get("scope", "").split()
        roles = token_info.get("roles", [])
        
        permissions = {
            "user_id": token_info.get("sub"),
            "username": token_info.get("username"),
            "roles": roles,
            "scopes": scopes,
            "can_modify_weights": "weight_modify" in scopes,
            "can_view_reports": "reports_view" in scopes,
            "can_manage_devices": "device_admin" in scopes,
            "is_load_master": "load_master" in roles,
            "is_operations": "operations" in roles,
            "is_maintenance": "maintenance" in roles
        }
        
        return permissions