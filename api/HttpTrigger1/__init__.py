import logging

from fastapi import FastAPI
import azure.functions as func
from routers import endpoints
from fastapi.middleware.cors import CORSMiddleware
from config.config import settings


app = FastAPI()
app.include_router(endpoints.router)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )



def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    return func.AsgiMiddleware(app).handle(req, context)