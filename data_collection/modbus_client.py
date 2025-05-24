"""
Обновленный клиент Modbus для новой схемы БД
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ModbusDataCollector:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.clients = {}
        self.equipment_list = []
        self.meters_cache = {}
    
    async def initialize(self):
        """Инициализация коллектора"""
        await self.load_equipment_configuration()
    
    async def load_equipment_configuration(self):
        """Загрузка конфигурации оборудования из БД"""
        try:
            self.equipment_list = await self.db_manager.get_equipment_list()
            
            # Загрузка счетчиков для каждого оборудования
            for equipment in self.equipment_list:
                equipment_id = equipment['equipment_id']
                meters = await self.db_manager.get_meters_by_equipment(equipment_id)
                self.meters_cache[equipment_id] = meters
            
            logger.info(f"Загружено {len(self.equipment_list)} единиц оборудования")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации оборудования: {e}")
            raise
    
    async def connect_to_equipment(self, equipment: Dict[str, Any]) -> bool:
        """Подключение к оборудованию"""
        equipment_id = equipment['equipment_id']
        equipment_name = equipment['equipment_name']
        
        try:
            if not equipment['ip_address']:
                logger.warning(f"Не указан IP-адрес для {equipment_name}")
                return False
            
            client = ModbusTcpClient(equipment['ip_address'], port=equipment['port'])
            if client.connect():
                self.clients[equipment_id] = client
                logger.info(f"Подключение к {equipment_name} установлено")
                return True
            else:
                logger.error(f"Не удалось подключиться к {equipment_name}")
                return False
        except Exception as e:
            logger.error(f"Ошибка подключения к {equipment_name}: {e}")
            return False
    
    async def read_mercury_meter_data(self, equipment: Dict[str, Any], client: ModbusTcpClient) -> List[Dict[str, Any]]:
        """Чтение данных со счетчика Меркурий"""
        equipment_id = equipment['equipment_id']
        equipment_name = equipment['equipment_name']
        readings = []
        
        try:
            meters = self.meters_cache.get(equipment_id, [])
            
            for meter in meters:
                meter_id = meter['meter_id']
                unit_id = equipment['unit_id']
                
                reading_data = {
                    'meter_id': meter_id,
                    'equipment_id': equipment_id,
                    'equipment_name': equipment_name,
                    'timestamp': datetime.now(),
                    'data_quality': 'good'
                }
                
                try:
                    # Чтение активной мощности (регистры 0x0000-0x0001)
                    result = client.read_holding_registers(0x0000, 2, unit_id)
                    if not result.isError():
                        # Преобразование 32-битного значения (IEEE 754)
                        raw_value = (result.registers[0] << 16) | result.registers[1]
                        reading_data['active_power'] = self._convert_ieee754(raw_value) / 1000.0  # кВт
                    
                    # Чтение реактивной мощности (регистры 0x0002-0x0003)
                    result = client.read_holding_registers(0x0002, 2, unit_id)
                    if not result.isError():
                        raw_value = (result.registers[0] << 16) | result.registers[1]
                        reading_data['reactive_power'] = self._convert_ieee754(raw_value) / 1000.0  # кВАр
                    
                    # Расчет полной мощности
                    if 'active_power' in reading_data and 'reactive_power' in reading_data:
                        active = reading_data['active_power']
                        reactive = reading_data['reactive_power']
                        reading_data['apparent_power'] = (active**2 + reactive**2)**0.5
                        
                        # Расчет коэффициента мощности
                        if reading_data['apparent_power'] > 0:
                            reading_data['power_factor'] = active / reading_data['apparent_power']
                    
                    # Чтение напряжений по фазам
                    for phase, reg_addr in [('l1', 0x0004), ('l2', 0x0006), ('l3', 0x0008)]:
                        result = client.read_holding_registers(reg_addr, 2, unit_id)
                        if not result.isError():
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                            reading_data[f'voltage_{phase}'] = self._convert_ieee754(raw_value) / 100.0  # В
                    
                    # Чтение токов по фазам
                    for phase, reg_addr in [('l1', 0x000A), ('l2', 0x000C), ('l3', 0x000E)]:
                        result = client.read_holding_registers(reg_addr, 2, unit_id)
                        if not result.isError():
                            raw_value = (result.registers[0] << 16) | result.registers[1]
                            reading_data[f'current_{phase}'] = self._convert_ieee754(raw_value) / 1000.0  # А
                    
                    # Чтение частоты (регистры 0x0010-0x0011)
                    result = client.read_holding_registers(0x0010, 2, unit_id)
                    if not result.isError():
                        raw_value = (result.registers[0] << 16) | result.registers[1]
                        reading_data['frequency'] = self._convert_ieee754(raw_value) / 100.0  # Гц
                    
                    # Применение коэффициентов трансформации
                    if meter['meter_transformation_ratio_current'] != 1.0:
                        for phase in ['l1', 'l2', 'l3']:
                            if f'current_{phase}' in reading_data:
                                reading_data[f'current_{phase}'] *= meter['meter_transformation_ratio_current']
                    
                    if meter['meter_transformation_ratio_voltage'] != 1.0:
                        for phase in ['l1', 'l2', 'l3']:
                            if f'voltage_{phase}' in reading_data:
                                reading_data[f'voltage_{phase}'] *= meter['meter_transformation_ratio_voltage']
                    
                    readings.append(reading_data)
                    
                except Exception as e:
                    logger.error(f"Ошибка чтения данных счетчика {meter_id} оборудования {equipment_name}: {e}")
                    reading_data['data_quality'] = 'bad'
                    readings.append(reading_data)
            
            return readings
            
        except Exception as e:
            logger.error(f"Ошибка чтения данных с оборудования {equipment_name}: {e}")
            return []
    
    async def read_plc_data(self, equipment: Dict[str, Any], client: ModbusTcpClient) -> Dict[str, Any]:
        """Чтение данных с ПЛК"""
        equipment_id = equipment['equipment_id']
        equipment_name = equipment['equipment_name']
        
        try:
            unit_id = equipment['unit_id']
            
            state_data = {
                'equipment_id': equipment_id,
                'timestamp': datetime.now(),
                'state_name': 'unknown',
                'additional_data': {}
            }
            
            # Чтение состояния оборудования (регистры 0x0100-0x0109)
            result = client.read_holding_registers(0x0100, 10, unit_id)
            if not result.isError():
                state_data['additional_data']['equipment_status'] = result.registers
                
                # Интерпретация состояния (зависит от конкретного ПЛК)
                status_word = result.registers[0]
                if status_word & 0x0001:  # Бит 0 - работа
                    state_data['state_name'] = 'running'
                elif status_word & 0x0002:  # Бит 1 - остановка
                    state_data['state_name'] = 'stopped'
                elif status_word & 0x0004:  # Бит 2 - ошибка
                    state_data['state_name'] = 'error'
                else:
                    state_data['state_name'] = 'idle'
                
                # Код операции (если доступен)
                if len(result.registers) > 1:
                    state_data['state_operation_code'] = str(result.registers[1])
            
            # Чтение дискретных входов (адреса 0x0200-0x020F)
            result = client.read_discrete_inputs(0x0200, 16, unit_id)
            if not result.isError():
                state_data['additional_data']['discrete_inputs'] = result.bits[:16]
            
            return state_data
            
        except Exception as e:
            logger.error(f"Ошибка чтения данных ПЛК {equipment_name}: {e}")
            return None
    
    def _convert_ieee754(self, raw_value: int) -> float:
        """Преобразование 32-битного значения в float IEEE 754"""
        import struct
        # Преобразование в байты и обратно в float
        bytes_value = struct.pack('>I', raw_value)
        return struct.unpack('>f', bytes_value)[0]
    
    async def collect_equipment_data(self, equipment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Сбор данных с одного оборудования"""
        equipment_id = equipment['equipment_id']
        equipment_name = equipment['equipment_name']
        
        # Проверка активности оборудования
        if equipment['equipment_status'] != 'active':
            return []
        
        # Подключение если не подключен
        if equipment_id not in self.clients:
            if not await self.connect_to_equipment(equipment):
                return []
        
        client = self.clients[equipment_id]
        
        # Проверка соединения
        if not client.is_socket_open():
            if not await self.connect_to_equipment(equipment):
                return []
            client = self.clients[equipment_id]
        
        all_data = []
        
        try:
            # Чтение данных энергопотребления (для всех типов оборудования со счетчиками)
            energy_readings = await self.read_mercury_meter_data(equipment, client)
            all_data.extend(energy_readings)
            
            # Чтение состояния оборудования (для ПЛК и управляемого оборудования)
            if equipment['equipment_type'] in ['ПЛК', 'Токарный станок', 'Фрезерный станок']:
                state_data = await self.read_plc_data(equipment, client)
                if state_data:
                    # Сохранение состояния оборудования
                    await self.db_manager.save_equipment_state(equipment_id, state_data)
            
            # Обновление статуса связи
            if all_data:
                # Обновление будет выполнено триггером в БД
                pass
            
        except Exception as e:
            logger.error(f"Ошибка сбора данных с {equipment_name}: {e}")
            
            # Создание лога об ошибке связи
            await self.db_manager.create_log({
                'equipment_id': equipment_id,
                'log_type': 'communication_error',
                'message': f'Ошибка связи с оборудованием: {str(e)}',
                'severity': 'high'
            })
        
        return all_data
    
    async def collect_all_data(self) -> List[Dict[str, Any]]:
        """Сбор данных со всего оборудования"""
        # Обновление конфигурации оборудования
        await self.load_equipment_configuration()
        
        all_readings = []
        
        # Создание задач для параллельного сбора данных
        tasks = []
        for equipment in self.equipment_list:
            if equipment['equipment_status'] == 'active':
                tasks.append(self.collect_equipment_data(equipment))
        
        # Выполнение задач
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                equipment_name = self.equipment_list[i]['equipment_name']
                logger.error(f"Ошибка сбора данных с {equipment_name}: {result}")
            elif result:
                all_readings.extend(result)
        
        return all_readings
    
    def disconnect_all(self):
        """Отключение от всего оборудования"""
        for equipment_id, client in self.clients.items():
            try:
                client.close()
                equipment_name = next(
                    (eq['equipment_name'] for eq in self.equipment_list if eq['equipment_id'] == equipment_id),
                    f"ID:{equipment_id}"
                )
                logger.info(f"Отключение от {equipment_name}")
            except Exception as e:
                logger.error(f"Ошибка отключения от оборудования ID:{equipment_id}: {e}")
        
        self.clients.clear()
