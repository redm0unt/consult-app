from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.auth import check_rights
from app.auth.policies import EventsPolicy
from app.models import Event, EventStatus, SlotStatus, Teacher, db
from app.repositories import EventRepository, get_repository
from app.routes import bp, get_pages


event_repository: EventRepository = get_repository('events')


@dataclass(frozen=True)
class MetaItem:
    label: str
    value: str


@dataclass(frozen=True)
class StatItem:
    label: str
    value: str


@dataclass(frozen=True)
class BookingItem:
    building: str
    rooms: tuple[str, ...]


@dataclass(frozen=True)
class EventViewModel:
    event_id: int
    title_label: Optional[str]
    title_text: str
    period_text: str
    info_label: Optional[str]
    status_label: str
    status_modifier: str
    status_hint: Optional[str]
    meta_items: tuple[MetaItem, ...]
    stats: tuple[StatItem, ...]
    bookings: tuple[BookingItem, ...]
    consultations_count: int
    duration_minutes: int
    consultation_duration_minutes: int
    teacher_ids: tuple[int, ...]
    teacher_names: tuple[str, ...]
    menu_config: Optional[dict[str, object]]


STATUS_LABELS: dict[EventStatus, str] = {
    EventStatus.scheduled: 'Запланировано',
    EventStatus.ongoing: 'Идёт сейчас',
    EventStatus.completed: 'Завершено',
    EventStatus.cancelled: 'Отменено',
}

DATETIME_INPUT_FORMAT = '%Y-%m-%dT%H:%M'


def format_datetime_value(value: datetime) -> str:
    return value.strftime('%d.%m.%Y %H:%M')


def format_input_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_INPUT_FORMAT)


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


def parse_datetime_input(value: str, *, field_label: str, errors: list[str]) -> Optional[datetime]:
    if not value:
        errors.append(f'Укажите {field_label}')
        return None
    try:
        return datetime.strptime(value, DATETIME_INPUT_FORMAT)
    except ValueError:
        errors.append(f'Некорректный формат для поля "{field_label}"')
        return None


def build_meta_items(event: Event) -> tuple[MetaItem, ...]:
    meta: list[MetaItem] = [
        MetaItem(label='Начало', value=format_datetime_value(event.start_time)),
        MetaItem(label='Окончание', value=format_datetime_value(event.end_time)),
        MetaItem(label='Создано', value=format_datetime_value(event.created_at)),
    ]
    return tuple(meta)


