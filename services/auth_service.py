from typing import Dict, Any, Optional
import httpx
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from urllib.parse import urlencode, quote
import os

class AuthService:
    def __init__(self):
        self.sso_endpoint = os.getenv("PINGFEDERATE_SSO_ENDPOINT")
        self.client_id = os.getenv("PINGFEDERATE_CLIENT_ID")
        self.redirect_uri = os.getenv("PINGFEDERATE_REDIRECT_URI")
        self.logout_url = os.getenv("PINGFEDERATE_LOGOUT_URL")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.introspection_endpoint = f"{self.sso_endpoint}/as/introspect.oauth2"
        
    def get_sso_login_url(self, state: str = None) -> str:
        """Generate PingFederate SSO login URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email"
        }
        
        if state:
            params["state"] = state
            
        query_string = urlencode(params)
        return f"{self.sso_endpoint}/as/authorization.oauth2?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        try:
            token_url = f"{self.sso_endpoint}/as/token.oauth2"
            
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    user_info = await self.get_user_info(token_data["access_token"])
                    return {
                        "access_token": token_data["access_token"],
                        "user_info": user_info,
                        "expires_in": token_data.get("expires_in", 3600)
                    }
                    
        except Exception as e:
            print(f"Token exchange error: {e}")
            
        return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from PingFederate"""
        try:
            userinfo_url = f"{self.sso_endpoint}/idp/userinfo.openid"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "user_id": user_data.get("sub"),
                        "username": user_data.get("preferred_username"),
                        "email": user_data.get("email"),
                        "name": user_data.get("name"),
                        "roles": user_data.get("roles", ["user"]),
                        "authenticated": True
                    }
                    
        except Exception as e:
            print(f"User info error: {e}")
            
        return None
    
    def get_logout_url(self, return_url: str = None) -> str:
        """Generate PingFederate logout URL"""
        if return_url:
            return f"{self.logout_url}?TargetResource={quote(return_url)}"
        return self.logout_url
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "roles": user_data["roles"],
            "exp": datetime.utcnow() + timedelta(hours=8),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
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