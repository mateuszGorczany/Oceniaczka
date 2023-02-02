# %%
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID
from flask import session
from auth import _get_token_from_cache
import app_config
import requests
from pydantic import parse_obj_as
from abc import ABC, abstractmethod
import requests as reqs
# %%

class QueryExecutor(ABC):

    @abstractmethod
    def query_items(
        self,
        query,  # type: str
        parameters=None,  # type: Optional[List[Dict[str, object]]]
        partition_key=None,  # type: Optional[Any]
        enable_cross_partition_query=None,  # type: Optional[bool]
        max_item_count=None,  # type: Optional[int]
        enable_scan_in_query=None,  # type: Optional[bool]
        populate_query_metrics=None,  # type: Optional[bool]
        **kwargs  # type: Any
    ):
        pass

# %%

# %%

class UserID(str):
    pass

# %%
class Faculty(str, Enum):
    WFiIS="Wydział Fizyki i Informatyki Stosowanej"
    WiEIT="Wydział Elektroniki i Telekomunikacji"
    WIMIP="Wydział Inżynierii Metali i Informatyki Przemysłowej"

class Applicant(BaseModel):
    ID: UUID = Field(alias="id")
    Name: str = Field(alias="name")
    Surname: str = Field(alias="surname")
    Age: int = Field(alias="age")
    Faculty: str = Field(alias="faculty")
    Votes: Optional[int]

# %%
class User(BaseModel):
    ID: UserID = Field(alias="id")
    Surname: str = Field(alias="surname")
    DisplayName: str = Field(alias="displayName")


class UserSerivce:
    def __init__(self) -> None:
        self.current_user = None

    @staticmethod
    def is_user_logged_in() -> bool:
        return session.get("user") is not None

    def load_current_user(self):
        if self.current_user is not None:
            return self.current_user

        token = _get_token_from_cache(app_config.SCOPE)
        if not token:
            return None
        user = requests.get(  # Use token to call downstream service
            app_config.ENDPOINT,
            headers={"Authorization": "Bearer " + token["access_token"]},
        ).json().get("value", {})[0]
        self.current_user = User.parse_obj(user)

        return self.current_user


# %%
class ApplicantsService:
    
    def __init__(self, db_client: QueryExecutor) -> None:
        self.db_client: QueryExecutor = db_client
        self.voting_service = VotingService()

    def list_applicants(self, with_votes=True) -> List[Applicant]:
        applicants_raw = self.db_client.query_items(
            query="SELECT c.id, c.name, c.surname, c.age, c.faculty FROM c",
            enable_cross_partition_query=True
        )

        applicants = parse_obj_as(List[Applicant], list(applicants_raw))
        if with_votes:
            for i in range(len(applicants)):
                applicants[i].Votes = self.voting_service.votes_for_applicant(applicants[i].ID)
           

        return applicants

    def get_applicant_by_id(self, uuid: UUID) -> Optional[Applicant]:
        applicant_raw = list(self.db_client.query_items(
            query=f"SELECT c.id, c.name, c.surname, c.age, c.faculty from c where c.id = '{uuid}'",
            enable_cross_partition_query=True
        ))
        if len(applicant_raw) == 0:
            return None
        return Applicant(**applicant_raw[0])
# %%
# %%
class VotingService:

    def __init__(self) -> None:
        self.voting_service_url = app_config.VOTING_SERVICE_URL if app_config.VOTING_SERVICE_URL != "" else ""

    def vote(self, voted_applicant_id: UUID, voting_user_id: UserID, vote_type):
        if vote_type == "yes":
            reqs.post(f"{self.voting_service_url}/votes/applicants/{voted_applicant_id}?user_id={voting_user_id}&vote_type=yes").json()
        if vote_type == "no":
            reqs.post(f"{self.voting_service_url}/votes/applicants/{voted_applicant_id}?user_id={voting_user_id}&vote_type=no").json()

    def votes_for_applicant(self, applicant_id: UUID) -> int:
        resp = reqs.get(f"{self.voting_service_url}/votes/applicants/{applicant_id}").json()
        return len(resp)

    def votes_of_user(self, user_id: UserID) -> int:
        resp = reqs.get(f"{self.voting_service_url}/votes/users/{user_id}").json()
        return len(resp)
    
    def has_user_voted_for(self, user_id, applicant_id):
        reqs.get(f"{self.voting_service_url}/votes/users/{user_id}").json()

# %%