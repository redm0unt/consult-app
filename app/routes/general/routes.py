from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.auth import check_rights
from app.auth.policies import AccountPolicy
from app.models import User, db
from app.routes import bp, get_pages


@bp.route('/')
def index() -> ResponseReturnValue:
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
        pages=get_pages(),
        school=school,
        invite_link=invite_link,
        can_manage_school=can_manage_school,
    )
