from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from flask import abort, render_template, request
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required

from app.models import Event, EventStatus
from app.repositories import EventRepository, get_repository
from app.routes import bp, get_pages


event_repository: EventRepository = get_repository('events')


@dataclass(frozen=True)
class MetaItem:
	label: str
	value: str


@dataclass(frozen=True)
class BookingItem:
	building: str
	rooms: tuple[str, ...]


@dataclass(frozen=True)
class TeacherEventViewModel:
	event_id: int
	title_text: str
	status_label: str
	status_modifier: str
	status_hint: Optional[str]
	period_text: str
	consultations_count: int
	consultation_duration_minutes: int
	duration_minutes: int
	meta_items: tuple[MetaItem, ...]
	bookings: tuple[BookingItem, ...]


STATUS_LABELS: dict[EventStatus, str] = {
	EventStatus.scheduled: 'Запланировано',
	EventStatus.ongoing: 'Идёт сейчас',
	EventStatus.completed: 'Завершено',
	EventStatus.cancelled: 'Отменено',
}


def format_datetime_value(value: datetime) -> str:
	return value.strftime('%d.%m.%Y %H:%M')


def format_event_period(start: datetime, end: datetime) -> str:
	same_day = start.date() == end.date()
	if same_day:
		start_date = start.strftime('%d.%m.%Y')
		return f"{start_date}, {start.strftime('%H:%M')} — {end.strftime('%H:%M')}"
	return f"{start.strftime('%d.%m.%Y %H:%M')} — {end.strftime('%d.%m.%Y %H:%M')}"


def build_status_hint(event: Event) -> Optional[str]:
	if event.status == EventStatus.scheduled:
		return f"Старт {format_datetime_value(event.start_time)}"
	if event.status == EventStatus.ongoing:
		return f"Идёт до {format_datetime_value(event.end_time)}"
	if event.status == EventStatus.completed:
		return f"Завершено {format_datetime_value(event.end_time)}"
	if event.status == EventStatus.cancelled:
		return 'Мероприятие отменено'
	return None


def build_meta_items(event: Event) -> tuple[MetaItem, ...]:
	meta: list[MetaItem] = [
		MetaItem(label='Начало', value=format_datetime_value(event.start_time)),
		MetaItem(label='Окончание', value=format_datetime_value(event.end_time)),
		MetaItem(label='Консультаций', value=str(event.consultations_count or 0)),
		MetaItem(label='Длительность консультации', value=f"{event.consultation_duration_minutes or 0} мин"),
		MetaItem(
			label='Длительность мероприятия',
			value=f"{event.duration_minutes or 0} мин",
		),
	]
	return tuple(meta)


def build_bookings(event: Event) -> tuple[BookingItem, ...]:
	bookings_map: dict[str, set[str]] = {}

	for booking in event.building_bookings:
		building_name = booking.building.name if booking.building else 'Помещение не указано'
		rooms = bookings_map.setdefault(building_name, set())
		if booking.classroom:
			rooms.add(booking.classroom)

	bookings_sorted = sorted(bookings_map.items(), key=lambda item: item[0].lower())
	bookings: list[BookingItem] = [
		BookingItem(building=building, rooms=tuple(sorted(rooms)))
		for building, rooms in bookings_sorted
	]
	return tuple(bookings)


def build_event_view_model(event: Event) -> TeacherEventViewModel:
	status_label = STATUS_LABELS.get(event.status, event.status.value.title())
	duration_minutes = event.duration_minutes or int((event.end_time - event.start_time).total_seconds() // 60)
	return TeacherEventViewModel(
		event_id=event.event_id,
		title_text=event.name or 'Без названия',
		status_label=status_label,
		status_modifier=event.status.value,
		status_hint=build_status_hint(event),
		period_text=format_event_period(event.start_time, event.end_time),
		consultations_count=event.consultations_count or 0,
		consultation_duration_minutes=event.consultation_duration_minutes or 0,
		duration_minutes=duration_minutes,
		meta_items=build_meta_items(event),
		bookings=build_bookings(event),
	)


def matches_search(view_model: TeacherEventViewModel, query_lower: str) -> bool:
	searchable_values = [
		str(view_model.event_id),
		view_model.title_text,
		view_model.status_label,
		view_model.status_modifier,
		view_model.period_text,
		view_model.status_hint or '',
		str(view_model.consultations_count),
		str(view_model.consultation_duration_minutes),
		str(view_model.duration_minutes),
	]

	for value in searchable_values:
		if query_lower in value.lower():
			return True

	for meta in view_model.meta_items:
		if query_lower in meta.label.lower() or query_lower in meta.value.lower():
			return True

	for booking in view_model.bookings:
		if query_lower in booking.building.lower():
			return True
		for room in booking.rooms:
			if query_lower in room.lower():
				return True

	return False


@bp.route('/teacher/events', methods=['GET'])
@login_required
def teacher_events() -> ResponseReturnValue:
	if current_user.role != 'teacher':
		abort(403)

	teacher_id = getattr(current_user, 'teacher_id', None)
	if teacher_id is None:
		abort(403)

	school = current_user.school
	search_query = (request.args.get('q') or '').strip()

	view_models: list[TeacherEventViewModel] = []
	if school:
		event_repository.refresh_statuses_for_school(school.school_id)
		raw_events: Iterable[Event] = event_repository.get_for_teacher(teacher_id)
		view_models = [build_event_view_model(event) for event in raw_events]
		if search_query:
			search_lower = search_query.lower()
			view_models = [
				view_model
				for view_model in view_models
				if matches_search(view_model, search_lower)
			]

	return render_template(
		'teacher/events.html',
		page_title='Мероприятия',
		page_description='Встречи и консультации, где вы участвуете',
		pages=get_pages(),
		events=view_models,
		search_query=search_query,
	)


__all__ = ['teacher_events']
