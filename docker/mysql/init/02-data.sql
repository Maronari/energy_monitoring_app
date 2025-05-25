-- Добавление тестовых данных для демонстрации системы

-- Добавление исторических данных энергопотребления за последние 7 дней
DELIMITER //

CREATE PROCEDURE GenerateTestData()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE meter_id_var INT;
    DECLARE equipment_id_var INT;
    DECLARE equipment_name_var VARCHAR(255);
    DECLARE nominal_power_var DECIMAL(10,3);
    DECLARE current_time DATETIME;
    DECLARE days_back INT DEFAULT 7;
    DECLARE hours_in_day INT DEFAULT 24;
    DECLARE measurements_per_hour INT DEFAULT 12; -- каждые 5 минут
    
    -- Курсор для получения всех счетчиков
    DECLARE meter_cursor CURSOR FOR 
        SELECT m.meter_id, e.equipment_id, e.equipment_name, e.equipment_nominal_power_kw
        FROM meters m
        INNER JOIN equipment e ON m.meter_equipment_id = e.equipment_id
        WHERE m.is_active = TRUE;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    SET current_time = DATE_SUB(NOW(), INTERVAL days_back DAY);
    
    OPEN meter_cursor;
    
    meter_loop: LOOP
        FETCH meter_cursor INTO meter_id_var, equipment_id_var, equipment_name_var, nominal_power_var;
        IF done THEN
            LEAVE meter_loop;
        END IF;
        
        -- Генерация данных для каждого счетчика
        SET @day_counter = 0;
        WHILE @day_counter < days_back DO
            SET @hour_counter = 0;
            WHILE @hour_counter < hours_in_day DO
                SET @measurement_counter = 0;
                WHILE @measurement_counter < measurements_per_hour DO
                    
                    SET @timestamp = DATE_ADD(current_time, INTERVAL (@day_counter * 24 + @hour_counter) HOUR);
                    SET @timestamp = DATE_ADD(@timestamp, INTERVAL (@measurement_counter * 5) MINUTE);
                    
                    -- Генерация реалистичных данных в зависимости от времени и типа оборудования
                    SET @base_power = nominal_power_var * 0.7; -- базовая нагрузка 70% от номинала
                    
                    -- Вариация по времени суток (рабочие часы 8-18)
                    SET @hour_of_day = HOUR(@timestamp);
                    IF @hour_of_day >= 8 AND @hour_of_day <= 18 THEN
                        SET @time_factor = 1.0 + 0.3 * SIN((@hour_of_day - 8) * PI() / 10); -- пик в середине дня
                    ELSE
                        SET @time_factor = 0.2; -- ночная нагрузк��
                    END IF;
                    
                    -- Случайная вариация ±20%
                    SET @random_factor = 0.8 + (RAND() * 0.4);
                    
                    -- Активная мощность
                    SET @active_power = @base_power * @time_factor * @random_factor;
                    
                    -- Реактивная мощность (зависит от коэффициента мощности)
                    SET @power_factor = 0.8 + (RAND() * 0.15); -- 0.8-0.95
                    SET @reactive_power = @active_power * TAN(ACOS(@power_factor));
                    
                    -- Полная мощность
                    SET @apparent_power = SQRT(POW(@active_power, 2) + POW(@reactive_power, 2));
                    
                    -- Напряжения (220В ±5%)
                    SET @voltage_l1 = 220 + (RAND() - 0.5) * 22;
                    SET @voltage_l2 = 220 + (RAND() - 0.5) * 22;
                    SET @voltage_l3 = 220 + (RAND() - 0.5) * 22;
                    
                    -- Токи (рассчитываются из мощности и напряжения)
                    SET @current_l1 = @active_power * 1000 / (@voltage_l1 * SQRT(3));
                    SET @current_l2 = @active_power * 1000 / (@voltage_l2 * SQRT(3));
                    SET @current_l3 = @active_power * 1000 / (@voltage_l3 * SQRT(3));
                    
                    -- Частота
                    SET @frequency = 50 + (RAND() - 0.5) * 0.5;
                    
                    -- Качество данных (95% хорошие, 4% удовлетворительные, 1% плохие)
                    SET @quality_rand = RAND();
                    SET @data_quality = CASE 
                        WHEN @quality_rand < 0.95 THEN 'good'
                        WHEN @quality_rand < 0.99 THEN 'poor'
                        ELSE 'bad'
                    END;
                    
                    -- Вставка данных
                    INSERT INTO energy_readings (
                        energy_readings_meter_id,
                        energy_readings_timestamp,
                        energy_readings_active_power_kw,
                        energy_readings_reactive_power_kvar,
                        energy_readings_apparent_power_kva,
                        energy_readings_power_factor,
                        energy_readings_voltage_l1,
                        energy_readings_voltage_l2,
                        energy_readings_voltage_l3,
                        energy_readings_current_l1,
                        energy_readings_current_l2,
                        energy_readings_current_l3,
                        energy_readings_frequency,
                        data_quality
                    ) VALUES (
                        meter_id_var,
                        @timestamp,
                        @active_power,
                        @reactive_power,
                        @apparent_power,
                        @power_factor,
                        @voltage_l1,
                        @voltage_l2,
                        @voltage_l3,
                        @current_l1,
                        @current_l2,
                        @current_l3,
                        @frequency,
                        @data_quality
                    );
                    
                    SET @measurement_counter = @measurement_counter + 1;
                END WHILE;
                SET @hour_counter = @hour_counter + 1;
            END WHILE;
            SET @day_counter = @day_counter + 1;
        END WHILE;
        
        SET done = FALSE;
    END LOOP;
    
    CLOSE meter_cursor;
