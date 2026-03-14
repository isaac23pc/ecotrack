from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('resident', 'collector', 'admin'), nullable=False, default='resident')
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    zone = db.Column(db.String(50))          # for collectors
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pickups_as_resident = db.relationship('PickupRequest', foreign_keys='PickupRequest.resident_id',
                                          backref='resident', lazy='dynamic')
    pickups_as_collector = db.relationship('PickupRequest', foreign_keys='PickupRequest.collector_id',
                                           backref='collector', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'

    @property
    def initials(self):
        parts = self.full_name.split()
        return ''.join(p[0].upper() for p in parts[:2])

    def is_admin(self):
        return self.role == 'admin'

    def is_collector(self):
        return self.role == 'collector'

    def is_resident(self):
        return self.role == 'resident'


class WasteType(db.Model):
    __tablename__ = 'waste_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))          # Lucide icon name
    color_class = db.Column(db.String(50))   # CSS class
    requires_special_handling = db.Column(db.Boolean, default=False)
    pickups = db.relationship('PickupRequest', backref='waste_type_obj', lazy='dynamic')

    def __repr__(self):
        return f'<WasteType {self.name}>'


class PickupRequest(db.Model):
    __tablename__ = 'pickup_requests'

    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    collector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    waste_type_id = db.Column(db.Integer, db.ForeignKey('waste_types.id'), nullable=False)

    address = db.Column(db.String(255), nullable=False)
    landmark = db.Column(db.String(255))
    special_instructions = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    pickup_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(30), nullable=False)   # e.g. "08:00-10:00"

    status = db.Column(
        db.Enum('pending', 'scheduled', 'in_progress', 'completed', 'missed', 'cancelled', 'delayed'),
        default='pending', nullable=False
    )
    issue_report = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<PickupRequest #{self.id} [{self.status}]>'

    @property
    def status_badge_class(self):
        return {
            'pending': 'badge-warning',
            'scheduled': 'badge-info',
            'in_progress': 'badge-primary',
            'completed': 'badge-success',
            'missed': 'badge-danger',
            'cancelled': 'badge-secondary',
            'delayed': 'badge-warning',
        }.get(self.status, 'badge-secondary')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('info', 'success', 'warning', 'error'), default='info')
    is_read = db.Column(db.Boolean, default=False)
    pickup_id = db.Column(db.Integer, db.ForeignKey('pickup_requests.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.title} -> User#{self.user_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action}>'
