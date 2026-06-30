import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

GITLAB_URL = "https://git.webis.de"
ADMIN_GROUP = "auth/auth-webis-admin"

_bearer = HTTPBearer()


async def require_admin(
    creds: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """FastAPI dependency — verifies the token via GitLab userinfo and checks admin group."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITLAB_URL}/oauth/userinfo",
            headers={"Authorization": f"Bearer {creds.credentials}"},
        )
    if resp.status_code != 200:
        raise HTTPException(401, "Invalid or expired token")

    payload = resp.json()
    if ADMIN_GROUP not in (payload.get("groups") or []):
        raise HTTPException(403, "Admin group membership required")
    return payload
