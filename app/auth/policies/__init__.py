from typing import Any, Callable, Dict, Optional, Type

from .account_policy import AccountPolicy
from .base_policy import BasePolicy, authentication_required
from .schools_policy import SchoolsPolicy
from .teachers_policy import TeachersPolicy
from .buildings_policy import BuildingsPolicy
from .events_policy import EventsPolicy


PolicyClass = Type[BasePolicy]


policies_registry: Dict[str, PolicyClass] = {
    'account': AccountPolicy,
    'teachers': TeachersPolicy,
    'schools': SchoolsPolicy,
    'buildings': BuildingsPolicy,
    'events': EventsPolicy,
}


def get_policy(resource: str, **kwargs: Any) -> Optional[BasePolicy]:
    policy_cls = policies_registry.get(resource)
    if not policy_cls:
        return None
    return policy_cls(**kwargs)


def user_allowed(resource: str, action: str, **kwargs: Any) -> bool:
    policy = get_policy(resource, **kwargs)
    if not policy:
        return False

    permission: Optional[Callable[..., bool]] = getattr(policy, action, None)
    if not callable(permission):
        return False

    return bool(permission())


__all__ = [
    'AccountPolicy',
    'TeachersPolicy',
    'SchoolsPolicy',
    'BuildingsPolicy',
    'EventsPolicy',
    'BasePolicy',
    'authentication_required',
    'policies_registry',
    'get_policy',
    'user_allowed',
]
