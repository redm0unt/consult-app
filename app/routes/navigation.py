from typing import List, Mapping, TypedDict

from flask_login import current_user


class PageConfig(TypedDict):
    label: str
    endpoint: str
    icon: str


RolePagesMap = Mapping[str, List[PageConfig]]


PAGES_BY_ROLE: RolePagesMap = {
    'admin': [
        {'label': 'Главная', 'endpoint': 'main.index', 'icon': 'img/nav/home.svg'},
        {'label': 'Мероприятия', 'endpoint': 'main.events', 'icon': 'img/nav/events.svg'},
        {'label': 'Учителя', 'endpoint': 'main.teachers', 'icon': 'img/nav/teachers.svg'},
        {'label': 'Здания', 'endpoint': 'main.buildings', 'icon': 'img/nav/buildings.svg'},
    ],
    'teacher': [
        {'label': 'Консультации', 'endpoint': 'main.teacher_consultations', 'icon': 'img/nav/home.svg'},
        {'label': 'Мероприятия', 'endpoint': 'main.teacher_events', 'icon': 'img/nav/events.svg'},
    ],
    'parent': [
        {'label': 'Главная', 'endpoint': 'main.parent_events', 'icon': 'img/nav/home.svg'},
        {'label': 'Мои записи', 'endpoint': 'main.parent_bookings', 'icon': 'img/nav/events.svg'},
    ],
}


DEFAULT_PAGES: List[PageConfig] = [
    {'label': 'Главная', 'endpoint': 'main.index', 'icon': 'img/nav/home.svg'},
    {'label': 'Мероприятия', 'endpoint': 'main.index', 'icon': 'img/nav/events.svg'},
    {'label': 'Учителя', 'endpoint': 'main.teachers', 'icon': 'img/nav/teachers.svg'},
]


def get_pages(role: str | None = None) -> List[PageConfig]:
    resolved_role: str | None = role
    if resolved_role is None:
        if current_user.is_authenticated:
            resolved_role = getattr(current_user, 'role', None)

    pages = PAGES_BY_ROLE.get(resolved_role) if resolved_role else None
    if pages is None:
        pages = DEFAULT_PAGES

    return [dict(page) for page in pages]


__all__ = ['get_pages', 'PageConfig', 'PAGES_BY_ROLE']
