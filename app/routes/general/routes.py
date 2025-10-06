from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Optional

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.auth import check_rights
from app.auth.policies import AccountPolicy
from app.models import Event, Slot, SlotStatus, Teacher, User, db
from app.repositories import EventRepository, get_repository
from app.routes import bp, get_pages


event_repository: EventRepository = get_repository('events')


@dataclass(frozen=True)
class DashboardSlotView:
    label: str
    state: str


@dataclass(frozen=True)
class DashboardTeacherView:
    teacher_id: int
    name: str
    email: str
    slots: tuple[DashboardSlotView, ...]
    total_slots: int
    taken_slots: int
    has_availability: bool


@dataclass(frozen=True)
class DashboardEventView:
    event_id: int
    name: str
    date_label: str
    time_label: str
    start_iso: str
    end_iso: str
    is_ongoing: bool
    is_future: bool


def format_time_range(start: datetime, end: datetime) -> str:
    return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"


def format_date(value: datetime) -> str:
    return value.strftime('%d.%m.%Y')


def build_dashboard_slot(slot_start: datetime, slot_end: datetime, slot: Optional[Slot]) -> DashboardSlotView:
    state = 'free'
    if slot is not None:
        if slot.status == SlotStatus.cancelled:
            state = 'cancelled'
        elif slot.parent_id is not None and slot.status == SlotStatus.booked:
            state = 'taken'
    label = format_time_range(slot_start, slot_end)
    return DashboardSlotView(label=label, state=state)


def build_dashboard_teacher(
    teacher: Teacher,
    slot_times: Iterable[tuple[datetime, datetime]],
    existing_slots: Mapping[tuple[int, datetime], Slot],
) -> DashboardTeacherView:
    slot_items: list[DashboardSlotView] = []
    taken_slots = 0

    for slot_start, slot_end in slot_times:
        slot = existing_slots.get((teacher.teacher_id, slot_start))
        slot_view = build_dashboard_slot(slot_start, slot_end, slot)
        slot_items.append(slot_view)
        if slot_view.state == 'taken':
            taken_slots += 1

    total_slots = len(slot_items)
    has_availability = any(slot.state == 'free' for slot in slot_items)

    return DashboardTeacherView(
        teacher_id=teacher.teacher_id,
        name=teacher.full_name or teacher.email,
        email=teacher.email,
        slots=tuple(slot_items),
        total_slots=total_slots,
        taken_slots=taken_slots,
        has_availability=has_availability,
    )


def build_dashboard_event(event: Event, reference_time: datetime) -> DashboardEventView:
    is_ongoing = event.start_time <= reference_time < event.end_time
    is_future = reference_time < event.start_time
    return DashboardEventView(
        event_id=event.event_id,
        name=event.name or 'Мероприятие',
        date_label=format_date(event.start_time),
        time_label=format_time_range(event.start_time, event.end_time),
        start_iso=event.start_time.isoformat(),
        end_iso=event.end_time.isoformat(),
        is_ongoing=is_ongoing,
        is_future=is_future,
    )


def generate_slot_times(event: Event) -> list[tuple[datetime, datetime]]:
    total = event.consultations_count or 0
    duration = event.consultation_duration_minutes or 0
    if total <= 0 or duration <= 0:
        return []

    times: list[tuple[datetime, datetime]] = []
    start_time = event.start_time
    for index in range(total):
        slot_start = start_time + timedelta(minutes=index * duration)
        slot_end = slot_start + timedelta(minutes=duration)
        times.append((slot_start, slot_end))

    return times


def render_admin_dashboard() -> ResponseReturnValue:
    pages = get_pages()
    school = current_user.school
    search_query = (request.args.get('q') or '').strip()

    if not school:
        return render_template(
            'admin/dashboard.html',
            page_title='Главная',
            page_description='Ближайшее мероприятие',
            pages=pages,
            dashboard_event=None,
            teacher_cards=(),
            search_query=search_query,
        )

    event_repository.refresh_statuses_for_school(school.school_id)
    event = event_repository.get_closest_for_school(school.school_id)

    if not event:
        return render_template(
            'admin/dashboard.html',
            page_title='Главная',
            page_description='Ближайшее мероприятие',
            pages=pages,
            dashboard_event=None,
            teacher_cards=(),
            search_query=search_query,
        )

    reference_time = datetime.now(event.start_time.tzinfo) if event.start_time.tzinfo else datetime.now()

    dashboard_event = build_dashboard_event(event, reference_time)

    slot_times = generate_slot_times(event)
    slots_map: dict[tuple[int, datetime], Slot] = {}
    for slot in event.slots:
        key = (slot.teacher_id, slot.start_time)
        if key not in slots_map:
            slots_map[key] = slot

    teacher_cards: list[DashboardTeacherView] = []
    teachers_sorted = sorted(event.teachers, key=lambda teacher: teacher.full_name or teacher.email or '')
    for teacher in teachers_sorted:
        card = build_dashboard_teacher(teacher, slot_times, slots_map)
        teacher_cards.append(card)

    if search_query:
        lowered = search_query.lower()
        teacher_cards = [
            card for card in teacher_cards
            if lowered in card.name.lower() or lowered in card.email.lower()
        ]

    return render_template(
        'admin/dashboard.html',
        page_title='Главная',
        page_description='Ближайшее мероприятие',
        pages=pages,
        dashboard_event=dashboard_event,
        teacher_cards=teacher_cards,
        search_query=search_query,
    )


