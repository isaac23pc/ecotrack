from datetime import date
from app import db
from app.models import PickupRequest


class PickupRepository:
    """Data access layer for PickupRequest model."""

    def get_by_id(self, pickup_id: int) -> PickupRequest | None:
        return PickupRequest.query.get(pickup_id)

    def get_all(self, page=1, per_page=20):
        return PickupRequest.query.order_by(
            PickupRequest.pickup_date.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

    def get_by_resident(self, resident_id: int) -> list[PickupRequest]:
        return PickupRequest.query.filter_by(resident_id=resident_id).order_by(
            PickupRequest.pickup_date.desc()
        ).all()

    def get_upcoming_by_resident(self, resident_id: int) -> list[PickupRequest]:
        return PickupRequest.query.filter(
            PickupRequest.resident_id == resident_id,
            PickupRequest.pickup_date >= date.today(),
            PickupRequest.status.in_(['pending', 'scheduled'])
        ).order_by(PickupRequest.pickup_date.asc()).all()

    def get_by_collector_today(self, collector_id: int) -> list[PickupRequest]:
        return PickupRequest.query.filter(
            PickupRequest.collector_id == collector_id,
            PickupRequest.pickup_date == date.today()
        ).order_by(PickupRequest.time_slot).all()

    def get_by_collector(self, collector_id: int) -> list[PickupRequest]:
        return PickupRequest.query.filter_by(collector_id=collector_id).order_by(
            PickupRequest.pickup_date.desc()
        ).all()

    def get_unassigned(self) -> list[PickupRequest]:
        return PickupRequest.query.filter(
            PickupRequest.collector_id.is_(None),
            PickupRequest.status == 'pending',
            PickupRequest.pickup_date >= date.today()
        ).order_by(PickupRequest.pickup_date.asc()).all()

    def get_by_date(self, pickup_date: date) -> list[PickupRequest]:
        return PickupRequest.query.filter_by(pickup_date=pickup_date).all()

    def count_by_status(self, status: str) -> int:
        return PickupRequest.query.filter_by(status=status).count()

    def count_today(self) -> int:
        return PickupRequest.query.filter_by(pickup_date=date.today()).count()

    def count_today_completed(self) -> int:
        return PickupRequest.query.filter(
            PickupRequest.pickup_date == date.today(),
            PickupRequest.status == 'completed'
        ).count()

    def check_slot_availability(self, pickup_date: date, time_slot: str, address: str) -> bool:
        """Returns True if slot is available (no double booking for same address+slot)."""
        existing = PickupRequest.query.filter(
            PickupRequest.pickup_date == pickup_date,
            PickupRequest.time_slot == time_slot,
            PickupRequest.address == address,
            PickupRequest.status.notin_(['cancelled', 'missed'])
        ).first()
        return existing is None

    def get_filter(self, status=None, waste_type_id=None, collector_id=None, page=1, per_page=20):
        q = PickupRequest.query
        if status:
            q = q.filter_by(status=status)
        if waste_type_id:
            q = q.filter_by(waste_type_id=waste_type_id)
        if collector_id:
            q = q.filter_by(collector_id=collector_id)
        return q.order_by(PickupRequest.pickup_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def save(self, pickup: PickupRequest) -> PickupRequest:
        db.session.add(pickup)
        db.session.commit()
        return pickup

    def update(self) -> None:
        db.session.commit()

    def delete(self, pickup: PickupRequest) -> None:
        db.session.delete(pickup)
        db.session.commit()
