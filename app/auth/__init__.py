from flask import Blueprint, request, render_template, url_for, flash, redirect, session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from functools import wraps
# from .checkers import check_password

from .policies import user_allowed

from ..repositories import get_repository

bp = Blueprint('auth', __name__, url_prefix='/auth')

from . import login
from . import register

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)

user_repository = get_repository('users')

def load_user(user_id):
    user = user_repository.get_by_id(user_id)
    if user is not None:
        return user
    return None

@bp.route('/logout', methods=['GET'])
def logout():
    was_authenticated = current_user.is_authenticated
    logout_user()
    if was_authenticated:
        flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('auth.login'))

# def user_allowed(resource, action, **kwargs):
def check_rights(resource, action, redirect_endpoint='main.index'):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if not user_allowed(resource, action, **kwargs):
                flash('У вас недостаточно прав для доступа к данной странице.', 'warning')
                return redirect(url_for(redirect_endpoint))
            return function(*args, **kwargs)
        return wrapper
    return decorator
