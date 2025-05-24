"""
Главный модуль информационной системы мониторинга энергопотребления
"""
import asyncio
import logging
from datetime import datetime
from nicegui import ui, app
from database.db_manager import DatabaseManager
from data_collection.modbus_client import ModbusDataCollector
from data_processing.processor import DataProcessor
from analysis.analyzer import EnergyAnalyzer
from web_interface.dashboard import Dashboard
from web_interface.reports import ReportsManager
from web_interface.admin import AdminPanel
from config.settings import Settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('energy_monitoring.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnergyMonitoringSystem:
    def __init__(self):
        self.settings = Settings()
        self.db_manager = DatabaseManager()
        self.data_collector = ModbusDataCollector(self.db_manager)
        self.data_processor = DataProcessor(self.db_manager)
        self.analyzer = EnergyAnalyzer(self.db_manager)
        self.dashboard = Dashboard()
        self.reports_manager = ReportsManager()
        self.admin_panel = AdminPanel()
        
        # Флаг для остановки сбора данных
        self.running = False
        
    async def start_data_collection(self):
        """Запуск процесса сбора данных"""
        self.running = True
        logger.info("Запуск системы сбора данных")
        
        while self.running:
            try:
                # Сбор данных с устройств
                raw_data = await self.data_collector.collect_all_data()
                
                if raw_data:
                    # Обработка данных
                    processed_data = self.data_processor.process_data(raw_data)
                    
                    # Сохранение в БД
                    await self.db_manager.save_energy_data(processed_data)
                    
                    # Анализ данных
                    analysis_results = self.analyzer.analyze_data(processed_data)
                    
                    # Обновление дашборда
                    await self.dashboard.update_real_time_data(processed_data, analysis_results)
                    
                await asyncio.sleep(self.settings.COLLECTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ошибка в процессе сбора данных: {e}")
                await asyncio.sleep(5)
    
    def stop_data_collection(self):
        """Остановка сбора данных"""
        self.running = False
        logger.info("Остановка системы сбора данных")

# Глобальный экземпляр системы
energy_system = EnergyMonitoringSystem()

@ui.page('/')
async def main_page():
    """Главная страница системы"""
    ui.page_title('Система мониторинга энергопотребления')
    
    with ui.header().classes('bg-blue-600 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('Система мониторинга энергопотребления').classes('text-xl font-bold')
            ui.space()
            ui.label(f'Время: {datetime.now().strftime("%H:%M:%S")}').classes('text-sm')
    
    with ui.left_drawer().classes('bg-gray-100'):
        with ui.column():
            ui.button('Дашборд', on_click=lambda: ui.navigate.to('/')).classes('w-full')
            ui.button('Отчеты', on_click=lambda: ui.navigate.to('/reports')).classes('w-full')
            ui.button('Администрирование', on_click=lambda: ui.navigate.to('/admin')).classes('w-full')
            ui.separator()
            
            with ui.row():
                start_btn = ui.button('Запуск', on_click=start_monitoring).classes('bg-green-500')
                stop_btn = ui.button('Стоп', on_click=stop_monitoring).classes('bg-red-500')
    
    # Основной контент - дашборд
    await energy_system.dashboard.render()

async def start_monitoring():
    """Запуск мониторинга"""
    if not energy_system.running:
        asyncio.create_task(energy_system.start_data_collection())
        ui.notify('Мониторинг запущен', type='positive')

def stop_monitoring():
    """Остановка мониторинга"""
    energy_system.stop_data_collection()
    ui.notify('Мониторинг остановлен', type='warning')

@ui.page('/reports')
async def reports_page():
    """Страница отчетов"""
    ui.page_title('Отчеты')
    await energy_system.reports_manager.render()

@ui.page('/admin')
async def admin_page():
    """Страница администрирования"""
    ui.page_title('Администрирование')
    await energy_system.admin_panel.render()

if __name__ in {"__main__", "__mp_main__"}:
    # Инициализация базы данных
    asyncio.run(energy_system.db_manager.initialize())
    
    # Запуск веб-приложения
    ui.run(
        title='Система мониторинга энергопотребления',
        port=8080,
        host='0.0.0.0',
        reload=False
    )
