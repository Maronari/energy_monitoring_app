"""
Обновленный дашборд с авторизацией и расширенной функциональностью
"""
import asyncio
from datetime import datetime, timedelta
from nicegui import ui, app
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Dashboard:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.real_time_data = []
        self.analysis_results = {}
        self.charts = {}
        self.current_time_label = None
        self.alerts_container = None
        self.stats_container = None
    
    def start_time_update(self):
        """Запуск обновления времени каждую секунду"""
        async def update_time():
            while True:
                if self.current_time_label:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.current_time_label.text = f'Время: {current_time}'
                await asyncio.sleep(1)
        
        asyncio.create_task(update_time())
    
    async def render(self, session_data: Dict[str, Any]):
        """Отрисовка дашборда"""
        user_role = session_data.get('role', 'viewer')

        self.start_time_update()
        
        with ui.row().classes('w-full h-screen flex-nowrap'):
            # Левая колонка - основные графики (50%)
            with ui.column().classes('w-full md:w-1/2'):
                await self.render_main_charts()
            
            # Правая колонка - статистика и уведомления (50%)
            with ui.column().classes('w-full md:w-1/2'):
                await self.render_statistics()
                await self.render_alerts()
                if user_role in ['admin', 'operator']:
                    await self.render_quick_actions()
    
    async def render_main_charts(self):
        """Отрисовка основных графиков"""
        # График мощности в реальном времени
        with ui.card().classes('w-full mb-4'):
            ui.label('Активная мощность в реальном времени').classes('text-lg font-bold')
            self.power_chart = ui.plotly({}).classes('w-full h-64')
        
        # Графики по участкам
        with ui.card().classes('w-full mb-4'):
            ui.label('Потребление по участкам за последние 24 часа').classes('text-lg font-bold')
            self.area_chart = ui.plotly({}).classes('w-full h-64')
        
        # Графики напряжения и тока
        # with ui.row().classes('w-full gap-4 mb-4'):
        #     with ui.card().classes('flex-1'):
        #         ui.label('Напряжение по фазам').classes('text-lg font-bold')
        #         self.voltage_chart = ui.plotly({}).classes('w-full h-48')
            
        #     with ui.card().classes('flex-1'):
        #         ui.label('Ток по фазам').classes('text-lg font-bold')
        #         self.current_chart = ui.plotly({}).classes('w-full h-48')

        #     with ui.card().classes('flex-1'):
        #         ui.label('Коэффициент мощности').classes('text-lg font-bold')
        #         self.pf_chart = ui.plotly({}).classes('w-full h-48')
            
        #     with ui.card().classes('flex-1'):
        #         ui.label('Эффективность оборудования').classes('text-lg font-bold')
        #         self.efficiency_chart = ui.plotly({}).classes('w-full h-48')
        
        # Исторический график энергопотребления
        with ui.card().classes('w-full mb-4'):
            ui.label('Энергопотребление за последние 7 дней').classes('text-lg font-bold')
            self.historical_chart = ui.plotly({}).classes('w-full h-64')
        
        # Загрузка исторических данных
        await self.load_historical_data()
    
    async def render_statistics(self):
        """Отрисовка статистики"""
        with ui.card().classes('w-full gap-4 mb-4'):
            with ui.card().classes('w-full'):
                ui.label('Напряжение по фазам').classes('text-lg font-bold')
                self.voltage_chart = ui.plotly({}).classes('w-full h-full')
            
            with ui.card().classes('w-full'):
                ui.label('Ток по фазам').classes('text-lg font-bold')
                self.current_chart = ui.plotly({}).classes('w-full h-full')

            with ui.card().classes('w-full'):
                ui.label('Коэффициент мощности').classes('text-lg font-bold')
                self.pf_chart = ui.plotly({}).classes('w-full h-full')
            
            with ui.card().classes('w-full'):
                ui.label('Эффективность оборудования').classes('text-lg font-bold')
                self.efficiency_chart = ui.plotly({}).classes('w-full h-full')
            
            with ui.card().classes('w-full gap-2'):
                ui.label('Текущие показатели').classes('text-lg font-bold')
            
            self.stats_container = ui.column().classes('w-full gap-2')
            
            # Инициализация пустой статистики
            with self.stats_container:
                ui.label('Загрузка данных...').classes('text-gray-500')
    
    async def render_alerts(self):
        """Отрисовка уведомлений"""
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Уведомления').classes('text-lg font-bold')
                ui.button('Обновить', on_click=self.refresh_alerts).classes('bg-blue-500 text-xs')
            
            self.alerts_container = ui.column().classes('w-full gap-2 max-h-64 overflow-y-auto')
            
            # Загрузка активных уведомлений
            await self.load_active_alerts()
    
    async def render_quick_actions(self):
        """Быстрые действия для операторов и администраторов"""
        with ui.card().classes('w-full'):
            ui.label('Быстрые действия').classes('text-lg font-bold mb-4')
            
            with ui.column().classes('w-full gap-2'):
                ui.button('Экспорт отчета', on_click=self.export_quick_report).classes('w-full bg-green-500')
                ui.button('Сброс уведомлений', on_click=self.reset_alerts).classes('w-full bg-orange-500')
                ui.button('Обновить данные', on_click=self.refresh_all_data).classes('w-full bg-blue-500')
    
    async def load_historical_data(self):
        """Загрузка исторических данных"""
        try:
            # Получение данных за последние 7 дней
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            historical_data = await self.db_manager.get_energy_readings_by_period(start_time, end_time)
            
            if historical_data:
                await self.update_historical_chart(historical_data)
                await self.update_area_chart()
                await self.update_efficiency_chart()
        
        except Exception as e:
            logger.error(f"Ошибка загрузки исторических данных: {e}")
    
    async def load_active_alerts(self):
        """Загрузка активных уведомлений"""
        try:
            active_alerts = await self.db_manager.get_active_logs(limit=10)
            await self.update_alerts_display(active_alerts)
        
        except Exception as e:
            logger.error(f"Ошибка загрузки уведомлений: {e}")
    
    def create_power_chart(self, data):
        """Создание графика мощности"""
        if not data:
            return {}
        
        # Группировка данных по оборудованию
        equipment_data = {}
        for record in data:
            equipment_name = record.get('equipment_name', 'Unknown')
            if equipment_name not in equipment_data:
                equipment_data[equipment_name] = {'timestamps': [], 'power': []}
            
            equipment_data[equipment_name]['timestamps'].append(record['timestamp'])
            equipment_data[equipment_name]['power'].append(record.get('active_power', 0))
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, (equipment_name, eq_data) in enumerate(equipment_data.items()):
            fig.add_trace(go.Scatter(
                x=eq_data['timestamps'],
                y=eq_data['power'],
                mode='lines+markers',
                name=equipment_name,
                line=dict(width=2, color=colors[i % len(colors)]),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title='Активная мощность по оборудованию',
            xaxis_title='Время',
            yaxis_title='Мощность, кВт',
            height=250,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    async def update_historical_chart(self, historical_data):
        """Обновление исторического графика"""
        try:
            # Группировка данных по дням
            daily_data = {}
            
            for record in historical_data:
                date = record['energy_readings_timestamp'].date()
                if date not in daily_data:
                    daily_data[date] = []
                daily_data[date].append(record['energy_readings_active_power_kw'] or 0)
            
            # Расчет средних значений по дням
            dates = []
            avg_powers = []
            max_powers = []
            min_powers = []
            
            for date in sorted(daily_data.keys()):
                powers = daily_data[date]
                dates.append(date)
                avg_powers.append(sum(powers) / len(powers))
                max_powers.append(max(powers))
                min_powers.append(min(powers))
            
            fig = go.Figure()
            
            # Средняя мощность
            fig.add_trace(go.Scatter(
                x=dates,
                y=avg_powers,
                mode='lines+markers',
                name='Средняя мощность',
                line=dict(color='blue', width=3)
            ))
            
            # Максимальная мощность
            fig.add_trace(go.Scatter(
                x=dates,
                y=max_powers,
                mode='lines',
                name='Максимальная мощность',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            # Минимальная мощность
            fig.add_trace(go.Scatter(
                x=dates,
                y=min_powers,
                mode='lines',
                name='Минимальная мощность',
                line=dict(color='green', width=2, dash='dot')
            ))
            
            fig.update_layout(
                title='Энергопотребление за последние 7 дней',
                xaxis_title='Дата',
                yaxis_title='Мощность, кВт',
                height=250,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            self.historical_chart.update_figure(fig)
        
        except Exception as e:
            logger.error(f"Ошибка обновления исторического графика: {e}")
    
    async def update_area_chart(self):
        """Обновление графика по участкам"""
        try:
            area_stats = await self.db_manager.get_area_statistics()
            
            if not area_stats:
                return
            
            areas = [stat['area_name'] for stat in area_stats]
            avg_powers = [stat['avg_power_kw'] or 0 for stat in area_stats]
            max_powers = [stat['max_power_kw'] or 0 for stat in area_stats]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=areas,
                y=avg_powers,
                name='Средняя мощность',
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                x=areas,
                y=max_powers,
                name='Максимальная мощность',
                marker_color='darkblue'
            ))
            
            fig.update_layout(
                title='Потребление по участкам',
                xaxis_title='Участок',
                yaxis_title='Мощность, кВт',
                height=250,
                margin=dict(l=50, r=50, t=50, b=50),
                barmode='group'
            )
            
            self.area_chart.update_figure(fig)
        
        except Exception as e:
            logger.error(f"Ошибка обновления графика по участкам: {e}")
    
    async def update_efficiency_chart(self):
        """Обновление графика эффективности"""
        try:
            efficiency_data = await self.db_manager.get_equipment_efficiency()
            
            if not efficiency_data:
                return
            
            equipment_names = [eq['equipment_name'] for eq in efficiency_data]
            load_factors = [eq['load_factor_percent'] or 0 for eq in efficiency_data]
            power_factors = [eq['avg_power_factor'] or 0 for eq in efficiency_data]
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Коэффициент загрузки
            fig.add_trace(
                go.Bar(x=equipment_names, y=load_factors, name="Коэффициент загрузки, %", 
                      marker_color='lightgreen'),
                secondary_y=False,
            )
            
            # Коэффициент мощности
            fig.add_trace(
                go.Scatter(x=equipment_names, y=power_factors, mode='lines+markers',
                          name="Коэффициент мощности", line=dict(color='red', width=3)),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="Оборудование")
            fig.update_yaxes(title_text="Коэффициент загрузки, %", secondary_y=False)
            fig.update_yaxes(title_text="Коэффициент мощности", secondary_y=True)
            
            fig.update_layout(
                title='Эффективность оборудования',
                height=200,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            self.efficiency_chart.update_figure(fig)
        
        except Exception as e:
            logger.error(f"Ошибка обновления графика эффективности: {e}")
    
    def create_voltage_chart(self, data):
        """Создание графика напряжения"""
        if not data:
            return {}
        
        # Берем последние 20 точек
        latest_data = data[-20:] if len(data) > 20 else data
        
        timestamps = [record['timestamp'] for record in latest_data]
        voltage_l1 = [record.get('voltage_l1', 0) for record in latest_data]
        voltage_l2 = [record.get('voltage_l2', 0) for record in latest_data]
        voltage_l3 = [record.get('voltage_l3', 0) for record in latest_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l1, name='L1', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l2, name='L2', line=dict(color='yellow')))
        fig.add_trace(go.Scatter(x=timestamps, y=voltage_l3, name='L3', line=dict(color='blue')))
        
        # Добавление пороговых линий
        fig.add_hline(y=220, line_dash="dash", line_color="green", 
                     annotation_text="Номинал 220В")
        fig.add_hline(y=200, line_dash="dot", line_color="orange", 
                     annotation_text="Мин. порог")
        fig.add_hline(y=250, line_dash="dot", line_color="red", 
                     annotation_text="Макс. порог")
        
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
        
        # Берем последние 20 точек
        latest_data = data[-20:] if len(data) > 20 else data
        
        timestamps = [record['timestamp'] for record in latest_data]
        current_l1 = [record.get('current_l1', 0) for record in latest_data]
        current_l2 = [record.get('current_l2', 0) for record in latest_data]
        current_l3 = [record.get('current_l3', 0) for record in latest_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=timestamps, y=current_l1, name='L1', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=timestamps, y=current_l2, name='L2', line=dict(color='yellow')))
        fig.add_trace(go.Scatter(x=timestamps, y=current_l3, name='L3', line=dict(color='blue')))
        
        # Добавление пороговой линии
        fig.add_hline(y=100, line_dash="dot", line_color="red", 
                     annotation_text="Макс. порог 100А")
        
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
            try:
                # Получение общей статистики
                area_stats = await self.db_manager.get_area_statistics()
                efficiency_data = await self.db_manager.get_equipment_efficiency()
                
                if area_stats:
                    total_power = sum(stat['avg_power_kw'] or 0 for stat in area_stats)
                    total_equipment = sum(stat['equipment_count'] or 0 for stat in area_stats)
                    
                    ui.label(f"Общая мощность: {total_power:.2f} кВт").classes('text-sm font-semibold')
                    ui.label(f"Активного оборудования: {total_equipment}").classes('text-sm')
                
                if efficiency_data:
                    avg_load_factor = sum(eq['load_factor_percent'] or 0 for eq in efficiency_data) / len(efficiency_data)
                    avg_power_factor = sum(eq['avg_power_factor'] or 0 for eq in efficiency_data) / len(efficiency_data)
                    
                    ui.label(f"Средний коэффициент загрузки: {avg_load_factor:.1f}%").classes('text-sm')
                    ui.label(f"Средний коэффициент мощности: {avg_power_factor:.3f}").classes('text-sm')
                
                # Статус системы
                ui.separator()
                ui.label(f"Последнее обновление: {datetime.now().strftime('%H:%M:%S')}").classes('text-xs text-gray-600')
                
                # Активные уведомления
                active_alerts = await self.db_manager.get_active_logs(limit=5)
                critical_count = len([alert for alert in active_alerts if alert['severity'] == 'critical'])
                high_count = len([alert for alert in active_alerts if alert['severity'] == 'high'])
                
                if critical_count > 0:
                    ui.label(f"Критических уведомлений: {critical_count}").classes('text-sm text-red-600 font-bold')
                if high_count > 0:
                    ui.label(f"Важных уведомлений: {high_count}").classes('text-sm text-orange-600')
                
                if critical_count == 0 and high_count == 0:
                    ui.label("Критических уведомлений нет").classes('text-sm text-green-600')
            
            except Exception as e:
                logger.error(f"Ошибка обновления статистики: {e}")
                ui.label('Ошибка загрузки статистики').classes('text-sm text-red-600')
    
    async def update_alerts_display(self, alerts):
        """Обновление отображения уведомлений"""
        self.alerts_container.clear()
        
        with self.alerts_container:
            if not alerts:
                ui.label('Нет активных уведомлений').classes('text-green-600 text-sm')
                return
            
            # Группировка по серьезности
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            high_alerts = [a for a in alerts if a['severity'] == 'high']
            medium_alerts = [a for a in alerts if a['severity'] == 'medium']
            
            # Отображение критических уведомлений
            for alert in critical_alerts:
                with ui.card().classes('w-full bg-red-50 border-l-4 border-red-500 mb-2'):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.icon('error', color='red').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label(f"{alert['equipment_name'] or 'Система'}").classes('font-bold text-red-800 text-sm')
                            ui.label(alert['log_message']).classes('text-red-700 text-xs')
                            ui.label(alert['log_timestamp'].strftime('%H:%M:%S')).classes('text-red-600 text-xs')
                        
                        if alert['log_status'] == 'new':
                            ui.button('✓', on_click=lambda a=alert: self.acknowledge_alert(a['log_id'])).classes('bg-red-500 text-white text-xs')
            
            # Отображение важных уведомлений
            for alert in high_alerts:
                with ui.card().classes('w-full bg-orange-50 border-l-4 border-orange-500 mb-2'):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.icon('warning', color='orange').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label(f"{alert['equipment_name'] or 'Система'}").classes('font-bold text-orange-800 text-sm')
                            ui.label(alert['log_message']).classes('text-orange-700 text-xs')
                            ui.label(alert['log_timestamp'].strftime('%H:%M:%S')).classes('text-orange-600 text-xs')
                        
                        if alert['log_status'] == 'new':
                            ui.button('✓', on_click=lambda a=alert: self.acknowledge_alert(a['log_id'])).classes('bg-orange-500 text-white text-xs')
            
            # Отображение обычных уведомлений (только первые 3)
            for alert in medium_alerts[:3]:
                with ui.card().classes('w-full bg-blue-50 border-l-4 border-blue-500 mb-2'):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.icon('info', color='blue').classes('text-lg')
                        with ui.column().classes('flex-1'):
                            ui.label(f"{alert['equipment_name'] or 'Система'}").classes('font-bold text-blue-800 text-sm')
                            ui.label(alert['log_message']).classes('text-blue-700 text-xs')
                            ui.label(alert['log_timestamp'].strftime('%H:%M:%S')).classes('text-blue-600 text-xs')
    
    async def acknowledge_alert(self, log_id: int):
        """Подтверждение уведомления"""
        try:
            # В реальной системе здесь должен быть ID текущего пользователя
            await self.db_manager.acknowledge_log(log_id, 1)  # Временно используем ID=1
            ui.notify('Уведомление подтверждено', type='positive')
            await self.load_active_alerts()  # Перезагрузка уведомлений
        except Exception as e:
            logger.error(f"Ошибка подтверждения уведомления: {e}")
            ui.notify('Ошибка подтверждения уведомления', type='negative')
    
    async def refresh_alerts(self):
        """Обновление уведомлений"""
        await self.load_active_alerts()
        ui.notify('Уведомления обновлены', type='info')
    
    async def export_quick_report(self):
        """Быстрый экспорт отчета"""
        ui.notify('Функция экспорта отчета в разработке', type='info')
    
    async def reset_alerts(self):
        """Сброс всех уведомлений"""
        try:
            # Подтверждение всех новых уведомлений
            active_alerts = await self.db_manager.get_active_logs()
            for alert in active_alerts:
                if alert['log_status'] == 'new':
                    await self.db_manager.acknowledge_log(alert['log_id'], 1)
            
            ui.notify('Все уведомления подтверждены', type='positive')
            await self.load_active_alerts()
        except Exception as e:
            logger.error(f"Ошибка сброса уведомлений: {e}")
            ui.notify('Ошибка сброса уведомлений', type='negative')
    
    async def refresh_all_data(self):
        """Обновление всех данных"""
        try:
            await self.load_historical_data()
            await self.load_active_alerts()
            await self.update_statistics({})
            ui.notify('Данные обновлены', type='positive')
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {e}")
            ui.notify('Ошибка обновления данных', type='negative')
    
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
            await self.load_active_alerts()
            
        except Exception as e:
            logger.error(f"Ошибка обновления дашборда: {e}")
