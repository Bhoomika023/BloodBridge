-- BloodBridge database schema
-- Run this file in your MySQL client to create the schema and tables.

CREATE DATABASE IF NOT EXISTS bloodbridge_db;
USE bloodbridge_db;

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
  admin_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL
);

-- Donor table
CREATE TABLE IF NOT EXISTS donor (
  donor_id INT PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(150) NOT NULL,
  age INT NOT NULL,
  gender ENUM('Male','Female','Other') NOT NULL,
  blood_group VARCHAR(5) NOT NULL,
  city VARCHAR(100) NOT NULL,
  district VARCHAR(100),
  state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
  availability_status ENUM('Available','Recently Donated','Inactive') NOT NULL DEFAULT 'Available',
  contact_number VARCHAR(20) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE,
  last_donation_date DATE,
  KEY idx_donor_match (blood_group, city, availability_status)
);

-- Blood stock
CREATE TABLE IF NOT EXISTS blood_stock (
  stock_id INT PRIMARY KEY AUTO_INCREMENT,
  blood_group VARCHAR(5) NOT NULL UNIQUE,
  units_available INT NOT NULL DEFAULT 0
);

-- Hospital network
CREATE TABLE IF NOT EXISTS hospitals (
  hospital_id INT PRIMARY KEY AUTO_INCREMENT,
  hospital_name VARCHAR(150) NOT NULL,
  city VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
  emergency_contact VARCHAR(20) NOT NULL
);

-- City-wise stock for realistic emergency coordination
CREATE TABLE IF NOT EXISTS city_stock (
  stock_id INT PRIMARY KEY AUTO_INCREMENT,
  city VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
  blood_group VARCHAR(5) NOT NULL,
  units_available INT NOT NULL DEFAULT 0,
  UNIQUE KEY unique_city_blood (city, blood_group)
);

-- Blood request
CREATE TABLE IF NOT EXISTS blood_request (
  request_id INT PRIMARY KEY AUTO_INCREMENT,
  patient_name VARCHAR(150) NOT NULL,
  blood_group VARCHAR(5) NOT NULL,
  units_needed INT NOT NULL,
  hospital_name VARCHAR(150) NOT NULL,
  city VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
  state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
  request_date DATE NOT NULL,
  created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Active','Resolved') NOT NULL DEFAULT 'Active',
  priority ENUM('Normal','High','Critical') NOT NULL DEFAULT 'Normal',
  contact_number VARCHAR(15) NOT NULL DEFAULT '',
  KEY idx_request_queue (status, priority, created_time)
);

-- Emergency alerts raised by hospitals or coordinators
CREATE TABLE IF NOT EXISTS emergency_alerts (
  alert_id INT PRIMARY KEY AUTO_INCREMENT,
  request_id INT NULL,
  patient_name VARCHAR(150) NOT NULL,
  blood_group VARCHAR(5) NOT NULL,
  city VARCHAR(100) NOT NULL,
  district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
  state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
  hospital_name VARCHAR(150) NOT NULL,
  urgency_level ENUM('NORMAL','HIGH','CRITICAL') NOT NULL DEFAULT 'NORMAL',
  required_units INT NOT NULL,
  request_time DATETIME NOT NULL,
  status ENUM('OPEN','CONTACTING_DONORS','FULFILLED','CLOSED') NOT NULL DEFAULT 'OPEN',
  KEY idx_alert_queue (status, urgency_level, request_time),
  CONSTRAINT fk_emergency_alert_request
    FOREIGN KEY (request_id) REFERENCES blood_request(request_id)
    ON DELETE SET NULL
);

-- Donation history
CREATE TABLE IF NOT EXISTS donation_history (
  donation_id INT PRIMARY KEY AUTO_INCREMENT,
  donor_id INT NOT NULL,
  donation_date DATE NOT NULL,
  units_donated INT NOT NULL,
  FOREIGN KEY (donor_id) REFERENCES donor(donor_id) ON DELETE CASCADE
);
