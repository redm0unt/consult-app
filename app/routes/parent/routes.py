from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from flask import abort, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.models import Event, Slot, SlotStatus, Teacher
from app.repositories import EventRepository, SlotRepository, get_repository
from app.routes import bp, get_pages


event_repository: EventRepository = get_repository('events')
slot_repository: SlotRepository = get_repository('slots')


@dataclass(frozen=True)
class ParentSlotView:
	index: int
	label: str
	state: str
	disabled: bool
	slot_id: Optional[int] = None


@dataclass(frozen=True)
class ParentTeacherView:
	teacher_id: int
	name: str
	email: str
	slots: tuple[ParentSlotView, ...]


@dataclass(frozen=True)
class ParentEventView:
	event_id: int
	title: str
	date_label: str
	time_label: str
	can_book: bool
	is_ongoing: bool


@dataclass(frozen=True)
class ParentBookingCard:
	slot_id: int
	event_title: str
	event_date_label: str
	event_time_label: str
	slot_time_label: str
	teacher_name: str
	teacher_email: str
	location_label: Optional[str]
	status_label: str
	status_modifier: str
	status_hint: Optional[str]
	can_cancel: bool


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


def resolve_slot_for_cancellation(
	*,
	slot_id: Optional[int],
	parent_id: int,
	event: Optional[Event] = None,
	teacher_id: Optional[int] = None,
	slot_index: Optional[int] = None,
	slot_times: Optional[list[tuple[int, datetime, datetime]]] = None,
) -> Optional[Slot]:
	slot: Optional[Slot] = None
	if slot_id is not None:
		slot = slot_repository.get_by_id(slot_id)
		if slot and event and slot.event_id != event.event_id:
			slot = None

	if slot is None and event and slot_times and teacher_id is not None and slot_index is not None:
		if 0 <= slot_index < len(slot_times):
			_, slot_start, _ = slot_times[slot_index]
			slot = slot_repository.find_existing(
				event_id=event.event_id,
				teacher_id=teacher_id,
				start_time=slot_start,
			)

	return slot


def attempt_cancel_slot(slot: Slot, parent_id: int) -> tuple[bool, str, str]:
	if slot.parent_id != parent_id:
		return False, 'warning', 'Эта запись больше не принадлежит вам.'
	reference_time = datetime.now(slot.start_time.tzinfo) if slot.start_time.tzinfo else datetime.now()
	if slot.start_time <= reference_time:
		return False, 'warning', 'Нельзя отменить встречу, время которой уже наступило.'
	try:
		slot_repository.delete_slot(slot)
	except SQLAlchemyError:
		slot_repository.rollback()
		return False, 'danger', 'Не удалось отменить запись. Попробуйте позже.'
	return True, 'success', 'Ваша запись отменена.'


def build_booking_cards(parent_id: int) -> list[ParentBookingCard]:
	slots = slot_repository.get_booked_for_parent(parent_id)
	cards: list[ParentBookingCard] = []
	for slot in slots:
		event = slot.event
		teacher = slot.teacher
		if not event or not teacher:
			continue
		reference_time = datetime.now(slot.start_time.tzinfo) if slot.start_time.tzinfo else datetime.now()
		status_label, status_modifier, status_hint = determine_slot_status(slot, reference_time)
		cards.append(
			ParentBookingCard(
				slot_id=slot.slot_id,
				event_title=event.name,
				event_date_label=format_date(slot.start_time),
				event_time_label=format_time_range(event.start_time, event.end_time),
				slot_time_label=format_time_range(slot.start_time, slot.end_time),
				teacher_name=teacher.full_name or teacher.email,
				teacher_email=teacher.email,
				location_label=find_location_label(event, teacher.teacher_id),
				status_label=status_label,
				status_modifier=status_modifier,
				status_hint=status_hint,
				can_cancel=slot.start_time > reference_time,
			),
		)
	return cards


