from flask import Blueprint, render_template
from .models import db

bp = Blueprint('main', __name__)

def get_pages():
    return ['Главная', 'Мероприятия', 'Учителя', 'Здания']


@bp.route('/')
def index():
    return render_template('base.html',
                           pages=get_pages())
