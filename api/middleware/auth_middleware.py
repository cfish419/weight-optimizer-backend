from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import re

from services.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()

class AuthMiddleware:
    def __init__(self):
        self.public_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/devices/readings"  # Allow IoT devices to post without auth
        ]
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            response = await call_next(request)
            return response
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Validate token with PingFederate
            token_info = await auth_service.validate_token(token)
            user_permissions = await auth_service.get_user_permissions(token_info)
            
            # Add user info to request state
            request.state.user = user_permissions
            request.state.token_info = token_info
            
            # Check path-specific permissions
            if not await self._check_path_permissions(request.url.path, user_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this resource"
                )
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    async def _check_path_permissions(self, path: str, permissions: dict) -> bool:
        """Check if user has permission for specific path"""
        
        # Admin paths - require device_admin scope
        if re.match(r"/devices/(register|status)", path):
            return permissions.get("can_manage_devices", False)
        
        # Weight modification - require weight_modify scope
        if re.match(r"/(weight-balance|baggage).*", path) and "POST|PUT|DELETE" in path:
            return permissions.get("can_modify_weights", False)
        
        # Reports - require reports_view scope
        if "/reports" in path:
            return permissions.get("can_view_reports", False)
        
        # Maintenance paths - require maintenance role
        if "/maintenance" in path:
            return permissions.get("is_maintenance", False)
        
        # Default: allow read access for authenticated users
        return True

async def get_current_user(request: Request) -> dict:
    """Dependency to get current user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user