def generate_slot_times(event: Event) -> list[tuple[int, datetime, datetime]]:
	total = event.consultations_count or 0
	duration = event.consultation_duration_minutes or 0
	if total <= 0 or duration <= 0:
		return []
	slots: list[tuple[int, datetime, datetime]] = []
	start_time = event.start_time
	for index in range(total):
		slot_start = start_time + timedelta(minutes=index * duration)
		slot_end = slot_start + timedelta(minutes=duration)
		slots.append((index, slot_start, slot_end))
	return slots


def build_event_view(event: Event, reference_time: datetime) -> ParentEventView:
	is_ongoing = event.start_time <= reference_time < event.end_time
	can_book = reference_time < event.end_time
	return ParentEventView(
		event_id=event.event_id,
		title=event.name or 'Мероприятие',
		date_label=format_date(event.start_time),
		time_label=format_time_range(event.start_time, event.end_time),
		can_book=can_book,
		is_ongoing=is_ongoing,
	)


def build_teacher_view(
	*,
	teacher: Teacher,
	event: Event,
	slot_times: Iterable[tuple[int, datetime, datetime]],
	existing_slots: dict[tuple[int, datetime], Slot],
	parent_id: Optional[int],
	reference_time: datetime,
) -> ParentTeacherView:
	slot_views: list[ParentSlotView] = []
	for index, slot_start, slot_end in slot_times:
		key = (teacher.teacher_id, slot_start)
		slot = existing_slots.get(key)
		label = format_time_range(slot_start, slot_end)
		state = 'available'
		disabled = False
		slot_id: Optional[int] = slot.slot_id if slot else None

		if slot and slot.status == SlotStatus.booked:
			if slot.parent_id == parent_id:
				state = 'mine'
				disabled = False
			else:
				state = 'taken'
				disabled = True

		if slot_start <= reference_time:
			if not slot or slot.status == SlotStatus.cancelled:
				state = 'closed'
			disabled = True

		slot_views.append(
			ParentSlotView(
				index=index,
				label=label,
				state=state,
				disabled=disabled,
				slot_id=slot_id,
			)
		)

	return ParentTeacherView(
		teacher_id=teacher.teacher_id,
		name=teacher.full_name or teacher.email,
		email=teacher.email,
		slots=tuple(slot_views),
	)


def ensure_parent_role() -> None:
	if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'parent':
		abort(403)


def resolve_booking_context() -> tuple[Optional[ParentEventView], list[ParentTeacherView]]:
	school = current_user.school
	if not school:
		return None, []

	event_repository.refresh_statuses_for_school(school.school_id)
	event = event_repository.get_closest_for_school(school.school_id, include_past=False)
	if not event:
		return None, []

	reference_time = datetime.now(event.start_time.tzinfo) if event.start_time.tzinfo else datetime.now()
	event_view = build_event_view(event, reference_time)

	slot_times = generate_slot_times(event)
	if not slot_times:
		return event_view, []

	slots = slot_repository.get_for_event(event.event_id)
	slot_map: dict[tuple[int, datetime], Slot] = {
		(slot.teacher_id, slot.start_time): slot
		for slot in slots
		if slot.status != SlotStatus.cancelled
	}

	teacher_views: list[ParentTeacherView] = []
	teachers_sorted = sorted(event.teachers, key=lambda teacher: teacher.full_name or teacher.email or '')
	parent_id = getattr(current_user, 'parent_id', None)

	for teacher in teachers_sorted:
		teacher_views.append(
			build_teacher_view(
				teacher=teacher,
				event=event,
				slot_times=slot_times,
				existing_slots=slot_map,
				parent_id=parent_id,
				reference_time=reference_time,
			)
		)

	return event_view, teacher_views


