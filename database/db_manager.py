"""
Обновленный менеджер базы данных для новой схемы
"""
import asyncio
import aiomysql
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.docker_settings import DockerSettings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, settings: DockerSettings = None):
        self.settings = settings or DockerSettings()
        self.pool = None
    
    async def initialize(self):
        """Инициализация подключения к БД"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.settings.DATABASE.host,
                port=self.settings.DATABASE.port,
                user=self.settings.DATABASE.username,
                password=self.settings.DATABASE.password,
                db=self.settings.DATABASE.database,
                autocommit=True,
                maxsize=10,
                charset='utf8mb4'
            )
            
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    async def save_energy_readings(self, readings_data: List[Dict[str, Any]]):
        """Сохранение показаний энергопотребления"""
        if not readings_data:
            return
        
        sql = '''
            INSERT INTO energy_readings 
            (energy_readings_meter_id, energy_readings_timestamp, energy_readings_active_power_kw, 
             energy_readings_reactive_power_kvar, energy_readings_apparent_power_kva, 
             energy_readings_power_factor, energy_readings_voltage_l1, energy_readings_voltage_l2, 
             energy_readings_voltage_l3, energy_readings_current_l1, energy_readings_current_l2, 
             energy_readings_current_l3, energy_readings_frequency, data_quality)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for record in readings_data:
                    await cursor.execute(sql, (
                        record.get('meter_id'),
                        record.get('timestamp'),
                        record.get('active_power'),
                        record.get('reactive_power'),
                        record.get('apparent_power'),
                        record.get('power_factor'),
                        record.get('voltage_l1'),
                        record.get('voltage_l2'),
                        record.get('voltage_l3'),
                        record.get('current_l1'),
                        record.get('current_l2'),
                        record.get('current_l3'),
                        record.get('frequency'),
                        record.get('data_quality', 'good')
                    ))
    
    async def save_equipment_state(self, equipment_id: int, state_data: Dict[str, Any]):
        """Сохранение состояния оборудования"""
        sql = '''
            INSERT INTO equipment_states 
            (state_equipment_id, state_name, state_timestamp, state_operation_code, 
             state_tool_used, state_duration_minutes, state_power_consumption_kwh, 
             state_efficiency_percent, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    equipment_id,
                    state_data.get('state_name'),
                    state_data.get('timestamp', datetime.now()),
                    state_data.get('operation_code'),
                    state_data.get('tool_used'),
                    state_data.get('duration_minutes'),
                    state_data.get('power_consumption_kwh'),
                    state_data.get('efficiency_percent'),
                    state_data.get('additional_data')
                ))
    
    async def create_log(self, log_data: Dict[str, Any]):
        """Создание записи в логах"""
        sql = '''
            INSERT INTO logs 
            (log_equipment_id, log_meter_id, log_timestamp, log_type, log_parameter_name, 
             log_value, log_threshold_value, log_message, severity, additional_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    log_data.get('equipment_id'),
                    log_data.get('meter_id'),
                    log_data.get('timestamp', datetime.now()),
                    log_data.get('log_type'),
                    log_data.get('parameter_name'),
                    log_data.get('value'),
                    log_data.get('threshold_value'),
                    log_data.get('message'),
                    log_data.get('severity', 'medium'),
                    log_data.get('additional_data')
                ))
    
    async def get_equipment_list(self) -> List[Dict[str, Any]]:
        """Получение списка оборудования"""
        sql = '''
            SELECT 
                e.equipment_id,
                e.equipment_name,
                e.equipment_nominal_power_kw,
                e.equipment_status,
                e.communication_status,
                e.ip_address,
                e.port,
                e.unit_id,
                a.name as area_name,
                et.type_name as equipment_type,
                COUNT(m.meter_id) as meters_count
            FROM equipment e
            LEFT JOIN areas a ON e.equipment_area_id = a.area_id
            LEFT JOIN equipment_types et ON e.equipment_type_id = et.type_id
            LEFT JOIN meters m ON e.equipment_id = m.meter_equipment_id AND m.is_active = TRUE
            GROUP BY e.equipment_id
            ORDER BY a.name, e.equipment_name
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()
    
    async def get_meters_by_equipment(self, equipment_id: int) -> List[Dict[str, Any]]:
        """Получение счетчиков для оборудования"""
        sql = '''
            SELECT 
                m.*,
                e.equipment_name
            FROM meters m
            INNER JOIN equipment e ON m.meter_equipment_id = e.equipment_id
            WHERE e.equipment_id = %s AND m.is_active = TRUE
            ORDER BY m.meter_id
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (equipment_id,))
                return await cursor.fetchall()
    
    async def get_latest_energy_readings(self, limit: int = 100, equipment_id: int = None) -> List[Dict[str, Any]]:
        """Получение последних показаний энергопотребления"""
        sql = '''
            SELECT * FROM latest_energy_readings
            WHERE (%s IS NULL OR equipment_id = %s)
            ORDER BY energy_readings_timestamp DESC 
            LIMIT %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (equipment_id, equipment_id, limit))
                return await cursor.fetchall()
    
    async def get_energy_readings_by_period(self, start_time: datetime, end_time: datetime, 
                                          equipment_id: int = None, area_id: int = None) -> List[Dict[str, Any]]:
        """Получение показаний за период"""
        sql = '''
            SELECT 
                er.*,
                e.equipment_name,
                a.name as area_name,
                et.type_name as equipment_type
            FROM energy_readings er
            INNER JOIN meters m ON er.energy_readings_meter_id = m.meter_id
            INNER JOIN equipment e ON m.meter_equipment_id = e.equipment_id
            INNER JOIN areas a ON e.equipment_area_id = a.area_id
            INNER JOIN equipment_types et ON e.equipment_type_id = et.type_id
            WHERE er.energy_readings_timestamp BETWEEN %s AND %s
                AND (%s IS NULL OR e.equipment_id = %s)
                AND (%s IS NULL OR e.equipment_area_id = %s)
            ORDER BY er.energy_readings_timestamp
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (start_time, end_time, equipment_id, equipment_id, area_id, area_id))
                return await cursor.fetchall()
    
    async def get_active_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение активных уведомлений"""
        sql = '''
            SELECT * FROM active_logs
            ORDER BY severity DESC, log_timestamp DESC
            LIMIT %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (limit,))
                return await cursor.fetchall()
    
    async def acknowledge_log(self, log_id: int, user_id: int):
        """Подтверждение уведомления"""
        sql = '''
            UPDATE logs 
            SET log_status = 'acknowledged',
                log_acknowledged_by_user_id = %s,
                log_acknowledged_at = NOW()
            WHERE log_id = %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (user_id, log_id))
    
    async def resolve_log(self, log_id: int):
        """Разрешение уведомления"""
        sql = '''
            UPDATE logs 
            SET log_status = 'resolved',
                log_resolved_at = NOW()
            WHERE log_id = %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (log_id,))
    
    async def get_area_statistics(self, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """Получение статистики по участкам"""
        if start_time and end_time:
            sql = '''
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
                WHERE er.energy_readings_timestamp BETWEEN %s AND %s
                GROUP BY a.area_id, a.name
                ORDER BY a.name
            '''
            
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, (start_time, end_time))
                    return await cursor.fetchall()
        else:
            sql = 'SELECT * FROM area_energy_stats_24h ORDER BY area_name'
            
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    return await cursor.fetchall()
    
    async def get_equipment_efficiency(self) -> List[Dict[str, Any]]:
        """Получение показателей эффективности оборудования"""
        sql = 'SELECT * FROM equipment_efficiency ORDER BY equipment_name'
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()
    
    async def get_thresholds(self, equipment_id: int = None, area_id: int = None) -> List[Dict[str, Any]]:
        """Получение пороговых значений"""
        sql = '''
            SELECT 
                t.*,
                e.equipment_name,
                a.name as area_name
            FROM threshold t
            LEFT JOIN equipment e ON t.threshold_equipment_id = e.equipment_id
            LEFT JOIN areas a ON t.threshold_area_id = a.area_id
            WHERE t.is_active = TRUE
                AND (%s IS NULL OR t.threshold_equipment_id = %s)
                AND (%s IS NULL OR t.threshold_area_id = %s)
            ORDER BY t.parameter_name, e.equipment_name, a.name
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (equipment_id, equipment_id, area_id, area_id))
                return await cursor.fetchall()
    
    async def update_threshold(self, threshold_id: int, threshold_data: Dict[str, Any]):
        """Обновление порогового значения"""
        sql = '''
            UPDATE threshold 
            SET warning_level = %s,
                critical_level = %s,
                min_warning_level = %s,
                min_critical_level = %s,
                updated_at = NOW()
            WHERE threshold_id = %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    threshold_data.get('warning_level'),
                    threshold_data.get('critical_level'),
                    threshold_data.get('min_warning_level'),
                    threshold_data.get('min_critical_level'),
                    threshold_id
                ))
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Получение списка пользователей"""
        sql = '''
            SELECT 
                user_id,
                user_username,
                user_full_name,
                user_email,
                user_role,
                is_active,
                last_login,
                created_at
            FROM users
            ORDER BY user_username
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя"""
        sql = '''
            SELECT 
                user_id,
                user_username,
                user_full_name,
                user_role,
                user_salt,
                is_active,
                failed_login_attempts,
                locked_until
            FROM users
            WHERE user_username = %s 
                AND user_password = SHA2(CONCAT(%s, user_salt), 256)
                AND is_active = TRUE
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (username, password))
                user = await cursor.fetchone()
                
                if user:
                    # Обновление времени последнего входа
                    await cursor.execute(
                        'UPDATE users SET last_login = NOW(), failed_login_attempts = 0 WHERE user_id = %s',
                        (user['user_id'],)
                    )
                
                return user
    
    async def get_system_settings(self, category: str = None) -> List[Dict[str, Any]]:
        """Получение системных настроек"""
        if category:
            sql = '''
                SELECT * FROM system_settings 
                WHERE category = %s 
                ORDER BY setting_key
            '''
            params = (category,)
        else:
            sql = 'SELECT * FROM system_settings ORDER BY category, setting_key'
            params = ()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, params)
                return await cursor.fetchall()
    
    async def update_system_setting(self, setting_key: str, setting_value: str):
        """Обновление системной настройки"""
        sql = '''
            UPDATE system_settings 
            SET setting_value = %s, updated_at = NOW()
            WHERE setting_key = %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (setting_value, setting_key))
    
    async def get_energy_statistics(self, equipment_id: int = None, area_id: int = None, 
                                  start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Получение статистики энергопотребления через хранимую процедуру"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.callproc('GetEnergyStatistics', (equipment_id, area_id, start_date, end_date))
                return await cursor.fetchall()
