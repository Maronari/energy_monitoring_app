"""
Конфигурация системы
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
    device_type: str  # 'meter' или 'plc'

@dataclass
class DatabaseConfig:
    host: str = 'localhost'
    port: int = 3306
    database: str = 'energy_monitoring'
    username: str = 'root'
    password: str = 'root_password_123'

class Settings:
    def __init__(self):
        # Интервал сбора данных (секунды)
        self.COLLECTION_INTERVAL = 5
        
        # Конфигурация базы данных
        self.DATABASE = DatabaseConfig()
        
        # Устройства Modbus
        self.MODBUS_DEVICES = [
            ModbusDevice(
                name="Счетчик Меркурий 1",
                ip_address="192.168.1.100",
                port=502,
                unit_id=1,
                device_type="meter"
            ),
            ModbusDevice(
                name="ПЛК ОВЕН 1",
                ip_address="192.168.1.101",
                port=502,
                unit_id=2,
                device_type="plc"
            )
        ]
        
        # Пороговые значения
        self.THRESHOLDS = {
            'max_power': 1000.0,  # кВт
            'max_current': 100.0,  # А
            'min_voltage': 200.0,  # В
            'max_voltage': 250.0   # В
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
