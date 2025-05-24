-- Инициализация базы данных для системы мониторинга энергопотребления

-- Создание таблицы данных энергопотребления
CREATE TABLE IF NOT EXISTS energy_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    timestamp DATETIME(3) NOT NULL,
    active_power DECIMAL(10,3),
    reactive_power DECIMAL(10,3),
    apparent_power DECIMAL(10,3),
    power_factor DECIMAL(5,3),
    voltage_l1 DECIMAL(8,2),
    voltage_l2 DECIMAL(8,2),
    voltage_l3 DECIMAL(8,2),
    current_l1 DECIMAL(8,3),
    current_l2 DECIMAL(8,3),
    current_l3 DECIMAL(8,3),
    frequency DECIMAL(6,3),
    energy_consumed DECIMAL(12,3),
    data_quality ENUM('good', 'poor', 'bad') DEFAULT 'good',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_time (device_name, timestamp),
    INDEX idx_timestamp (timestamp),
    INDEX idx_device (device_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы состояния оборудования
CREATE TABLE IF NOT EXISTS equipment_status (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    timestamp DATETIME(3) NOT NULL,
    status JSON,
    equipment_state ENUM('running', 'stopped', 'maintenance', 'error') DEFAULT 'stopped',
    discrete_inputs JSON,
    analog_inputs JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_time (device_name, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы уведомлений
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    message TEXT,
    parameter_name VARCHAR(50),
    current_value DECIMAL(15,6),
    threshold_value DECIMAL(15,6),
    timestamp DATETIME(3) NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at DATETIME(3),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at DATETIME(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_time (device_name, timestamp),
    INDEX idx_severity (severity),
    INDEX idx_acknowledged (acknowledged),
    INDEX idx_resolved (resolved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    role ENUM('admin', 'operator', 'viewer') NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME(3),
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы устройств
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    device_type ENUM('meter', 'plc', 'sensor') NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    port INT NOT NULL DEFAULT 502,
    unit_id INT NOT NULL DEFAULT 1,
    protocol ENUM('modbus_tcp', 'modbus_rtu', 'opc_ua') DEFAULT 'modbus_tcp',
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    location VARCHAR(200),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_communication DATETIME(3),
    communication_status ENUM('online', 'offline', 'error') DEFAULT 'offline',
    configuration JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_type (device_type),
    INDEX idx_active (is_active),
    INDEX idx_status (communication_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы пороговых значений
CREATE TABLE IF NOT EXISTS thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100),
    parameter_name VARCHAR(50) NOT NULL,
    min_value DECIMAL(15,6),
    max_value DECIMAL(15,6),
    warning_min DECIMAL(15,6),
    warning_max DECIMAL(15,6),
    critical_min DECIMAL(15,6),
    critical_max DECIMAL(15,6),
    unit VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_param (device_name, parameter_name),
    INDEX idx_parameter (parameter_name),
    INDEX idx_active (is_active),
    UNIQUE KEY unique_device_parameter (device_name, parameter_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы системных настроек
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    category VARCHAR(50),
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (setting_key),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы логов системы
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(3) NOT NULL,
    level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    logger_name VARCHAR(100),
    message TEXT,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INT,
    user_id INT,
    device_name VARCHAR(100),
    additional_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level),
    INDEX idx_logger (logger_name),
    INDEX idx_user (user_id),
    INDEX idx_device (device_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы отчетов
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    report_type ENUM('summary', 'detailed', 'efficiency', 'violations', 'custom') NOT NULL,
    parameters JSON,
    file_path VARCHAR(500),
    file_format ENUM('pdf', 'excel', 'csv') NOT NULL,
    generated_by INT,
    generated_at DATETIME(3) NOT NULL,
    file_size BIGINT,
    status ENUM('generating', 'completed', 'failed') DEFAULT 'generating',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (report_type),
    INDEX idx_generated_by (generated_by),
    INDEX idx_generated_at (generated_at),
    INDEX idx_status (status),
    FOREIGN KEY (generated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Вставка начальных данных

-- Создание администратора по умолчанию
-- Пароль: admin123 (в реальной системе должен быть изменен)
INSERT INTO users (username, email, password_hash, salt, role) VALUES 
('admin', 'admin@company.com', SHA2(CONCAT('admin123', 'default_salt'), 256), 'default_salt', 'admin');

-- Вставка устройств по умолчанию
INSERT INTO devices (name, device_type, ip_address, port, unit_id, manufacturer, model, location, description) VALUES 
('Счетчик Меркурий 1', 'meter', '192.168.1.100', 502, 1, 'Инкотекс', 'Меркурий 234 ARTM2-00 DPBR.G', 'Цех №1, Участок А', 'Основной счетчик электроэнергии участка А'),
('ПЛК ОВЕН 1', 'plc', '192.168.1.101', 502, 2, 'ОВЕН', 'ПЛК210-03-CS', 'Цех №1, Участок А', 'Контроллер управления оборудованием участка А'),
('Модуль дискретного ввода 1', 'sensor', '192.168.1.102', 502, 3, 'ОВЕН', 'МВ110-224.16ДН', 'Цех №1, Участок А', 'Модуль дискретного ввода для контроля состояния оборудования');

-- Вставка пороговых значений по умолчанию
INSERT INTO thresholds (device_name, parameter_name, max_value, warning_max, critical_max, unit) VALUES 
(NULL, 'active_power', 1000.0, 900.0, 1000.0, 'кВт'),
(NULL, 'current_l1', 100.0, 90.0, 100.0, 'А'),
(NULL, 'current_l2', 100.0, 90.0, 100.0, 'А'),
(NULL, 'current_l3', 100.0, 90.0, 100.0, 'А'),
(NULL, 'voltage_l1', 250.0, 240.0, 250.0, 'В'),
(NULL, 'voltage_l2', 250.0, 240.0, 250.0, 'В'),
(NULL, 'voltage_l3', 250.0, 240.0, 250.0, 'В');

INSERT INTO thresholds (device_name, parameter_name, min_value, warning_min, critical_min, unit) VALUES 
(NULL, 'voltage_l1', 200.0, 210.0, 200.0, 'В'),
(NULL, 'voltage_l2', 200.0, 210.0, 200.0, 'В'),
(NULL, 'voltage_l3', 200.0, 210.0, 200.0, 'В'),
(NULL, 'power_factor', 0.8, 0.85, 0.8, '');

-- Вставка системных настроек
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
('company_name', 'ООО "Производственная компания"', 'string', 'Название компании', 'general');

-- Создание представлений для удобства работы с данными

-- Представление последних данных по устройствам
CREATE VIEW latest_energy_data AS
SELECT 
    ed.*,
    d.device_type,
    d.location,
    d.communication_status
FROM energy_data ed
INNER JOIN devices d ON ed.device_name = d.name
INNER JOIN (
    SELECT device_name, MAX(timestamp) as max_timestamp
    FROM energy_data
    GROUP BY device_name
) latest ON ed.device_name = latest.device_name AND ed.timestamp = latest.max_timestamp;

-- Представление активных уведомлений
CREATE VIEW active_alerts AS
SELECT 
    a.*,
    d.device_type,
    d.location
FROM alerts a
INNER JOIN devices d ON a.device_name = d.name
WHERE a.acknowledged = FALSE AND a.resolved = FALSE
ORDER BY a.severity DESC, a.timestamp DESC;

-- Представление статистики по устройствам за последние 24 часа
CREATE VIEW device_stats_24h AS
SELECT 
    device_name,
    COUNT(*) as data_points,
    AVG(active_power) as avg_power,
    MAX(active_power) as max_power,
    MIN(active_power) as min_power,
    AVG(power_factor) as avg_power_factor,
    AVG((voltage_l1 + voltage_l2 + voltage_l3) / 3) as avg_voltage,
    AVG((current_l1 + current_l2 + current_l3) / 3) as avg_current
FROM energy_data
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY device_name;

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
    
    -- Удаление старых данных энергопотребления
    DELETE FROM energy_data 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    -- Удаление старых логов
    DELETE FROM system_logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    -- Удаление старых разрешенных уведомлений
    DELETE FROM alerts 
    WHERE resolved = TRUE AND resolved_at < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    COMMIT;
END //

-- Процедура получения статистики энергопотребления
CREATE PROCEDURE GetEnergyStats(
    IN device_name_param VARCHAR(100),
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT 
        device_name,
        COUNT(*) as total_measurements,
        AVG(active_power) as avg_active_power,
        MAX(active_power) as max_active_power,
        MIN(active_power) as min_active_power,
        SUM(active_power * TIMESTAMPDIFF(SECOND, LAG(timestamp) OVER (ORDER BY timestamp), timestamp) / 3600) as total_energy_kwh,
        AVG(power_factor) as avg_power_factor,
        MIN(power_factor) as min_power_factor,
        COUNT(CASE WHEN data_quality = 'poor' THEN 1 END) as poor_quality_count,
        COUNT(CASE WHEN data_quality = 'bad' THEN 1 END) as bad_quality_count
    FROM energy_data
    WHERE (device_name_param IS NULL OR device_name = device_name_param)
        AND timestamp BETWEEN start_date AND end_date
    GROUP BY device_name
    ORDER BY device_name;
END //

DELIMITER ;

-- Создание триггеров

-- Триггер для обновления статуса связи устройства
DELIMITER //
CREATE TRIGGER update_device_communication_status
AFTER INSERT ON energy_data
FOR EACH ROW
BEGIN
    UPDATE devices 
    SET 
        last_communication = NEW.timestamp,
        communication_status = 'online'
    WHERE name = NEW.device_name;
END //
DELIMITER ;

-- Триггер для автоматического создания уведомлений при превышении порогов
DELIMITER //
CREATE TRIGGER check_thresholds_after_insert
AFTER INSERT ON energy_data
FOR EACH ROW
BEGIN
    -- Проверка активной мощности
    IF NEW.active_power IS NOT NULL THEN
        INSERT INTO alerts (device_name, alert_type, severity, message, parameter_name, current_value, threshold_value, timestamp)
        SELECT 
            NEW.device_name,
            'threshold_exceeded',
            CASE 
                WHEN NEW.active_power > t.critical_max THEN 'critical'
                WHEN NEW.active_power > t.warning_max THEN 'high'
                ELSE 'medium'
            END,
            CONCAT('Превышение мощности: ', NEW.active_power, ' кВт (порог: ', COALESCE(t.critical_max, t.warning_max, t.max_value), ' кВт)'),
            'active_power',
            NEW.active_power,
            COALESCE(t.critical_max, t.warning_max, t.max_value),
            NEW.timestamp
        FROM thresholds t
        WHERE (t.device_name = NEW.device_name OR t.device_name IS NULL)
            AND t.parameter_name = 'active_power'
            AND t.is_active = TRUE
            AND (
                (t.critical_max IS NOT NULL AND NEW.active_power > t.critical_max) OR
                (t.warning_max IS NOT NULL AND NEW.active_power > t.warning_max) OR
                (t.max_value IS NOT NULL AND NEW.active_power > t.max_value)
            )
        ORDER BY t.device_name DESC
        LIMIT 1;
    END IF;
    
    -- Аналогичные проверки можно добавить для других параметров
END //
DELIMITER ;

-- Создание индексов для оптимизации производительности
CREATE INDEX idx_energy_data_composite ON energy_data (device_name, timestamp, active_power);
CREATE INDEX idx_alerts_composite ON alerts (device_name, severity, acknowledged, timestamp);
CREATE INDEX idx_system_logs_composite ON system_logs (timestamp, level, logger_name);

-- Настройка автоматической очистки данных (событие)
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
