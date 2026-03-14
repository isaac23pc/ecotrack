-- ============================================================
--  EcoTrack — MySQL Database Schema
--  Run this ONCE to create the database and tables.
--  Then update .env: USE_SQLITE=false  DATABASE_URL=...
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecotrack_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ecotrack_db;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  full_name     VARCHAR(120) NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  phone         VARCHAR(30),
  password_hash VARCHAR(256) NOT NULL,
  role          ENUM('resident','collector','admin') NOT NULL DEFAULT 'resident',
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  zone          VARCHAR(50),
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_email  (email),
  INDEX idx_role   (role),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Waste types
CREATE TABLE IF NOT EXISTS waste_types (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(80) NOT NULL UNIQUE,
  description VARCHAR(255),
  icon        VARCHAR(50),
  color_class VARCHAR(50),
  requires_special_handling BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB;

-- Pickup requests
CREATE TABLE IF NOT EXISTS pickup_requests (
  id                    INT AUTO_INCREMENT PRIMARY KEY,
  resident_id           INT NOT NULL,
  collector_id          INT,
  waste_type_id         INT NOT NULL,
  address               VARCHAR(255) NOT NULL,
  landmark              VARCHAR(255),
  special_instructions  TEXT,
  latitude              DOUBLE,
  longitude             DOUBLE,
  pickup_date           DATE NOT NULL,
  time_slot             VARCHAR(30) NOT NULL,
  status                ENUM('pending','scheduled','in_progress','completed','missed','cancelled','delayed')
                        NOT NULL DEFAULT 'pending',
  issue_report          TEXT,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  completed_at          DATETIME,
  FOREIGN KEY (resident_id)   REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (collector_id)  REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (waste_type_id) REFERENCES waste_types(id),
  INDEX idx_resident    (resident_id),
  INDEX idx_collector   (collector_id),
  INDEX idx_date        (pickup_date),
  INDEX idx_status      (status)
) ENGINE=InnoDB;

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  title      VARCHAR(120) NOT NULL,
  message    TEXT NOT NULL,
  type       ENUM('info','success','warning','error') NOT NULL DEFAULT 'info',
  is_read    BOOLEAN NOT NULL DEFAULT FALSE,
  pickup_id  INT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)   REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (pickup_id) REFERENCES pickup_requests(id) ON DELETE SET NULL,
  INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB;

-- Activity logs
CREATE TABLE IF NOT EXISTS activity_logs (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT,
  action     VARCHAR(120) NOT NULL,
  details    TEXT,
  ip_address VARCHAR(45),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_created (created_at),
  INDEX idx_action  (action)
) ENGINE=InnoDB;

-- Seed waste types
INSERT IGNORE INTO waste_types (name, description, icon, color_class, requires_special_handling) VALUES
  ('Household',  'General domestic waste',          'trash-2',        'waste-household',  FALSE),
  ('Recyclable', 'Plastic, paper, glass, metal',    'recycle',        'waste-recyclable', FALSE),
  ('Organic',    'Food and garden waste',            'leaf',           'waste-organic',    FALSE),
  ('Hazardous',  'Chemicals, batteries, e-waste',   'alert-triangle', 'waste-hazardous',  TRUE);

-- ============================================================
-- To switch from SQLite → MySQL:
--   1. Run this file: mysql -u root -p < schema.sql
--   2. Edit .env:
--        USE_SQLITE=false
--        DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ecotrack_db
--   3. Restart: python run.py
-- ============================================================
