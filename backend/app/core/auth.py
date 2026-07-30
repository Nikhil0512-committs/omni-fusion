from typing import List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase_client import supabase
from app.models.enums import Role

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        
        # Fetch profile to get role and link details
        profile_response = supabase.table('profiles').select('*').eq('id', user.id).execute()
        profile = None
        if profile_response.data and len(profile_response.data) > 0:
            profile = profile_response.data[0]
            
        return {
            "auth": user,
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {str(e)}"
        )

def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(optional_security)):
    """Return authenticated user data when a bearer token is present."""
    if credentials is None:
        return None
    return get_current_user(credentials)

def require_role(allowed_roles: List[Union[str, Role]]):
    role_values = [role.value if isinstance(role, Role) else role for role in allowed_roles]
    def role_checker(user_data: dict = Depends(get_current_user)):
        profile = user_data.get("profile")
        if not profile or profile.get("role") not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user_data
    return role_checker
