from typing import Any

from flask_login import current_user

from .base_policy import BasePolicy, authentication_required


class SchoolsPolicy(BasePolicy):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.school_id = kwargs.get('school_id')

    @authentication_required
    def get_page(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def create(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def show(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.school_id == self.school_id

    @authentication_required
    def edit(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def delete(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def manage_invite_code(self) -> bool:
        return current_user.role == 'admin'
