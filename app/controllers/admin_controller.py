from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.services.admin_service import AdminService
from app.services.pickup_service import PickupService
from app.repositories import UserRepository, PickupRepository, ActivityLogRepository, WasteTypeRepository, NotificationRepository

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
admin_service = AdminService()
pickup_service = PickupService()
user_repo = UserRepository()
pickup_repo = PickupRepository()
log_repo = ActivityLogRepository()
waste_repo = WasteTypeRepository()
notif_repo = NotificationRepository()


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = admin_service.get_dashboard_stats()
    recent_logs = log_repo.get_recent(limit=10)
    recent_pickups = pickup_repo.get_filter(page=1, per_page=5)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_logs=recent_logs,
                           recent_pickups=recent_pickups,
                           unread=unread)


# ── Users ──────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '')
    if q:
        pagination = user_repo.search(q, page=page)
    else:
        pagination = user_repo.get_all(page=page)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/users.html',
                           pagination=pagination,
                           q=q,
                           role_filter=role_filter,
                           unread=unread)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        user, error = admin_service.create_user(
            full_name=request.form.get('full_name', ''),
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            password=request.form.get('password', 'EcoTrack@2026'),
            role=request.form.get('role', 'resident')
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'User "{user.full_name}" created successfully.', 'success')
            return redirect(url_for('admin.users'))
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/user_form.html', user=None, unread=unread)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = user_repo.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        ok, msg = admin_service.update_user(
            user_id=user_id,
            full_name=request.form.get('full_name', ''),
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            role=request.form.get('role', 'resident'),
            zone=request.form.get('zone', ''),
            admin_id=current_user.id
        )
        flash(msg, 'success' if ok else 'danger')
        if ok:
            return redirect(url_for('admin.users'))

    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/user_form.html', user=user, unread=unread)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    ok, msg = admin_service.toggle_user_status(user_id, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    ok, msg = admin_service.delete_user(user_id, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    new_pw = request.form.get('new_password', 'EcoTrack@2026')
    ok, msg = admin_service.reset_user_password(user_id, new_pw, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('admin.users'))


# ── Pickups ─────────────────────────────────────────────────────────
@admin_bp.route('/pickups')
@login_required
@admin_required
def pickups():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    waste_type_id = request.args.get('waste_type_id', '', type=int) or None
    collector_id = request.args.get('collector_id', '', type=int) or None
    pagination = pickup_repo.get_filter(
        status=status or None,
        waste_type_id=waste_type_id,
        collector_id=collector_id,
        page=page
    )
    collectors = user_repo.get_collectors()
    waste_types = waste_repo.get_all()
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/pickups.html',
                           pagination=pagination,
                           collectors=collectors,
                           waste_types=waste_types,
                           status=status,
                           unread=unread)


@admin_bp.route('/pickups/<int:pickup_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_collector(pickup_id):
    collector_id = request.form.get('collector_id', type=int)
    if not collector_id:
        flash('Please select a collector.', 'danger')
        return redirect(url_for('admin.pickups'))
    ok, msg = pickup_service.assign_collector(pickup_id, collector_id, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('admin.pickups'))


@admin_bp.route('/pickups/<int:pickup_id>/status', methods=['POST'])
@login_required
@admin_required
def update_pickup_status(pickup_id):
    status = request.form.get('status')
    ok, msg = pickup_service.update_status(pickup_id, status, current_user.id)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('admin.pickups'))


@admin_bp.route('/pickups/unassigned')
@login_required
@admin_required
def unassigned_pickups():
    pickups_list = pickup_repo.get_unassigned()
    collectors = user_repo.get_collectors()
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/unassigned.html',
                           pickups=pickups_list,
                           collectors=collectors,
                           unread=unread)


# ── Collectors ───────────────────────────────────────────────────────
@admin_bp.route('/collectors')
@login_required
@admin_required
def collectors():
    from datetime import date
    collectors_list = user_repo.get_collectors()
    collector_stats = []
    for c in collectors_list:
        today_tasks = pickup_repo.get_by_collector_today(c.id)
        done = sum(1 for p in today_tasks if p.status == 'completed')
        collector_stats.append({
            'collector': c,
            'total_today': len(today_tasks),
            'done_today': done,
            'pct': int((done / len(today_tasks) * 100) if today_tasks else 0),
        })
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/collectors.html',
                           collector_stats=collector_stats,
                           unread=unread)


# ── Reports ──────────────────────────────────────────────────────────
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    from sqlalchemy import func
    from app.models import PickupRequest, WasteType
    from app import db
    stats = admin_service.get_dashboard_stats()
    waste_dist = db.session.query(
        WasteType.name, WasteType.color_class,
        func.count(PickupRequest.id).label('count')
    ).join(PickupRequest, WasteType.id == PickupRequest.waste_type_id, isouter=True
    ).group_by(WasteType.id).all()
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/reports.html',
                           stats=stats,
                           waste_dist=waste_dist,
                           unread=unread)


# ── Activity Logs ────────────────────────────────────────────────────
@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    pagination = log_repo.get_all(page=page, per_page=30)
    unread = notif_repo.get_unread_count(current_user.id)
    return render_template('admin/logs.html', pagination=pagination, unread=unread)
