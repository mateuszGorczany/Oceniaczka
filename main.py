# Opencensus imports
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES

# FastAPI imports
from fastapi import FastAPI, Request
import os

# uvicorn
import uvicorn

app = FastAPI()

HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]

APPINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
exporter = AzureExporter(connection_string=f"{APPINSIGHTS_CONNECTION_STRING}")
sampler = ProbabilitySampler(1.0)

# fastapi middleware for opencensus
@app.middleware("http")
async def middleware_opencensus(request: Request, call_next):
    tracer = Tracer(exporter=exporter, sampler=sampler)
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        response = await call_next(request)

        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE, attribute_value=response.status_code
        )
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL, attribute_value=str(request.url)
        )

    return response


@app.get("/")
async def root():
    return "Hello World!"


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("WEBSITES_PORT", 8080)),
        log_level="info",
    )
