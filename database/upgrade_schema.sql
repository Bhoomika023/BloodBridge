USE bloodbridge_db;

-- Use this when you already created an older BloodBridge database.
-- If your MySQL version does not support IF NOT EXISTS for ALTER TABLE,
-- create a fresh database with schema.sql instead.

ALTER TABLE donor ADD COLUMN IF NOT EXISTS district VARCHAR(100) AFTER city;
ALTER TABLE donor ADD COLUMN IF NOT EXISTS availability_status ENUM('Available','Recently Donated','Inactive') NOT NULL DEFAULT 'Available' AFTER district;
ALTER TABLE donor ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20) AFTER availability_status;
UPDATE donor SET contact_number = phone WHERE contact_number IS NULL AND phone IS NOT NULL;
ALTER TABLE donor MODIFY contact_number VARCHAR(20) NOT NULL;
ALTER TABLE donor ADD UNIQUE KEY IF NOT EXISTS unique_contact_number (contact_number);

CREATE TABLE IF NOT EXISTS hospitals (
  hospital_id INT PRIMARY KEY AUTO_INCREMENT,
  hospital_name VARCHAR(150) NOT NULL,
  city VARCHAR(100) NOT NULL,
  emergency_contact VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS city_stock (
  stock_id INT PRIMARY KEY AUTO_INCREMENT,
  city VARCHAR(100) NOT NULL,
  blood_group VARCHAR(5) NOT NULL,
  units_available INT NOT NULL DEFAULT 0,
  UNIQUE KEY unique_city_blood (city, blood_group)
);

ALTER TABLE blood_request ADD COLUMN IF NOT EXISTS city VARCHAR(100) NOT NULL DEFAULT 'Mysore' AFTER hospital_name;
ALTER TABLE blood_request ADD COLUMN IF NOT EXISTS priority ENUM('Normal','High','Critical') NOT NULL DEFAULT 'Normal' AFTER status;
ALTER TABLE blood_request ADD COLUMN IF NOT EXISTS contact_number VARCHAR(15) NOT NULL DEFAULT '' AFTER priority;
ALTER TABLE blood_request ADD COLUMN IF NOT EXISTS created_time DATETIME NULL AFTER request_date;
UPDATE blood_request SET created_time = CONCAT(request_date, ' 09:00:00') WHERE created_time IS NULL;
ALTER TABLE blood_request MODIFY created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
UPDATE blood_request SET status='Resolved' WHERE status IN ('Approved','Rejected');
UPDATE blood_request SET status='Active' WHERE status IN ('Pending','Escalated');
ALTER TABLE blood_request MODIFY status ENUM('Active','Resolved') NOT NULL DEFAULT 'Active';
CREATE INDEX IF NOT EXISTS idx_request_queue ON blood_request (status, priority, created_time);

CREATE TABLE IF NOT EXISTS emergency_alerts (
  alert_id INT PRIMARY KEY AUTO_INCREMENT,
  request_id INT NULL,
  patient_name VARCHAR(150) NOT NULL,
  blood_group VARCHAR(5) NOT NULL,
  city VARCHAR(100) NOT NULL,
  hospital_name VARCHAR(150) NOT NULL,
  urgency_level ENUM('NORMAL','HIGH','CRITICAL') NOT NULL DEFAULT 'NORMAL',
  required_units INT NOT NULL,
  request_time DATETIME NOT NULL,
  status ENUM('OPEN','CONTACTING_DONORS','FULFILLED','CLOSED') NOT NULL DEFAULT 'OPEN'
);

ALTER TABLE emergency_alerts ADD COLUMN IF NOT EXISTS request_id INT NULL AFTER alert_id;
ALTER TABLE emergency_alerts
  ADD CONSTRAINT fk_emergency_alert_request
  FOREIGN KEY (request_id) REFERENCES blood_request(request_id)
  ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_donor_match ON donor (blood_group, city, availability_status);
CREATE INDEX IF NOT EXISTS idx_alert_queue ON emergency_alerts (status, urgency_level, request_time);
