from typing import Dict, Optional

from flask import flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import login_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..models import School, User
from ..repositories import SchoolRepository, UserRepository, get_repository
from . import bp

user_repository: UserRepository = get_repository('users')
school_repository: SchoolRepository = get_repository('schools')


def _parse_full_name(full_name: str) -> tuple[str, str, Optional[str]]:
    parts = [part for part in full_name.split() if part]
    if len(parts) < 2:
        raise ValueError('Пожалуйста, укажите как минимум фамилию и имя')
    if len(parts) > 3:
        raise ValueError('Пожалуйста, укажите не более трёх частей имени (Фамилия Имя Отчество)')

    if len(parts) == 2:
        last_name, first_name = parts
        return first_name, last_name, None

    last_name, first_name, middle_name = parts
    return first_name, last_name, middle_name

def _render_admin_form(
    form_data: Optional[Dict[str, str]] = None,
    status: int = 200,
) -> ResponseReturnValue:
    return (
        render_template(
            'auth/registration/register_admin.html',
            page_title='Регистрация – Администраторы',
            form_heading='Регистрация',
            form_subheading='Администратор',
            form_data=form_data or {},
        ),
        status,
    )

def _render_parent_form(
    form_data: Optional[Dict[str, str]] = None,
    status: int = 200,
    *,
    show_invite_input: bool = True,
    school_name: Optional[str] = None,
    invite_code: Optional[str] = None,
) -> ResponseReturnValue:
    form_data = form_data or {}
    if invite_code is not None:
        form_data.setdefault('invite_code', invite_code)

    return (
        render_template(
            'auth/registration/register_parent.html',
            page_title='Регистрация – Родители',
            form_heading='Регистрация',
            form_subheading='Родитель',
            form_data=form_data,
            show_invite_input=show_invite_input,
            invite_code=invite_code,
            school_name=school_name,
        ),
        status,
    )


@bp.route('/register_admins', methods=['GET', 'POST'])
def register_admin() -> ResponseReturnValue:
    if request.method == 'POST':
        form_data: Dict[str, str] = {
            'full_name': request.form.get('full_name', '').strip(),
            'school_name': request.form.get('school_name', '').strip(),
            'email': request.form.get('email', '').strip(),
        }
        password = request.form.get('password', '')

        if not all([form_data['full_name'], form_data['school_name'], form_data['email'], password]):
            flash('Пожалуйста, заполните все поля формы', 'warning')
            return _render_admin_form(form_data, 400)

        try:
            first_name, last_name, middle_name = _parse_full_name(form_data['full_name'])
        except ValueError as exc:
            flash(str(exc), 'warning')
            return _render_admin_form(form_data, 400)

        try:
            school: School = school_repository.create(school_name=form_data['school_name'])
        except IntegrityError:
            school_repository.rollback()
            flash('Школа с таким названием уже существует', 'warning')
            return _render_admin_form(form_data, 400)
        except SQLAlchemyError:
            school_repository.rollback()
            flash('Ошибка при создании школы. Пожалуйста, попробуйте ещё раз', 'danger')
            return _render_admin_form(form_data, 500)

        try:
            user: User = user_repository.create(
                email=form_data['email'],
                password=password,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                school_id=school.school_id,
                role='admin',
            )
        except IntegrityError:
            user_repository.rollback()
            school_repository.delete(school.school_id)
            flash('Пользователь с такой электронной почтой уже зарегистрирован', 'warning')
            return _render_admin_form(form_data, 400)
        except SQLAlchemyError:
            user_repository.rollback()
            school_repository.delete(school.school_id)
            flash('Ошибка при создании пользователя. Пожалуйста, попробуйте ещё раз', 'danger')
            return _render_admin_form(form_data, 500)

        login_user(user)
        flash('Вы успешно зарегистрировались!', 'success')
        return redirect(url_for('main.index'))

    return _render_admin_form()

@bp.route('register_parents', methods=['GET', 'POST'])
def register_parent() -> ResponseReturnValue:
    invite_code_param = request.args.get('invite_code', '').strip()
    initial_school: Optional[School] = (
        school_repository.get_by_invite_code(invite_code=invite_code_param)
        if invite_code_param
        else None
    )
    school_name = initial_school.school_name if initial_school else None
    show_invite_input = not bool(school_name)

    if request.method == 'POST':
        form_data: Dict[str, str] = {
            'full_name': request.form.get('full_name', '').strip(),
            'email': request.form.get('email', '').strip(),
        }
        password = request.form.get('password', '')

        invite_code = invite_code_param or request.form.get('invite_code', '').strip()
        form_data['invite_code'] = invite_code

        if not all([form_data['full_name'], form_data['email'], invite_code, password]):
            flash('Пожалуйста, заполните все поля формы', 'warning')
            return _render_parent_form(
                form_data,
                400,
                show_invite_input=show_invite_input,
                invite_code=invite_code,
                school_name=school_name,
            )

        try:
            first_name, last_name, middle_name = _parse_full_name(form_data['full_name'])
        except ValueError as exc:
            flash(str(exc), 'warning')
            return _render_parent_form(
                form_data,
                400,
                show_invite_input=show_invite_input,
                invite_code=invite_code,
                school_name=school_name,
            )

        school = school_repository.get_by_invite_code(invite_code) if invite_code else None
        if school and not school_name:
            school_name = school.school_name
        if not school:
            flash('Школа с таким кодом приглашения не найдена', 'warning')
            return _render_parent_form(
                form_data,
                400,
                show_invite_input=show_invite_input,
                invite_code=invite_code,
                school_name=school_name,
            )

        try:
            user: User = user_repository.create(
                email=form_data['email'],
                password=password,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                school_id=school.school_id,
                role='parent',
            )
        except IntegrityError:
            user_repository.rollback()
            flash('Пользователь с такой электронной почтой уже зарегистрирован', 'warning')
            return _render_parent_form(
                form_data,
                400,
                show_invite_input=show_invite_input,
                invite_code=invite_code,
                school_name=school_name,
            )
        except SQLAlchemyError:
            user_repository.rollback()
            flash('Ошибка при создании пользователя. Пожалуйста, попробуйте ещё раз', 'danger')
            return _render_parent_form(
                form_data,
                500,
                show_invite_input=show_invite_input,
                invite_code=invite_code,
                school_name=school_name,
            )

        login_user(user)
        flash('Вы успешно зарегистрировались!', 'success')
        return redirect(url_for('main.index'))

    return _render_parent_form(
        {'invite_code': invite_code_param} if invite_code_param else None,
        show_invite_input=show_invite_input,
        invite_code=invite_code_param or None,
        school_name=school_name,
    )
