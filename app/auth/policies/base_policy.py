from functools import wraps
from typing import Any, Callable

from flask_login import current_user


def authentication_required(func: Callable[..., bool]) -> Callable[..., bool]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> bool:
        if not current_user.is_authenticated:
            return False
        return func(*args, **kwargs)

    return wrapper


class BasePolicy:
    def __init__(self, **kwargs: Any) -> None:
        self.user_id = self._normalize_id(kwargs.get('user_id'))

    @staticmethod
    def _normalize_id(value: Any) -> Any:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    def get_page(self) -> bool:
        raise NotImplementedError

    def create(self) -> bool:
        raise NotImplementedError

    def show(self) -> bool:
        raise NotImplementedError

    def edit(self) -> bool:
        raise NotImplementedError

    def delete(self) -> bool:
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


__all__ = ["BasePolicy", "authentication_required"]