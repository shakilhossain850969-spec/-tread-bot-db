import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config import settings


async def verify_google_token(token: str) -> dict:
    """
    Verifies a Google ID token and returns the decoded payload.
    Returns dict with: sub, email, name, picture
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        return {
            "google_id": idinfo["sub"],
            "email": idinfo["email"],
            "full_name": idinfo.get("name", ""),
            "avatar_url": idinfo.get("picture", None),
        }
    except ValueError as e:
        raise ValueError(f"Invalid Google token: {e}")
