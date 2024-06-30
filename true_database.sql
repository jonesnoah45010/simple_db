USE YOUR_DATABASE_NAME;

CREATE TABLE simple_db (
    id INT NOT NULL AUTO_INCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED,
    search_key VARCHAR(255),
    user_id VARCHAR(255),
    data JSON,
    PRIMARY KEY (id, created_at, user_id),
    INDEX idx_search_key (search_key),
    INDEX idx_user_id (user_id)
)
PARTITION BY RANGE COLUMNS(user_id) (
    PARTITION p0 VALUES LESS THAN ('user_id1'),
    PARTITION p1 VALUES LESS THAN ('user_id2'),
    PARTITION p_future VALUES LESS THAN (MAXVALUE)
);




DELIMITER //

CREATE PROCEDURE AddUserPartition(IN new_user_id VARCHAR(255))
BEGIN
    DECLARE partition_name VARCHAR(16);
    SET partition_name = CONCAT('p', new_user_id);

    SET @stmt = CONCAT('ALTER TABLE simple_db REORGANIZE PARTITION p_future INTO (',
                       'PARTITION ', partition_name, ' VALUES LESS THAN (''', new_user_id, '''), ',
                       'PARTITION p_future VALUES LESS THAN MAXVALUE)');
    PREPARE stmt FROM @stmt;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

DELIMITER ;




DELIMITER //

CREATE EVENT add_user_partition
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE new_user_id VARCHAR(255);
    DECLARE cur CURSOR FOR
    SELECT DISTINCT user_id FROM simple_db
    WHERE user_id NOT IN (SELECT DISTINCT PARTITION_NAME FROM information_schema.PARTITIONS WHERE TABLE_NAME = 'simple_db');
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO new_user_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        CALL AddUserPartition(new_user_id);
    END LOOP;

    CLOSE cur;
END //

DELIMITER ;





CREATE TABLE simple_db_users (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(255) NULL,
  `email` VARCHAR(255) NULL,
  `password` VARCHAR(255) NULL,
  `is_validated` TINYINT(1) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE);




CREATE TABLE simple_db_temp_passwords (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`username`));











