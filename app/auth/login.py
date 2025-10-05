from typing import Any, Dict, Optional

from flask import flash, redirect, render_template, request, session, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_user

from ..repositories import UserRepository, get_repository
from . import bp

user_repository: UserRepository = get_repository('users')


@bp.route('/login', methods=['GET', 'POST'])
def login() -> ResponseReturnValue:
    next_url: Optional[str] = request.args.get('next')

    if current_user.is_authenticated:
        flash('Вы уже аутентифицированы', 'info')
        return redirect(next_url or url_for('main.index'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') is not None

        if email and password:
            user = user_repository.get_authorized_user(email, password)
            if user is not None:
                login_user(user, remember=remember_me)
                flash('Вы успешно аутентифицированы!', 'success')
                return redirect(next_url or url_for('main.index'))

        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
        session['login_form_data'] = {
            'email': email,
            'remember_me': remember_me,
        }
        redirect_kwargs: Dict[str, Any] = {}
        if next_url:
            redirect_kwargs['next'] = next_url
        return redirect(url_for('auth.login', **redirect_kwargs))

    form_data: Dict[str, Any] = session.pop('login_form_data', None) or {}

    return render_template(
        'auth/login/login.html',
        page_title="Вход",
        form_heading="Вход",
        form_subheading="Добро пожаловать",
        form_data=form_data,
        next_url=next_url,
    )