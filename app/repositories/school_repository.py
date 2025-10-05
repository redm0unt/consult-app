from typing import Optional

from .base_repository import BaseRepository
from ..models import School


class SchoolRepository(BaseRepository):
    model = School
    default_order_by = (School.school_name.asc(),)

    def get_by_id(self, school_id: int) -> Optional[School]:
        return self._get_one(school_id=school_id)

    def get_by_invite_code(self, invite_code: str) -> Optional[School]:
        return self._get_one(invite_code=invite_code)

    def get_all(self, sort: bool = False) -> list[School]:
        order_by = self.default_order_by if sort else ()
        return self._get_all(order_by=order_by)

    def create(self, school_name: str) -> School:
        school = School(school_name=school_name)
        school.assign_invite_code()
        self.add(school)
        self.commit()
        return school

    def update(
        self,
        school_id: int,
        school_name: Optional[str] = None,
        invite_code: Optional[str] = None,
        regenerate_invite_code: bool = False,
    ) -> Optional[School]:
        school = self.get_by_id(school_id)
        if school:
            updated = False
            if school_name is not None:
                school.school_name = school_name
                updated = True
            if invite_code is not None:
                if len(invite_code) == school.INVITE_CODE_LENGTH:
                    school.invite_code = invite_code
                    updated = True
                else:
                    raise ValueError(f"Invite code must be {school.INVITE_CODE_LENGTH} characters long")
            elif regenerate_invite_code:
                school.assign_invite_code()
                updated = True
            if updated:
                self.commit()
        return school

    def regenerate_invite_code(self, school_id: int) -> Optional[str]:
        school = self.update(school_id, regenerate_invite_code=True)
        if school:
            return school.invite_code
        return None

    def delete(self, school_id: int) -> bool:
        school = self.get_by_id(school_id)
        if not school:
            return False
        self.session.delete(school)
        self.commit()
        return True
