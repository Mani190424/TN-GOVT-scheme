-- TN GOVT SCHEME BOT Database Schema
-- MySQL Database Setup

-- Create Database
CREATE DATABASE IF NOT EXISTS tn_scheme_bot;
USE tn_scheme_bot;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20),
    district VARCHAR(100),
    age INT,
    gender ENUM('Male', 'Female', 'Other', 'Prefer Not to Say'),
    occupation VARCHAR(100),
    category ENUM('General', 'OBC', 'SC', 'ST'),
    annual_income BIGINT,
    profile_image VARCHAR(500),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM('Super Admin', 'Admin', 'Moderator') DEFAULT 'Admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Schemes Table
CREATE TABLE IF NOT EXISTS schemes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scheme_name VARCHAR(255) NOT NULL,
    scheme_code VARCHAR(50) UNIQUE,
    category VARCHAR(100),
    description TEXT,
    eligibility TEXT,
    age_min INT,
    age_max INT,
    gender_specific VARCHAR(50),
    occupation_specific VARCHAR(255),
    category_specific VARCHAR(255),
    income_limit BIGINT,
    required_documents TEXT,
    benefits TEXT,
    benefit_amount VARCHAR(255),
    application_process TEXT,
    application_deadline DATE,
    district VARCHAR(100),
    is_state_wide BOOLEAN DEFAULT TRUE,
    official_link VARCHAR(500),
    application_link VARCHAR(500),
    helpline VARCHAR(20),
    email VARCHAR(255),
    office_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_category (category),
    INDEX idx_district (district),
    INDEX idx_active (is_active)
);

-- Chat History Table
CREATE TABLE IF NOT EXISTS chat_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    session_id VARCHAR(255),
    user_query TEXT NOT NULL,
    bot_response TEXT,
    language ENUM('English', 'Tamil') DEFAULT 'English',
    schemes_recommended JSON,
    intent VARCHAR(100),
    entities JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at)
);

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    chat_history_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    is_helpful BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_history_id) REFERENCES chat_history(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating)
);

-- Favorite Schemes Table
CREATE TABLE IF NOT EXISTS favorite_schemes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    scheme_id INT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (scheme_id) REFERENCES schemes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, scheme_id),
    INDEX idx_user_id (user_id)
);

-- Eligibility Results Table
CREATE TABLE IF NOT EXISTS eligibility_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    query_text TEXT,
    eligible_schemes JSON,
    partially_eligible_schemes JSON,
    not_eligible_schemes JSON,
    required_documents JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    admin_id INT,
    title VARCHAR(255),
    message TEXT,
    notification_type ENUM('Scheme Update', 'New Scheme', 'Important Notice', 'System Update'),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read)
);

-- Analytics Table
CREATE TABLE IF NOT EXISTS analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    total_users INT DEFAULT 0,
    total_schemes INT DEFAULT 0,
    total_queries INT DEFAULT 0,
    average_response_time FLOAT,
    user_satisfaction FLOAT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sample schemes data
INSERT INTO schemes (scheme_name, scheme_code, category, description, eligibility, age_min, age_max, benefit_amount, official_link, is_state_wide, is_active) 
VALUES 
('Pongal Scheme', 'PS-001', 'Agricultural', 'Annual pongal cash assistance for farmers', 'Registered farmers in Tamil Nadu', 18, 80, '₹1500', 'https://tnagri.gov.in', TRUE, TRUE),
('Puratchi Thalaivi Dr. J. Jayalalithaa Uniform Distribution Scheme', 'UT-001', 'Education', 'Free uniform for school children', 'Class 1-12 students', 5, 18, 'Free Uniform', 'https://tnschools.gov.in', TRUE, TRUE),
('Amma Unavagam', 'AU-001', 'Social Welfare', 'Subsidised meals for poor people', 'BPL and AADHAR card holders', 0, 120, '₹5 meal', 'https://tnsc.gov.in', TRUE, TRUE),
('Dr. Ambedkar Housing Scheme', 'DAS-001', 'Housing', 'Housing assistance for SC/ST communities', 'SC/ST families with income below specified limit', 18, 65, 'Up to 1 lakh', 'https://tnhousing.gov.in', TRUE, TRUE),
('Jeeva Nalam Scheme', 'JN-001', 'Health', 'Health insurance for BPL families', 'BPL families', 0, 120, 'Coverage up to 5 lakhs', 'https://tnhealth.gov.in', TRUE, TRUE)
ON DUPLICATE KEY UPDATE id=id;

-- Initial analytics record
INSERT INTO analytics (total_users, total_schemes, total_queries, average_response_time, user_satisfaction)
VALUES (0, 5, 0, 0.0, 0.0)
ON DUPLICATE KEY UPDATE id=id;

COMMIT;