from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

GITLAB_URL = "https://git.webis.de"
ADMIN_GROUP = "auth/auth-webis-admin"

_bearer = HTTPBearer()


async def require_admin(
    request: Request,
    creds: HTTPAuthorizationCredentials = Security(_bearer),
) -> dict:
    """FastAPI dependency — verifies the token via GitLab userinfo and checks admin group."""
    # Reuses the app's shared AsyncClient (set up in main.py's lifespan) instead of
    # opening a new client/TLS connection on every admin request.
    client = request.app.state.client
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
