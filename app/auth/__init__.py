from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from flask import Blueprint, flash, redirect, url_for
from flask.app import Flask
from flask_login import LoginManager, current_user, logout_user

from ..models import User
from ..repositories import UserRepository, get_repository
from .policies import user_allowed

bp = Blueprint('auth', __name__, url_prefix='/auth')

from . import login
from . import register


def init_login_manager(app: Flask) -> None:
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = (
        'Для доступа к данной странице необходимо пройти процедуру аутентификации'
    )
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)


user_repository: UserRepository = get_repository('users')


def load_user(user_id: Optional[int | str]) -> Optional[User]:
    return user_repository.get_by_id(user_id) if user_id is not None else None


@bp.route('/logout', methods=['GET'])
def logout() -> Any:
    was_authenticated = current_user.is_authenticated
    logout_user()
    if was_authenticated:
        flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('auth.login'))


ViewFunc = TypeVar('ViewFunc', bound=Callable[..., Any])


def check_rights(
    resource: str,
    action: str,
    redirect_endpoint: str = 'main.index',
) -> Callable[[ViewFunc], ViewFunc]:
    def decorator(function: ViewFunc) -> ViewFunc:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not user_allowed(resource, action, **kwargs):
                flash('У вас недостаточно прав для доступа к данной странице', 'warning')
                return redirect(url_for(redirect_endpoint))
            return function(*args, **kwargs)

        return cast(ViewFunc, wrapper)

    return decorator