def build_stats(event: Event) -> tuple[StatItem, ...]:
    active_slots = [slot for slot in event.slots if slot.status != SlotStatus.cancelled]
    slot_count = len(active_slots)
    teacher_count = len(getattr(event, 'teachers', []) or [])
    if teacher_count == 0:
        teacher_count = len({slot.teacher_id for slot in active_slots if slot.teacher_id})
    parent_count = len({slot.parent_id for slot in active_slots if slot.parent_id})
    building_count = len({booking.building_id for booking in event.building_bookings})
    classroom_count = len({
        (booking.building_id, booking.classroom)
        for booking in event.building_bookings
        if booking.classroom
    })
    duration_minutes = (
        event.duration_minutes
        if getattr(event, 'duration_minutes', None) is not None
        else int((event.end_time - event.start_time).total_seconds() // 60)
    )

    stats: list[StatItem] = [
        StatItem(label='Консультаций', value=str(event.consultations_count or 0)),
        StatItem(label='Длительность, мин', value=str(duration_minutes)),
        StatItem(label='Консультация, мин', value=str(event.consultation_duration_minutes or 0)),
        StatItem(label='Записей', value=str(slot_count)),
        StatItem(label='Педагогов', value=str(teacher_count)),
        StatItem(label='Родителей', value=str(parent_count)),
        StatItem(label='Зданий', value=str(building_count)),
    ]

    stats.append(StatItem(label='Аудиторий', value=str(classroom_count)))
    return tuple(stats)


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


def build_menu_config(event: Event, *, can_edit: bool, can_delete: bool) -> Optional[dict[str, object]]:
    items: list[dict[str, object]] = []
    duration_minutes = (
        event.duration_minutes
        if getattr(event, 'duration_minutes', None) is not None
        else int((event.end_time - event.start_time).total_seconds() // 60)
    )
    teacher_ids = [teacher.teacher_id for teacher in getattr(event, 'teachers', [])]
    if can_edit:
        items.append(
            {
                'action': 'edit',
                'label': 'Править',
                'attrs': {
                    'data-event-id': str(event.event_id),
                    'data-event-start': format_input_datetime(event.start_time),
                    'data-event-name': event.name,
                    'data-event-consultations': str(event.consultations_count),
                    'data-event-consultation-duration': str(event.consultation_duration_minutes),
                    'data-event-end': format_input_datetime(event.end_time),
                    'data-event-duration-minutes': str(duration_minutes),
                    'data-event-teachers': ','.join(str(teacher_id) for teacher_id in teacher_ids),
                },
            }
        )
    if can_delete:
        items.append(
            {
                'action': 'delete',
                'label': 'Удалить',
                'danger': True,
                'attrs': {
                    'data-event-id': str(event.event_id),
                    'data-event-period': format_event_period(event.start_time, event.end_time),
                    'data-event-name': event.name,
                    'data-event-consultations': str(event.consultations_count),
                },
            }
        )
    if not items:
        return None
    return {
        'aria_label': 'Действия с мероприятием',
        'items': items,
    }


def build_event_view_model(event: Event, *, can_edit: bool, can_delete: bool) -> EventViewModel:
    status_label = STATUS_LABELS.get(event.status, event.status.value.title())
    duration_minutes = (
        event.duration_minutes
        if getattr(event, 'duration_minutes', None) is not None
        else int((event.end_time - event.start_time).total_seconds() // 60)
    )
    teachers = tuple(getattr(event, 'teachers', []) or ())
    teacher_ids = tuple(teacher.teacher_id for teacher in teachers)
    teacher_names = tuple(teacher.full_name or teacher.email for teacher in teachers)
    return EventViewModel(
        event_id=event.event_id,
        title_label='Мероприятие',
        title_text=event.name or 'Без названия',
        period_text=format_event_period(event.start_time, event.end_time),
        info_label=None,
        status_label=status_label,
        status_modifier=event.status.value,
        status_hint=build_status_hint(event),
        meta_items=build_meta_items(event),
        stats=build_stats(event),
        bookings=build_bookings(event),
        consultations_count=event.consultations_count or 0,
        duration_minutes=duration_minutes,
        consultation_duration_minutes=event.consultation_duration_minutes or 0,
        teacher_ids=teacher_ids,
        teacher_names=teacher_names,
        menu_config=build_menu_config(event, can_edit=can_edit, can_delete=can_delete),
    )


def matches_search(view_model: EventViewModel, query_lower: str) -> bool:
    if query_lower in str(view_model.event_id):
        return True
    if query_lower and query_lower in view_model.title_text.lower():
        return True
    if query_lower and query_lower in view_model.period_text.lower():
        return True
    if query_lower and query_lower in view_model.status_label.lower():
        return True
    if query_lower and query_lower in str(view_model.consultations_count):
        return True
    if query_lower and query_lower in str(view_model.duration_minutes):
        return True
    if query_lower and query_lower in str(view_model.consultation_duration_minutes):
        return True
    for teacher_name in view_model.teacher_names:
        if query_lower in teacher_name.lower():
            return True

    for meta in view_model.meta_items:
        if query_lower in meta.label.lower() or query_lower in meta.value.lower():
            return True

    for stat in view_model.stats:
        if query_lower in stat.label.lower() or query_lower in stat.value.lower():
            return True

    for booking in view_model.bookings:
        if query_lower in booking.building.lower():
            return True
        for room in booking.rooms:
            if query_lower in room.lower():
                return True

    return False


@bp.route('/events', methods=['GET', 'POST'])
@login_required
@check_rights('events', 'get_page')
def events() -> ResponseReturnValue:
    events_policy = EventsPolicy(user_id=current_user.user_id)
    can_create = events_policy.create()
    can_edit = events_policy.edit()
    can_delete = events_policy.delete()

    school = current_user.school
    search_query = (request.args.get('q') or '').strip()

    teachers: list[Teacher] = []
    teacher_map: dict[int, Teacher] = {}
    teacher_options: list[dict[str, str]] = []
    if school:
        teacher_stmt = (
            select(Teacher)
            .where(Teacher.school_id == school.school_id)
            .order_by(Teacher.last_name.asc(), Teacher.first_name.asc(), Teacher.middle_name.asc())
        )
        teachers = db.session.execute(teacher_stmt).scalars().all()
        teacher_map = {teacher.teacher_id: teacher for teacher in teachers}
        teacher_options = [
            {
                'id': teacher.teacher_id,
                'name': teacher.full_name,
                'email': teacher.email,
            }
            for teacher in teachers
        ]

    form_data: dict[str, object] = {}
    form_mode = 'create'
    form_event_id: Optional[int] = None
    show_event_form = False

    if request.method == 'POST':
        if not can_create:
            abort(403)

        form_type = (request.form.get('form_type') or 'create').strip().lower()

        if form_type == 'delete':
            event_id = request.form.get('event_id', type=int)
            if not event_id:
                flash('Не удалось определить мероприятие для удаления', 'warning')
                return redirect(url_for('main.events'))

            event = event_repository.get_by_id(event_id)
            if not event or not school or event.school_id != school.school_id:
                flash('Мероприятие не найдено или не относится к вашей школе', 'warning')
                return redirect(url_for('main.events'))

            try:
                event_repository.delete(event_id)
            except SQLAlchemyError:
                event_repository.rollback()
                current_app.logger.exception('Failed to delete event %s', event_id)
                flash('Не удалось удалить мероприятие, попробуйте ещё раз позже', 'danger')
            else:
                flash('Мероприятие успешно удалено!', 'success')
            return redirect(url_for('main.events'))

        start_value = (request.form.get('start_time') or '').strip()
        name_value = (request.form.get('name') or '').strip()
        consultations_value_str = (request.form.get('consultations_count') or '').strip()
        consultation_duration_value_str = (request.form.get('consultation_duration_minutes') or '').strip()
        current_step_raw = (request.form.get('current_step') or 'basic').strip().lower()
        current_step_value = 'teachers' if current_step_raw == 'teachers' else 'basic'

        teacher_ids_raw = request.form.getlist('teacher_ids')
        selected_teacher_ids_set: set[int] = set()
        selected_teacher_ids_view: list[str] = []
        invalid_teacher_values: list[str] = []
        unknown_teacher_ids: list[str] = []

        for raw_teacher_id in teacher_ids_raw:
            cleaned = raw_teacher_id.strip()
            if not cleaned:
                continue
            if not cleaned.isdigit():
                invalid_teacher_values.append(cleaned)
                continue
            teacher_id = int(cleaned)
            if teacher_id not in teacher_map:
                unknown_teacher_ids.append(cleaned)
                continue
            if teacher_id not in selected_teacher_ids_set:
                selected_teacher_ids_set.add(teacher_id)
                selected_teacher_ids_view.append(str(teacher_id))

        form_data = {
            'start_time': start_value,
            'name': name_value,
            'consultations_count': consultations_value_str,
            'consultation_duration_minutes': consultation_duration_value_str,
            'calculated_end_time': '',
            'selected_teacher_ids': selected_teacher_ids_view,
            'current_step': current_step_value,
        }

        errors: list[str] = []

        missing_teacher_selection = bool(teacher_map) and not selected_teacher_ids_set

        if invalid_teacher_values:
            errors.append('Переданы некорректные значения учителей — обновите страницу и попробуйте снова')
            current_step_value = 'teachers'
            form_data['current_step'] = current_step_value
        if unknown_teacher_ids:
            errors.append('Выбранные учителя не найдены или не относятся к вашей школе')
            current_step_value = 'teachers'
            form_data['current_step'] = current_step_value

        if not name_value:
            errors.append('Укажите название мероприятия')
        elif len(name_value) > 120:
            errors.append('Название мероприятия не должно превышать 120 символов')

        consultations_count_value: Optional[int] = None
        if consultations_value_str:
            if consultations_value_str.isdigit():
                consultations_count_value = int(consultations_value_str)
                if consultations_count_value < 1:
                    errors.append('Количество консультаций должно быть не меньше 1')
                    consultations_count_value = None
            else:
                errors.append('Количество консультаций должно быть числом')
        else:
            errors.append('Укажите количество консультаций')

        consultation_duration_value: Optional[int] = None
        if consultation_duration_value_str:
            if consultation_duration_value_str.isdigit():
                consultation_duration_value = int(consultation_duration_value_str)
                if consultation_duration_value < 1:
                    errors.append('Длительность одной консультации должна быть не меньше 1 минуты')
                    consultation_duration_value = None
            else:
                errors.append('Длительность одной консультации должна быть числом')
        else:
            errors.append('Укажите длительность одной консультации')

        start_dt = parse_datetime_input(start_value, field_label='время начала', errors=errors)
        end_dt: Optional[datetime] = None
        total_minutes = None
        if (
            start_dt
            and consultations_count_value is not None
            and consultation_duration_value is not None
        ):
            total_minutes = consultations_count_value * consultation_duration_value
            end_dt = start_dt + timedelta(minutes=total_minutes)
            if total_minutes <= 0:
                errors.append('Итоговая длительность мероприятия должна быть больше нуля')

        event: Optional[Event] = None

        if form_type == 'update':
            form_mode = 'update'
            event_id = request.form.get('event_id', type=int)
            form_event_id = event_id
            if not event_id:
                errors.append('Не удалось определить мероприятие для обновления')
            elif not can_edit:
                abort(403)
            else:
                event = event_repository.get_by_id(event_id)
                if not event or not school or event.school_id != school.school_id:
                    errors.append('Мероприятие не найдено или не относится к вашей школе')
                else:
                    if not selected_teacher_ids_set and getattr(event, 'teachers', None):
                        existing_teacher_ids = [
                            teacher.teacher_id
                            for teacher in event.teachers
                            if teacher.teacher_id in teacher_map
                        ]
                        selected_teacher_ids_set = set(existing_teacher_ids)
                        selected_teacher_ids_view = [str(teacher_id) for teacher_id in existing_teacher_ids]
                        form_data['selected_teacher_ids'] = selected_teacher_ids_view

        if missing_teacher_selection and not selected_teacher_ids_set:
            errors.append('Выберите хотя бы одного учителя для мероприятия')
            current_step_value = 'teachers'
            form_data['current_step'] = current_step_value

        if start_dt and end_dt:
            form_data['calculated_end_time'] = format_event_period(start_dt, end_dt)
        else:
            form_data['calculated_end_time'] = ''

        if errors:
            show_event_form = True
            for error in errors:
                flash(error, 'warning')
        else:
            if not school:
                flash('Не удаётся определить школу пользователя — обратитесь к администратору системы', 'danger')
                show_event_form = True
            else:
                consultations_count_safe = consultations_count_value if consultations_count_value is not None else 0
                consultation_duration_safe = consultation_duration_value if consultation_duration_value is not None else 0
                try:
                    if form_type == 'create':
                        event_repository.create(
                            name=name_value,
                            school_id=school.school_id,
                            start_time=start_dt,
                            end_time=end_dt,
                            consultations_count=consultations_count_safe,
                            consultation_duration_minutes=consultation_duration_safe,
                            teacher_ids=selected_teacher_ids_set,
                        )
                    elif form_type == 'update' and event:
                        event_repository.update(
                            event_id=event.event_id,
                            name=name_value,
                            start_time=start_dt,
                            end_time=end_dt,
                            consultations_count=consultations_count_value,
                            consultation_duration_minutes=consultation_duration_value,
                            teacher_ids=selected_teacher_ids_set,
                        )
                except SQLAlchemyError:
                    event_repository.rollback()
                    action = 'обновить' if form_type == 'update' else 'создать'
                    current_app.logger.exception('Failed to %s event', action)
                    flash('Не удалось сохранить данные мероприятия — попробуйте ещё раз позже', 'danger')
                    show_event_form = True
                else:
                    if form_type == 'update':
                        flash('Мероприятие успешно обновлено!', 'success')
                    else:
                        flash('Мероприятие успешно создано!', 'success')
                    return redirect(url_for('main.events'))

    view_models: list[EventViewModel] = []
    if school:
        event_repository.refresh_statuses_for_school(school.school_id)
        raw_events: Iterable[Event] = event_repository.get_for_school(school.school_id)
        view_models = [
            build_event_view_model(event, can_edit=can_edit, can_delete=can_delete)
            for event in raw_events
        ]
        if search_query:
            search_lower = search_query.lower()
            view_models = [
                view_model
                for view_model in view_models
                if matches_search(view_model, search_lower)
            ]

    if not form_data:
        form_data = {
            'name': '',
            'start_time': '',
            'consultations_count': '1',
            'consultation_duration_minutes': '15',
            'calculated_end_time': '',
            'selected_teacher_ids': [str(teacher.teacher_id) for teacher in teachers],
            'current_step': 'basic',
        }

    return render_template(
        'admin/events.html',
        page_title='Мероприятия',
        pages=get_pages(),
        events=view_models,
        search_query=search_query,
        can_manage_events=can_create,
        event_form_data=form_data,
        show_event_form=show_event_form,
        event_form_mode=form_mode,
        event_form_event_id=form_event_id,
        teacher_options=teacher_options,
    )
