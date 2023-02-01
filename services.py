# %%
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID, uuid4
from flask import session
from auth import _get_token_from_cache
import app_config
import requests
from pydantic import parse_obj_as
from abc import ABC, abstractmethod

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
# %%
class User(BaseModel):
    ID: UserID = Field(alias="id")
    Surname: str = Field(alias="surname")
    DisplayName: str = Field(alias="displayName")

applicants_db: List[Applicant] = [
    Applicant(id= uuid4(),name="Mateusz", surname="Górczany", age=23, faculty=Faculty.WFiIS)
]

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

    def list_applicants(self) -> List[Applicant]:
        applicants_raw = self.db_client.query_items(
            query="SELECT c.id, c.name, c.surname, c.age, c.faculty FROM c",
            enable_cross_partition_query=True
        )
        return parse_obj_as(List[Applicant], list(applicants_raw))

    def get_applicant_by_id(self, uuid: UUID) -> Optional[Applicant]:
        applicant_raw = list(self.db_client.query_items(
            query=f"SELECT c.id, c.name, c.surname, c.age, c.faculty from c where c.id = '{uuid}'",
            enable_cross_partition_query=True
        ))
        if len(applicant_raw) == 0:
            return None
        return Applicant(**applicant_raw[0])
# %%
class VotingService:

    def __init__(self) -> None:
        pass

    @staticmethod
    def vote_yes(voted_applicant_id: UUID, voting_user_id: UserID):
        pass
        # if votes_db_yes.get(voted_applicant_id) is None:
        #     votes_db_yes[voted_applicant_id] = []
        # votes_db_yes[voted_applicant_id].append(voting_user_id)

    @staticmethod
    def vote_no(voted_applicant_id: UUID, voting_user_id: UserID):
        pass
        # if votes_db_no.get(voted_applicant_id) is None:
        #     votes_db_no[voted_applicant_id] = []
        # votes_db_no[voted_applicant_id].append(voting_user_id)
# %%