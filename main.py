from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import jwt

app = FastAPI()

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-gpzgnyl4.apps.exam.local"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
PASTE_YOUR_COMPLETE_ASSIGNED_PUBLIC_KEY_HERE
-----END PUBLIC KEY-----"""


@app.get("/healthz")
def healthz():
    return {"status": "ok", "redis": "up"}


@app.post("/verify")
async def verify_token(request: Request):
    try:
        body = await request.json()
        token = body.get("token") if isinstance(body, dict) else None

        if not isinstance(token, str) or not token:
            raise ValueError("Missing token")

        claims = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["exp", "iss", "aud", "email", "sub"]
            },
        )

        return {
            "valid": True,
            "email": claims["email"],
            "sub": claims["sub"],
            "aud": claims["aud"],
        }

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )
