from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from flask import abort, render_template, request
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required

from app.models import Event, EventStatus, Slot, SlotStatus
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


@dataclass(frozen=True)
class TeacherConsultationSlotView:
	slot_id: int
	slot_label: str
	parent_alias: str
	status_label: str
	status_modifier: str
	status_hint: Optional[str]
	slot_code: str


@dataclass(frozen=True)
class TeacherConsultationEventView:
	event_id: int
	title_text: str
	status_label: str
	status_modifier: str
	status_hint: Optional[str]
	date_label: str
	time_label: str
	location_label: Optional[str]
	slots: tuple[TeacherConsultationSlotView, ...]


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


def format_date(value: datetime) -> str:
	return value.strftime('%d.%m.%Y')


def format_time_range(start: datetime, end: datetime) -> str:
	return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"


def format_time_until(delta: timedelta) -> str:
	total_minutes = int(delta.total_seconds() // 60)
	if total_minutes <= 0:
		return 'Скоро'
	days, remainder = divmod(total_minutes, 1440)
	hours, minutes = divmod(remainder, 60)
	parts: list[str] = []
	if days:
		parts.append(f'{days} д.')
	if hours and len(parts) < 2:
		parts.append(f'{hours} ч.')
	if minutes and len(parts) < 2 and not days:
		parts.append(f'{minutes} мин.')
	return 'Через ' + ' '.join(parts)


def determine_slot_status(slot: Slot, reference_time: datetime) -> tuple[str, str, Optional[str]]:
	if slot.start_time <= reference_time < slot.end_time:
		return 'Идёт сейчас', 'live', None
	if slot.start_time > reference_time:
		hint = format_time_until(slot.start_time - reference_time)
		return 'Запланировано', 'upcoming', hint
	return 'Завершено', 'past', None


def find_location_label(event: Event, teacher_id: int) -> Optional[str]:
	for booking in event.building_bookings:
		if booking.teacher_id == teacher_id:
			if booking.classroom:
				return f"{booking.building.name}, ауд. {booking.classroom}"
			return booking.building.name
	return None


def build_parent_alias(slot: Slot) -> str:
	parent = slot.parent
	identifier_source: Optional[int] = None
	if parent and parent.parent_id:
		identifier_source = parent.parent_id
	elif slot.parent_id:
		identifier_source = slot.parent_id
	else:
		identifier_source = slot.slot_id
	suffix = str(identifier_source).zfill(4)[-4:]
	return f'Родитель #{suffix}'


def build_consultation_slot_view(slot: Slot) -> TeacherConsultationSlotView:
	reference_time = datetime.now(slot.start_time.tzinfo) if slot.start_time.tzinfo else datetime.now()
	status_label, status_modifier, status_hint = determine_slot_status(slot, reference_time)
	return TeacherConsultationSlotView(
		slot_id=slot.slot_id,
		slot_label=format_time_range(slot.start_time, slot.end_time),
		parent_alias=build_parent_alias(slot),
		status_label=status_label,
		status_modifier=status_modifier,
		status_hint=status_hint,
		slot_code=f"Слот №{slot.slot_id}",
	)


def build_consultation_event_view(event: Event, teacher_id: int) -> TeacherConsultationEventView:
	slots = [
		slot
		for slot in event.slots
		if slot.teacher_id == teacher_id and slot.status == SlotStatus.booked
	]
	slots.sort(key=lambda slot: (slot.start_time, slot.slot_id))
	return TeacherConsultationEventView(
		event_id=event.event_id,
		title_text=event.name or 'Без названия',
		status_label=STATUS_LABELS.get(event.status, event.status.value.title()),
		status_modifier=event.status.value,
		status_hint=build_status_hint(event),
		date_label=format_date(event.start_time),
		time_label=format_time_range(event.start_time, event.end_time),
		location_label=find_location_label(event, teacher_id),
		slots=tuple(build_consultation_slot_view(slot) for slot in slots),
	)


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


@bp.route('/teacher/consultations', methods=['GET'])
@login_required
def teacher_consultations() -> ResponseReturnValue:
	if current_user.role != 'teacher':
		abort(403)

	teacher_id = getattr(current_user, 'teacher_id', None)
	if teacher_id is None:
		abort(403)

	school = current_user.school
	pages = get_pages()
	if not school:
		return render_template(
			'teacher/consultations.html',
			page_title='Консультации',
			page_description='Ваши встречи с родителями',
			pages=pages,
			event_cards=(),
		)

	event_repository.refresh_statuses_for_school(school.school_id)
	events = event_repository.get_for_teacher(teacher_id)
	event_cards = tuple(build_consultation_event_view(event, teacher_id) for event in events)

	return render_template(
		'teacher/consultations.html',
		page_title='Консультации',
		page_description='Ваши встречи с родителями',
		pages=pages,
		event_cards=event_cards,
	)


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


__all__ = ['teacher_consultations', 'teacher_events']
