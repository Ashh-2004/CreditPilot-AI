CREATE DATABASE loaniq_db;
USE loaniq_db;

CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','officer','viewer') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE borrowers (
  borrower_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  email VARCHAR(100),
  phone VARCHAR(15),
  credit_score INT,
  annual_income DECIMAL(12,2),
  employment_type ENUM('Salaried','Self-Employed','Business','Government'),
  property_area ENUM('Urban','Semi-Urban','Rural'),
  existing_loans INT DEFAULT 0,
  date_of_birth DATE
);

CREATE TABLE loan_applications (
  application_id INT AUTO_INCREMENT PRIMARY KEY,
  borrower_id INT,
  reviewed_by INT,
  loan_amount DECIMAL(12,2),
  loan_purpose ENUM('Home Loan','Personal Loan','Education Loan','Vehicle Loan','Business Loan'),
  interest_rate DECIMAL(5,2),
  tenure_months INT,
  status ENUM('pending','approved','rejected','review') DEFAULT 'pending',
  approval_probability DECIMAL(5,2),
  ml_default_probability DECIMAL(5,2) DEFAULT NULL,
  ml_risk_band ENUM('Low','Medium','High') DEFAULT NULL,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (borrower_id) REFERENCES borrowers(borrower_id),
  FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
);

CREATE TABLE loans (
  loan_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT,
  outstanding_balance DECIMAL(12,2),
  disbursement_date DATE,
  last_payment_date DATE,
  loan_status ENUM('active','closed','defaulted','npa'),
  processing_fee DECIMAL(10,2),
  FOREIGN KEY (application_id) REFERENCES loan_applications(application_id)
);

CREATE TABLE payments (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  loan_id INT,
  amount_paid DECIMAL(12,2),
  principal_component DECIMAL(12,2),
  interest_component DECIMAL(12,2),
  payment_date DATE,
  payment_mode ENUM('NEFT','UPI','Cash','Cheque'),
  FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE emi_schedule (
  emi_id INT AUTO_INCREMENT PRIMARY KEY,
  loan_id INT,
  month_number INT,
  opening_balance DECIMAL(12,2),
  emi_amount DECIMAL(12,2),
  principal DECIMAL(12,2),
  interest DECIMAL(12,2),
  closing_balance DECIMAL(12,2),
  due_date DATE,
  is_paid BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

CREATE TABLE collateral (
  collateral_id INT AUTO_INCREMENT PRIMARY KEY,
  borrower_id INT,
  loan_id INT,
  collateral_type ENUM('Property','Vehicle','FD','Gold','Other'),
  estimated_value DECIMAL(12,2),
  description VARCHAR(255),
  FOREIGN KEY (borrower_id) REFERENCES borrowers(borrower_id),
  FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);