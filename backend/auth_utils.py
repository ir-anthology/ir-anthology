import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

GITLAB_URL = "https://git.webis.de"
ADMIN_GROUP = "auth/auth-webis-admin"

_bearer = HTTPBearer()
_jwks_client = PyJWKClient(f"{GITLAB_URL}/oauth/discovery/keys", cache_keys=True)


async def require_admin(
    creds: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """FastAPI dependency — verifies the GitLab ID token (JWT) and checks admin group."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(creds.credentials)
        payload = jwt.decode(
            creds.credentials,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"Invalid or expired token: {e}")

    if ADMIN_GROUP not in (payload.get("groups_direct") or []):
        raise HTTPException(403, "Admin group membership required")
    return payload
