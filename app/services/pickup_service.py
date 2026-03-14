from datetime import date, datetime
from app.models import PickupRequest, Notification, ActivityLog
from app.repositories import PickupRepository, NotificationRepository, ActivityLogRepository


pickup_repo = PickupRepository()
notif_repo = NotificationRepository()
log_repo = ActivityLogRepository()


class PickupService:
    """Business logic for scheduling and managing waste pickups."""

    VALID_SLOTS = [
        '06:00-08:00', '08:00-10:00', '10:00-12:00',
        '14:00-16:00', '16:00-18:00'
    ]

    def schedule(self, resident_id: int, waste_type_id: int, pickup_date_str: str,
                 time_slot: str, address: str, landmark: str = '',
                 special_instructions: str = '') -> tuple[PickupRequest | None, str | None]:

        try:
            pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()
        except ValueError:
            return None, 'Invalid date format.'

        if pickup_date < date.today():
            return None, 'Cannot schedule a pickup in the past.'

        if time_slot not in self.VALID_SLOTS:
            return None, 'Invalid time slot selected.'

        available = pickup_repo.check_slot_availability(pickup_date, time_slot, address)
        if not available:
            return None, 'This time slot is already booked for that address.'

        pickup = PickupRequest(
            resident_id=resident_id,
            waste_type_id=waste_type_id,
            pickup_date=pickup_date,
            time_slot=time_slot,
            address=address,
            landmark=landmark,
            special_instructions=special_instructions,
            status='pending'
        )
        pickup_repo.save(pickup)

        notif_repo.save(Notification(
            user_id=resident_id,
            title='Pickup Scheduled',
            message=f'Your pickup on {pickup_date.strftime("%b %d, %Y")} ({time_slot}) has been confirmed.',
            type='success',
            pickup_id=pickup.id
        ))
        self._log(resident_id, 'PICKUP_SCHEDULED',
                  f'Pickup #{pickup.id} on {pickup_date} ({time_slot})')
        return pickup, None

    def assign_collector(self, pickup_id: int, collector_id: int,
                         admin_id: int) -> tuple[bool, str]:
        pickup = pickup_repo.get_by_id(pickup_id)
        if not pickup:
            return False, 'Pickup not found.'

        pickup.collector_id = collector_id
        pickup.status = 'scheduled'
        pickup_repo.update()

        notif_repo.save(Notification(
            user_id=pickup.resident_id,
            title='Collector Assigned',
            message=f'A collector has been assigned to your pickup on {pickup.pickup_date.strftime("%b %d")}.',
            type='info',
            pickup_id=pickup_id
        ))
        notif_repo.save(Notification(
            user_id=collector_id,
            title='New Pickup Assigned',
            message=f'You have a new pickup at {pickup.address} on {pickup.pickup_date.strftime("%b %d")} ({pickup.time_slot}).',
            type='info',
            pickup_id=pickup_id
        ))
        self._log(admin_id, 'COLLECTOR_ASSIGNED',
                  f'Collector #{collector_id} assigned to Pickup #{pickup_id}')
        return True, 'Collector assigned successfully.'

    def update_status(self, pickup_id: int, status: str,
                      user_id: int, issue_report: str = None) -> tuple[bool, str]:
        pickup = pickup_repo.get_by_id(pickup_id)
        if not pickup:
            return False, 'Pickup not found.'

        valid_statuses = ['in_progress', 'completed', 'missed', 'cancelled', 'delayed']
        if status not in valid_statuses:
            return False, 'Invalid status.'

        pickup.status = status
        if status == 'completed':
            pickup.completed_at = datetime.utcnow()
        if issue_report:
            pickup.issue_report = issue_report

        pickup_repo.update()

        if status == 'completed':
            notif_repo.save(Notification(
                user_id=pickup.resident_id,
                title='Pickup Completed',
                message=f'Your waste pickup at {pickup.address} has been completed.',
                type='success', pickup_id=pickup_id
            ))
        elif status in ('missed', 'delayed'):
            notif_repo.save(Notification(
                user_id=pickup.resident_id,
                title=f'Pickup {status.capitalize()}',
                message=f'Your pickup on {pickup.pickup_date.strftime("%b %d")} was {status}. Please reschedule.',
                type='warning', pickup_id=pickup_id
            ))

        self._log(user_id, 'PICKUP_STATUS_UPDATE',
                  f'Pickup #{pickup_id} status → {status}')
        return True, f'Status updated to {status}.'

    def cancel(self, pickup_id: int, resident_id: int) -> tuple[bool, str]:
        pickup = pickup_repo.get_by_id(pickup_id)
        if not pickup:
            return False, 'Pickup not found.'
        if pickup.resident_id != resident_id:
            return False, 'Unauthorized.'
        if pickup.status in ('completed', 'cancelled'):
            return False, f'Cannot cancel a {pickup.status} pickup.'
        pickup.status = 'cancelled'
        pickup_repo.update()
        self._log(resident_id, 'PICKUP_CANCELLED', f'Pickup #{pickup_id} cancelled by resident')
        return True, 'Pickup cancelled.'

    def _log(self, user_id, action, details):
        log_repo.save(ActivityLog(user_id=user_id, action=action, details=details))
