from app import db
from app.models import User


class UserRepository:
    """Data access layer for User model."""

    def get_by_id(self, user_id: int) -> User | None:
        return User.query.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email.lower().strip()).first()

    def get_all(self, page=1, per_page=20):
        return User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_by_role(self, role: str) -> list[User]:
        return User.query.filter_by(role=role, is_active=True).all()

    def get_collectors(self) -> list[User]:
        return self.get_by_role('collector')

    def count_by_role(self, role: str) -> int:
        return User.query.filter_by(role=role).count()

    def count_active(self) -> int:
        return User.query.filter_by(is_active=True).count()

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def delete(self, user: User) -> None:
        db.session.delete(user)
        db.session.commit()

    def update(self) -> None:
        db.session.commit()

    def search(self, query: str, page=1, per_page=20):
        q = f'%{query}%'
        return User.query.filter(
            (User.full_name.ilike(q)) | (User.email.ilike(q))
        ).paginate(page=page, per_page=per_page, error_out=False)
