from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.repositories import UserRepository

main_bp = Blueprint('main', __name__)
_user_repo = UserRepository()


@main_bp.route('/')
def home():
    # First run: no admin exists → go straight to setup
    if _user_repo.count_by_role('admin') == 0:
        return redirect(url_for('auth.setup_admin'))

    if current_user.is_authenticated:
        mapping = {
            'admin':     'admin.dashboard',
            'collector': 'collector.dashboard',
            'resident':  'resident.dashboard',
        }
        return redirect(url_for(mapping.get(current_user.role, 'resident.dashboard')))

    return render_template('home.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    return render_template('contact.html')