@bp.route('/parent/events', methods=['GET', 'POST'])
@login_required
def parent_events() -> ResponseReturnValue:
	ensure_parent_role()

	pages = get_pages()
	school = current_user.school
	if not school:
		flash('Ваша учётная запись не привязана к школе. Обратитесь к администратору.', 'warning')
		return render_template(
			'parent/events.html',
			page_title='Мероприятия',
			page_description='Запись на консультацию',
			pages=pages,
			event_view=None,
			teachers=[],
		)

	event_repository.refresh_statuses_for_school(school.school_id)
	event = event_repository.get_closest_for_school(school.school_id, include_past=False)
	if request.method == 'POST':
		if not event:
			flash('Нет доступного мероприятия для записи.', 'warning')
			return redirect(url_for('main.parent_events'))

		parent_id = getattr(current_user, 'parent_id', None)
		if parent_id is None:
			abort(403)

		action = request.form.get('action', 'book')
		slot_times = generate_slot_times(event)

		if action == 'cancel':
			slot = resolve_slot_for_cancellation(
				slot_id=request.form.get('slot_id', type=int),
				parent_id=parent_id,
				event=event,
				teacher_id=request.form.get('teacher_id', type=int),
				slot_index=request.form.get('slot_index', type=int),
				slot_times=slot_times,
			)
			if not slot:
				flash('Не удалось найти запись для отмены.', 'warning')
				return redirect(url_for('main.parent_events'))

			success, category, message = attempt_cancel_slot(slot, parent_id)
			flash(message, category)
			return redirect(url_for('main.parent_events'))

		teacher_id = request.form.get('teacher_id', type=int)
		slot_index = request.form.get('slot_index', type=int)

		if teacher_id is None or slot_index is None:
			flash('Не удалось определить выбранный слот.', 'warning')
			return redirect(url_for('main.parent_events'))

		teachers = {teacher.teacher_id: teacher for teacher in event.teachers}
		teacher = teachers.get(teacher_id)
		if not teacher:
			flash('Выбранный учитель не участвует в мероприятии.', 'warning')
			return redirect(url_for('main.parent_events'))

		if slot_index < 0 or slot_index >= len(slot_times):
			flash('Выбранный слот больше не доступен.', 'warning')
			return redirect(url_for('main.parent_events'))

		_, slot_start, slot_end = slot_times[slot_index]
		reference_time = datetime.now(slot_start.tzinfo) if slot_start.tzinfo else datetime.now()

		if slot_start <= reference_time:
			flash('Этот слот уже недоступен для записи.', 'warning')
			return redirect(url_for('main.parent_events'))

		existing = slot_repository.find_existing(
			event_id=event.event_id,
			teacher_id=teacher.teacher_id,
			start_time=slot_start,
		)
		if existing:
			if existing.status == SlotStatus.booked and existing.parent_id == parent_id:
				flash('Вы уже записаны на этот слот.', 'info')
			else:
				flash('Этот слот уже занят.', 'warning')
			return redirect(url_for('main.parent_events'))

		try:
			slot_repository.create_booked(
				event_id=event.event_id,
				teacher_id=teacher.teacher_id,
				parent_id=parent_id,
				start_time=slot_start,
				end_time=slot_end,
			)
		except SQLAlchemyError:
			slot_repository.rollback()
			flash('Не удалось записаться на консультацию. Попробуйте позже.', 'danger')
		else:
			flash('Запись успешно создана!', 'success')
		return redirect(url_for('main.parent_events'))

	event_view, teachers = resolve_booking_context()
	return render_template(
		'parent/events.html',
		page_title='Мероприятия',
		page_description='Запись на консультацию',
		pages=pages,
		event_view=event_view,
		teachers=teachers,
	)


@bp.route('/parent/bookings', methods=['GET', 'POST'])
@login_required
def parent_bookings() -> ResponseReturnValue:
	ensure_parent_role()
	parent_id = getattr(current_user, 'parent_id', None)
	if parent_id is None:
		abort(403)

	pages = get_pages()

	if request.method == 'POST':
		slot = resolve_slot_for_cancellation(
			slot_id=request.form.get('slot_id', type=int),
			parent_id=parent_id,
		)
		if not slot:
			flash('Не удалось найти запись для отмены.', 'warning')
		else:
			success, category, message = attempt_cancel_slot(slot, parent_id)
			flash(message, category)
		return redirect(url_for('main.parent_bookings'))

	booking_cards = build_booking_cards(parent_id)
	return render_template(
		'parent/bookings.html',
		page_title='Мои записи',
		page_description='Список забронированных консультаций',
		pages=pages,
		booking_cards=booking_cards,
	)


__all__ = ['parent_events', 'parent_bookings']
