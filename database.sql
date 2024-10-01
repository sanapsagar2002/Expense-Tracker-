-- database.sql
CREATE DATABASE expense_tracker;
USE expense_tracker;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);
CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    item VARCHAR(100) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    expense_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    budget DECIMAL(10, 2) NOT NULL,
    month VARCHAR(20),
    year VARCHAR(4),
    FOREIGN KEY (user_id) REFERENCES users(id)
);