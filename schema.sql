CREATE TABLE IF NOT EXISTS test_drivers.driver_info (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(100),
    current_location VARCHAR(60),
    current_day_of_week VARCHAR(60)
);

CREATE TABLE IF NOT EXISTS test_drivers.trailer_info (
    trailer_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT NOT NULL,
    total_amount VARCHAR(40),

    flat_48 VARCHAR(40),
    flat_53 VARCHAR(40),
    step_48 VARCHAR(40),
    step_53 VARCHAR(40),
    bee_equipment VARCHAR(70),
    notes TEXT,
    company VARCHAR(100),
    MC VARCHAR(30),

    FOREIGN KEY (driver_id) REFERENCES test_drivers.driver_info(driver_id)
        ON DELETE CASCADE
);