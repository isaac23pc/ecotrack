from app.models import User, ActivityLog
from app.repositories import UserRepository, PickupRepository, ActivityLogRepository
from app.services.auth_service import AuthService, bcrypt

user_repo = UserRepository()
pickup_repo = PickupRepository()
log_repo = ActivityLogRepository()
auth_service = AuthService()


class AdminService:
    """Business logic for admin-level operations."""

    def get_dashboard_stats(self) -> dict:
        from datetime import date
        return {
            'total_users': user_repo.count_active(),
            'total_residents': user_repo.count_by_role('resident'),
            'total_collectors': user_repo.count_by_role('collector'),
            'total_admins': user_repo.count_by_role('admin'),
            'pickups_today': pickup_repo.count_today(),
            'pickups_completed_today': pickup_repo.count_today_completed(),
            'pickups_pending': pickup_repo.count_by_status('pending'),
            'pickups_scheduled': pickup_repo.count_by_status('scheduled'),
            'pickups_completed': pickup_repo.count_by_status('completed'),
            'pickups_missed': pickup_repo.count_by_status('missed'),
            'pickups_cancelled': pickup_repo.count_by_status('cancelled'),
        }

    def create_user(self, full_name, email, phone, password, role) -> tuple[User | None, str | None]:
        return auth_service.register(full_name, email, phone, password, role)

    def toggle_user_status(self, user_id: int, admin_id: int) -> tuple[bool, str]:
        user = user_repo.get_by_id(user_id)
        if not user:
            return False, 'User not found.'
        if user.id == admin_id:
            return False, 'Cannot disable your own account.'
        user.is_active = not user.is_active
        user_repo.update()
        action = 'enabled' if user.is_active else 'disabled'
        log_repo.save(ActivityLog(
            user_id=admin_id, action='USER_STATUS_CHANGED',
            details=f'User {user.email} {action} by admin #{admin_id}'
        ))
        return True, f'User account {action}.'

    def update_user(self, user_id: int, full_name: str, email: str,
                    phone: str, role: str, zone: str, admin_id: int) -> tuple[bool, str]:
        user = user_repo.get_by_id(user_id)
        if not user:
            return False, 'User not found.'
        existing = user_repo.get_by_email(email)
        if existing and existing.id != user_id:
            return False, 'Email already used by another account.'
        user.full_name = full_name.strip()
        user.email = email.lower().strip()
        user.phone = phone
        user.role = role
        user.zone = zone
        user_repo.update()
        log_repo.save(ActivityLog(
            user_id=admin_id, action='USER_UPDATED',
            details=f'User #{user_id} updated'
        ))
        return True, 'User updated.'

    def delete_user(self, user_id: int, admin_id: int) -> tuple[bool, str]:
        user = user_repo.get_by_id(user_id)
        if not user:
            return False, 'User not found.'
        if user.id == admin_id:
            return False, 'Cannot delete your own account.'
        user_repo.delete(user)
        log_repo.save(ActivityLog(
            user_id=admin_id, action='USER_DELETED',
            details=f'User #{user_id} ({user.email}) deleted'
        ))
        return True, 'User deleted.'

    def reset_user_password(self, user_id: int, new_password: str, admin_id: int) -> tuple[bool, str]:
        user = user_repo.get_by_id(user_id)
        if not user:
            return False, 'User not found.'
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user_repo.update()
        log_repo.save(ActivityLog(
            user_id=admin_id, action='PASSWORD_RESET',
            details=f'Password reset for user #{user_id}'
        ))
        return True, 'Password reset successfully.'
