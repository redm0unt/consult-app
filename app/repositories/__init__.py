from ..models import db

from .user_repository import UserRepository
from .school_repository import SchoolRepository

from typing import Union

REPOSITORIES = {
    'users': UserRepository,
    'schools': SchoolRepository,
}

def get_repository(resource: str) -> Union[UserRepository, SchoolRepository]:
    if resource not in REPOSITORIES:
        raise ValueError(f"Repository '{resource}' not found. Available: {list(REPOSITORIES.keys())}")
    return REPOSITORIES[resource](db)
