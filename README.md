# EcoTrack — Smart Waste Disposal Scheduling System

A full-stack Flask web application with light theme, Lucide icons, and
**Controller → Service → Repository** architecture backed by MySQL (or SQLite for dev).

---

## Project Structure

```
ecotrack/
├── run.py                        # Entrypoint
├── schema.sql                    # MySQL schema (run once for MySQL setup)
├── .env                          # Environment variables
├── requirements.txt
├── config/
│   └── config.py                 # Flask configuration (MySQL / SQLite)
└── app/
    ├── __init__.py               # App factory, extensions, seed data
    ├── models/
    │   └── models.py             # SQLAlchemy models
    ├── repositories/             # DATA ACCESS LAYER
    │   ├── user_repository.py
    │   ├── pickup_repository.py
    │   └── support_repositories.py
    ├── services/                 # BUSINESS LOGIC LAYER
    │   ├── auth_service.py
    │   ├── pickup_service.py
    │   └── admin_service.py
    ├── controllers/              # PRESENTATION LAYER (Flask Blueprints)
    │   ├── main_controller.py
    │   ├── auth_controller.py
    │   ├── admin_controller.py
    │   ├── resident_controller.py
    │   └── collector_controller.py
    ├── static/
    │   └── css/main.css
    └── templates/
        ├── base.html
        ├── dashboard_base.html
        ├── home.html / about.html / contact.html
        ├── auth/   login.html  register.html
        ├── admin/  dashboard  users  pickups  collectors  reports  logs  unassigned
        ├── resident/ dashboard  schedule  upcoming  history  notifications
        └── collector/ dashboard  history  notifications
```

---

## Quick Start (SQLite — no MySQL needed)

```bash
# 1. Clone / unzip the project
cd ecotrack

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (SQLite is used by default)
python run.py
```

Open http://localhost:5000

### Demo Accounts (auto-seeded)

| Role      | Email                    | Password        |
|-----------|--------------------------|-----------------|
| Admin     | admin@ecotrack.bj        | Admin@2026!     |
| Resident  | resident@ecotrack.bj     | Resident@2026!  |
| Collector | collector@ecotrack.bj    | Collector@2026! |

---

## Switching to MySQL

```bash
# 1. Create the database
mysql -u root -p < schema.sql

# 2. Edit .env
USE_SQLITE=false
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ecotrack_db

# 3. Restart
python run.py
```

---

## Architecture

### Controller → Service → Repository

```
HTTP Request
    ↓
Controller  (Flask Blueprint — handles HTTP, calls service)
    ↓
Service     (Business logic — validates, orchestrates, sends notifications)
    ↓
Repository  (Data access — all SQLAlchemy queries live here)
    ↓
Model       (SQLAlchemy ORM — table definitions)
    ↓
Database    (MySQL or SQLite)
```

**Rule:** Controllers never touch the DB. Services never write raw SQL.
Repositories never contain business logic.

---

## User Roles & Permissions

| Feature                    | Resident | Collector | Admin |
|----------------------------|----------|-----------|-------|
| Schedule pickup            | ✅       | —         | —     |
| View own pickups           | ✅       | —         | —     |
| Cancel own pickup          | ✅       | —         | —     |
| View today's tasks         | —        | ✅        | —     |
| Mark pickup done/delayed   | —        | ✅        | —     |
| Report problem             | —        | ✅        | —     |
| Manage all users           | —        | —         | ✅    |
| Assign collectors          | —        | —         | ✅    |
| View reports & analytics   | —        | —         | ✅    |
| View activity logs         | —        | —         | ✅    |
