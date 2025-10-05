from typing import Optional

from sqlalchemy import func, select

from .base_repository import BaseRepository
from ..models import Building


class BuildingRepository(BaseRepository[Building]):
    model = Building
    default_order_by = (Building.name.asc(),)

    def get_by_id(self, building_id: int) -> Optional[Building]:
        return self._get_one(building_id=building_id)

    def get_for_school(self, school_id: int, search: str | None = None) -> list[Building]:
        stmt = select(Building).where(Building.school_id == school_id)
        if search:
            like_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(Building.name).like(like_pattern)
                | func.lower(Building.address).like(like_pattern)
            )
        stmt = stmt.order_by(Building.name.asc())
        result = self.session.execute(stmt)
        return list(result.scalars())

    def create(self, *, school_id: int, name: str, address: str) -> Building:
        building = Building(name=name, address=address, school_id=school_id)
        self.add(building)
        self.commit()
        return building

    def update(
        self,
        building_id: int,
        *,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[Building]:
        building = self.get_by_id(building_id)
        if not building:
            return None

        updated = False
        if name is not None:
            building.name = name
            updated = True
        if address is not None:
            building.address = address
            updated = True

        if updated:
            self.commit()

        return building

    def delete(self, building_id: int) -> bool:
        building = self.get_by_id(building_id)
        if not building:
            return False
        self.session.delete(building)
        self.commit()
        return True


__all__ = ['BuildingRepository']
