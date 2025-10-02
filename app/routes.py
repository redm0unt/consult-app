from flask import Blueprint, redirect, render_template, url_for
from .models import db

bp = Blueprint('main', __name__)

def get_pages():
    return ['Главная', 'Мероприятия', 'Учителя', 'Здания']

@bp.route('/')
def index():
    return render_template('base.html',
                           pages=get_pages())

@bp.route('/login')
def login_redirect():
    return redirect(url_for('auth.login'))
