"""Authentication Routes for Web Interface.

Provides login/logout functionality using signed session cookies.
"""

from typing import Any

from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from starlette.templating import _TemplateResponse

from app.config import get_settings
from app.utils.security import verify_password

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

# Session cookie configuration
SESSION_MAX_AGE = 86400 * 7  # 7 days in seconds
SESSION_COOKIE_NAME = "session"


def get_serializer() -> URLSafeTimedSerializer:
    """Get the session token serializer using encryption_key."""
    settings = get_settings()
    return URLSafeTimedSerializer(settings.encryption_key)


def create_session_token() -> str:
    """Create a signed session token for authenticated user."""
    return get_serializer().dumps({"authenticated": True})


def verify_session_token(token: str) -> bool:
    """Verify session token is valid and not expired.

    Args:
        token: The session token to verify.

    Returns:
        True if token is valid and not expired, False otherwise.
    """
    if not token:
        return False
    try:
        data = get_serializer().loads(token, max_age=SESSION_MAX_AGE)
        return data.get("authenticated", False)
    except (SignatureExpired, BadSignature):
        return False


def get_current_user(session: str | None = Cookie(default=None)) -> bool:
    """Dependency to check if user is authenticated.

    Args:
        session: Session cookie value.

    Returns:
        True if authenticated, False otherwise.
    """
    return verify_session_token(session) if session else False


def render_template(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
) -> _TemplateResponse:
    """Render template with automatic is_authenticated injection.

    Args:
        request: The FastAPI request object.
        template_name: Name of the template file.
        context: Additional context variables.
        status_code: HTTP status code for response.

    Returns:
        Rendered template response with is_authenticated set.
    """
    session = request.cookies.get(SESSION_COOKIE_NAME)
    is_authenticated = verify_session_token(session) if session else False

    full_context = {"is_authenticated": is_authenticated}
    if context:
        full_context.update(context)

    return templates.TemplateResponse(
        request, template_name, full_context, status_code=status_code
    )


@router.get("/login")
async def login_page(request: Request, session: str | None = Cookie(default=None)):
    """Display the login page.

    If user is already authenticated, redirect to home.
    """
    if verify_session_token(session) if session else False:
        return RedirectResponse(url="/", status_code=303)
    return render_template(request, "auth/login.html")


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    """Process login form submission.

    Validates password against ADMIN_PASSWORD and creates session cookie.
    """
    settings = get_settings()
    if not verify_password(password, settings.admin_password):
        return render_template(
            request,
            "auth/login.html",
            {"message": "密码错误", "message_type": "error"},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(),
        httponly=True,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout():
    """Process logout request.

    Clears the session cookie and redirects to login page.
    """
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
