from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.services.pickup_service import PickupService
from app.repositories import PickupRepository, NotificationRepository

collector_bp = Blueprint('collector', __name__, url_prefix='/collector')
pickup_service = PickupService()
pickup_repo = PickupRepository()
notif_repo = NotificationRepository()


def collector_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('collector', 'admin'):
            flash('Collector access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@collector_bp.route('/dashboard')
@login_required
@collector_required
def dashboard():
    today_tasks = pickup_repo.get_by_collector_today(current_user.id)
    done = sum(1 for t in today_tasks if t.status == 'completed')
    pending = [t for t in today_tasks if t.status in ('scheduled', 'in_progress')]
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('collector/dashboard.html',
                           today_tasks=today_tasks,
                           done=done,
                           pending=pending,
                           unread=unread)


@collector_bp.route('/task/<int:pickup_id>/update', methods=['POST'])
@login_required
@collector_required
def update_task(pickup_id):
    status = request.form.get('status')
    issue = request.form.get('issue_report', '')
    ok, msg = pickup_service.update_status(pickup_id, status, current_user.id, issue)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('collector.dashboard'))


@collector_bp.route('/history')
@login_required
@collector_required
def history():
    pickups = pickup_repo.get_by_collector(current_user.id)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('collector/history.html', pickups=pickups, unread=unread)


@collector_bp.route('/notifications')
@login_required
@collector_required
def notifications():
    notifs = notif_repo.get_by_user(current_user.id, limit=50)
    notif_repo.mark_all_read(current_user.id)
    return render_template('collector/notifications.html', notifs=notifs, unread=0)
