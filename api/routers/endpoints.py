from fastapi import APIRouter, Request
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi import Security
from config.config import settings

router = APIRouter()

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        f'api://{settings.APP_CLIENT_ID}/user_impersonation': 'user_impersonation',
    }
)


@router.get("/{person}", dependencies=[Security(azure_scheme)])
async def get_person(req: Request, person: str):
    return {"name": person, "surname": "Goooot it", "tenant_id": settings.TENANT_ID}
