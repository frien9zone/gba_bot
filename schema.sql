CREATE TABLE IF NOT EXISTS defaultdb.driver_info (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(100),
    current_location VARCHAR(60),
    current_day_of_week TEXT
);

CREATE TABLE IF NOT EXISTS defaultdb.trailer_info (
    trailer_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT NOT NULL,
    trailer_type TEXT,
    length INT,
    bee_nets TEXT,
    special_equipment TEXT,
    MC TEXT,

    FOREIGN KEY (driver_id) REFERENCES defaultdb.driver_info(driver_id)
        ON DELETE CASCADE
);
