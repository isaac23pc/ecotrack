from flask import request
from flask_bcrypt import Bcrypt
from app.models import User, ActivityLog
from app.repositories import UserRepository, ActivityLogRepository

bcrypt = Bcrypt()

user_repo = UserRepository()
log_repo = ActivityLogRepository()


class AuthService:
    """Handles registration, login, and password management."""

    def register(self, full_name: str, email: str, phone: str,
                 password: str, role: str = 'resident') -> tuple[User | None, str | None]:
        if user_repo.get_by_email(email):
            return None, 'An account with this email already exists.'

        if len(password) < 8:
            return None, 'Password must be at least 8 characters.'

        if role not in ('resident', 'collector', 'admin'):
            role = 'resident'

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            full_name=full_name.strip(),
            email=email.lower().strip(),
            phone=phone,
            password_hash=hashed,
            role=role,
            email_verified=True,  # skip email verification for demo
        )
        user_repo.save(user)
        self._log(user.id, 'USER_REGISTERED', f'{full_name} registered as {role}')
        return user, None

    def login(self, email: str, password: str) -> tuple[User | None, str | None]:
        user = user_repo.get_by_email(email)
        if not user:
            return None, 'No account found with that email.'
        if not user.is_active:
            return None, 'This account has been disabled.'
        if not bcrypt.check_password_hash(user.password_hash, password):
            return None, 'Incorrect password.'
        self._log(user.id, 'USER_LOGIN', f'{user.full_name} logged in')
        return user, None

    def change_password(self, user: User, old_pw: str, new_pw: str) -> tuple[bool, str]:
        if not bcrypt.check_password_hash(user.password_hash, old_pw):
            return False, 'Current password is incorrect.'
        if len(new_pw) < 8:
            return False, 'New password must be at least 8 characters.'
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        user_repo.update()
        return True, 'Password updated successfully.'

    def _log(self, user_id, action, details):
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr if request else None
        )
        log_repo.save(log)
