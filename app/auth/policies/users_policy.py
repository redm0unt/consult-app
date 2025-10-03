from flask_login import current_user

from . import BasePolicy, authentication_required


class UsersPolicy(BasePolicy):
    """Generic permissions for working with user records."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_user_id = self._normalize_id(kwargs.get('user_id'))

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
        return current_user.user_id == self.target_user_id

    @authentication_required
    def edit(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.user_id == self.target_user_id

    @authentication_required
    def delete(self) -> bool:
        return current_user.role == 'admin'
