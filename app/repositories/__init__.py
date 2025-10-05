from typing import Dict, Type

from ..models import db

from .base_repository import BaseRepository
from .school_repository import SchoolRepository
from .user_repository import UserRepository
from .building_repository import BuildingRepository

RepositoryMap = Dict[str, Type[BaseRepository]]

_REPOSITORIES: RepositoryMap = {
    "users": UserRepository,
    "schools": SchoolRepository,
    "buildings": BuildingRepository,
}


def get_repository(resource: str) -> BaseRepository:
    try:
        repository_class: Type[BaseRepository] = _REPOSITORIES[resource]
    except KeyError as exc:
        available = ", ".join(sorted(_REPOSITORIES))
        raise ValueError(f"Repository '{resource}' not found. Available: {available}") from exc
    return repository_class(db)


__all__ = [
    "BaseRepository",
    "SchoolRepository",
    "UserRepository",
    "BuildingRepository",
    "get_repository",
]
