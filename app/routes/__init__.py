from flask import Blueprint

from .navigation import get_pages

bp = Blueprint('main', __name__)

from .general import routes as general_routes
from .admin import teachers as admin_teachers
from .admin import buildings as admin_buildings
from .parent import routes as parent_routes
from .teacher import routes as teacher_routes

__all__ = ['bp', 'get_pages']
