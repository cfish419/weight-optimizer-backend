from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.responses import RedirectResponse
from services.auth_service import AuthService
import secrets
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_auth_service():
    return AuthService()

@router.get("/login")
async def login(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    """Initiate PingFederate SSO login"""
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in session (you might want to use Redis for production)
    request.session["oauth_state"] = state
    
    # Get SSO login URL
    login_url = auth_service.get_sso_login_url(state=state)
    
    return RedirectResponse(url=login_url)

@router.get("/callback")
async def auth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Handle PingFederate SSO callback"""
    
    if error:
        raise HTTPException(status_code=400, detail=f"Authentication error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    # Verify state parameter
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for token
    token_data = await auth_service.exchange_code_for_token(code)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    # Create JWT token for our application
    jwt_token = auth_service.create_jwt_token(token_data["user_info"])
    
    # Set JWT token in httpOnly cookie
    frontend_url = os.getenv("FRONTEND_URL", "https://demo.dev.balanceiq.com")
    response = RedirectResponse(url=f"{frontend_url}/dashboard")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=28800  # 8 hours
    )
    
    # Clear state from session
    request.session.pop("oauth_state", None)
    
    return response

@router.get("/logout")
async def logout(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    """Logout user and redirect to PingFederate logout"""
    
    # Clear local session
    request.session.clear()
    
    # Get logout URL
    return_url = os.getenv("FRONTEND_URL", "https://demo.dev.balanceiq.com")
    logout_url = auth_service.get_logout_url(return_url)
    
    # Clear cookie and redirect to PingFederate logout
    response = RedirectResponse(url=logout_url)
    response.delete_cookie(key="access_token")
    
    return response

@router.get("/user")
async def get_current_user(request: Request, auth_service: AuthService = Depends(get_auth_service)):
    """Get current authenticated user information"""
    
    # Get token from cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate token
    try:
        user_data = await auth_service.validate_token(token)
        return {
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "roles": user_data["roles"],
            "authenticated": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/check")
async def check_auth_status(request: Request):
    """Check if user is authenticated"""
    token = request.cookies.get("access_token")
    
    return {
        "authenticated": bool(token),
        "sso_login_url": "/auth/login" if not token else None
    }