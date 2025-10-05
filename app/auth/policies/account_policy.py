from typing import Any

from flask_login import current_user

from .base_policy import BasePolicy, authentication_required


class AccountPolicy(BasePolicy):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        target_user_id = kwargs.get('target_user_id')
        if target_user_id is None:
            target_user_id = getattr(current_user, 'user_id', None)
        self.target_user_id = self._normalize_id(target_user_id)

    def create(self) -> bool:
        return False

    @authentication_required
    def get_page(self) -> bool:
        return self._can_view()

    @authentication_required
    def show(self) -> bool:
        return self._can_view()

    @authentication_required
    def edit(self) -> bool:
        return self._can_edit()

    def delete(self) -> bool:
        return False

    @authentication_required
    def manage_school(self) -> bool:
        return current_user.role == 'admin'

    @authentication_required
    def view_invite_link(self) -> bool:
        return current_user.role == 'admin'

    def _can_view(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.user_id == self.target_user_id

    def _can_edit(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.user_id == self.target_user_id
