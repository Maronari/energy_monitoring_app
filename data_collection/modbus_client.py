"""
Клиент для сбора данных по протоколу Modbus
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from config.settings import Settings

logger = logging.getLogger(__name__)

class ModbusDataCollector:
    def __init__(self):
        self.settings = Settings()
        self.clients = {}
    
    async def connect_to_device(self, device):
        """Подключение к устройству"""
        try:
            client = ModbusTcpClient(device.ip_address, port=device.port)
            if client.connect():
                self.clients[device.name] = client
                logger.info(f"Подключение к {device.name} установлено")
                return True
            else:
                logger.error(f"Не удалось подключиться к {device.name}")
                return False
        except Exception as e:
            logger.error(f"Ошибка подключения к {device.name}: {e}")
            return False
    
    async def read_mercury_data(self, device, client):
        """Чтение данных со счетчика Меркурий"""
        data = {
            'device_name': device.name,
            'timestamp': datetime.now(),
            'device_type': 'meter'
        }
        
        try:
            # Чтение активной мощности
            result = client.read_holding_registers(
                self.settings.MERCURY_REGISTERS['active_power'], 2, device.unit_id
            )
            if not result.isError():
                # Преобразование в float (зависит от формата данных счетчика)
                data['active_power'] = (result.registers[0] << 16 | result.registers[1]) / 1000.0
            
            # Чтение реактивной мощности
            result = client.read_holding_registers(
                self.settings.MERCURY_REGISTERS['reactive_power'], 2, device.unit_id
            )
            if not result.isError():
                data['reactive_power'] = (result.registers[0] << 16 | result.registers[1]) / 1000.0
            
            # Чтение напряжений
            for phase, reg in [('l1', 'voltage_l1'), ('l2', 'voltage_l2'), ('l3', 'voltage_l3')]:
                result = client.read_holding_registers(
                    self.settings.MERCURY_REGISTERS[reg], 2, device.unit_id
                )
                if not result.isError():
                    data[reg] = (result.registers[0] << 16 | result.registers[1]) / 100.0
            
            # Чтение токов
            for phase, reg in [('l1', 'current_l1'), ('l2', 'current_l2'), ('l3', 'current_l3')]:
                result = client.read_holding_registers(
                    self.settings.MERCURY_REGISTERS[reg], 2, device.unit_id
                )
                if not result.isError():
                    data[reg] = (result.registers[0] << 16 | result.registers[1]) / 1000.0
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка чтения данных с {device.name}: {e}")
            return None
    
    async def read_plc_data(self, device, client):
        """Чтение данных с ПЛК ОВЕН"""
        data = {
            'device_name': device.name,
            'timestamp': datetime.now(),
            'device_type': 'plc'
        }
        
        try:
            # Чтение состояния оборудования
            result = client.read_holding_registers(
                self.settings.OVEN_REGISTERS['equipment_status'], 10, device.unit_id
            )
            if not result.isError():
                data['equipment_status'] = result.registers
            
            # Чтение дискретных входов
            result = client.read_discrete_inputs(
                self.settings.OVEN_REGISTERS['discrete_inputs'], 16, device.unit_id
            )
            if not result.isError():
                data['discrete_inputs'] = result.bits
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка чтения данных с ПЛК {device.name}: {e}")
            return None
    
    async def collect_device_data(self, device):
        """Сбор данных с одного устройства"""
        # Подключение если не подключен
        if device.name not in self.clients:
            if not await self.connect_to_device(device):
                return None
        
        client = self.clients[device.name]
        
        # Проверка соединения
        if not client.is_socket_open():
            if not await self.connect_to_device(device):
                return None
            client = self.clients[device.name]
        
        # Чтение данных в зависимости от типа устройства
        if device.device_type == 'meter':
            return await self.read_mercury_data(device, client)
        elif device.device_type == 'plc':
            return await self.read_plc_data(device, client)
        
        return None
    
    async def collect_all_data(self):
        """Сбор данных со всех устройств"""
        all_data = []
        
        tasks = []
        for device in self.settings.MODBUS_DEVICES:
            tasks.append(self.collect_device_data(device))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка сбора данных: {result}")
            elif result is not None:
                all_data.append(result)
        
        return all_data
    
    def disconnect_all(self):
        """Отключение от всех устройств"""
        for name, client in self.clients.items():
            try:
                client.close()
                logger.info(f"Отключение от {name}")
            except Exception as e:
                logger.error(f"Ошибка отключения от {name}: {e}")
        
        self.clients.clear()
