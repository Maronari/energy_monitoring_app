"""
Модуль генерации отчетов
"""
from datetime import datetime, timedelta
from nicegui import ui
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)

class ReportsManager:
    def __init__(self):
        self.db_manager = None  # Будет инициализирован в main.py
    
    async def render(self):
        """Отрисовка интерфейса отчетов"""
        with ui.column().classes('w-full gap-4'):
            # Заголовок
            ui.label('Генерация отчетов').classes('text-2xl font-bold')
            
            # Параметры отчета
            with ui.card().classes('w-full'):
                ui.label('Параметры отчета').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    # Период
                    with ui.column().classes('w-1/3'):
                        ui.label('Период отчета')
                        period_select = ui.select(
                            ['Смена', 'Сутки', 'Неделя', 'Месяц', 'Произвольный'],
                            value='Сутки'
                        ).classes('w-full')
                    
                    # Даты
                    with ui.column().classes('w-1/3'):
                        ui.label('Дата начала')
                        start_date = ui.date(value=datetime.now().date()).classes('w-full')
                    
                    with ui.column().classes('w-1/3'):
                        ui.label('Дата окончания')
                        end_date = ui.date(value=datetime.now().date()).classes('w-full')
                
                with ui.row().classes('w-full gap-4 mt-4'):
                    # Устройства
                    with ui.column().classes('w-1/2'):
                        ui.label('Устройства')
                        device_select = ui.select(
                            ['Все устройства', 'Счетчик Меркурий 1', 'ПЛК ОВЕН 1'],
                            value='Все устройства',
                            multiple=True
                        ).classes('w-full')
                    
                    # Тип отчета
                    with ui.column().classes('w-1/2'):
                        ui.label('Тип отчета')
                        report_type = ui.select(
                            ['Сводный', 'Детальный', 'Анализ эффективности', 'Нарушения'],
                            value='Сводный'
                        ).classes('w-full')
                
                # Кнопки генерации
                with ui.row().classes('w-full gap-4 mt-4'):
                    ui.button(
                        'Предварительный просмотр',
                        on_click=lambda: self.generate_preview(
                            period_select.value, start_date.value, end_date.value,
                            device_select.value, report_type.value
                        )
                    ).classes('bg-blue-500')
                    
                    ui.button(
                        'Экспорт в PDF',
                        on_click=lambda: self.export_pdf(
                            period_select.value, start_date.value, end_date.value,
                            device_select.value, report_type.value
                        )
                    ).classes('bg-red-500')
                    
                    ui.button(
                        'Экспорт в Excel',
                        on_click=lambda: self.export_excel(
                            period_select.value, start_date.value, end_date.value,
                            device_select.value, report_type.value
                        )
                    ).classes('bg-green-500')
            
            # Область предварительного просмотра
            self.preview_container = ui.column().classes('w-full')
    
    async def generate_preview(self, period, start_date, end_date, devices, report_type):
        """Генерация предварительного просмотра отчета"""
        self.preview_container.clear()
        
        with self.preview_container:
            with ui.card().classes('w-full'):
                ui.label('Предварительный просмотр отчета').classes('text-lg font-bold mb-4')
                
                # Заголовок отчета
                ui.label(f'Отчет по энергопотреблению - {report_type}').classes('text-xl font-bold')
                ui.label(f'Период: {start_date} - {end_date}').classes('text-sm text-gray-600')
                ui.label(f'Устройства: {", ".join(devices) if isinstance(devices, list) else devices}').classes('text-sm text-gray-600')
                
                ui.separator().classes('my-4')
                
                # Получение данных (заглушка)
                data = await self.get_report_data(start_date, end_date, devices)
                
                if report_type == 'Сводный':
                    await self.render_summary_report(data)
                elif report_type == 'Детальный':
                    await self.render_detailed_report(data)
                elif report_type == 'Анализ эффективности':
                    await self.render_efficiency_report(data)
                elif report_type == 'Нарушения':
                    await self.render_violations_report(data)
    
    async def get_report_data(self, start_date, end_date, devices):
        """Получение данных для отчета"""
        # В реальной системе здесь будет запрос к БД
        # Пока возвращаем тестовые данные
        return {
            'energy_data': [
                {
                    'device_name': 'Счетчик Меркурий 1',
                    'timestamp': datetime.now() - timedelta(hours=i),
                    'active_power': 150 + i * 10,
                    'reactive_power': 50 + i * 5,
                    'voltage_l1': 220 + i,
                    'current_l1': 10 + i * 0.5
                }
                for i in range(24)
            ],
            'violations': [
                {
                    'device_name': 'Счетчик Меркурий 1',
                    'timestamp': datetime.now() - timedelta(hours=2),
                    'type': 'power_exceeded',
                    'message': 'Превышение максимальной мощности',
                    'value': 1050,
                    'threshold': 1000
                }
            ]
        }
    
    async def render_summary_report(self, data):
        """Отрисовка сводного отчета"""
        with ui.column().classes('w-full gap-4'):
            # Основные показатели
            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Общее потребление').classes('text-sm text-gray-600')
                    ui.label('1,250 кВт·ч').classes('text-2xl font-bold text-blue-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Средняя мощность').classes('text-sm text-gray-600')
                    ui.label('185 кВт').classes('text-2xl font-bold text-green-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Максимальная мощность').classes('text-sm text-gray-600')
                    ui.label('380 кВт').classes('text-2xl font-bold text-orange-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Нарушений').classes('text-sm text-gray-600')
                    ui.label('3').classes('text-2xl font-bold text-red-600')
            
            # График потребления
            with ui.card().classes('w-full'):
                ui.label('График потребления энергии').classes('text-lg font-bold mb-4')
                
                # Создание графика
                fig = go.Figure()
                timestamps = [d['timestamp'] for d in data['energy_data']]
                power_values = [d['active_power'] for d in data['energy_data']]
                
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=power_values,
                    mode='lines+markers',
                    name='Активная мощность',
                    line=dict(color='blue', width=2)
                ))
                
                fig.update_layout(
                    title='Потребление активной мощности',
                    xaxis_title='Время',
                    yaxis_title='Мощность, кВт',
                    height=400
                )
                
                ui.plotly(fig).classes('w-full')
            
            # Таблица по устройствам
            with ui.card().classes('w-full'):
                ui.label('Потребление по устройствам').classes('text-lg font-bold mb-4')
                
                # Группировка данных по устройствам
                device_summary = {}
                for record in data['energy_data']:
                    device = record['device_name']
                    if device not in device_summary:
                        device_summary[device] = {
                            'total_energy': 0,
                            'avg_power': 0,
                            'max_power': 0,
                            'data_points': 0
                        }
                    
                    device_summary[device]['total_energy'] += record['active_power'] * 0.25  # Предполагаем 15-минутные интервалы
                    device_summary[device]['avg_power'] += record['active_power']
                    device_summary[device]['max_power'] = max(device_summary[device]['max_power'], record['active_power'])
                    device_summary[device]['data_points'] += 1
                
                # Вычисление средних значений
                for device in device_summary:
                    if device_summary[device]['data_points'] > 0:
                        device_summary[device]['avg_power'] /= device_summary[device]['data_points']
                
                # Создание таблицы
                columns = [
                    {'name': 'device', 'label': 'Устройство', 'field': 'device'},
                    {'name': 'total_energy', 'label': 'Общее потребление, кВт·ч', 'field': 'total_energy'},
                    {'name': 'avg_power', 'label': 'Средняя мощность, кВт', 'field': 'avg_power'},
                    {'name': 'max_power', 'label': 'Максимальная мощность, кВт', 'field': 'max_power'}
                ]
                
                rows = []
                for device, summary in device_summary.items():
                    rows.append({
                        'device': device,
                        'total_energy': f"{summary['total_energy']:.2f}",
                        'avg_power': f"{summary['avg_power']:.2f}",
                        'max_power': f"{summary['max_power']:.2f}"
                    })
                
                ui.table(columns=columns, rows=rows).classes('w-full')
    
    async def render_detailed_report(self, data):
        """Отрисовка детального отчета"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Детальный отчет по энергопотреблению').classes('text-xl font-bold')
            
            # Детальная таблица всех измерений
            with ui.card().classes('w-full'):
                ui.label('Все измерения').classes('text-lg font-bold mb-4')
                
                columns = [
                    {'name': 'timestamp', 'label': 'Время', 'field': 'timestamp'},
                    {'name': 'device', 'label': 'Устройство', 'field': 'device'},
                    {'name': 'active_power', 'label': 'Активная мощность, кВт', 'field': 'active_power'},
                    {'name': 'reactive_power', 'label': 'Реактивная мощность, кВАр', 'field': 'reactive_power'},
                    {'name': 'voltage', 'label': 'Напряжение, В', 'field': 'voltage'},
                    {'name': 'current', 'label': 'Ток, А', 'field': 'current'}
                ]
                
                rows = []
                for record in data['energy_data'][:50]:  # Показываем первые 50 записей
                    rows.append({
                        'timestamp': record['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'device': record['device_name'],
                        'active_power': f"{record['active_power']:.2f}",
                        'reactive_power': f"{record['reactive_power']:.2f}",
                        'voltage': f"{record['voltage_l1']:.1f}",
                        'current': f"{record['current_l1']:.2f}"
                    })
                
                ui.table(columns=columns, rows=rows, pagination=10).classes('w-full')
    
    async def render_efficiency_report(self, data):
        """Отрисовка отчета по эффективности"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Анализ энергоэффективности').classes('text-xl font-bold')
            
            # КПИ эффективности
            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('w-1/3 text-center'):
                    ui.label('Коэффициент загрузки').classes('text-sm text-gray-600')
                    ui.label('68%').classes('text-2xl font-bold text-blue-600')
                    ui.label('Хорошо').classes('text-sm text-green-600')
                
                with ui.card().classes('w-1/3 text-center'):
                    ui.label('Коэффициент мощности').classes('text-sm text-gray-600')
                    ui.label('0.82').classes('text-2xl font-bold text-orange-600')
                    ui.label('Требует внимания').classes('text-sm text-orange-600')
                
                with ui.card().classes('w-1/3 text-center'):
                    ui.label('Стабильность нагрузки').classes('text-sm text-gray-600')
                    ui.label('85%').classes('text-2xl font-bold text-green-600')
                    ui.label('Отлично').classes('text-sm text-green-600')
            
            # Рекомендации
            with ui.card().classes('w-full'):
                ui.label('Рекомендации по повышению эффективности').classes('text-lg font-bold mb-4')
                
                recommendations = [
                    "Установить компенсирующие устройства для повышения коэффициента мощности",
                    "Оптимизировать режимы работы оборудования в периоды низкой загрузки",
                    "Рассмотреть возможность перераспределения нагрузки между фазами"
                ]
                
                for i, rec in enumerate(recommendations, 1):
                    with ui.row().classes('w-full items-start gap-2'):
                        ui.label(f"{i}.").classes('font-bold text-blue-600')
                        ui.label(rec).classes('text-sm')
    
    async def render_violations_report(self, data):
        """Отрисовка отчета по нарушениям"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Отчет по нарушениям и превышениям').classes('text-xl font-bold')
            
            # Статистика нарушений
            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Всего нарушений').classes('text-sm text-gray-600')
                    ui.label('3').classes('text-2xl font-bold text-red-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Критических').classes('text-sm text-gray-600')
                    ui.label('1').classes('text-2xl font-bold text-red-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Предупреждений').classes('text-sm text-gray-600')
                    ui.label('2').classes('text-2xl font-bold text-orange-600')
                
                with ui.card().classes('w-1/4 text-center'):
                    ui.label('Время устранения').classes('text-sm text-gray-600')
                    ui.label('15 мин').classes('text-2xl font-bold text-blue-600')
            
            # Таблица нарушений
            with ui.card().classes('w-full'):
                ui.label('Детали нарушений').classes('text-lg font-bold mb-4')
                
                columns = [
                    {'name': 'timestamp', 'label': 'Время', 'field': 'timestamp'},
                    {'name': 'device', 'label': 'Устройство', 'field': 'device'},
                    {'name': 'type', 'label': 'Тип нарушения', 'field': 'type'},
                    {'name': 'value', 'label': 'Значение', 'field': 'value'},
                    {'name': 'threshold', 'label': 'Порог', 'field': 'threshold'},
                    {'name': 'severity', 'label': 'Серьезность', 'field': 'severity'}
                ]
                
                rows = []
                for violation in data['violations']:
                    rows.append({
                        'timestamp': violation['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'device': violation['device_name'],
                        'type': violation['type'],
                        'value': f"{violation['value']:.2f}",
                        'threshold': f"{violation['threshold']:.2f}",
                        'severity': 'Критическое' if violation.get('severity') == 'high' else 'Предупреждение'
                    })
                
                ui.table(columns=columns, rows=rows).classes('w-full')
    
    async def export_pdf(self, period, start_date, end_date, devices, report_type):
        """Экспорт отчета в PDF"""
        try:
            # Создание PDF документа
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Заголовок
            title = Paragraph(f"Отчет по энергопотреблению - {report_type}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Информация о периоде
            period_info = Paragraph(f"Период: {start_date} - {end_date}", styles['Normal'])
            story.append(period_info)
            
            devices_info = Paragraph(f"Устройства: {', '.join(devices) if isinstance(devices, list) else devices}", styles['Normal'])
            story.append(devices_info)
            story.append(Spacer(1, 12))
            
            # Получение данных
            data = await self.get_report_data(start_date, end_date, devices)
            
            # Создание таблицы с данными
            table_data = [['Время', 'Устройство', 'Мощность, кВт', 'Напряжение, В', 'Ток, А']]
            
            for record in data['energy_data'][:20]:  # Первые 20 записей
                table_data.append([
                    record['timestamp'].strftime('%H:%M'),
                    record['device_name'],
                    f"{record['active_power']:.2f}",
                    f"{record['voltage_l1']:.1f}",
                    f"{record['current_l1']:.2f}"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # Генерация PDF
            doc.build(story)
            
            # Скачивание файла
            buffer.seek(0)
            ui.download(buffer.getvalue(), f'energy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
            ui.notify('PDF отчет сгенерирован', type='positive')
            
        except Exception as e:
            logger.error(f"Ошибка генерации PDF: {e}")
            ui.notify('Ошибка генерации PDF отчета', type='negative')
    
    async def export_excel(self, period, start_date, end_date, devices, report_type):
        """Экспорт отчета в Excel"""
        try:
            # Получение данных
            data = await self.get_report_data(start_date, end_date, devices)
            
            # Создание DataFrame
            df_data = []
            for record in data['energy_data']:
                df_data.append({
                    'Время': record['timestamp'],
                    'Устройство': record['device_name'],
                    'Активная мощность, кВт': record['active_power'],
                    'Реактивная мощность, кВАр': record['reactive_power'],
                    'Напряжение L1, В': record['voltage_l1'],
                    'Ток L1, А': record['current_l1']
                })
            
            df = pd.DataFrame(df_data)
            
            # Сохранение в Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Данные энергопотребления', index=False)
                
                # Добавление листа с нарушениями
                if data['violations']:
                    violations_data = []
                    for violation in data['violations']:
                        violations_data.append({
                            'Время': violation['timestamp'],
                            'Устройство': violation['device_name'],
                            'Тип нарушения': violation['type'],
                            'Сообщение': violation['message'],
                            'Значение': violation['value'],
                            'Порог': violation['threshold']
                        })
                    
                    df_violations = pd.DataFrame(violations_data)
                    df_violations.to_excel(writer, sheet_name='Нарушения', index=False)
            
            # Скачивание файла
            buffer.seek(0)
            ui.download(buffer.getvalue(), f'energy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
            ui.notify('Excel отчет сгенерирован', type='positive')
            
        except Exception as e:
            logger.error(f"Ошибка генерации Excel: {e}")
            ui.notify('Ошибка генерации Excel отчета', type='negative')
