from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models import BuildingBooking, Event, Parent, Slot, SlotStatus, Teacher


class SlotRepository(BaseRepository[Slot]):
    model = Slot
    default_order_by = (Slot.start_time.asc(), Slot.slot_id.asc())

    def get_by_id(self, slot_id: int) -> Optional[Slot]:
        return self._get_one(slot_id=slot_id)

    def get_for_event(self, event_id: int) -> list[Slot]:
        stmt = (
            select(Slot)
            .where(Slot.event_id == event_id)
            .options(
                selectinload(Slot.teacher),
                selectinload(Slot.parent),
            )
            .order_by(Slot.start_time.asc(), Slot.slot_id.asc())
        )
        result = self.session.execute(stmt)
        return list(result.scalars().unique())

    def get_booked_for_parent(self, parent_id: int) -> list[Slot]:
        stmt = (
            select(Slot)
            .where(
                Slot.parent_id == parent_id,
                Slot.status == SlotStatus.booked,
            )
            .options(
                selectinload(Slot.teacher),
                selectinload(Slot.event)
                .selectinload(Event.building_bookings)
                .selectinload(BuildingBooking.building),
                selectinload(Slot.event).selectinload(Event.teachers),
            )
            .order_by(Slot.start_time.asc(), Slot.slot_id.asc())
        )
        result = self.session.execute(stmt)
        return list(result.scalars().unique())

    def find_existing(
        self,
        *,
        event_id: int,
        teacher_id: int,
        start_time: datetime,
    ) -> Optional[Slot]:
        stmt = (
            select(Slot)
            .where(
                Slot.event_id == event_id,
                Slot.teacher_id == teacher_id,
                Slot.start_time == start_time,
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_booked(
        self,
        *,
        event_id: int,
        teacher_id: int,
        parent_id: int,
        start_time: datetime,
        end_time: datetime,
    ) -> Slot:
        slot = Slot(
            event_id=event_id,
            teacher_id=teacher_id,
            parent_id=parent_id,
            start_time=start_time,
            end_time=end_time,
            status=SlotStatus.booked,
        )
        self.add(slot)
        self.commit()
        return slot

    def delete_slot(self, slot: Slot) -> None:
        self.session.delete(slot)
        self.commit()


__all__ = ["SlotRepository"]
