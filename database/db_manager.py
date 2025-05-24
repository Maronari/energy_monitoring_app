"""
Менеджер базы данных
"""
import asyncio
import aiomysql
import logging
from datetime import datetime
from typing import List, Dict, Any
from config.settings import Settings
from config.docker_settings import DockerSettings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.settings = DockerSettings()
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
                maxsize=10
            )
            
            await self.create_tables()
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    async def create_tables(self):
        """Создание таблиц"""
        tables = {
            'energy_data': '''
                CREATE TABLE IF NOT EXISTS energy_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    active_power FLOAT,
                    reactive_power FLOAT,
                    voltage_l1 FLOAT,
                    voltage_l2 FLOAT,
                    voltage_l3 FLOAT,
                    current_l1 FLOAT,
                    current_l2 FLOAT,
                    current_l3 FLOAT,
                    INDEX idx_device_time (device_name, timestamp)
                )
            ''',
            'equipment_status': '''
                CREATE TABLE IF NOT EXISTS equipment_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status JSON,
                    INDEX idx_device_time (device_name, timestamp)
                )
            ''',
            'alerts': '''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(100) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    message TEXT,
                    value FLOAT,
                    threshold_value FLOAT,
                    timestamp DATETIME NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''',
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for table_name, sql in tables.items():
                    await cursor.execute(sql)
                    logger.info(f"Таблица {table_name} создана/проверена")
    
    async def save_energy_data(self, data: List[Dict[str, Any]]):
        """Сохранение данных энергопотребления"""
        if not data:
            return
        
        sql = '''
            INSERT INTO energy_data 
            (device_name, timestamp, active_power, reactive_power, 
             voltage_l1, voltage_l2, voltage_l3, current_l1, current_l2, current_l3)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for record in data:
                    await cursor.execute(sql, (
                        record['device_name'],
                        record['timestamp'],
                        record.get('active_power'),
                        record.get('reactive_power'),
                        record.get('voltage_l1'),
                        record.get('voltage_l2'),
                        record.get('voltage_l3'),
                        record.get('current_l1'),
                        record.get('current_l2'),
                        record.get('current_l3')
                    ))
    
    async def save_alert(self, device_name: str, alert_type: str, message: str, 
                        value: float, threshold: float):
        """Сохранение уведомления"""
        sql = '''
            INSERT INTO alerts (device_name, alert_type, message, value, threshold_value, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, (
                    device_name, alert_type, message, value, threshold, datetime.now()
                ))
    
    async def get_latest_data(self, device_name: str = None, limit: int = 100):
        """Получение последних данных"""
        sql = '''
            SELECT * FROM energy_data 
            WHERE (%s IS NULL OR device_name = %s)
            ORDER BY timestamp DESC 
            LIMIT %s
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (device_name, device_name, limit))
                return await cursor.fetchall()
    
    async def get_data_by_period(self, start_time: datetime, end_time: datetime, 
                                device_name: str = None):
        """Получение данных за период"""
        sql = '''
            SELECT * FROM energy_data 
            WHERE timestamp BETWEEN %s AND %s
            AND (%s IS NULL OR device_name = %s)
            ORDER BY timestamp
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql, (start_time, end_time, device_name, device_name))
                return await cursor.fetchall()
    
    async def get_active_alerts(self):
        """Получение активных уведомлений"""
        sql = '''
            SELECT * FROM alerts 
            WHERE acknowledged = FALSE 
            ORDER BY timestamp DESC
        '''
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()