@bp.route('/')
@login_required
def index() -> ResponseReturnValue:
    if current_user.is_authenticated:
        role = getattr(current_user, 'role', None)
        if role == 'admin':
            return render_admin_dashboard()
        if role == 'parent':
            return redirect(url_for('main.parent_events'))
    return render_template('base.html', pages=get_pages())


@bp.route('/login')
def login_redirect() -> ResponseReturnValue:
    return redirect(url_for('auth.login'))


@bp.route('/account', methods=['GET', 'POST'])
@login_required
@check_rights('account', 'show')
def account() -> ResponseReturnValue:
    policy = AccountPolicy(target_user_id=current_user.user_id)

    school = current_user.school
    can_manage_school = policy.manage_school()

    if request.method == 'POST':
        if not policy.edit():
            abort(403)

        form = request.form
        errors: list[str] = []
        updated = False

        email_input = (form.get('email') or '').strip()
        normalized_email = email_input.lower()

        first_name = (form.get('first_name') or '').strip()
        last_name = (form.get('last_name') or '').strip()
        middle_name = (form.get('middle_name') or '').strip()
        school_name = (form.get('school_name') or '').strip()
        password_old = form.get('password_old') or ''
        password_new = form.get('password_new') or ''

        if not email_input:
            errors.append('Электронная почта не может быть пустой')
        elif (
            '@' not in normalized_email
            or normalized_email.startswith('@')
            or normalized_email.endswith('@')
            or ' ' in email_input
            or '.' not in normalized_email.split('@', 1)[-1]
        ):
            errors.append('Введите корректный адрес электронной почты')
        else:
            current_email_normalized = (current_user.email or '').lower()
            if normalized_email != current_email_normalized:
                stmt = select(User).where(User.email == normalized_email)
                existing_user = db.session.execute(stmt).scalar_one_or_none()
                if existing_user and existing_user.user_id != current_user.user_id:
                    errors.append('Пользователь с такой электронной почтой уже существует')
                else:
                    current_user.email = normalized_email
                    updated = True

        if not first_name:
            errors.append('Имя не может быть пустым')
        elif first_name != current_user.first_name:
            current_user.first_name = first_name
            updated = True

        if not last_name:
            errors.append('Фамилия не может быть пустой')
        elif last_name != current_user.last_name:
            current_user.last_name = last_name
            updated = True

        middle_value = middle_name or None
        if current_user.middle_name != middle_value:
            current_user.middle_name = middle_value
            updated = True

        if can_manage_school:
            if not school:
                if school_name:
                    errors.append('Не удалось найти школу для обновления — обратитесь к администратору')
            else:
                if not school_name:
                    errors.append('Название школы не может быть пустым')
                elif school.school_name != school_name:
                    school.school_name = school_name
                    updated = True

        if password_old or password_new:
            if not password_old or not password_new:
                errors.append('Для смены пароля заполните оба поля')
            elif not current_user.check_password(password_old):
                errors.append('Старый пароль указан неверно')
            elif len(password_new) < 8:
                errors.append('Новый пароль должен содержать не менее 8 символов')
            else:
                current_user.set_password(password_new)
                updated = True

        if errors:
            db.session.rollback()
            for message in errors:
                flash(message, 'warning')
        elif updated:
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                current_app.logger.exception('Failed to update account information')
                flash('Не удалось сохранить изменения, попробуйте ещё раз позже', 'danger')
            else:
                flash('Изменения успешно сохранены!', 'success')
                return redirect(url_for('main.account'))
        else:
            flash('Изменений не обнаружено', 'info')
            return redirect(url_for('main.account'))

        school = current_user.school

    invite_link = None

    if policy.view_invite_link() and school and school.invite_code:
        invite_link = url_for('auth.register_parent', invite_code=school.invite_code, _external=True)

    return render_template(
        'general/account.html',
        page_title='Аккаунт',
        pages=get_pages(),
        school=school,
        invite_link=invite_link,
        can_manage_school=can_manage_school,
    )
