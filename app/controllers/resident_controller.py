from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.services.pickup_service import PickupService
from app.repositories import PickupRepository, NotificationRepository, WasteTypeRepository

resident_bp = Blueprint('resident', __name__, url_prefix='/resident')
pickup_service = PickupService()
pickup_repo = PickupRepository()
notif_repo = NotificationRepository()
waste_repo = WasteTypeRepository()


def resident_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('resident', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@resident_bp.route('/dashboard')
@login_required
@resident_required
def dashboard():
    upcoming = pickup_repo.get_upcoming_by_resident(current_user.id)
    recent = pickup_repo.get_by_resident(current_user.id)[:5]
    unread = notif_repo.get_unread_count(current_user.id)
    total = len(pickup_repo.get_by_resident(current_user.id))
    completed = sum(1 for p in pickup_repo.get_by_resident(current_user.id) if p.status == 'completed')
    return render_template('resident/dashboard.html',
                           upcoming=upcoming,
                           recent=recent,
                           unread=unread,
                           total=total,
                           completed=completed)


@resident_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
@resident_required
def schedule():
    waste_types = waste_repo.get_all()
    if request.method == 'POST':
        pickup, error = pickup_service.schedule(
            resident_id=current_user.id,
            waste_type_id=request.form.get('waste_type_id', type=int),
            pickup_date_str=request.form.get('pickup_date', ''),
            time_slot=request.form.get('time_slot', ''),
            address=request.form.get('address', ''),
            landmark=request.form.get('landmark', ''),
            special_instructions=request.form.get('special_instructions', ''),
        )
        if error:
            flash(error, 'danger')
        else:
            flash('Pickup scheduled successfully!', 'success')
            return redirect(url_for('resident.upcoming'))
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('resident/schedule.html',
                           waste_types=waste_types,
                           time_slots=pickup_service.VALID_SLOTS,
                           unread=unread)


@resident_bp.route('/upcoming')
@login_required
@resident_required
def upcoming():
    pickups = pickup_repo.get_upcoming_by_resident(current_user.id)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('resident/upcoming.html', pickups=pickups, unread=unread)


@resident_bp.route('/history')
@login_required
@resident_required
def history():
    pickups = pickup_repo.get_by_resident(current_user.id)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('resident/history.html', pickups=pickups, unread=unread)


@resident_bp.route('/notifications')
@login_required
@resident_required
def notifications():
    notifs = notif_repo.get_by_user(current_user.id, limit=50)
    notif_repo.mark_all_read(current_user.id)
    return render_template('resident/notifications.html', notifs=notifs, unread=0)


@resident_bp.route('/cancel/<int:pickup_id>', methods=['POST'])
@login_required
@resident_required
def cancel(pickup_id):
    ok, msg = pickup_service.cancel(pickup_id, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('resident.upcoming'))
