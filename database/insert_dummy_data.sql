USE bloodbridge_db;

-- Insert an admin user with SHA2 hashed password (password: admin123)
INSERT INTO admin (username, password_hash)
VALUES ('admin', SHA2('admin123',256))
ON DUPLICATE KEY UPDATE username = username;

-- Sample blood stock
INSERT INTO blood_stock (blood_group, units_available) VALUES
('A+', 36), ('A-', 10), ('B+', 24), ('B-', 9), ('AB+', 18), ('AB-', 4), ('O+', 32), ('O-', 6)
ON DUPLICATE KEY UPDATE units_available = VALUES(units_available);

-- Hospital network
INSERT IGNORE INTO hospitals (hospital_name, city, district, state, emergency_contact) VALUES
('Apollo Hospital', 'Mysore', 'Mysuru', 'Karnataka', '0821123456'),
('JSS Hospital', 'Mysore', 'Mysuru', 'Karnataka', '0821654321'),
('Manipal Hospital', 'Bangalore', 'Bengaluru Urban', 'Karnataka', '0802233445'),
('City Care Hospital', 'Mangalore', 'Dakshina Kannada', 'Karnataka', '0824223344'),
('KIMS Emergency', 'Hubli', 'Dharwad', 'Karnataka', '0836221100');

-- City-wise stock used by the request-driven emergency workflow.
INSERT INTO city_stock (city, district, state, blood_group, units_available) VALUES
('Mysore','Mysuru','Karnataka','A+',12), ('Mysore','Mysuru','Karnataka','O+',8), ('Mysore','Mysuru','Karnataka','O-',1), ('Mysore','Mysuru','Karnataka','B+',6), ('Mysore','Mysuru','Karnataka','AB-',2),
('Bangalore','Bengaluru Urban','Karnataka','A+',18), ('Bangalore','Bengaluru Urban','Karnataka','O+',14), ('Bangalore','Bengaluru Urban','Karnataka','O-',4), ('Bangalore','Bengaluru Urban','Karnataka','AB+',20), ('Bangalore','Bengaluru Urban','Karnataka','B-',3),
('Mangalore','Dakshina Kannada','Karnataka','A-',4), ('Mangalore','Dakshina Kannada','Karnataka','B+',8), ('Mangalore','Dakshina Kannada','Karnataka','O-',2), ('Mangalore','Dakshina Kannada','Karnataka','O+',6),
('Hubli','Dharwad','Karnataka','A+',6), ('Hubli','Dharwad','Karnataka','B-',2), ('Hubli','Dharwad','Karnataka','O+',7), ('Hubli','Dharwad','Karnataka','AB-',1)
ON DUPLICATE KEY UPDATE units_available = VALUES(units_available);

-- Sample donors
INSERT IGNORE INTO donor
(full_name, age, gender, blood_group, city, district, state, availability_status, contact_number, email, last_donation_date) VALUES
('Arjun Rao', 29, 'Male', 'O-', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010001', 'arjun.rao@example.com', '2026-01-12'),
('Nisha Gowda', 34, 'Female', 'O-', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010002', 'nisha.gowda@example.com', '2025-12-08'),
('Vikram Hegde', 41, 'Male', 'O-', 'Mysore', 'Mysuru', 'Karnataka', 'Recently Donated', '9000010003', 'vikram.hegde@example.com', CURDATE()),
('Meera Shetty', 26, 'Female', 'A+', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010004', 'meera.shetty@example.com', '2026-02-20'),
('Rahul Menon', 31, 'Male', 'O+', 'Bangalore', 'Bengaluru Urban', 'Karnataka', 'Available', '9000010005', 'rahul.menon@example.com', '2026-03-14'),
('Sneha Patel', 32, 'Female', 'AB+', 'Bangalore', 'Bengaluru Urban', 'Karnataka', 'Available', '9000010006', 'sneha.patel@example.com', '2026-02-15'),
('Rohan Verma', 28, 'Male', 'B+', 'Mangalore', 'Dakshina Kannada', 'Karnataka', 'Inactive', '9000010007', 'rohan.verma@example.com', '2025-11-01'),
('Farah Khan', 37, 'Female', 'O-', 'Mangalore', 'Dakshina Kannada', 'Karnataka', 'Available', '9000010008', 'farah.khan@example.com', '2026-01-21'),
('Kiran Desai', 24, 'Male', 'B-', 'Hubli', 'Dharwad', 'Karnataka', 'Available', '9000010009', 'kiran.desai@example.com', '2026-04-01');

-- Sample donation history
INSERT IGNORE INTO donation_history (donor_id, donation_date, units_donated) VALUES
(1, '2026-01-12', 1),
(2, '2025-12-08', 1),
(4, '2026-02-20', 1),
(5, '2026-03-14', 1),
(8, '2026-01-21', 1);

-- Ensure at least two donors for each common blood group (added extras)
INSERT IGNORE INTO donor
(full_name, age, gender, blood_group, city, district, state, availability_status, contact_number, email, last_donation_date) VALUES
('Priya Kumar', 30, 'Female', 'A+', 'Bangalore', 'Bengaluru Urban', 'Karnataka', 'Available', '9000010010', 'priya.kumar@example.com', '2025-10-10'),
('Anil Sharma', 45, 'Male', 'A-', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010011', 'anil.sharma@example.com', '2025-09-05'),
('Sana Reddy', 29, 'Female', 'A-', 'Mangalore', 'Dakshina Kannada', 'Karnataka', 'Available', '9000010012', 'sana.reddy@example.com', '2026-02-02'),
('Deepak Nair', 35, 'Male', 'B+', 'Bangalore', 'Bengaluru Urban', 'Karnataka', 'Available', '9000010013', 'deepak.nair@example.com', '2025-08-20'),
('Leela Naik', 38, 'Female', 'B-', 'Hubli', 'Dharwad', 'Karnataka', 'Available', '9000010014', 'leela.naik@example.com', '2026-03-30'),
('Manu Iyer', 27, 'Male', 'AB+', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010015', 'manu.iyer@example.com', '2026-01-05'),
('Rita Joshi', 33, 'Female', 'AB-', 'Bangalore', 'Bengaluru Urban', 'Karnataka', 'Available', '9000010016', 'rita.joshi@example.com', '2025-11-12'),
('Suresh Pillai', 50, 'Male', 'AB-', 'Mangalore', 'Dakshina Kannada', 'Karnataka', 'Available', '9000010017', 'suresh.pillai@example.com', '2026-02-28'),
('Asha Rao', 22, 'Female', 'O+', 'Mysore', 'Mysuru', 'Karnataka', 'Available', '9000010018', 'asha.rao@example.com', '2026-04-05')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- Emergency requests and alerts are created by the application workflow, not seeded by default.
