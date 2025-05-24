-- Инициализация базы данных для системы мониторинга энергопотребления
-- Обновленная схема БД

-- Создание таблиц согласно новой схеме

-- Таблица типов оборудования
CREATE TABLE `equipment_types` (
    `type_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `type_name` VARCHAR(255) NOT NULL,
    `type_description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`type_id`),
    INDEX idx_type_name (type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица участков/зон
CREATE TABLE `areas` (
    `area_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `name` VARCHAR(255) NOT NULL,
    `description` VARCHAR(255),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`area_id`),
    INDEX idx_area_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица оборудования
CREATE TABLE `equipment` (
    `equipment_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `equipment_type_id` INTEGER,
    `equipment_area_id` INTEGER,
    `equipment_name` VARCHAR(255) NOT NULL,
    `equipment_nominal_power_kw` DECIMAL(10,3),
    `equipment_installation_date` DATE,
    `equipment_status` VARCHAR(255) DEFAULT 'active',
    `ip_address` VARCHAR(45),
    `port` INTEGER DEFAULT 502,
    `unit_id` INTEGER DEFAULT 1,
    `protocol` ENUM('modbus_tcp', 'modbus_rtu', 'opc_ua') DEFAULT 'modbus_tcp',
    `manufacturer` VARCHAR(100),
    `model` VARCHAR(100),
    `serial_number` VARCHAR(100),
    `last_communication` TIMESTAMP NULL,
    `communication_status` ENUM('online', 'offline', 'error') DEFAULT 'offline',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`equipment_id`),
    INDEX idx_equipment_name (equipment_name),
    INDEX idx_equipment_status (equipment_status),
    INDEX idx_communication_status (communication_status),
    FOREIGN KEY(`equipment_type_id`) REFERENCES `equipment_types`(`type_id`) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY(`equipment_area_id`) REFERENCES `areas`(`area_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица счетчиков
CREATE TABLE `meters` (
    `meter_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `meter_equipment_id` INTEGER,
    `meter_model` VARCHAR(255),
    `meter_serial_number` VARCHAR(255),
    `meter_installation_date` DATE,
    `meter_check_date` DATE,
    `meter_next_check_date` DATE,
    `meter_accuracy_class` VARCHAR(10),
    `meter_transformation_ratio_current` DECIMAL(8,2) DEFAULT 1.0,
    `meter_transformation_ratio_voltage` DECIMAL(8,2) DEFAULT 1.0,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`meter_id`),
    INDEX idx_meter_serial (meter_serial_number),
    INDEX idx_meter_equipment (meter_equipment_id),
    INDEX idx_meter_active (is_active),
    FOREIGN KEY(`meter_equipment_id`) REFERENCES `equipment`(`equipment_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица показаний энергопотребления
CREATE TABLE `energy_readings` (
    `energy_readings_id` BIGINT NOT NULL AUTO_INCREMENT UNIQUE,
    `energy_readings_meter_id` INTEGER NOT NULL,
    `energy_readings_timestamp` TIMESTAMP(3) NOT NULL,
    `energy_readings_active_power_kw` DECIMAL(12,6),
    `energy_readings_reactive_power_kvar` DECIMAL(12,6),
    `energy_readings_apparent_power_kva` DECIMAL(12,6),
    `energy_readings_power_factor` DECIMAL(5,3),
    `energy_readings_voltage_l1` DECIMAL(8,2),
    `energy_readings_voltage_l2` DECIMAL(8,2),
    `energy_readings_voltage_l3` DECIMAL(8,2),
    `energy_readings_current_l1` DECIMAL(8,3),
    `energy_readings_current_l2` DECIMAL(8,3),
    `energy_readings_current_l3` DECIMAL(8,3),
    `energy_readings_frequency` DECIMAL(6,3),
    `energy_readings_total_active_energy` DECIMAL(15,6),
    `energy_readings_total_reactive_energy` DECIMAL(15,6),
    `data_quality` ENUM('good', 'poor', 'bad') DEFAULT 'good',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(`energy_readings_id`),
    INDEX idx_meter_timestamp (energy_readings_meter_id, energy_readings_timestamp),
    INDEX idx_timestamp (energy_readings_timestamp),
    INDEX idx_data_quality (data_quality),
    FOREIGN KEY(`energy_readings_meter_id`) REFERENCES `meters`(`meter_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица состояний оборудования
CREATE TABLE `equipment_states` (
    `state_id` BIGINT NOT NULL AUTO_INCREMENT UNIQUE,
    `state_equipment_id` INTEGER NOT NULL,
    `state_name` VARCHAR(255),
    `state_timestamp` TIMESTAMP(3) NOT NULL,
    `state_operation_code` VARCHAR(255),
    `state_tool_used` VARCHAR(255),
    `state_duration_minutes` INTEGER,
    `state_power_consumption_kwh` DECIMAL(10,6),
    `state_efficiency_percent` DECIMAL(5,2),
    `additional_data` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(`state_id`),
    INDEX idx_equipment_timestamp (state_equipment_id, state_timestamp),
    INDEX idx_state_name (state_name),
    INDEX idx_operation_code (state_operation_code),
    FOREIGN KEY(`state_equipment_id`) REFERENCES `equipment`(`equipment_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица пользователей
CREATE TABLE `users` (
    `user_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `user_username` VARCHAR(255) UNIQUE NOT NULL,
    `user_password` VARCHAR(255) NOT NULL,
    `user_full_name` VARCHAR(255),
    `user_email` VARCHAR(255),
    `user_role` ENUM('admin', 'operator', 'viewer') NOT NULL DEFAULT 'viewer',
    `user_salt` VARCHAR(32),
    `is_active` BOOLEAN DEFAULT TRUE,
    `last_login` TIMESTAMP NULL,
    `failed_login_attempts` INTEGER DEFAULT 0,
    `locked_until` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`user_id`),
    INDEX idx_username (user_username),
    INDEX idx_role (user_role),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица пороговых значений
CREATE TABLE `threshold` (
    `threshold_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `threshold_equipment_id` INTEGER,
    `threshold_area_id` INTEGER,
    `parameter_name` VARCHAR(255) NOT NULL,
    `warning_level` DECIMAL(15,6),
    `critical_level` DECIMAL(15,6),
    `min_warning_level` DECIMAL(15,6),
    `min_critical_level` DECIMAL(15,6),
    `unit` VARCHAR(20),
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`threshold_id`),
    INDEX idx_equipment_parameter (threshold_equipment_id, parameter_name),
    INDEX idx_area_parameter (threshold_area_id, parameter_name),
    INDEX idx_parameter (parameter_name),
    INDEX idx_active (is_active),
    FOREIGN KEY(`threshold_equipment_id`) REFERENCES `equipment`(`equipment_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY(`threshold_area_id`) REFERENCES `areas`(`area_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица логов/уведомлений
CREATE TABLE `logs` (
    `log_id` BIGINT NOT NULL AUTO_INCREMENT UNIQUE,
    `log_equipment_id` INTEGER,
    `log_meter_id` INTEGER,
    `log_timestamp` TIMESTAMP(3) NOT NULL,
    `log_type` ENUM('info', 'warning', 'error', 'critical', 'threshold_exceeded', 'communication_error', 'state_change') NOT NULL,
    `log_parameter_name` VARCHAR(255),
    `log_value` DECIMAL(15,6),
    `log_threshold_value` DECIMAL(15,6),
    `log_status` ENUM('new', 'acknowledged', 'resolved', 'ignored') DEFAULT 'new',
    `log_message` TEXT,
    `log_acknowledged_by_user_id` INTEGER,
    `log_acknowledged_at` TIMESTAMP NULL,
    `log_resolved_at` TIMESTAMP NULL,
    `severity` ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    `additional_data` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(`log_id`),
    INDEX idx_equipment_timestamp (log_equipment_id, log_timestamp),
    INDEX idx_meter_timestamp (log_meter_id, log_timestamp),
    INDEX idx_type_status (log_type, log_status),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (log_timestamp),
    INDEX idx_acknowledged (log_acknowledged_by_user_id),
    FOREIGN KEY(`log_equipment_id`) REFERENCES `equipment`(`equipment_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY(`log_meter_id`) REFERENCES `meters`(`meter_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY(`log_acknowledged_by_user_id`) REFERENCES `users`(`user_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица системных настроек
CREATE TABLE `system_settings` (
    `setting_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `setting_key` VARCHAR(100) UNIQUE NOT NULL,
    `setting_value` TEXT,
    `setting_type` ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    `description` TEXT,
    `category` VARCHAR(50),
    `is_editable` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(`setting_id`),
    INDEX idx_key (setting_key),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица отчетов
CREATE TABLE `reports` (
    `report_id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `report_name` VARCHAR(200) NOT NULL,
    `report_type` ENUM('summary', 'detailed', 'efficiency', 'violations', 'custom') NOT NULL,
    `report_parameters` JSON,
    `file_path` VARCHAR(500),
    `file_format` ENUM('pdf', 'excel', 'csv') NOT NULL,
    `generated_by_user_id` INTEGER,
    `generated_at` TIMESTAMP NOT NULL,
    `file_size` BIGINT,
    `status` ENUM('generating', 'completed', 'failed') DEFAULT 'generating',
    `error_message` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(`report_id`),
    INDEX idx_type (report_type),
    INDEX idx_generated_by (generated_by_user_id),
    INDEX idx_generated_at (generated_at),
    INDEX idx_status (status),
    FOREIGN KEY (generated_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Вставка начальных данных

-- Типы оборудования
INSERT INTO equipment_types (type_name, type_description) VALUES 
('Токарный станок', 'Металлообрабатывающий токарный станок'),
('Фрезерный станок', 'Металлообрабатывающий фрезерный станок'),
('Сверлильный станок', 'Сверлильный станок'),
('Шлифовальный станок', 'Шлифовальный станок'),
('Прессовое оборудование', 'Гидравлические и механические прессы'),
('Сварочное оборудование', 'Сварочные аппараты и установки'),
('Компрессорное оборудование', 'Воздушные компрессоры'),
('Вентиляционное оборудование', 'Системы вентиляции и кондиционирования'),
('Освещение', 'Системы освещения цеха'),
('Вспомогательное оборудование', 'Прочее вспомогательное оборудование');

-- Участки цеха
INSERT INTO areas (name, description) VALUES 
('Участок А - Токарная группа', 'Участок токарной обработки деталей'),
('Участок Б - Фрезерная группа', 'Участок фрезерной обработки'),
('Участок В - Сборочный', 'Участок сборки изделий'),
('Участок Г - Термообработка', 'Участок термической обработки'),
('Участок Д - Контроль качества', 'Участок контроля качества продукции'),
('Вспомогательные системы', 'Компрессоры, вентиляция, освещение');

-- Оборудование
INSERT INTO equipment (equipment_type_id, equipment_area_id, equipment_name, equipment_nominal_power_kw, 
                      equipment_installation_date, equipment_status, ip_address, port, unit_id, manufacturer, model) VALUES 
(1, 1, 'Токарный станок ТС-001', 15.5, '2020-03-15', 'active', '192.168.1.100', 502, 1, 'Инкотекс', 'Меркурий 234'),
(2, 2, 'Фрезерный станок ФС-001', 22.0, '2019-11-20', 'active', '192.168.1.101', 502, 2, 'ОВЕН', 'ПЛК210-03-CS'),
(1, 1, 'Токарный станок ТС-002', 18.0, '2021-05-10', 'active', '192.168.1.102', 502, 3, 'Инкотекс', 'Меркурий 234'),
(3, 1, 'Сверлильный станок СС-001', 5.5, '2020-08-12', 'active', '192.168.1.103', 502, 4, 'ОВЕН', 'МВ110-224.16ДН'),
(7, 6, 'Компрессор КМП-001', 45.0, '2018-12-01', 'active', '192.168.1.104', 502, 5, 'Atlas Copco', 'GA22'),
(8, 6, 'Вентиляция ВНТ-001', 12.0, '2019-06-15', 'active', '192.168.1.105', 502, 6, 'Systemair', 'DVNI-560');

-- Счетчики
INSERT INTO meters (meter_equipment_id, meter_model, meter_serial_number, meter_installation_date, 
                   meter_check_date, meter_next_check_date, meter_accuracy_class) VALUES 
(1, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234001', '2020-03-15', '2023-03-15', '2027-03-15', '0.5S'),
(2, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234002', '2019-11-20', '2023-11-20', '2027-11-20', '0.5S'),
(3, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234003', '2021-05-10', '2024-05-10', '2028-05-10', '0.5S'),
(4, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234004', '2020-08-12', '2023-08-12', '2027-08-12', '0.5S'),
(5, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234005', '2018-12-01', '2023-12-01', '2027-12-01', '0.5S'),
(6, 'Меркурий 234 ARTM2-00 DPBR.G', 'M234006', '2019-06-15', '2023-06-15', '2027-06-15', '0.5S');

-- Пользователи
-- Пароль: admin123 (в реальной системе должен быть изменен)
INSERT INTO users (user_username, user_password, user_full_name, user_email, user_role, user_salt) VALUES 
('admin', SHA2(CONCAT('admin123', 'default_salt'), 256), 'Администратор системы', 'admin@company.com', 'admin', 'default_salt'),
('operator1', SHA2(CONCAT('operator123', 'default_salt'), 256), 'Оператор участка А', 'operator1@company.com', 'operator', 'default_salt'),
('viewer1', SHA2(CONCAT('viewer123', 'default_salt'), 256), 'Наблюдатель', 'viewer1@company.com', 'viewer', 'default_salt');

-- Пороговые значения
INSERT INTO threshold (threshold_equipment_id, parameter_name, warning_level, critical_level, unit) VALUES 
-- Общие пороги для активной мощности
(NULL, 'energy_readings_active_power_kw', 50.0, 60.0, 'кВт'),
-- Пороги для конкретного оборудования
(1, 'energy_readings_active_power_kw', 18.0, 20.0, 'кВт'),
(2, 'energy_readings_active_power_kw', 25.0, 30.0, 'кВт'),
(5, 'energy_readings_active_power_kw', 50.0, 55.0, 'кВт'),
-- Пороги для напряжения
(NULL, 'energy_readings_voltage_l1', 250.0, 260.0, 'В'),
(NULL, 'energy_readings_voltage_l2', 250.0, 260.0, 'В'),
(NULL, 'energy_readings_voltage_l3', 250.0, 260.0, 'В'),
-- Минимальные пороги для напряжения
(NULL, 'energy_readings_voltage_l1', NULL, NULL, 'В'),
(NULL, 'energy_readings_voltage_l2', NULL, NULL, 'В'),
(NULL, 'energy_readings_voltage_l3', NULL, NULL, 'В');

UPDATE threshold SET min_warning_level = 210.0, min_critical_level = 200.0 
WHERE parameter_name LIKE 'energy_readings_voltage_%';

-- Пороги для тока
INSERT INTO threshold (threshold_equipment_id, parameter_name, warning_level, critical_level, unit) VALUES 
(NULL, 'energy_readings_current_l1', 90.0, 100.0, 'А'),
(NULL, 'energy_readings_current_l2', 90.0, 100.0, 'А'),
(NULL, 'energy_readings_current_l3', 90.0, 100.0, 'А'),
-- Пороги для коэффициента мощности
(NULL, 'energy_readings_power_factor', NULL, NULL, '');

UPDATE threshold SET min_warning_level = 0.85, min_critical_level = 0.8 
WHERE parameter_name = 'energy_readings_power_factor';

-- Пороги по участкам
INSERT INTO threshold (threshold_area_id, parameter_name, warning_level, critical_level, unit) VALUES 
(1, 'total_power_consumption', 80.0, 100.0, 'кВт'),
(2, 'total_power_consumption', 60.0, 80.0, 'кВт'),
(6, 'total_power_consumption', 70.0, 90.0, 'кВт');

-- Системные настройки
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, category) VALUES 
('collection_interval', '5', 'integer', 'Интервал сбора данных в секундах', 'data_collection'),
('connection_timeout', '10', 'integer', 'Таймаут подключения к устройствам в секундах', 'data_collection'),
('data_retention_days', '365', 'integer', 'Период хранения данных в днях', 'database'),
('max_failed_login_attempts', '5', 'integer', 'Максимальное количество неудачных попыток входа', 'security'),
('account_lockout_duration', '30', 'integer', 'Время блокировки аккаунта в минутах', 'security'),
('enable_email_notifications', 'false', 'boolean', 'Включить уведомления по email', 'notifications'),
('smtp_server', '', 'string', 'SMTP сервер для отправки email', 'notifications'),
('smtp_port', '587', 'integer', 'Порт SMTP сервера', 'notifications'),
('system_name', 'Система мониторинга энергопотребления', 'string', 'Название системы', 'general'),
('company_name', 'ООО "Металлообрабатывающий завод"', 'string', 'Название компании', 'general'),
('auto_acknowledge_timeout', '24', 'integer', 'Автоматическое подтверждение уведомлений через часы', 'notifications'),
('energy_cost_per_kwh', '4.5', 'float', 'Стоимость электроэнергии за кВт·ч', 'economics');

-- Создание представлений для удобства работы с данными

-- Представление последних показаний по оборудованию
CREATE VIEW latest_energy_readings AS
SELECT 
    er.*,
    e.equipment_name,
    e.equipment_nominal_power_kw,
    e.equipment_status,
    e.communication_status,
    a.name as area_name,
    et.type_name as equipment_type,
    m.meter_model,
    m.meter_serial_number
FROM energy_readings er
INNER JOIN meters m ON er.energy_readings_meter_id = m.meter_id
INNER JOIN equipment e ON m.meter_equipment_id = e.equipment_id
INNER JOIN areas a ON e.equipment_area_id = a.area_id
INNER JOIN equipment_types et ON e.equipment_type_id = et.type_id
INNER JOIN (
    SELECT energy_readings_meter_id, MAX(energy_readings_timestamp) as max_timestamp
    FROM energy_readings
    GROUP BY energy_readings_meter_id
) latest ON er.energy_readings_meter_id = latest.energy_readings_meter_id 
    AND er.energy_readings_timestamp = latest.max_timestamp;

-- Представление активных уведомлений
CREATE VIEW active_logs AS
SELECT 
    l.*,
    e.equipment_name,
    a.name as area_name,
    et.type_name as equipment_type,
    u.user_full_name as acknowledged_by_name
FROM logs l
LEFT JOIN equipment e ON l.log_equipment_id = e.equipment_id
LEFT JOIN areas a ON e.equipment_area_id = a.area_id
LEFT JOIN equipment_types et ON e.equipment_type_id = et.type_id
LEFT JOIN users u ON l.log_acknowledged_by_user_id = u.user_id
WHERE l.log_status IN ('new', 'acknowledged') AND l.log_resolved_at IS NULL
ORDER BY l.severity DESC, l.log_timestamp DESC;

-- Представление статистики энергопотребления по участкам за последние 24 часа
CREATE VIEW area_energy_stats_24h AS
SELECT 
    a.area_id,
    a.name as area_name,
    COUNT(er.energy_readings_id) as total_readings,
    AVG(er.energy_readings_active_power_kw) as avg_power_kw,
    MAX(er.energy_readings_active_power_kw) as max_power_kw,
    MIN(er.energy_readings_active_power_kw) as min_power_kw,
    SUM(er.energy_readings_active_power_kw * 
        TIMESTAMPDIFF(SECOND, 
            LAG(er.energy_readings_timestamp) OVER (PARTITION BY a.area_id ORDER BY er.energy_readings_timestamp), 
            er.energy_readings_timestamp
        ) / 3600) as total_energy_kwh,
    AVG(er.energy_readings_power_factor) as avg_power_factor,
    COUNT(DISTINCT e.equipment_id) as equipment_count
FROM areas a
LEFT JOIN equipment e ON a.area_id = e.equipment_area_id
LEFT JOIN meters m ON e.equipment_id = m.meter_equipment_id
LEFT JOIN energy_readings er ON m.meter_id = er.energy_readings_meter_id
WHERE er.energy_readings_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY a.area_id, a.name;

-- Представление эффективности оборудования
CREATE VIEW equipment_efficiency AS
SELECT 
    e.equipment_id,
    e.equipment_name,
    e.equipment_nominal_power_kw,
    a.name as area_name,
    et.type_name as equipment_type,
    AVG(er.energy_readings_active_power_kw) as avg_actual_power_kw,
    (AVG(er.energy_readings_active_power_kw) / e.equipment_nominal_power_kw * 100) as load_factor_percent,
    AVG(er.energy_readings_power_factor) as avg_power_factor,
    COUNT(er.energy_readings_id) as readings_count,
    MAX(er.energy_readings_timestamp) as last_reading_time
FROM equipment e
LEFT JOIN areas a ON e.equipment_area_id = a.area_id
LEFT JOIN equipment_types et ON e.equipment_type_id = et.type_id
LEFT JOIN meters m ON e.equipment_id = m.meter_equipment_id
LEFT JOIN energy_readings er ON m.meter_id = er.energy_readings_meter_id
WHERE er.energy_readings_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY e.equipment_id, e.equipment_name, e.equipment_nominal_power_kw, a.name, et.type_name;

-- Создание хранимых процедур

DELIMITER //

-- Процедура очистки старых данных
CREATE PROCEDURE CleanupOldData(IN retention_days INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Удаление старых показаний энергопотребления
    DELETE FROM energy_readings 
    WHERE energy_readings_timestamp < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    -- Удаление старых состояний оборудования
    DELETE FROM equipment_states 
    WHERE state_timestamp < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    -- Удаление старых разрешенных логов
    DELETE FROM logs 
    WHERE log_status = 'resolved' AND log_resolved_at < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    COMMIT;
END //

-- Процедура получения статистики энергопотребления
CREATE PROCEDURE GetEnergyStatistics(
    IN equipment_id_param INT,
    IN area_id_param INT,
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT 
        e.equipment_id,
        e.equipment_name,
        a.name as area_name,
        et.type_name as equipment_type,
        COUNT(er.energy_readings_id) as total_measurements,
        AVG(er.energy_readings_active_power_kw) as avg_active_power,
        MAX(er.energy_readings_active_power_kw) as max_active_power,
        MIN(er.energy_readings_active_power_kw) as min_active_power,
        SUM(er.energy_readings_active_power_kw * 
            TIMESTAMPDIFF(SECOND, 
                LAG(er.energy_readings_timestamp) OVER (PARTITION BY e.equipment_id ORDER BY er.energy_readings_timestamp), 
                er.energy_readings_timestamp
            ) / 3600) as total_energy_kwh,
        AVG(er.energy_readings_power_factor) as avg_power_factor,
        MIN(er.energy_readings_power_factor) as min_power_factor,
        COUNT(CASE WHEN er.data_quality = 'poor' THEN 1 END) as poor_quality_count,
        COUNT(CASE WHEN er.data_quality = 'bad' THEN 1 END) as bad_quality_count,
        (AVG(er.energy_readings_active_power_kw) / e.equipment_nominal_power_kw * 100) as avg_load_factor_percent
    FROM equipment e
    LEFT JOIN areas a ON e.equipment_area_id = a.area_id
    LEFT JOIN equipment_types et ON e.equipment_type_id = et.type_id
    LEFT JOIN meters m ON e.equipment_id = m.meter_equipment_id
    LEFT JOIN energy_readings er ON m.meter_id = er.energy_readings_meter_id
    WHERE (equipment_id_param IS NULL OR e.equipment_id = equipment_id_param)
        AND (area_id_param IS NULL OR e.equipment_area_id = area_id_param)
        AND (er.energy_readings_timestamp IS NULL OR er.energy_readings_timestamp BETWEEN start_date AND end_date)
    GROUP BY e.equipment_id, e.equipment_name, a.name, et.type_name, e.equipment_nominal_power_kw
    ORDER BY e.equipment_name;
END //

-- Процедура создания уведомления
CREATE PROCEDURE CreateLog(
    IN equipment_id_param INT,
    IN meter_id_param INT,
    IN log_type_param VARCHAR(255),
    IN parameter_name_param VARCHAR(255),
    IN value_param DECIMAL(15,6),
    IN threshold_value_param DECIMAL(15,6),
    IN message_param TEXT,
    IN severity_param VARCHAR(20)
)
BEGIN
    INSERT INTO logs (
        log_equipment_id, 
        log_meter_id, 
        log_timestamp, 
        log_type, 
        log_parameter_name, 
        log_value, 
        log_threshold_value, 
        log_message, 
        severity
    ) VALUES (
        equipment_id_param,
        meter_id_param,
        NOW(3),
        log_type_param,
        parameter_name_param,
        value_param,
        threshold_value_param,
        message_param,
        severity_param
    );
END //

DELIMITER ;

-- Создание триггеров

-- Триггер для обновления статуса связи оборудования
DELIMITER //
CREATE TRIGGER update_equipment_communication_status
AFTER INSERT ON energy_readings
FOR EACH ROW
BEGIN
    UPDATE equipment e
    INNER JOIN meters m ON e.equipment_id = m.meter_equipment_id
    SET 
        e.last_communication = NEW.energy_readings_timestamp,
        e.communication_status = 'online'
    WHERE m.meter_id = NEW.energy_readings_meter_id;
END //
DELIMITER ;

-- Триггер для автоматического создания уведомлений при превышении порогов
DELIMITER //
CREATE TRIGGER check_thresholds_after_energy_reading
AFTER INSERT ON energy_readings
FOR EACH ROW
BEGIN
    DECLARE equipment_id_var INT;
    DECLARE area_id_var INT;
    
    -- Получение ID оборудования и участка
    SELECT e.equipment_id, e.equipment_area_id INTO equipment_id_var, area_id_var
    FROM equipment e
    INNER JOIN meters m ON e.equipment_id = m.meter_equipment_id
    WHERE m.meter_id = NEW.energy_readings_meter_id;
    
    -- Проверка активной мощности
    IF NEW.energy_readings_active_power_kw IS NOT NULL THEN
        -- Проверка порогов для конкретного оборудования
        INSERT INTO logs (log_equipment_id, log_meter_id, log_timestamp, log_type, log_parameter_name, 
                         log_value, log_threshold_value, log_message, severity)
        SELECT 
            equipment_id_var,
            NEW.energy_readings_meter_id,
            NEW.energy_readings_timestamp,
            'threshold_exceeded',
            'energy_readings_active_power_kw',
            NEW.energy_readings_active_power_kw,
            CASE 
                WHEN NEW.energy_readings_active_power_kw > t.critical_level THEN t.critical_level
                ELSE t.warning_level
            END,
            CONCAT('Превышение мощности: ', NEW.energy_readings_active_power_kw, ' кВт (порог: ', 
                   CASE 
                       WHEN NEW.energy_readings_active_power_kw > t.critical_level THEN t.critical_level
                       ELSE t.warning_level
                   END, ' кВт)'),
            CASE 
                WHEN NEW.energy_readings_active_power_kw > t.critical_level THEN 'critical'
                ELSE 'high'
            END
        FROM threshold t
        WHERE t.parameter_name = 'energy_readings_active_power_kw'
            AND t.is_active = TRUE
            AND (t.threshold_equipment_id = equipment_id_var OR 
                 (t.threshold_equipment_id IS NULL AND t.threshold_area_id IS NULL) OR
                 t.threshold_area_id = area_id_var)
            AND (
                (t.critical_level IS NOT NULL AND NEW.energy_readings_active_power_kw > t.critical_level) OR
                (t.warning_level IS NOT NULL AND NEW.energy_readings_active_power_kw > t.warning_level)
            )
        ORDER BY t.threshold_equipment_id DESC, t.threshold_area_id DESC
        LIMIT 1;
    END IF;
    
    -- Проверка коэффициента мощности
    IF NEW.energy_readings_power_factor IS NOT NULL THEN
        INSERT INTO logs (log_equipment_id, log_meter_id, log_timestamp, log_type, log_parameter_name, 
                         log_value, log_threshold_value, log_message, severity)
        SELECT 
            equipment_id_var,
            NEW.energy_readings_meter_id,
            NEW.energy_readings_timestamp,
            'threshold_exceeded',
            'energy_readings_power_factor',
            NEW.energy_readings_power_factor,
            CASE 
                WHEN NEW.energy_readings_power_factor < t.min_critical_level THEN t.min_critical_level
                ELSE t.min_warning_level
            END,
            CONCAT('Низкий коэффициент мощности: ', NEW.energy_readings_power_factor, 
                   ' (минимум: ', 
                   CASE 
                       WHEN NEW.energy_readings_power_factor < t.min_critical_level THEN t.min_critical_level
                       ELSE t.min_warning_level
                   END, ')'),
            CASE 
                WHEN NEW.energy_readings_power_factor < t.min_critical_level THEN 'critical'
                ELSE 'high'
            END
        FROM threshold t
        WHERE t.parameter_name = 'energy_readings_power_factor'
            AND t.is_active = TRUE
            AND (t.threshold_equipment_id = equipment_id_var OR 
                 (t.threshold_equipment_id IS NULL AND t.threshold_area_id IS NULL) OR
                 t.threshold_area_id = area_id_var)
            AND (
                (t.min_critical_level IS NOT NULL AND NEW.energy_readings_power_factor < t.min_critical_level) OR
                (t.min_warning_level IS NOT NULL AND NEW.energy_readings_power_factor < t.min_warning_level)
            )
        ORDER BY t.threshold_equipment_id DESC, t.threshold_area_id DESC
        LIMIT 1;
    END IF;
END //
DELIMITER ;

-- Создание индексов для оптимизации производительности
CREATE INDEX idx_energy_readings_composite ON energy_readings (energy_readings_meter_id, energy_readings_timestamp, energy_readings_active_power_kw);
CREATE INDEX idx_logs_composite ON logs (log_equipment_id, log_type, log_status, log_timestamp);
CREATE INDEX idx_equipment_states_composite ON equipment_states (state_equipment_id, state_timestamp, state_name);

-- Настройка автоматической очистки данных
SET GLOBAL event_scheduler = ON;

DELIMITER //
CREATE EVENT IF NOT EXISTS cleanup_old_data_event
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    DECLARE retention_days INT DEFAULT 365;
    
    -- Получение настройки периода хранения
    SELECT CAST(setting_value AS UNSIGNED) INTO retention_days
    FROM system_settings 
    WHERE setting_key = 'data_retention_days' 
    LIMIT 1;
    
    -- Вызов процедуры очистки
    CALL CleanupOldData(retention_days);
END //
DELIMITER ;

-- Создание события для автоматического подтверждения старых уведомлений
DELIMITER //
CREATE EVENT IF NOT EXISTS auto_acknowledge_old_logs
ON SCHEDULE EVERY 1 HOUR
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    DECLARE timeout_hours INT DEFAULT 24;
    
    -- Получение настройки таймаута
    SELECT CAST(setting_value AS UNSIGNED) INTO timeout_hours
    FROM system_settings 
    WHERE setting_key = 'auto_acknowledge_timeout' 
    LIMIT 1;
    
    -- Автоматическое подтверждение старых уведомлений
    UPDATE logs 
    SET log_status = 'acknowledged',
        log_acknowledged_at = NOW()
    WHERE log_status = 'new' 
        AND log_timestamp < DATE_SUB(NOW(), INTERVAL timeout_hours HOUR)
        AND log_type IN ('warning', 'info');
END //
DELIMITER ;
