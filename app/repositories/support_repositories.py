from app import db
from app.models import Notification, WasteType, ActivityLog
from datetime import datetime


class NotificationRepository:
    def get_by_user(self, user_id: int, limit=20) -> list[Notification]:
        return Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()

    def get_unread_count(self, user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def mark_all_read(self, user_id: int) -> None:
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()

    def save(self, notif: Notification) -> Notification:
        db.session.add(notif)
        db.session.commit()
        return notif


class WasteTypeRepository:
    def get_all(self) -> list[WasteType]:
        return WasteType.query.all()

    def get_by_id(self, wt_id: int) -> WasteType | None:
        return WasteType.query.get(wt_id)

    def get_by_name(self, name: str) -> WasteType | None:
        return WasteType.query.filter_by(name=name).first()

    def save(self, wt: WasteType) -> WasteType:
        db.session.add(wt)
        db.session.commit()
        return wt


class ActivityLogRepository:
    def get_all(self, page=1, per_page=30):
        return ActivityLog.query.order_by(
            ActivityLog.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    def get_recent(self, limit=50) -> list[ActivityLog]:
        return ActivityLog.query.order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()

    def save(self, log: ActivityLog) -> ActivityLog:
        db.session.add(log)
        db.session.commit()
        return log
