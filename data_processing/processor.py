"""
Модуль обработки данных
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from scipy import signal
from config.settings import Settings

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.settings = Settings()
    
    def filter_noise(self, values: List[float], window_size: int = 5) -> List[float]:
        """Фильтрация шумов методом скользящего среднего"""
        if len(values) < window_size:
            return values
        
        # Применение медианного фильтра для удаления выбросов
        filtered = signal.medfilt(values, kernel_size=min(window_size, len(values)))
        
        # Применение фильтра скользящего среднего
        smoothed = np.convolve(filtered, np.ones(window_size)/window_size, mode='same')
        
        return smoothed.tolist()
    
    def detect_anomalies(self, value: float, parameter: str) -> bool:
        """Обнаружение аномалий в данных"""
        thresholds = self.settings.THRESHOLDS
        
        if parameter == 'active_power' and value > thresholds['max_power']:
            return True
        elif parameter in ['current_l1', 'current_l2', 'current_l3'] and value > thresholds['max_current']:
            return True
        elif parameter in ['voltage_l1', 'voltage_l2', 'voltage_l3']:
            if value < thresholds['min_voltage'] or value > thresholds['max_voltage']:
                return True
        
        return False
    
    def validate_data_range(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка данных на соответствие диапазонам"""
        validated_data = data.copy()
        anomalies = []
        
        # Проверка каждого параметра
        for param in ['active_power', 'reactive_power', 'voltage_l1', 'voltage_l2', 
                     'voltage_l3', 'current_l1', 'current_l2', 'current_l3']:
            if param in data and data[param] is not None:
                value = data[param]
                
                # Проверка на отрицательные значения (кроме реактивной мощности)
                if param != 'reactive_power' and value < 0:
                    validated_data[param] = 0
                    anomalies.append(f"{param}: отрицательное значение {value}")
                
                # Проверка на аномалии
                elif self.detect_anomalies(value, param):
                    anomalies.append(f"{param}: превышение порога {value}")
                
                # Проверка на экстремальные значения
                elif value > 10000:  # Общий порог для всех параметров
                    validated_data[param] = None
                    anomalies.append(f"{param}: экстремальное значение {value}")
        
        if anomalies:
            validated_data['anomalies'] = anomalies
            logger.warning(f"Обнаружены аномалии в данных {data['device_name']}: {anomalies}")
        
        return validated_data
    
    def convert_to_unified_format(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных в унифицированный формат"""
        unified_data = {
            'device_name': raw_data.get('device_name'),
            'timestamp': raw_data.get('timestamp', datetime.now()),
            'device_type': raw_data.get('device_type'),
            'data_quality': 'good'
        }
        
        # Преобразование энергетических параметров
        energy_params = ['active_power', 'reactive_power', 'voltage_l1', 'voltage_l2', 
                        'voltage_l3', 'current_l1', 'current_l2', 'current_l3']
        
        for param in energy_params:
            if param in raw_data:
                unified_data[param] = float(raw_data[param]) if raw_data[param] is not None else None
        
        # Обработка данных ПЛК
        if raw_data.get('device_type') == 'plc':
            unified_data['equipment_status'] = raw_data.get('equipment_status', [])
            unified_data['discrete_inputs'] = raw_data.get('discrete_inputs', [])
        
        # Добавление вычисляемых параметров
        if unified_data.get('active_power') and unified_data.get('reactive_power'):
            # Полная мощность
            unified_data['apparent_power'] = np.sqrt(
                unified_data['active_power']**2 + unified_data['reactive_power']**2
            )
            
            # Коэффициент мощности
            if unified_data['apparent_power'] > 0:
                unified_data['power_factor'] = unified_data['active_power'] / unified_data['apparent_power']
        
        return unified_data
    
    def process_data(self, raw_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Основной метод обработки данных"""
        processed_data = []
        
        for raw_data in raw_data_list:
            try:
                # Преобразование в унифицированный формат
                unified_data = self.convert_to_unified_format(raw_data)
                
                # Валидация данных
                validated_data = self.validate_data_range(unified_data)
                
                # Фильтрация (если есть исторические данные)
                # В реальной системе здесь бы использовались данные из БД
                
                processed_data.append(validated_data)
                
            except Exception as e:
                logger.error(f"Ошибка обработки данных {raw_data}: {e}")
                continue
        
        return processed_data
