from config.config import settings, templates
import msal
from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import JSONResponse
import sys

router = APIRouter()


def _load_cache():
    cache = msal.SerializableTokenCache()
    # if session.get("token_cache"):
    #     cache.deserialize(session["token_cache"])
    return cache


def _build_msal_app(cache=None, authority=None):
    authority_with_tenant = authority or settings.AUTHORITY
    return msal.ConfidentialClientApplication(
        settings.CLIENT_ID,
        authority=authority_with_tenant,
        client_credential=settings.CLIENT_SECRET,
        token_cache=cache,
    )


def _build_auth_url(authority=None, scopes=None, state=None):
    print(settings.AUTH_REDIRECT_URL, file=sys.stderr)
    return _build_msal_app().get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=settings.AUTH_REDIRECT_URL,
    )


def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        return result


@router.get("/")
async def root(request: Request):
    auth_url = _build_auth_url(scopes=settings.SCOPE, state="/homepage")
    return templates.TemplateResponse(
        "login.html", {"request": request, "auth_url": auth_url}
    )


@router.get("/get_auth_token")
async def get_auth_token(request: Request, code: str, state: str):
    if code != "":
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        result = cca.acquire_token_by_authorization_code(
            code,
            scopes=settings.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=settings.AUTH_REDIRECT_URL,
        )
        print(result)
        print("Scopes : ", settings.SCOPE)
        if "error" in result:
            print(result)
            raise HTTPException(
                status_code=400, detail="Unable to validate social login"
            )
        token_to_encode = result.get("id_token_claims")
        accounts = cca.get_accounts()
        token = cca.acquire_token_silent(settings.SCOPE, account=accounts[0])
        real_token = token["access_token"]
    else:
        print("NO CODE GIVEN BY MICROSOFT")
        raise HTTPException(status_code=400, detail="NO CODE GIVEN BY MICROSOFT")
    try:
        email = token_to_encode["preferred_username"]
        username = token_to_encode["name"]
    except:
        raise HTTPException(status_code=400, detail="Unsupported Email ID")
    return templates.TemplateResponse(
        "microsoft_proxy.html",
        {
            "request": request,
            "redirect_url": state,
            "token": real_token,
            "username": username,
            "email": email,
        },
    )


@router.post("/add-microsoft-cookie")
async def get_token(request: Request):
    formdata = await request.form()
    token = formdata["sub"]
    response = JSONResponse({"access_token": token, "token_type": "bearer"})

    response.set_cookie(
        key="Authorization",
        value=f"Bearer {token}",
        domain="localhost",
        httponly=True,
        max_age=3600,  # 1 hours
        expires=3600,  # 1 hours
    )
    return response
