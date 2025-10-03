from flask_login import current_user

from . import BasePolicy, authentication_required


class AccountPolicy(BasePolicy):
    """Permissions related to viewing and updating a personal account page."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # user_id represents the owner of the account page that is being viewed
        target_user_id = kwargs.get('target_user_id')
        if target_user_id is None:
            target_user_id = getattr(current_user, 'user_id', None)
        self.target_user_id = self._normalize_id(target_user_id)

    def create(self):
        return False

    @authentication_required
    def get_page(self):
        return self._can_view()

    @authentication_required
    def show(self):
        return self._can_view()

    @authentication_required
    def edit(self):
        return self._can_edit()

    def delete(self):
        return False

    @authentication_required
    def manage_school(self) -> bool:
        """Whether the user can edit school settings from the account page."""
        return current_user.role == 'admin'

    @authentication_required
    def view_invite_link(self) -> bool:
        """Whether the user can view/copy the parent invite link."""
        return current_user.role == 'admin'

    def _can_view(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.user_id == self.target_user_id

    def _can_edit(self) -> bool:
        if current_user.role == 'admin':
            return True
        return current_user.user_id == self.target_user_id
