from ..models import db

from .user_repository import UserRepository

from typing import Union

REPOSITORIES = {
    'users': UserRepository
}

def get_repository(resource: str) -> Union[UserRepository]:
    if resource not in REPOSITORIES:
        raise ValueError(f"Repository '{resource}' not found. Available: {list(REPOSITORIES.keys())}")
    return REPOSITORIES[resource](db)
