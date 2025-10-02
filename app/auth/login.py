from . import bp

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user

from ..repositories import get_repository

user_repository = get_repository('users')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next')

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') is not None

        if email and password:
            user = user_repository.get_authorized_user(email, password)
            if user is not None:
                login_user(user, remember=remember_me)
                flash('Вы успешно аутентифицированы', 'success')
                return redirect(next_url or url_for('main.index'))

        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
        session['login_form_data'] = {
            'email': email,
            'remember_me': remember_me,
        }
        redirect_kwargs = {}
        if next_url:
            redirect_kwargs['next'] = next_url
        return redirect(url_for('auth.login', **redirect_kwargs))

    form_data = session.pop('login_form_data', None) or {}

    return render_template(
        'auth/login/login.html',
        page_title="Вход",
        form_heading="Вход",
        form_subheading="Добро пожаловать",
        form_data=form_data,
        next_url=next_url,
    )