END //

DELIMITER ;

-- Генерация состояний оборудования
DELIMITER //

CREATE PROCEDURE GenerateEquipmentStates()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE equipment_id_var INT;
    DECLARE equipment_name_var VARCHAR(255);
    DECLARE current_time DATETIME;
    DECLARE days_back INT DEFAULT 7;
    
    DECLARE equipment_cursor CURSOR FOR 
        SELECT equipment_id, equipment_name
        FROM equipment
        WHERE equipment_status = 'active';
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    SET current_time = DATE_SUB(NOW(), INTERVAL days_back DAY);
    
    OPEN equipment_cursor;
    
    equipment_loop: LOOP
        FETCH equipment_cursor INTO equipment_id_var, equipment_name_var;
        IF done THEN
            LEAVE equipment_loop;
        END IF;
        
        -- Генерация состояний для каждого оборудования
        SET @day_counter = 0;
        WHILE @day_counter < days_back DO
            -- Рабочий день: 8:00 - 18:00
            SET @work_start = DATE_ADD(current_time, INTERVAL (@day_counter * 24 + 8) HOUR);
            SET @work_end = DATE_ADD(current_time, INTERVAL (@day_counter * 24 + 18) HOUR);
            
            -- Начало работы
            INSERT INTO equipment_states (
                state_equipment_id,
                state_name,
                state_timestamp,
                state_operation_code,
                state_duration_minutes,
                additional_data
            ) VALUES (
                equipment_id_var,
                'running',
                @work_start,
                CONCAT('OP_', FLOOR(RAND() * 1000)),
                600, -- 10 часов работы
                JSON_OBJECT('shift', 'day', 'operator', CONCAT('Operator_', FLOOR(RAND() * 10)))
            );
            
            -- Обеденный перерыв
            SET @lunch_start = DATE_ADD(@work_start, INTERVAL 4 HOUR);
            INSERT INTO equipment_states (
                state_equipment_id,
                state_name,
                state_timestamp,
                state_operation_code,
                state_duration_minutes
            ) VALUES (
                equipment_id_var,
                'stopped',
                @lunch_start,
                'LUNCH_BREAK',
                60
            );
            
            -- Возобновление работы
            INSERT INTO equipment_states (
                state_equipment_id,
                state_name,
                state_timestamp,
                state_operation_code,
                state_duration_minutes
            ) VALUES (
                equipment_id_var,
                'running',
                DATE_ADD(@lunch_start, INTERVAL 1 HOUR),
                CONCAT('OP_', FLOOR(RAND() * 1000)),
                300
            );
            
            -- Окончание работы
            INSERT INTO equipment_states (
                state_equipment_id,
                state_name,
                state_timestamp,
                state_operation_code
            ) VALUES (
                equipment_id_var,
                'stopped',
                @work_end,
                'END_SHIFT'
            );
            
            SET @day_counter = @day_counter + 1;
        END WHILE;
        
        SET done = FALSE;
    END LOOP;
    
    CLOSE equipment_cursor;
