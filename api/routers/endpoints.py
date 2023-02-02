from fastapi import APIRouter, Request
from azure.cosmos import CosmosClient
from config.config import settings


def create_db_client():
    client = CosmosClient(settings.DB_ACCOUNT_URI, settings.DB_ACCOUNT_KEY)
    database = client.get_database_client(settings.DB_NAME)
    container = database.get_container_client("Votes")
    return container

router = APIRouter()
db_client = create_db_client()

@router.get("/{person}")
async def vote(req: Request, person: str):
    pass
      
    # return {"name": person, "surname": "Goooot it", "tenant_id": settings.TENANT_ID}


@router.get("/votes/users/{user_id}")
async def user_votes(req: Request, user_id: str):
    votes = db_client.query_items(
            query="SELECT  c.vote_id FROM c where c.user_id = '{user_id}'",
            enable_cross_partition_query=True
        )
    return list(votes)


@router.get("/votes/applicants/{voted_applicant_id}")
async def votes_for_applicant(req: Request, voted_applicant_id: str):
    return list(db_client.query_items(
            query="SELECT  c.vote_id FROM c where c.applicant_id = '{voted_applicant_id}'",
            enable_cross_partition_query=True
        ))