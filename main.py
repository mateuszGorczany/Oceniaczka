# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from fastapi.middleware.cors import CORSMiddleware
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi import Security

# FastAPI imports
from fastapi import Header

# uvicorn
from typing import Optional, Dict

import uvicorn
from fastapi import FastAPI, Request
from config.config import settings, templates
from auth import router as auth_router
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.exceptions import HTTPException

app = FastAPI(
    swagger_ui_oauth2_redirect_url="/get_auth_token",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.OPENAPI_CLIENT_ID,
    },
)
app.include_router(auth_router)
# app.mount("/static", StaticFiles(directory="./static"), name="static")
# app.include_router(auth.router)

scopes = {
    f"api://{settings.CLIENT_ID}/user_impersonation": "user_impersonation",
}


azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=scopes,
    token_version=1,
)


class CookieBasedOAuth2TokenBearer(OAuth2):
    def __init__(
        self,
        authorizationUrl: str,
        tokenUrl: str,
        refreshUrl: Optional[str] = None,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            authorizationCode={
                "authorizationUrl": authorizationUrl,
                "tokenUrl": tokenUrl,
                "refreshUrl": refreshUrl,
                "scopes": scopes,
            }
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.cookies.get("Authorization")
        # import sys

        # print("ok")
        # print(authorization, file=sys.stderr)
        def _error():
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None  # pragma: nocover

        if not authorization:
            return _error()
        scheme, param = authorization.split(" ")
        if scheme.lower() != "bearer":
            return _error()
        return param


azure_scheme.oauth = CookieBasedOAuth2TokenBearer(
    authorizationUrl=azure_scheme.authorization_url,
    tokenUrl=azure_scheme.token_url,
    scopes=scopes,
    scheme_name="AzureAuthorizationCodeBearerBase",
    description="`Leave client_secret blank`",
    auto_error=True,  # We catch this exception in __call__
)
azure_scheme.model = azure_scheme.oauth.model

exporter = AzureExporter(connection_string=f"{settings.APPINSIGHTS_CONNECTION_STRING}")
sampler = ProbabilitySampler(1.0)
# fastapi middleware for opencensus
@app.middleware("http")
async def middleware_opencensus(request: Request, call_next):
    tracer = Tracer(exporter=exporter, sampler=sampler)
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        response = await call_next(request)

        tracer.add_attribute_to_current_span(
            attribute_key=settings.HTTP_STATUS_CODE,
            attribute_value=response.status_code,
        )
        tracer.add_attribute_to_current_span(
            attribute_key=settings.HTTP_URL, attribute_value=str(request.url)
        )

    return response


def add_cors(app):
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


@app.on_event("startup")
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()


# @app.route("/.auth/login/aad/callback")
# def callback(request: Request):
#     return RedirectResponse(url=f"{settings.SELF_URL}/")


# @app.route("/login")
# def login(request: Request):
#     url = f"https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/authorize?client_id={settings.CLIENT_ID}&scope={settings.SCOPE}"
#     return RedirectResponse(url=url)


# @app.route("/logout")
# def logout(request: Request):
#     url = f"{settings.AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={settings.SELF_URL}"
#     return RedirectResponse(url=url)


@app.get("/home")
async def root(request: Request, hx_request: Optional[str] = Header(None)):
    applicants = [
        {"name": "Andrzej", "surname": "Popatrz w góre"},
        {"name": "Andrzej", "surname": azure_scheme.token_url},
    ]
    context = {"request": request, "applicants": applicants}
    if hx_request:
        return templates.TemplateResponse("applicants.html", context)

    return templates.TemplateResponse("index.html", context)


@app.get("/info", dependencies=[Security(azure_scheme)])
# @app.get("/info")
async def info(request: Request):
    # azure_scheme.openid_config.authorization_endpoint
    # request.state.
    return {"user": request.state.user.dict()}
    # return "Hello world!"


if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
        reload=True,
    )
