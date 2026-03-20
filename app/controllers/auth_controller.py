from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService
from app.repositories import UserRepository

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()
user_repo = UserRepository()


# ── helpers ──────────────────────────────────────────────────────────────────

def _dashboard_url(role: str) -> str:
    return url_for({
        'admin':     'admin.dashboard',
        'collector': 'collector.dashboard',
        'resident':  'resident.dashboard',
    }.get(role, 'resident.dashboard'))


def _no_admin_exists() -> bool:
    return user_repo.count_by_role('admin') == 0


# ── first-run admin setup ─────────────────────────────────────────────────────

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup_admin():
    """One-time admin account creation. Disabled once an admin exists."""
    if not _no_admin_exists():
        flash('System already has an administrator. Please sign in.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not all([full_name, email, password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/setup_admin.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/setup_admin.html')

        user, error = auth_service.register(full_name, email, phone, password, 'admin')
        if error:
            flash(error, 'danger')
            return render_template('auth/setup_admin.html')

        login_user(user)
        flash(f'Admin account created. Welcome, {user.full_name}!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('auth/setup_admin.html')


# ── register ──────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect to setup if no admin yet
    if _no_admin_exists():
        flash('Please create the admin account first.', 'warning')
        return redirect(url_for('auth.setup_admin'))

    if current_user.is_authenticated:
        return redirect(_dashboard_url(current_user.role))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        role      = request.form.get('role', 'resident')

        # Public registration only allows resident / collector
        if role not in ('resident', 'collector'):
            role = 'resident'

        if not all([full_name, email, password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        user, error = auth_service.register(full_name, email, phone, password, role)
        if error:
            flash(error, 'danger')
            return render_template('auth/register.html')

        login_user(user)
        flash(f'Welcome to EcoTrack, {user.full_name}!', 'success')
        return redirect(_dashboard_url(user.role))

    return render_template('auth/register.html')


# ── login ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # First run: no admin → must set up
    if _no_admin_exists():
        flash('Please create the admin account to get started.', 'warning')
        return redirect(url_for('auth.setup_admin'))

    if current_user.is_authenticated:
        return redirect(_dashboard_url(current_user.role))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user, error = auth_service.login(email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.full_name}!', 'success')
        return redirect(next_page or _dashboard_url(user.role))

    return render_template('auth/login.html')


# ── logout ────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.home'))


# ── forgot password ───────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = user_repo.get_by_email(email)
        # Always show the same message to prevent email enumeration
        flash(
            'If an account with that email exists, a reset link has been sent.',
            'info'
        )
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


# ── admin password reset (CLI only — not exposed via web) ─────────────────────

def reset_admin_password_cli(new_password: str = 'Admin@2026!'):
    """
    Run this from the Railway shell or local terminal to reset the admin password.
    Usage:
        python -c "from app.controllers.auth_controller import reset_admin_password_cli; reset_admin_password_cli('YourNewPassword')"
    """
    from app import create_app, db
    import os
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    with app.app_context():
        from app.models import User
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(app)
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print('No admin found.')
            return
        admin.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        print(f'Admin password reset for: {admin.email}')
        print(f'New password: {new_password}')
