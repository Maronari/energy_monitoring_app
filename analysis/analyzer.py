"""
Модуль анализа данных энергопотребления
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from config.settings import Settings

logger = logging.getLogger(__name__)

class EnergyAnalyzer:
    def __init__(self):
        self.settings = Settings()
    
    def calculate_efficiency_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Расчет показателей энергоэффективности"""
        if not data:
            return {}
        
        indicators = {}
        
        # Извлечение значений мощности
        power_values = [d.get('active_power', 0) for d in data if d.get('active_power')]
        
        if power_values:
            indicators['average_power'] = np.mean(power_values)
            indicators['max_power'] = np.max(power_values)
            indicators['min_power'] = np.min(power_values)
            indicators['power_std'] = np.std(power_values)
            
            # Коэффициент загрузки (отношение средней к максимальной мощности)
            if indicators['max_power'] > 0:
                indicators['load_factor'] = indicators['average_power'] / indicators['max_power']
        
        # Анализ коэффициента мощности
        pf_values = [d.get('power_factor', 0) for d in data if d.get('power_factor')]
        if pf_values:
            indicators['average_power_factor'] = np.mean(pf_values)
            indicators['min_power_factor'] = np.min(pf_values)
        
        # Анализ напряжения
        voltage_values = []
        for phase in ['voltage_l1', 'voltage_l2', 'voltage_l3']:
            phase_values = [d.get(phase, 0) for d in data if d.get(phase)]
            voltage_values.extend(phase_values)
        
        if voltage_values:
            indicators['average_voltage'] = np.mean(voltage_values)
            indicators['voltage_deviation'] = np.std(voltage_values)
        
        return indicators
    
    def detect_threshold_violations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обнаружение превышений пороговых значений"""
        violations = []
        thresholds = self.settings.THRESHOLDS
        
        # Проверка мощности
        if data.get('active_power') and data['active_power'] > thresholds['max_power']:
            violations.append({
                'type': 'power_exceeded',
                'parameter': 'active_power',
                'value': data['active_power'],
                'threshold': thresholds['max_power'],
                'severity': 'high',
                'message': f"Превышение максимальной мощности: {data['active_power']:.2f} кВт"
            })
        
        # Проверка тока
        for phase in ['current_l1', 'current_l2', 'current_l3']:
            if data.get(phase) and data[phase] > thresholds['max_current']:
                violations.append({
                    'type': 'current_exceeded',
                    'parameter': phase,
                    'value': data[phase],
                    'threshold': thresholds['max_current'],
                    'severity': 'medium',
                    'message': f"Превышение тока {phase}: {data[phase]:.2f} А"
                })
        
        # Проверка напряжения
        for phase in ['voltage_l1', 'voltage_l2', 'voltage_l3']:
            if data.get(phase):
                voltage = data[phase]
                if voltage < thresholds['min_voltage']:
                    violations.append({
                        'type': 'voltage_low',
                        'parameter': phase,
                        'value': voltage,
                        'threshold': thresholds['min_voltage'],
                        'severity': 'medium',
                        'message': f"Низкое напряжение {phase}: {voltage:.2f} В"
                    })
                elif voltage > thresholds['max_voltage']:
                    violations.append({
                        'type': 'voltage_high',
                        'parameter': phase,
                        'value': voltage,
                        'threshold': thresholds['max_voltage'],
                        'severity': 'medium',
                        'message': f"Высокое напряжение {phase}: {voltage:.2f} В"
                    })
        
        return violations
    
    def analyze_equipment_efficiency(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ эффективности работы оборудования"""
        analysis = {
            'total_devices': len(set(d['device_name'] for d in data)),
            'analysis_period': {
                'start': min(d['timestamp'] for d in data) if data else None,
                'end': max(d['timestamp'] for d in data) if data else None
            },
            'device_analysis': {}
        }
        
        # Группировка данных по устройствам
        devices_data = {}
        for record in data:
            device_name = record['device_name']
            if device_name not in devices_data:
                devices_data[device_name] = []
            devices_data[device_name].append(record)
        
        # Анализ каждого устройства
        for device_name, device_data in devices_data.items():
            device_analysis = {
                'data_points': len(device_data),
                'efficiency_indicators': self.calculate_efficiency_indicators(device_data),
                'violations': []
            }
            
            # Поиск нарушений для каждой записи
            for record in device_data:
                violations = self.detect_threshold_violations(record)
                device_analysis['violations'].extend(violations)
            
            # Статистика нарушений
            device_analysis['violation_count'] = len(device_analysis['violations'])
            device_analysis['violation_types'] = list(set(v['type'] for v in device_analysis['violations']))
            
            analysis['device_analysis'][device_name] = device_analysis
        
        return analysis
    
    def identify_inefficient_modes(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Выявление неэффективных режимов работы"""
        inefficient_modes = []
        
        # Группировка данных по устройствам
        devices_data = {}
        for record in data:
            device_name = record['device_name']
            if device_name not in devices_data:
                devices_data[device_name] = []
            devices_data[device_name].append(record)
        
        for device_name, device_data in devices_data.items():
            power_values = [d.get('active_power', 0) for d in device_data if d.get('active_power')]
            pf_values = [d.get('power_factor', 0) for d in device_data if d.get('power_factor')]
            
            if not power_values:
                continue
            
            avg_power = np.mean(power_values)
            max_power = np.max(power_values)
            
            # Низкий коэффициент загрузки
            if max_power > 0:
                load_factor = avg_power / max_power
                if load_factor < 0.3:  # Менее 30% загрузки
                    inefficient_modes.append({
                        'device_name': device_name,
                        'issue_type': 'low_load_factor',
                        'description': f'Низкий коэффициент загрузки: {load_factor:.2%}',
                        'recommendation': 'Рассмотреть возможность оптимизации режима работы'
                    })
            
            # Низкий коэффициент мощности
            if pf_values:
                avg_pf = np.mean(pf_values)
                if avg_pf < 0.85:  # Менее 0.85
                    inefficient_modes.append({
                        'device_name': device_name,
                        'issue_type': 'low_power_factor',
                        'description': f'Низкий коэффициент мощности: {avg_pf:.3f}',
                        'recommendation': 'Установить компенсирующие устройства'
                    })
            
            # Высокая вариативность потребления
            if len(power_values) > 1:
                power_cv = np.std(power_values) / avg_power if avg_power > 0 else 0
                if power_cv > 0.5:  # Коэффициент вариации более 50%
                    inefficient_modes.append({
                        'device_name': device_name,
                        'issue_type': 'high_power_variability',
                        'description': f'Высокая вариативность потребления: {power_cv:.2%}',
                        'recommendation': 'Проверить стабильность нагрузки'
                    })
        
        return inefficient_modes
    
    def analyze_data(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Основной метод анализа данных"""
        if not processed_data:
            return {'status': 'no_data'}
        
        analysis_results = {
            'timestamp': datetime.now(),
            'data_count': len(processed_data),
            'equipment_analysis': self.analyze_equipment_efficiency(processed_data),
            'inefficient_modes': self.identify_inefficient_modes(processed_data),
            'overall_indicators': self.calculate_efficiency_indicators(processed_data)
        }
        
        # Подсчет общего количества нарушений
        total_violations = 0
        for device_analysis in analysis_results['equipment_analysis']['device_analysis'].values():
            total_violations += device_analysis['violation_count']
        
        analysis_results['total_violations'] = total_violations
        
        return analysis_results