END //

DELIMITER ;

-- Генерация тестовых логов/уведомлений
DELIMITER //

CREATE PROCEDURE GenerateTestLogs()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE equipment_id_var INT;
    DECLARE meter_id_var INT;
    DECLARE equipment_name_var VARCHAR(255);
    
    DECLARE equipment_cursor CURSOR FOR 
        SELECT e.equipment_id, m.meter_id, e.equipment_name
        FROM equipment e
        INNER JOIN meters m ON e.equipment_id = m.meter_equipment_id
        WHERE e.equipment_status = 'active' AND m.is_active = TRUE;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN equipment_cursor;
    
    equipment_loop: LOOP
        FETCH equipment_cursor INTO equipment_id_var, meter_id_var, equipment_name_var;
        IF done THEN
            LEAVE equipment_loop;
        END IF;
        
        -- Генерация различных типов логов
        
        -- Превышение мощности (2 дня назад)
        INSERT INTO logs (
            log_equipment_id,
            log_meter_id,
            log_timestamp,
            log_type,
            log_parameter_name,
            log_value,
            log_threshold_value,
            log_message,
            severity,
            log_status
        ) VALUES (
            equipment_id_var,
            meter_id_var,
            DATE_SUB(NOW(), INTERVAL 2 DAY),
            'threshold_exceeded',
            'energy_readings_active_power_kw',
            25.5,
            25.0,
            CONCAT('Превышение мощности на оборудовании ', equipment_name_var, ': 25.5 кВт (порог: 25.0 кВт)'),
            'high',
            'resolved'
        );
        
        -- Низкий коэффициент мощности (1 день назад)
        INSERT INTO logs (
            log_equipment_id,
            log_meter_id,
            log_timestamp,
            log_type,
            log_parameter_name,
            log_value,
            log_threshold_value,
            log_message,
            severity,
            log_status
        ) VALUES (
            equipment_id_var,
            meter_id_var,
            DATE_SUB(NOW(), INTERVAL 1 DAY),
            'threshold_exceeded',
            'energy_readings_power_factor',
            0.75,
            0.80,
            CONCAT('Низкий коэффициент мощности на оборудовании ', equipment_name_var, ': 0.75 (минимум: 0.80)'),
            'medium',
            'acknowledged'
        );
        
        -- Активное уведомление (если это первое оборудование)
        IF equipment_id_var = 1 THEN
            INSERT INTO logs (
                log_equipment_id,
                log_meter_id,
                log_timestamp,
                log_type,
                log_parameter_name,
                log_value,
                log_threshold_value,
                log_message,
                severity,
                log_status
            ) VALUES (
                equipment_id_var,
                meter_id_var,
                DATE_SUB(NOW(), INTERVAL 2 HOUR),
                'threshold_exceeded',
                'energy_readings_voltage_l1',
                195.0,
                200.0,
                CONCAT('Низкое напряжение L1 на оборудовании ', equipment_name_var, ': 195.0 В (минимум: 200.0 В)'),
                'critical',
                'new'
            );
            
            INSERT INTO logs (
                log_equipment_id,
                log_meter_id,
                log_timestamp,
                log_type,
                log_message,
                severity,
                log_status
            ) VALUES (
                equipment_id_var,
                meter_id_var,
                DATE_SUB(NOW(), INTERVAL 1 HOUR),
                'communication_error',
                CONCAT('Потеря связи с оборудованием ', equipment_name_var),
                'high',
                'new'
            );
        END IF;
        
        SET done = FALSE;
    END LOOP;
    
    CLOSE equipment_cursor;
END //

DELIMITER ;

-- Выполнение процедур генерации тестовых данных
CALL GenerateTestData();
CALL GenerateEquipmentStates();
CALL GenerateTestLogs();

-- Удаление временных процедур
DROP PROCEDURE GenerateTestData;
DROP PROCEDURE GenerateEquipmentStates;
DROP PROCEDURE GenerateTestLogs;

-- Обновление статистики таблиц
ANALYZE TABLE energy_readings;
ANALYZE TABLE equipment_states;
ANALYZE TABLE logs;
    