import secrets

from fastapi import Request, Response

BUYER_COOKIE = "buyer_token"


def get_or_create_buyer_token(request: Request, response: Response) -> str:
    token = request.cookies.get(BUYER_COOKIE)
    if not token:
        token = secrets.token_hex(24)
        response.set_cookie(
            BUYER_COOKIE,
            token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
        )
    return token
