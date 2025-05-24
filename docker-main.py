"""
Главный модуль для Docker окружения
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from nicegui import ui, app
from database.db_manager import DatabaseManager
from data_collection.modbus_client import ModbusDataCollector
from data_processing.processor import DataProcessor
from analysis.analyzer import EnergyAnalyzer
from web_interface.dashboard import Dashboard
from web_interface.reports import ReportsManager
from web_interface.admin import AdminPanel
from config.docker_settings import DockerSettings

# Настройка логирования для Docker
def setup_logging():
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Создание директории для логов
    log_dir = '/app/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Настройка логгеров
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # Вывод в консоль для Docker
            logging.FileHandler('/app/logs/energy_monitoring.log')
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

class DockerEnergyMonitoringSystem:
    def __init__(self):
        self.settings = DockerSettings()
        self.db_manager = DatabaseManager(self.settings)
        self.data_collector = ModbusDataCollector(self.settings)
        self.data_processor = DataProcessor(self.settings)
        self.analyzer = EnergyAnalyzer(self.settings)
        self.dashboard = Dashboard()
        self.reports_manager = ReportsManager()
        self.admin_panel = AdminPanel()
        
        self.running = False
        
        logger.info("Система мониторинга энергопотребления инициализирована")
        logger.info(f"База данных: {self.settings.DATABASE.host}:{self.settings.DATABASE.port}")
        logger.info(f"Устройств настроено: {len(self.settings.MODBUS_DEVICES)}")
    
    async def wait_for_database(self, max_retries=30, delay=2):
        """Ожидание готовности базы данных"""
        logger.info("Ожидание готовности базы данных...")
        
        for attempt in range(max_retries):
            try:
                await self.db_manager.initialize()
                logger.info("База данных готова")
                return True
            except Exception as e:
                logger.warning(f"Попытка {attempt + 1}/{max_retries} подключения к БД неудачна: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error("Не удалось подключиться к базе данных")
                    return False
        
        return False
    
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
                    
                    logger.debug(f"Обработано {len(processed_data)} записей данных")
                
                await asyncio.sleep(self.settings.COLLECTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Ошибка в процессе сбора данных: {e}")
                await asyncio.sleep(5)
    
    def stop_data_collection(self):
        """Остановка сбора данных"""
        self.running = False
        logger.info("Остановка системы сбора данных")

# Глобальный экземпляр системы
energy_system = DockerEnergyMonitoringSystem()

# Добавление health check endpoint
@ui.page('/health')
async def health_check():
    """Health check для Docker"""
    try:
        # Проверка подключения к БД
        await energy_system.db_manager.get_latest_data(limit=1)
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'data_collection': 'running' if energy_system.running else 'stopped'
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

@ui.page('/')
async def main_page():
    """Главная страница системы"""
    ui.page_title('Система мониторинга энергопотребления')
    
    with ui.header().classes('bg-blue-600 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('Система мониторинга энергопотребления').classes('text-xl font-bold')
            ui.space()
            ui.label(f'Время: {datetime.now().strftime("%H:%M:%S")}').classes('text-sm')
            
            # Индикатор состояния
            status_color = 'green' if energy_system.running else 'red'
            status_text = 'Работает' if energy_system.running else 'Остановлен'
            ui.badge(status_text, color=status_color).classes('ml-4')
    
    with ui.left_drawer().classes('bg-gray-100'):
        with ui.column():
            ui.button('Дашборд', on_click=lambda: ui.navigate.to('/')).classes('w-full')
            ui.button('Отчеты', on_click=lambda: ui.navigate.to('/reports')).classes('w-full')
            ui.button('Администрирование', on_click=lambda: ui.navigate.to('/admin')).classes('w-full')
            ui.separator()
            
            with ui.row():
                start_btn = ui.button('Запуск', on_click=start_monitoring).classes('bg-green-500')
                stop_btn = ui.button('Стоп', on_click=stop_monitoring).classes('bg-red-500')
            
            ui.separator()
            
            # Информация о системе
            with ui.column().classes('text-xs text-gray-600'):
                ui.label(f'Хост БД: {energy_system.settings.DATABASE.host}')
                ui.label(f'Устройств: {len(energy_system.settings.MODBUS_DEVICES)}')
                ui.label(f'Интервал: {energy_system.settings.COLLECTION_INTERVAL}с')
    
    # Основной контент - дашборд
    await energy_system.dashboard.render()

async def start_monitoring():
    """Запуск мониторинга"""
    if not energy_system.running:
        asyncio.create_task(energy_system.start_data_collection())
        ui.notify('Мониторинг запущен', type='positive')
        logger.info("Мониторинг запущен пользователем")

def stop_monitoring():
    """Остановка мониторинга"""
    energy_system.stop_data_collection()
    ui.notify('Мониторинг остановлен', type='warning')
    logger.info("Мониторинг остановлен пользователем")

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

async def startup():
    """Инициализация при запуске"""
    logger.info("Запуск системы мониторинга энергопотребления")
    
    # Ожидание готовности базы данных
    if not await energy_system.wait_for_database():
        logger.error("Не удалось подключиться к базе данных. Завершение работы.")
        sys.exit(1)
    
    # Автоматический запуск сбора данных
    if os.getenv('AUTO_START_COLLECTION', 'true').lower() == 'true':
        asyncio.create_task(energy_system.start_data_collection())
        logger.info("Автоматический запуск сбора данных")

if __name__ in {"__main__", "__mp_main__"}:
    # Регистрация функции запуска
    app.on_startup(startup)
    
    # Запуск веб-приложения
    ui.run(
        title='Система мониторинга энергопотребления',
        port=energy_system.settings.WEB_PORT,
        host=energy_system.settings.WEB_HOST,
        reload=False,
        show=False  # Не открывать браузер в Docker
    )
