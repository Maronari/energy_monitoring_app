"""
Конфигурация для Docker окружения
"""
import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ModbusDevice:
    name: str
    ip_address: str
    port: int
    unit_id: int
    device_type: str

@dataclass
class DatabaseConfig:
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '3306'))
    database: str = os.getenv('DB_NAME', 'energy_monitoring')
    username: str = os.getenv('DB_USER', 'energy_user')
    password: str = os.getenv('DB_PASSWORD', 'energy_password_123')

class DockerSettings:
    def __init__(self):
        # Интервал сбора данных (секунды)
        self.COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', '5'))
        
        # Конфигурация базы данных
        self.DATABASE = DatabaseConfig()
        
        # Устройства Modbus (можно настроить через переменные окружения)
        self.MODBUS_DEVICES = self._load_devices_from_env()
        
        # Пороговые значения
        self.THRESHOLDS = {
            'max_power': float(os.getenv('THRESHOLD_MAX_POWER', '1000.0')),
            'max_current': float(os.getenv('THRESHOLD_MAX_CURRENT', '100.0')),
            'min_voltage': float(os.getenv('THRESHOLD_MIN_VOLTAGE', '200.0')),
            'max_voltage': float(os.getenv('THRESHOLD_MAX_VOLTAGE', '250.0'))
        }
        
        # Регистры Modbus для счетчика Меркурий
        self.MERCURY_REGISTERS = {
            'active_power': 0x0000,
            'reactive_power': 0x0002,
            'voltage_l1': 0x0004,
            'voltage_l2': 0x0006,
            'voltage_l3': 0x0008,
            'current_l1': 0x000A,
            'current_l2': 0x000C,
            'current_l3': 0x000E
        }
        
        # Регистры для ПЛК ОВЕН
        self.OVEN_REGISTERS = {
            'equipment_status': 0x0100,
            'discrete_inputs': 0x0200
        }
        
        # Настройки логирования
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', '/app/logs/energy_monitoring.log')
        
        # Настройки веб-сервера
        self.WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
        self.WEB_PORT = int(os.getenv('WEB_PORT', '8080'))
        
        # Настройки безопасности
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 час
    
    def _load_devices_from_env(self):
        """Загрузка устройств из переменных окружения"""
        devices = []
        
        # Устройства по умолчанию
        default_devices = [
            ModbusDevice(
                name="Счетчик Меркурий 1",
                ip_address=os.getenv('DEVICE1_IP', '192.168.1.100'),
                port=int(os.getenv('DEVICE1_PORT', '502')),
                unit_id=int(os.getenv('DEVICE1_UNIT', '1')),
                device_type="meter"
            ),
            ModbusDevice(
                name="ПЛК ОВЕН 1",
                ip_address=os.getenv('DEVICE2_IP', '192.168.1.101'),
                port=int(os.getenv('DEVICE2_PORT', '502')),
                unit_id=int(os.getenv('DEVICE2_UNIT', '2')),
                device_type="plc"
            )
        ]
        
        devices.extend(default_devices)
        
        # Дополнительные устройства из переменных окружения
        device_count = int(os.getenv('ADDITIONAL_DEVICES_COUNT', '0'))
        for i in range(3, 3 + device_count):
            device = ModbusDevice(
                name=os.getenv(f'DEVICE{i}_NAME', f'Устройство {i}'),
                ip_address=os.getenv(f'DEVICE{i}_IP', f'192.168.1.{100+i}'),
                port=int(os.getenv(f'DEVICE{i}_PORT', '502')),
                unit_id=int(os.getenv(f'DEVICE{i}_UNIT', str(i))),
                device_type=os.getenv(f'DEVICE{i}_TYPE', 'meter')
            )
            devices.append(device)
        
        return devices
