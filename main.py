# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from fastapi.middleware.cors import CORSMiddleware
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

# FastAPI imports
from fastapi import FastAPI, Request, Security

# uvicorn
import uvicorn
from typing import Union
from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    SECRET_KEY: str = Field("my super secret key", env="SECRET_KEY")
    BACKEND_CORS_ORIGINS: list[Union[str, AnyHttpUrl]] = ["http://localhost:8000"]
    OPENAPI_CLIENT_ID: str = Field(default="", env="OPENAPI_CLIENT_ID")
    APP_CLIENT_ID: str = Field(default="", env="APP_CLIENT_ID")
    TENANT_ID: str = Field(default="", env="TENANT_ID")
    HTTP_URL = Field(default=COMMON_ATTRIBUTES["HTTP_URL"])
    HTTP_STATUS_CODE = Field(default=COMMON_ATTRIBUTES["HTTP_STATUS_CODE"])
    APPINSIGHTS_CONNECTION_STRING = Field(
        default="", env="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    PORT = Field(default=8080, env="PORT")
    HOST = Field(default="0.0.0.0", env="HOST")
    LOG_LEVEL = Field(default="info", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

app = FastAPI()


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


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        f"api://{settings.APP_CLIENT_ID}/user_impersonation": "user_impersonation",
    },
)


@app.on_event("startup")
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()


@app.get("/")
async def root():
    return "Hello World!"


@app.get("/info", dependencies=[Security(azure_scheme)])
async def info():
    return "Hello World!"


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
    )
