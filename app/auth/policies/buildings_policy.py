from typing import Any

from flask_login import current_user

from .base_policy import BasePolicy, authentication_required


class BuildingsPolicy(BasePolicy):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @authentication_required
    def get_page(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def create(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def edit(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def delete(self) -> bool:
        return current_user.role == 'admin'


__all__ = ['BuildingsPolicy']
