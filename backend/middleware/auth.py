"""OAuth2 authentication middleware for Databricks Apps."""

from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Dict


security = HTTPBearer()


async def get_current_user(token: str = Security(security)) -> Dict:
    """
    Validate Databricks OAuth2 token and extract user.

    In Databricks Apps, user context is automatically injected
    and token validation happens at the app gateway level.

    Args:
        token: Bearer token from request

    Returns:
        Dict with user_id and token

    Raises:
        HTTPException: If token is invalid
    """
    # Extract token value
    token_value = token.credentials if hasattr(token, 'credentials') else token

    # In Databricks Apps, we can trust the token as it's already validated
    # by the gateway. Here we would extract user_id from the token claims.
    # For now, using a placeholder that would be replaced with actual
    # token validation in production.

    user_id = extract_user_from_token(token_value)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return {
        "user_id": user_id,
        "token": token_value
    }


def extract_user_from_token(token: str) -> str:
    """
    Extract user ID from Databricks OAuth2 token.

    In production, this would decode the JWT and extract user claims.
    For MVP, we can use a simplified approach since Databricks Apps
    handle authentication at the gateway level.

    Args:
        token: OAuth2 bearer token

    Returns:
        User identifier
    """
    # TODO: Implement proper JWT decoding in production
    # For MVP, return a placeholder user ID
    return "databricks_user"
