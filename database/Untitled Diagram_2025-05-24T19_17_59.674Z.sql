CREATE TABLE `equipment` (
	`equipment_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`equipment_type_id` INTEGER,
	`equipment_area_id` INTEGER,
	`equipment_name` VARCHAR(255),
	`equipment_nominal_power_kw` DECIMAL,
	`equipment_installation_date` DATE,
	`equipment_status` VARCHAR(255),
	PRIMARY KEY(`equipment_id`)
);


CREATE TABLE `threshold` (
	`threshold_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`threshold_equipment_id` INTEGER,
	`threshold_area_id` INTEGER,
	`parameter_name` VARCHAR(255),
	`warning_level` DECIMAL,
	`critical_level` DECIMAL,
	PRIMARY KEY(`threshold_id`)
);


CREATE TABLE `areas` (
	`area_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`name` VARCHAR(255),
	`description` VARCHAR(255),
	PRIMARY KEY(`area_id`)
);


CREATE TABLE `energy_readings` (
	`energy_readings_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`energy_readings_meter_id` INTEGER,
	`energy_readings_timestamp` TIMESTAMP,
	`energy_readings_active_power_kw` DECIMAL,
	`energy_readings_reactive_power_kvar` DECIMAL,
	PRIMARY KEY(`energy_readings_id`)
);


CREATE TABLE `logs` (
	`log_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`log_equipment_id` INTEGER,
	`log_meter_id` INTEGER,
	`log_timestamp` TIMESTAMP,
	`log_type` VARCHAR(255),
	`log_parameter_name` VARCHAR(255),
	`log_value` DECIMAL,
	`log_threshold_value` DECIMAL,
	`log_status` VARCHAR(255),
	`log_aknowledged_by_user_id` INTEGER,
	`log_aknowledged_at` TIMESTAMP,
	PRIMARY KEY(`log_id`)
);


CREATE TABLE `users` (
	`user_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`user_username` VARCHAR(255),
	`user_password` VARCHAR(255),
	`user_full_name` VARCHAR(255),
	`user_role` VARCHAR(255),
	PRIMARY KEY(`user_id`)
);


CREATE TABLE `equipment_states` (
	`state_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`state_equipment_id` INTEGER,
	`state_name` VARCHAR(255),
	`state_timestamp` TIMESTAMP,
	`state_operation_code_` VARCHAR(255),
	`state_tool_used` VARCHAR(255),
	PRIMARY KEY(`state_id`)
);


CREATE TABLE `equipment_types` (
	`type_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`type_name` VARCHAR(255),
	`type_description` TEXT(65535),
	PRIMARY KEY(`type_id`)
);


CREATE TABLE `meters` (
	`meter_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
	`meter_equipment_id` INTEGER,
	`meter_model` VARCHAR(255),
	`meter_serial_number` VARCHAR(255),
	`meter_installation_date` DATE,
	`meter_check_date` DATE,
	PRIMARY KEY(`meter_id`)
);


ALTER TABLE `equipment_states`
ADD FOREIGN KEY(`state_equipment_id`) REFERENCES `equipment`(`equipment_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `threshold`
ADD FOREIGN KEY(`threshold_equipment_id`) REFERENCES `equipment`(`equipment_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `energy_readings`
ADD FOREIGN KEY(`energy_readings_meter_id`) REFERENCES `meters`(`meter_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `meters`
ADD FOREIGN KEY(`meter_equipment_id`) REFERENCES `equipment`(`equipment_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `logs`
ADD FOREIGN KEY(`log_meter_id`) REFERENCES `meters`(`meter_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `logs`
ADD FOREIGN KEY(`log_aknowledged_by_user_id`) REFERENCES `users`(`user_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `equipment`
ADD FOREIGN KEY(`equipment_type_id`) REFERENCES `equipment_types`(`type_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `equipment`
ADD FOREIGN KEY(`equipment_area_id`) REFERENCES `areas`(`area_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `threshold`
ADD FOREIGN KEY(`threshold_area_id`) REFERENCES `areas`(`area_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `logs`
ADD FOREIGN KEY(`log_equipment_id`) REFERENCES `equipment`(`equipment_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;