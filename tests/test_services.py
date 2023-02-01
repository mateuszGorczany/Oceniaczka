import pytest
import services as svc
from services import QueryExecutor, Applicant

applicant_service = svc.UserSerivce()
test_applicant = Applicant(**{'id': 'f9dd32d6-c072-44c8-b8fa-3d26bfc14235', 'name': 'Kamila', 'surname': 'Obrót', 'age': 19, 'faculty': 'WIMIP'})

class FakeDB(QueryExecutor):

    def __init__(self) -> None:
        super().__init__()
    
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
        return [test_applicant]


@pytest.fixture
def applicant_service():
    return svc.ApplicantsService(FakeDB())

@pytest.fixture
def user_service() -> svc.UserSerivce:
    return svc.UserSerivce()

def test_current_user(user_service):
    assert user_service.current_user is None
        

def test_list_applicants(applicant_service):
    assert applicant_service.list_applicants() == [test_applicant]
        
