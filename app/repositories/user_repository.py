from typing import List, Optional

from .base_repository import BaseRepository
from ..models import User, Admin, Parent, Teacher

ROLE_MODEL_MAP = {
    "teacher": Teacher,
    "parent": Parent,
    "admin": Admin,
}

class UserRepository(BaseRepository):
    model = User
    order_by = (User.created_at.desc(), User.last_name.asc(), User.first_name.asc(), User.middle_name.asc())
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._get_one(user_id=user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self._get_one(email=email)

    def get_all(self, sort: bool = False) -> List[User]:
        order_by = None
        if sort:
            order_by = self.order_by
        users = self._get_all(order_by=order_by)
        return users

    def create(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        school_id: Optional[int] = None,
        middle_name: Optional[str] = None,
        role: str = "user",
    ) -> User:
        model_cls = ROLE_MODEL_MAP.get(role, User)
        user_kwargs = {
            "email": email,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "school_id": school_id,
        }
        if model_cls is User:
            user_kwargs["role"] = role
        user = model_cls(**user_kwargs)
        if model_cls is not User and not getattr(user, "role", None):
            user.role = model_cls.__mapper_args__["polymorphic_identity"]
        user.set_password(password)
        self.db_connector.session.add(user)
        self.db_connector.session.commit()
        return user

    def update(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            updated = False
            if first_name is not None:
                user.first_name = first_name
                updated = True
            if last_name is not None:
                user.last_name = last_name
                updated = True
            if middle_name is not None:
                user.middle_name = middle_name
                updated = True
            if email is not None:
                user.email = email
                updated = True
            if updated:
                self.db_connector.session.commit()
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user:
            self.db_connector.session.delete(user)
            self.db_connector.session.commit()
            return True
        return False

    def get_authorized_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    def update_password(self, user_id: int, new_password: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.set_password(new_password)
            self.db_connector.session.commit()
        return user