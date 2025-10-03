from functools import wraps
from typing import Callable, Dict, Optional, Type

from flask_login import current_user

def authentication_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return False
        return func(*args, **kwargs)
    return wrapper

class BasePolicy:
    def __init__(self, **kwargs):
        self.user_id = self._normalize_id(kwargs.get('user_id'))

    @staticmethod
    def _normalize_id(value):
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    def get_page(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def show(self):
        raise NotImplementedError

    def edit(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def _allow_only(self, role: str) -> bool:
        return current_user.role == role

    def _admin_all_user_self(self) -> bool:
        if current_user.role == 'admin':
            return True
        if current_user.role == 'user':
            assert self.user_id is not None
            return current_user.user_id == self.user_id
        return False


from .account_policy import AccountPolicy
from .users_policy import UsersPolicy
from .schools_policy import SchoolsPolicy

PolicyClass = Type[BasePolicy]


policies_registry: Dict[str, PolicyClass] = {
    'account': AccountPolicy,
    'users': UsersPolicy,
    'schools': SchoolsPolicy,
}


def get_policy(resource: str, **kwargs) -> Optional[BasePolicy]:
    policy_cls = policies_registry.get(resource)
    if not policy_cls:
        return None
    return policy_cls(**kwargs)


def user_allowed(resource: str, action: str, **kwargs) -> bool:
    policy = get_policy(resource, **kwargs)
    if not policy:
        return False

    permission: Optional[Callable] = getattr(policy, action, None)
    if not callable(permission):
        return False

    return bool(permission())


__all__ = [
    'AccountPolicy',
    'UsersPolicy',
    'SchoolsPolicy',
    'BasePolicy',
    'authentication_required',
    'policies_registry',
    'get_policy',
    'user_allowed',
]
