from datetime import datetime
from typing import Optional

from sqlalchemy import case, select
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models import BuildingBooking, Event, EventStatus, Slot, Teacher, event_teachers_table


class EventRepository(BaseRepository[Event]):
    model = Event
    default_order_by = (Event.start_time.asc(), Event.event_id.desc())

    def get_by_id(self, event_id: int) -> Optional[Event]:
        return self._get_one(event_id=event_id)

    def get_for_school(self, school_id: int) -> list[Event]:
        status_order = case(
            (Event.status == EventStatus.ongoing, 0),
            (Event.status == EventStatus.scheduled, 1),
            (Event.status == EventStatus.completed, 2),
            (Event.status == EventStatus.cancelled, 3),
            else_=4,
        )
        stmt = (
            select(Event)
            .where(Event.school_id == school_id)
            .options(
                selectinload(Event.slots),
                selectinload(Event.building_bookings).selectinload(BuildingBooking.building),
                selectinload(Event.teachers),
            )
            .order_by(status_order, Event.start_time.asc(), Event.event_id.desc())
        )
        result = self.session.execute(stmt)
        return list(result.scalars().unique())

    def get_for_teacher(self, teacher_id: int) -> list[Event]:
        status_order = case(
            (Event.status == EventStatus.ongoing, 0),
            (Event.status == EventStatus.scheduled, 1),
            (Event.status == EventStatus.completed, 2),
            (Event.status == EventStatus.cancelled, 3),
            else_=4,
        )
        stmt = (
            select(Event)
            .join(event_teachers_table, event_teachers_table.c.event_id == Event.event_id)
            .where(event_teachers_table.c.teacher_id == teacher_id)
            .options(
                selectinload(Event.slots),
                selectinload(Event.building_bookings).selectinload(BuildingBooking.building),
                selectinload(Event.teachers),
            )
            .order_by(status_order, Event.start_time.asc(), Event.event_id.desc())
        )
        result = self.session.execute(stmt)
        return list(result.scalars().unique())

    def get_closest_for_school(
        self,
        school_id: int,
        *,
        reference_time: Optional[datetime] = None,
        include_past: bool = False,
    ) -> Optional[Event]:
        now = reference_time or datetime.now()
        status_order = case(
            (Event.status == EventStatus.ongoing, 0),
            (Event.status == EventStatus.scheduled, 1),
            (Event.status == EventStatus.completed, 2),
            (Event.status == EventStatus.cancelled, 3),
            else_=4,
        )
        stmt = (
            select(Event)
            .where(Event.school_id == school_id)
            .options(
                selectinload(Event.slots).selectinload(Slot.teacher),
                selectinload(Event.building_bookings).selectinload(BuildingBooking.building),
                selectinload(Event.teachers),
            )
            .order_by(status_order, Event.start_time.asc(), Event.event_id.desc())
        )
        if not include_past:
            stmt = stmt.where(Event.end_time >= now)

        stmt = stmt.limit(1)
        result = self.session.execute(stmt)
        return result.scalars().unique().first()

    def _resolve_teachers(self, teacher_ids: Optional[set[int]]) -> list[Teacher]:
        if not teacher_ids:
            return []
        stmt = select(Teacher).where(Teacher.teacher_id.in_(teacher_ids))
        result = self.session.execute(stmt)
        return list(result.scalars().unique())

    def create(
        self,
        *,
        name: str,
        school_id: int,
        start_time: datetime,
        end_time: datetime,
        consultations_count: int = 0,
        consultation_duration_minutes: int = 15,
        status: EventStatus = EventStatus.scheduled,
        teacher_ids: Optional[set[int]] = None,
    ) -> Event:
        event = Event(
            name=name,
            school_id=school_id,
            start_time=start_time,
            end_time=end_time,
            consultations_count=consultations_count,
            consultation_duration_minutes=consultation_duration_minutes,
            status=status,
        )
        if teacher_ids is not None:
            event.teachers = self._resolve_teachers(teacher_ids)
        self.add(event)
        self.commit()
        return event

    def update(
        self,
        event_id: int,
        *,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        consultations_count: Optional[int] = None,
        consultation_duration_minutes: Optional[int] = None,
        teacher_ids: Optional[set[int]] = None,
    ) -> Optional[Event]:
        event = self.get_by_id(event_id)
        if not event:
            return None

        updated = False
        if name is not None:
            event.name = name
            updated = True
        if start_time is not None:
            event.start_time = start_time
            updated = True
        if end_time is not None:
            event.end_time = end_time
            updated = True
        if consultations_count is not None:
            event.consultations_count = consultations_count
            updated = True
        if consultation_duration_minutes is not None:
            event.consultation_duration_minutes = consultation_duration_minutes
            updated = True
        if teacher_ids is not None:
            event.teachers = self._resolve_teachers(teacher_ids)
            updated = True
        if updated:
            self.commit()

        return event

    def delete(self, event_id: int) -> bool:
        event = self.get_by_id(event_id)
        if not event:
            return False
        self.session.delete(event)
        self.commit()
        return True

    def refresh_statuses_for_school(self, school_id: int, *, reference_time: Optional[datetime] = None) -> None:
        now = reference_time or datetime.now()
        stmt = select(Event).where(Event.school_id == school_id)
        result = self.session.execute(stmt)
        events = list(result.scalars())

        updated = False
        for event in events:
            if event.status == EventStatus.cancelled:
                continue

            if event.end_time <= now:
                desired_status = EventStatus.completed
            elif event.start_time <= now:
                desired_status = EventStatus.ongoing
            else:
                desired_status = EventStatus.scheduled

            if event.status != desired_status:
                event.status = desired_status
                updated = True

        if updated:
            self.commit()


__all__ = ["EventRepository"]
