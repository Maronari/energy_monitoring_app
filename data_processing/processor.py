"""
Обновленный модуль обработки данных для новой схемы БД
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from scipy import signal
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.thresholds_cache = {}
        self.last_threshold_update = None
    
    async def load_thresholds(self):
        """Загрузка пороговых значений из БД"""
        try:
            thresholds = await self.db_manager.get_thresholds()
            
            # Организация порогов по оборудованию и параметрам
            self.thresholds_cache = {}
            
            for threshold in thresholds:
                equipment_id = threshold['threshold_equipment_id']
                area_id = threshold['threshold_area_id']
                parameter = threshold['parameter_name']
                
                # Ключ для поиска порога (приоритет: оборудование > участок > общий)
                if equipment_id:
                    key = f"equipment_{equipment_id}_{parameter}"
                elif area_id:
                    key = f"area_{area_id}_{parameter}"
                else:
                    key = f"global_{parameter}"
                
                self.thresholds_cache[key] = threshold
            
            self.last_threshold_update = datetime.now()
            logger.info(f"Загружено {len(thresholds)} пороговых значений")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки пороговых значений: {e}")
    
    def get_threshold_for_parameter(self, equipment_id: int, area_id: int, parameter: str) -> Dict[str, Any]:
        """Получение порогового значения для параметра"""
        # Поиск в порядке приоритета
        keys_to_check = [
            f"equipment_{equipment_id}_{parameter}",
            f"area_{area_id}_{parameter}",
            f"global_{parameter}"
        ]
        
        for key in keys_to_check:
            if key in self.thresholds_cache:
                return self.thresholds_cache[key]
        
        return None
    
    def filter_noise(self, values: List[float], window_size: int = 5) -> List[float]:
        """Фильтрация шумов методом скользящего среднего"""
        if len(values) < window_size:
            return values
        
        try:
            # Применение медианного фильтра для удаления выбросов
            filtered = signal.medfilt(values, kernel_size=min(window_size, len(values)))
            
            # Применение фильтра скользящего среднего
            smoothed = np.convolve(filtered, np.ones(window_size)/window_size, mode='same')
            
            return smoothed.tolist()
        except Exception as e:
            logger.error(f"Ошибка фильтрации данных: {e}")
            return values
    
    async def detect_threshold_violations(self, reading_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обнаружение превышений пороговых значений"""
        violations = []
        equipment_id = reading_data.get('equipment_id')
        
        # Получение информации об участке (нужно для поиска порогов)
        # В реальной реализации это можно кэшировать
        equipment_list = await self.db_manager.get_equipment_list()
        equipment_info = next((eq for eq in equipment_list if eq['equipment_id'] == equipment_id), None)
        
        if not equipment_info:
            return violations
        
        area_id = equipment_info.get('equipment_area_id')
        
        # Параметры для проверки
        parameters_to_check = [
            ('active_power', 'energy_readings_active_power_kw', 'кВт'),
            ('reactive_power', 'energy_readings_reactive_power_kvar', 'кВАр'),
            ('voltage_l1', 'energy_readings_voltage_l1', 'В'),
            ('voltage_l2', 'energy_readings_voltage_l2', 'В'),
            ('voltage_l3', 'energy_readings_voltage_l3', 'В'),
            ('current_l1', 'energy_readings_current_l1', 'А'),
            ('current_l2', 'energy_readings_current_l2', 'А'),
            ('current_l3', 'energy_readings_current_l3', 'А'),
            ('power_factor', 'energy_readings_power_factor', '')
        ]
        
        for param_key, param_db_name, unit in parameters_to_check:
            if param_key not in reading_data or reading_data[param_key] is None:
                continue
            
            value = reading_data[param_key]
            threshold = self.get_threshold_for_parameter(equipment_id, area_id, param_db_name)
            
            if not threshold:
                continue
            
            violation_type = None
            threshold_value = None
            severity = 'medium'
            
            # Проверка максимальных порогов
            if threshold['critical_level'] and value > threshold['critical_level']:
                violation_type = 'critical_max_exceeded'
                threshold_value = threshold['critical_level']
                severity = 'critical'
            elif threshold['warning_level'] and value > threshold['warning_level']:
                violation_type = 'warning_max_exceeded'
                threshold_value = threshold['warning_level']
                severity = 'high'
            
            # Проверка минимальных порогов
            elif threshold['min_critical_level'] and value < threshold['min_critical_level']:
                violation_type = 'critical_min_exceeded'
                threshold_value = threshold['min_critical_level']
                severity = 'critical'
            elif threshold['min_warning_level'] and value < threshold['min_warning_level']:
                violation_type = 'warning_min_exceeded'
                threshold_value = threshold['min_warning_level']
                severity = 'high'
            
            if violation_type:
                violations.append({
                    'equipment_id': equipment_id,
                    'meter_id': reading_data.get('meter_id'),
                    'log_type': 'threshold_exceeded',
                    'parameter_name': param_db_name,
                    'value': value,
                    'threshold_value': threshold_value,
                    'severity': severity,
                    'message': f"Превышение порога {param_key}: {value:.3f} {unit} (порог: {threshold_value:.3f} {unit})",
                    'timestamp': reading_data.get('timestamp')
                })
        
        return violations
    
    def validate_data_range(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка данных на соответствие физическим диапазонам"""
        validated_data = reading_data.copy()
        anomalies = []
        
        # Диапазоны для проверки
        ranges = {
            'active_power': (0, 1000),  # 0-1000 кВт
            'reactive_power': (-500, 500),  # -500 до +500 кВАр
            'voltage_l1': (100, 400),  # 100-400 В
            'voltage_l2': (100, 400),
            'voltage_l3': (100, 400),
            'current_l1': (0, 200),  # 0-200 А
            'current_l2': (0, 200),
            'current_l3': (0, 200),
            'power_factor': (0, 1),  # 0-1
            'frequency': (45, 65)  # 45-65 Гц
        }
        
        for param, (min_val, max_val) in ranges.items():
            if param in validated_data and validated_data[param] is not None:
                value = validated_data[param]
                
                if value < min_val or value > max_val:
                    anomalies.append(f"{param}: значение {value} вне диапазона [{min_val}, {max_val}]")
                    validated_data[param] = None
                    validated_data['data_quality'] = 'bad'
                
                # Проверка на NaN и бесконечность
                if np.isnan(value) or np.isinf(value):
                    anomalies.append(f"{param}: некорректное значение {value}")
                    validated_data[param] = None
                    validated_data['data_quality'] = 'bad'
        
        # Проверка согласованности данных
        if all(k in validated_data and validated_data[k] is not None 
               for k in ['active_power', 'reactive_power', 'apparent_power']):
            
            calculated_apparent = np.sqrt(validated_data['active_power']**2 + 
                                        validated_data['reactive_power']**2)
            
            if abs(calculated_apparent - validated_data['apparent_power']) > 0.1:
                anomalies.append("Несогласованность активной, реактивной и полной мощности")
                validated_data['data_quality'] = 'poor'
        
        if anomalies:
            validated_data['anomalies'] = anomalies
            logger.warning(f"Обнаружены аномалии в данных оборудования {reading_data.get('equipment_name', 'Unknown')}: {anomalies}")
        
        return validated_data
    
    def convert_to_unified_format(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных в унифицированный формат для БД"""
        unified_data = {
            'meter_id': raw_data.get('meter_id'),
            'timestamp': raw_data.get('timestamp', datetime.now()),
            'data_quality': raw_data.get('data_quality', 'good')
        }
        
        # Маппинг параметров
        parameter_mapping = {
            'active_power': 'energy_readings_active_power_kw',
            'reactive_power': 'energy_readings_reactive_power_kvar',
            'apparent_power': 'energy_readings_apparent_power_kva',
            'power_factor': 'energy_readings_power_factor',
            'voltage_l1': 'energy_readings_voltage_l1',
            'voltage_l2': 'energy_readings_voltage_l2',
            'voltage_l3': 'energy_readings_voltage_l3',
            'current_l1': 'energy_readings_current_l1',
            'current_l2': 'energy_readings_current_l2',
            'current_l3': 'energy_readings_current_l3',
            'frequency': 'energy_readings_frequency'
        }
        
        for source_key, target_key in parameter_mapping.items():
            if source_key in raw_data and raw_data[source_key] is not None:
                unified_data[target_key] = float(raw_data[source_key])
        
        # Расчет дополнительных параметров если они отсутствуют
        if ('energy_readings_active_power_kw' in unified_data and 
            'energy_readings_reactive_power_kvar' in unified_data and
            'energy_readings_apparent_power_kva' not in unified_data):
            
            active = unified_data['energy_readings_active_power_kw']
            reactive = unified_data['energy_readings_reactive_power_kvar']
            unified_data['energy_readings_apparent_power_kva'] = np.sqrt(active**2 + reactive**2)
        
        if ('energy_readings_active_power_kw' in unified_data and 
            'energy_readings_apparent_power_kva' in unified_data and
            'energy_readings_power_factor' not in unified_data):
            
            active = unified_data['energy_readings_active_power_kw']
            apparent = unified_data['energy_readings_apparent_power_kva']
            if apparent > 0:
                unified_data['energy_readings_power_factor'] = active / apparent
        
        return unified_data
    
    async def process_readings(self, raw_readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Основной метод обработки показаний энергопотребления"""
        if not raw_readings:
            return []
        
        # Обновление кэша порогов если необходимо
        if (not self.last_threshold_update or 
            (datetime.now() - self.last_threshold_update).seconds > 300):  # 5 минут
            await self.load_thresholds()
        
        processed_readings = []
        violations = []
        
        for raw_reading in raw_readings:
            try:
                # Валидация данных
                validated_reading = self.validate_data_range(raw_reading)
                
                # Преобразование в унифицированный формат
                unified_reading = self.convert_to_unified_format(validated_reading)
                
                # Проверка пороговых значений
                reading_violations = await self.detect_threshold_violations(raw_reading)
                violations.extend(reading_violations)
                
                processed_readings.append(unified_reading)
                
            except Exception as e:
                logger.error(f"Ошибка обработки показания: {e}")
                continue
        
        # Сохранение показаний в БД
        if processed_readings:
            await self.db_manager.save_energy_readings(processed_readings)
        
        # Создание логов о нарушениях
        for violation in violations:
            await self.db_manager.create_log(violation)
        
        return processed_readings
