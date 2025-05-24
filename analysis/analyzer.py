"""
Обновленный модуль анализа данных для новой схемы БД
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class EnergyAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def calculate_equipment_efficiency(self, equipment_id: int = None, 
                                           hours_back: int = 24) -> List[Dict[str, Any]]:
        """Расчет показателей эффективности оборудования"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Получение статистики через хранимую процедуру
            statistics = await self.db_manager.get_energy_statistics(
                equipment_id=equipment_id,
                start_date=start_time,
                end_date=end_time
            )
            
            efficiency_results = []
            
            for stat in statistics:
                if not stat['total_measurements']:
                    continue
                
                efficiency_data = {
                    'equipment_id': stat['equipment_id'],
                    'equipment_name': stat['equipment_name'],
                    'area_name': stat['area_name'],
                    'equipment_type': stat['equipment_type'],
                    'analysis_period_hours': hours_back,
                    'total_measurements': stat['total_measurements'],
                    'avg_active_power_kw': stat['avg_active_power'],
                    'max_active_power_kw': stat['max_active_power'],
                    'min_active_power_kw': stat['min_active_power'],
                    'total_energy_kwh': stat['total_energy_kwh'] or 0,
                    'avg_power_factor': stat['avg_power_factor'],
                    'min_power_factor': stat['min_power_factor'],
                    'load_factor_percent': stat['avg_load_factor_percent'],
                    'data_quality_score': self._calculate_data_quality_score(stat),
                    'efficiency_rating': 'unknown'
                }
                
                # Оценка эффективности
                efficiency_data['efficiency_rating'] = self._rate_equipment_efficiency(efficiency_data)
                
                # Расчет стоимости энергопотребления
                energy_cost_per_kwh = await self._get_energy_cost_per_kwh()
                efficiency_data['energy_cost'] = efficiency_data['total_energy_kwh'] * energy_cost_per_kwh
                
                # Расчет удельного потребления (кВт·ч на час работы)
                if hours_back > 0:
                    efficiency_data['specific_consumption_kwh_per_hour'] = efficiency_data['total_energy_kwh'] / hours_back
                
                efficiency_results.append(efficiency_data)
            
            return efficiency_results
            
        except Exception as e:
            logger.error(f"Ошибка расчета эффективности оборудования: {e}")
            return []
    
    def _calculate_data_quality_score(self, stat: Dict[str, Any]) -> float:
        """Расчет оценки качества данных"""
        total_measurements = stat['total_measurements']
        poor_quality = stat.get('poor_quality_count', 0)
        bad_quality = stat.get('bad_quality_count', 0)
        
        if total_measurements == 0:
            return 0.0
        
        good_quality = total_measurements - poor_quality - bad_quality
        quality_score = (good_quality + poor_quality * 0.5) / total_measurements * 100
        
        return round(quality_score, 2)
    
    def _rate_equipment_efficiency(self, efficiency_data: Dict[str, Any]) -> str:
        """Оценка эффективности оборудования"""
        load_factor = efficiency_data.get('load_factor_percent', 0)
        power_factor = efficiency_data.get('avg_power_factor', 0)
        data_quality = efficiency_data.get('data_quality_score', 0)
        
        # Критерии оценки
        if data_quality < 80:
            return 'insufficient_data'
        
        if load_factor >= 70 and power_factor >= 0.9:
            return 'excellent'
        elif load_factor >= 50 and power_factor >= 0.85:
            return 'good'
        elif load_factor >= 30 and power_factor >= 0.8:
            return 'satisfactory'
        else:
            return 'poor'
    
    async def _get_energy_cost_per_kwh(self) -> float:
        """Получение стоимости электроэнергии из настроек"""
        try:
            settings = await self.db_manager.get_system_settings('economics')
            cost_setting = next((s for s in settings if s['setting_key'] == 'energy_cost_per_kwh'), None)
            return float(cost_setting['setting_value']) if cost_setting else 4.5
        except:
            return 4.5  # Значение по умолчанию
    
    async def analyze_area_consumption(self, area_id: int = None, 
                                     hours_back: int = 24) -> List[Dict[str, Any]]:
        """Анализ энергопотребления по участкам"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            if area_id:
                # Анализ конкретного участка
                area_stats = await self.db_manager.get_area_statistics(start_time, end_time)
                area_stats = [stat for stat in area_stats if stat['area_id'] == area_id]
            else:
                # Анализ всех участков
                area_stats = await self.db_manager.get_area_statistics(start_time, end_time)
            
            analysis_results = []
            
            for stat in area_stats:
                if not stat['total_readings']:
                    continue
                
                area_analysis = {
                    'area_id': stat['area_id'],
                    'area_name': stat['area_name'],
                    'analysis_period_hours': hours_back,
                    'equipment_count': stat['equipment_count'],
                    'total_readings': stat['total_readings'],
                    'avg_power_kw': stat['avg_power_kw'],
                    'max_power_kw': stat['max_power_kw'],
                    'min_power_kw': stat['min_power_kw'],
                    'total_energy_kwh': stat['total_energy_kwh'] or 0,
                    'avg_power_factor': stat['avg_power_factor'],
                    'power_density_kw_per_equipment': 0,
                    'energy_efficiency_rating': 'unknown'
                }
                
                # Расчет плотности мощности
                if stat['equipment_count'] > 0:
                    area_analysis['power_density_kw_per_equipment'] = stat['avg_power_kw'] / stat['equipment_count']
                
                # Оценка энергоэффективности участка
                area_analysis['energy_efficiency_rating'] = self._rate_area_efficiency(area_analysis)
                
                # Расчет стоимости
                energy_cost_per_kwh = await self._get_energy_cost_per_kwh()
                area_analysis['energy_cost'] = area_analysis['total_energy_kwh'] * energy_cost_per_kwh
                
                analysis_results.append(area_analysis)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Ошибка анализа потребления по участкам: {e}")
            return []
    
    def _rate_area_efficiency(self, area_analysis: Dict[str, Any]) -> str:
        """Оценка энергоэффективности участка"""
        power_factor = area_analysis.get('avg_power_factor', 0)
        power_density = area_analysis.get('power_density_kw_per_equipment', 0)
        
        if power_factor >= 0.9 and power_density <= 50:
            return 'excellent'
        elif power_factor >= 0.85 and power_density <= 70:
            return 'good'
        elif power_factor >= 0.8 and power_density <= 100:
            return 'satisfactory'
        else:
            return 'needs_improvement'
    
    async def identify_inefficient_operations(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Выявление неэффективных режимов работы"""
        try:
            inefficiencies = []
            
            # Получение данных по эффективности оборудования
            equipment_efficiency = await self.calculate_equipment_efficiency(hours_back=hours_back)
            
            for equipment in equipment_efficiency:
                equipment_issues = []
                
                # Низкий коэффициент загрузки
                if equipment['load_factor_percent'] < 30:
                    equipment_issues.append({
                        'issue_type': 'low_load_factor',
                        'description': f'Низкий коэффициент загрузки: {equipment["load_factor_percent"]:.1f}%',
                        'severity': 'medium',
                        'recommendation': 'Рассмотреть возможность оптимизации режима работы или перераспределения нагрузки'
                    })
                
                # Низкий коэффициент мощности
                if equipment['avg_power_factor'] < 0.85:
                    severity = 'high' if equipment['avg_power_factor'] < 0.8 else 'medium'
                    equipment_issues.append({
                        'issue_type': 'low_power_factor',
                        'description': f'Низкий коэффициент мощности: {equipment["avg_power_factor"]:.3f}',
                        'severity': severity,
                        'recommendation': 'Установить компенсирующие устройства (конденсаторы)'
                    })
                
                # Высокая вариативность потребления
                if equipment['max_active_power_kw'] > 0:
                    power_variation = (equipment['max_active_power_kw'] - equipment['min_active_power_kw']) / equipment['avg_active_power_kw']
                    if power_variation > 1.0:  # Вариация более 100%
                        equipment_issues.append({
                            'issue_type': 'high_power_variation',
                            'description': f'Высокая вариативность потребления: {power_variation:.1%}',
                            'severity': 'medium',
                            'recommendation': 'Проверить стабильность нагрузки и режимов работы'
                        })
                
                # Низкое качество данных
                if equipment['data_quality_score'] < 90:
                    severity = 'high' if equipment['data_quality_score'] < 80 else 'medium'
                    equipment_issues.append({
                        'issue_type': 'poor_data_quality',
                        'description': f'Низкое качество данных: {equipment["data_quality_score"]:.1f}%',
                        'severity': severity,
                        'recommendation': 'Проверить состояние счетчиков и каналов связи'
                    })
                
                # Высокое энергопотребление относительно номинала
                if equipment['avg_active_power_kw'] > equipment.get('nominal_power_kw', float('inf')) * 1.1:
                    equipment_issues.append({
                        'issue_type': 'overconsumption',
                        'description': f'Потребление превышает номинал на {((equipment["avg_active_power_kw"] / equipment.get("nominal_power_kw", 1)) - 1) * 100:.1f}%',
                        'severity': 'high',
                        'recommendation': 'Проверить техническое состояние оборудования'
                    })
                
                if equipment_issues:
                    inefficiencies.append({
                        'equipment_id': equipment['equipment_id'],
                        'equipment_name': equipment['equipment_name'],
                        'area_name': equipment['area_name'],
                        'equipment_type': equipment['equipment_type'],
                        'issues': equipment_issues,
                        'overall_efficiency_rating': equipment['efficiency_rating']
                    })
            
            return inefficiencies
            
        except Exception as e:
            logger.error(f"Ошибка выявления неэффективных операций: {e}")
            return []
    
    async def generate_energy_forecast(self, equipment_id: int = None, 
                                     forecast_hours: int = 24) -> Dict[str, Any]:
        """Генерация прогноза энергопотребления"""
        try:
            # Получение исторических данных за последние 7 дней
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            historical_data = await self.db_manager.get_energy_readings_by_period(
                start_time, end_time, equipment_id=equipment_id
            )
            
            if not historical_data:
                return {'error': 'Недостаточно исторических данных для прогноза'}
            
            # Простой прогноз на основе средних значений по часам
            hourly_averages = {}
            for reading in historical_data:
                hour = reading['energy_readings_timestamp'].hour
                if hour not in hourly_averages:
                    hourly_averages[hour] = []
                hourly_averages[hour].append(reading['energy_readings_active_power_kw'])
            
            # Расчет средних значений по часам
            hourly_forecast = {}
            for hour, values in hourly_averages.items():
                hourly_forecast[hour] = {
                    'avg_power_kw': np.mean(values),
                    'min_power_kw': np.min(values),
                    'max_power_kw': np.max(values),
                    'std_power_kw': np.std(values)
                }
            
            # Генерация прогноза
            forecast_data = []
            current_time = datetime.now()
            
            for i in range(forecast_hours):
                forecast_time = current_time + timedelta(hours=i)
                hour = forecast_time.hour
                
                if hour in hourly_forecast:
                    forecast_point = {
                        'timestamp': forecast_time,
                        'predicted_power_kw': hourly_forecast[hour]['avg_power_kw'],
                        'confidence_interval_min': hourly_forecast[hour]['avg_power_kw'] - hourly_forecast[hour]['std_power_kw'],
                        'confidence_interval_max': hourly_forecast[hour]['avg_power_kw'] + hourly_forecast[hour]['std_power_kw']
                    }
                else:
                    # Если нет данных для этого часа, используем общее среднее
                    all_values = [v for values in hourly_averages.values() for v in values]
                    avg_power = np.mean(all_values) if all_values else 0
                    
                    forecast_point = {
                        'timestamp': forecast_time,
                        'predicted_power_kw': avg_power,
                        'confidence_interval_min': avg_power * 0.8,
                        'confidence_interval_max': avg_power * 1.2
                    }
                
                forecast_data.append(forecast_point)
            
            # Расчет общих показателей прогноза
            total_predicted_energy = sum(point['predicted_power_kw'] for point in forecast_data)
            energy_cost_per_kwh = await self._get_energy_cost_per_kwh()
            predicted_cost = total_predicted_energy * energy_cost_per_kwh
            
            return {
                'equipment_id': equipment_id,
                'forecast_period_hours': forecast_hours,
                'forecast_data': forecast_data,
                'total_predicted_energy_kwh': total_predicted_energy,
                'predicted_cost': predicted_cost,
                'forecast_accuracy': 'medium',  # В реальной системе можно рассчитать на основе исторической точности
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации прогноза энергопотребления: {e}")
            return {'error': str(e)}
    
    async def analyze_energy_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """Анализ трендов энергопотребления"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            # Получение данных по дням
            daily_stats = []
            current_date = start_time.date()
            
            while current_date <= end_time.date():
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                day_data = await self.db_manager.get_energy_readings_by_period(day_start, day_end)
                
                if day_data:
                    daily_power = [reading['energy_readings_active_power_kw'] for reading in day_data 
                                 if reading['energy_readings_active_power_kw'] is not None]
                    
                    if daily_power:
                        daily_stats.append({
                            'date': current_date,
                            'avg_power_kw': np.mean(daily_power),
                            'max_power_kw': np.max(daily_power),
                            'total_energy_kwh': sum(daily_power) / len(daily_power) * 24,  # Упрощенный расчет
                            'readings_count': len(daily_power)
                        })
                
                current_date += timedelta(days=1)
            
            if not daily_stats:
                return {'error': 'Недостаточно данных для анализа трендов'}
            
            # Анализ трендов
            avg_powers = [stat['avg_power_kw'] for stat in daily_stats]
            total_energies = [stat['total_energy_kwh'] for stat in daily_stats]
            
            # Расчет трендов (простая линейная регрессия)
            days = list(range(len(avg_powers)))
            power_trend = np.polyfit(days, avg_powers, 1)[0] if len(avg_powers) > 1 else 0
            energy_trend = np.polyfit(days, total_energies, 1)[0] if len(total_energies) > 1 else 0
            
            return {
                'analysis_period_days': days_back,
                'daily_statistics': daily_stats,
                'trends': {
                    'power_trend_kw_per_day': power_trend,
                    'energy_trend_kwh_per_day': energy_trend,
                    'power_trend_direction': 'increasing' if power_trend > 0.1 else 'decreasing' if power_trend < -0.1 else 'stable',
                    'energy_trend_direction': 'increasing' if energy_trend > 1 else 'decreasing' if energy_trend < -1 else 'stable'
                },
                'summary': {
                    'avg_daily_power_kw': np.mean(avg_powers),
                    'avg_daily_energy_kwh': np.mean(total_energies),
                    'max_daily_power_kw': np.max([stat['max_power_kw'] for stat in daily_stats]),
                    'total_period_energy_kwh': sum(total_energies),
                    'data_coverage_percent': len(daily_stats) / days_back * 100
                },
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов энергопотребления: {e}")
            return {'error': str(e)}
