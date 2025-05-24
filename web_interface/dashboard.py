"""
Веб-интерфейс дашборда
"""
import asyncio
from datetime import datetime, timedelta
from nicegui import ui
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)

class Dashboard:
    def __init__(self):
        self.real_time_data = []
        self.analysis_results = {}
        self.charts = {}
    
    async def render(self):
        """Отрисовка дашборда"""
        with ui.row().classes('w-full gap-4'):
            # Левая колонка - основные показатели
            with ui.column().classes('w-2/3'):
                await self.render_main_charts()
            
            # Правая колонка - статистика и уведомления
            with ui.column().classes('w-1/3'):
                await self.render_statistics()
                await self.render_alerts()
    
    async def render_main_charts(self):
        """Отрисовка основных графиков"""
        # График мощности в реальном времени
        with ui.card().classes('w-full'):
            ui.label('Активная мощность в реальном времени').classes('text-lg font-bold')
            self.power_chart = ui.plotly({}).classes('w-full h-64')
        
        # Графики напряжения и тока
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('w-1/2'):
                ui.label('Напряжение по фазам').classes('text-lg font-bold')
                self.voltage_chart = ui.plotly({}).classes('w-full h-48')
            
            with ui.card().classes('w-1/2'):
                ui.label('Ток по фазам').classes('text-lg font-bold')
                self.current_chart = ui.plotly({}).classes('w-full h-48')
        
        # График коэффициента мощности
        with ui.card().classes('w-full'):
            ui.label('Коэффициент мощности').classes('text-lg font-bold')
            self.pf_chart = ui.plotly({}).classes('w-full h-48')
    
    async def render_statistics(self):
        """Отрисовка статистики"""
        with ui.card().classes('w-full'):
            ui.label('Текущие показатели').classes('text-lg font-bold')
            
            self.stats_container = ui.column().classes('w-full gap-2')
            
            # Инициализация пустой статистики
            with self.stats_container:
                ui.label('Ожидание данных...').classes('text-gray-500')
    
    async def render_alerts(self):
        """Отрисовка уведомлений"""
        with ui.card().classes('w-full'):
            ui.label('Уведомления').classes('text-lg font-bold')
            
            self.alerts_container = ui.column().classes('w-full gap-2 max-h-64 overflow-y-auto')
            
            # Инициализация пустых уведомлений
            with self.alerts_container:
                ui.label('Нет активных уведомлений').classes('text-green-600')
    
    def create_power_chart(self, data):
        """Создание графика мощности"""
        if not data:
            return {}
        
        # Группировка данных по устройствам
        devices = {}
        for record in data:
            device_name = record['device_name']
            if device_name not in devices:
                devices[device_name] = {'timestamps': [], 'power': []}
            
            devices[device_name]['timestamps'].append(record['timestamp'])
            devices[device_name]['power'].append(record.get('active_power', 0))
        
        fig = go.Figure()
        
        for device_name, device_data in devices.items():
            fig.add_trace(go.Scatter(
                x=device_data['timestamps'],
                y=device_data['power'],
                mode='lines+markers',
                name=device_name,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title='Активная мощность',
            xaxis_title='Время',
            yaxis_title='Мощность, кВт',
            height=250,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_voltage_chart(self, data):
        """Создание графика напряжения"""
        if not data:
            return {}
        
        # Берем последние данные
        latest_data = data[-10:] if len(data) > 10 else data
        
        timestamps = [record['timestamp'] for record in latest_data]
        voltage_l1 = [record.get('voltage_l1', 0) for record in latest_data]
        voltage_l2 = [record.get('voltage_l2', 0) for record in latest_data]
        voltage_l3 = [record.get('voltage_l3', 0) for record in latest_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l1, name='L1', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l2, name='L2', line=dict(color='yellow')))
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l3, name='L3', line=dict(color='blue')))
        
        fig.update_layout(
            title='Напряжение по фазам',
            xaxis_title='Время',
            yaxis_title='Напряжение, В',
            height=200,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def create_current_chart(self, data):
        """Создание графика тока"""
        if not data:
            return {}
        
        # Берем последние данные
        latest_data = data[-10:] if len(data) > 10 else data
        
        timestamps = [record['timestamp'] for record in latest_data]
        current_l1 = [record.get('current_l1', 0) for record in latest_data]
        current_l2 = [record.get('current_l2', 0) for record in latest_data]
        current_l3 = [record.get('current_l3', 0) for record in latest_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=timestamps, y=current_l1, name='L1', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=timestamps, y=current_l2, name='L2', line=dict(color='yellow')))
        fig.add_trace(go.Scatter(x=timestamps, y=current_l3, name='L3', line=dict(color='blue')))
        
        fig.update_layout(
            title='Ток по фазам',
            xaxis_title='Время',
            yaxis_title='Ток, А',
            height=200,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    async def update_statistics(self, analysis_results):
        """Обновление статистики"""
        self.stats_container.clear()
        
        with self.stats_container:
            if 'overall_indicators' in analysis_results:
                indicators = analysis_results['overall_indicators']
                
                if 'average_power' in indicators:
                    ui.label(f"Средняя мощность: {indicators['average_power']:.2f} кВт").classes('text-sm')
                
                if 'max_power' in indicators:
                    ui.label(f"Максимальная мощность: {indicators['max_power']:.2f} кВт").classes('text-sm')
                
                if 'load_factor' in indicators:
                    ui.label(f"Коэффициент загрузки: {indicators['load_factor']:.2%}").classes('text-sm')
                
                if 'average_power_factor' in indicators:
                    ui.label(f"Коэффициент мощности: {indicators['average_power_factor']:.3f}").classes('text-sm')
            
            # Общая статистика
            ui.separator()
            ui.label(f"Всего устройств: {analysis_results.get('equipment_analysis', {}).get('total_devices', 0)}").classes('text-sm')
            ui.label(f"Точек данных: {analysis_results.get('data_count', 0)}").classes('text-sm')
            ui.label(f"Нарушений: {analysis_results.get('total_violations', 0)}").classes('text-sm')
    
    async def update_alerts(self, analysis_results):
        """Обновление уведомлений"""
        self.alerts_container.clear()
        
        with self.alerts_container:
            # Показываем нарушения
            violations_found = False
            
            if 'equipment_analysis' in analysis_results:
                for device_name, device_analysis in analysis_results['equipment_analysis']['device_analysis'].items():
                    for violation in device_analysis['violations'][-5:]:  # Последние 5 нарушений
                        violations_found = True
                        
                        # Определение цвета по серьезности
                        color_class = 'text-red-600' if violation['severity'] == 'high' else 'text-orange-600'
                        
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.icon('warning').classes(f'{color_class} text-sm')
                            ui.label(f"{device_name}: {violation['message']}").classes(f'{color_class} text-xs')
            
            # Показываем неэффективные режимы
            if 'inefficient_modes' in analysis_results:
                for mode in analysis_results['inefficient_modes'][-3:]:  # Последние 3
                    violations_found = True
                    
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.icon('info').classes('text-blue-600 text-sm')
                        ui.label(f"{mode['device_name']}: {mode['description']}").classes('text-blue-600 text-xs')
            
            if not violations_found:
                ui.label('Нет активных уведомлений').classes('text-green-600 text-sm')
    
    async def update_real_time_data(self, processed_data, analysis_results):
        """Обновление данных в реальном времени"""
        # Сохранение данных
        self.real_time_data.extend(processed_data)
        
        # Ограничение количества точек для производительности
        if len(self.real_time_data) > 100:
            self.real_time_data = self.real_time_data[-100:]
        
        self.analysis_results = analysis_results
        
        # Обновление графиков
        try:
            power_fig = self.create_power_chart(self.real_time_data)
            if power_fig:
                self.power_chart.update_figure(power_fig)
            
            voltage_fig = self.create_voltage_chart(self.real_time_data)
            if voltage_fig:
                self.voltage_chart.update_figure(voltage_fig)
            
            current_fig = self.create_current_chart(self.real_time_data)
            if current_fig:
                self.current_chart.update_figure(current_fig)
            
            # Обновление статистики и уведомлений
            await self.update_statistics(analysis_results)
            await self.update_alerts(analysis_results)
            
        except Exception as e:
            logger.error(f"Ошибка обновления дашборда: {e}")
