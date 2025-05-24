"""
Панель администрирования
"""
from nicegui import ui
import hashlib
import logging

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.db_manager = None  # Будет инициализирован в main.py
    
    async def render(self):
        """Отрисовка панели администрирования"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Администрирование системы').classes('text-2xl font-bold')
            
            # Вкладки
            with ui.tabs().classes('w-full') as tabs:
                devices_tab = ui.tab('Устройства')
                users_tab = ui.tab('Пользователи')
                thresholds_tab = ui.tab('Пороговые значения')
                system_tab = ui.tab('Система')
            
            with ui.tab_panels(tabs, value=devices_tab).classes('w-full'):
                # Вкладка устройств
                with ui.tab_panel(devices_tab):
                    await self.render_devices_management()
                
                # Вкладка пользователей
                with ui.tab_panel(users_tab):
                    await self.render_users_management()
                
                # Вкладка пороговых значений
                with ui.tab_panel(thresholds_tab):
                    await self.render_thresholds_management()
                
                # Вкладка системы
                with ui.tab_panel(system_tab):
                    await self.render_system_management()
    
    async def render_devices_management(self):
        """Управление устройствами"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Управление устройствами').classes('text-xl font-bold')
            
            # Форма добавления устройства
            with ui.card().classes('w-full'):
                ui.label('Добавить новое устройство').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    device_name = ui.input('Название устройства').classes('w-1/4')
                    device_ip = ui.input('IP-адрес').classes('w-1/4')
                    device_port = ui.number('Порт', value=502).classes('w-1/4')
                    device_unit = ui.number('Unit ID', value=1).classes('w-1/4')
                
                with ui.row().classes('w-full gap-4'):
                    device_type = ui.select(['meter', 'plc'], value='meter', label='Тип устройства').classes('w-1/2')
                    ui.button('Добавить устройство', on_click=lambda: self.add_device(
                        device_name.value, device_ip.value, device_port.value, 
                        device_unit.value, device_type.value
                    )).classes('bg-green-500')
            
            # Список существующих устройств
            with ui.card().classes('w-full'):
                ui.label('Существующие устройства').classes('text-lg font-bold mb-4')
                
                # Таблица устройств
                columns = [
                    {'name': 'name', 'label': 'Название', 'field': 'name'},
                    {'name': 'ip', 'label': 'IP-адрес', 'field': 'ip'},
                    {'name': 'port', 'label': 'Порт', 'field': 'port'},
                    {'name': 'unit_id', 'label': 'Unit ID', 'field': 'unit_id'},
                    {'name': 'type', 'label': 'Тип', 'field': 'type'},
                    {'name': 'status', 'label': 'Статус', 'field': 'status'},
                    {'name': 'actions', 'label': 'Действия', 'field': 'actions'}
                ]
                
                # Тестовые данные устройств
                rows = [
                    {
                        'name': 'Счетчик Меркурий 1',
                        'ip': '192.168.1.100',
                        'port': '502',
                        'unit_id': '1',
                        'type': 'meter',
                        'status': 'Подключен',
                        'actions': 'Редактировать | Удалить'
                    },
                    {
                        'name': 'ПЛК ОВЕН 1',
                        'ip': '192.168.1.101',
                        'port': '502',
                        'unit_id': '2',
                        'type': 'plc',
                        'status': 'Отключен',
                        'actions': 'Редактировать | Удалить'
                    }
                ]
                
                ui.table(columns=columns, rows=rows).classes('w-full')
    
    async def render_users_management(self):
        """Управление пользователями"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Управление пользователями').classes('text-xl font-bold')
            
            # Форма добавления пользователя
            with ui.card().classes('w-full'):
                ui.label('Добавить нового пользователя').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    username = ui.input('Имя пользователя').classes('w-1/3')
                    password = ui.input('Пароль', password=True).classes('w-1/3')
                    role = ui.select(['admin', 'operator', 'viewer'], value='viewer', label='Роль').classes('w-1/3')
                
                ui.button('Добавить пользователя', on_click=lambda: self.add_user(
                    username.value, password.value, role.value
                )).classes('bg-green-500')
            
            # Список пользователей
            with ui.card().classes('w-full'):
                ui.label('Существующие пользователи').classes('text-lg font-bold mb-4')
                
                columns = [
                    {'name': 'username', 'label': 'Пользователь', 'field': 'username'},
                    {'name': 'role', 'label': 'Роль', 'field': 'role'},
                    {'name': 'created', 'label': 'Создан', 'field': 'created'},
                    {'name': 'last_login', 'label': 'Последний вход', 'field': 'last_login'},
                    {'name': 'actions', 'label': 'Действия', 'field': 'actions'}
                ]
                
                rows = [
                    {
                        'username': 'admin',
                        'role': 'Администратор',
                        'created': '2024-01-01',
                        'last_login': '2024-01-15 10:30',
                        'actions': 'Редактировать | Удалить'
                    },
                    {
                        'username': 'operator1',
                        'role': 'Оператор',
                        'created': '2024-01-05',
                        'last_login': '2024-01-15 09:15',
                        'actions': 'Редактировать | Удалить'
                    }
                ]
                
                ui.table(columns=columns, rows=rows).classes('w-full')
    
    async def render_thresholds_management(self):
        """Управление пороговыми значениями"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Пороговые значения').classes('text-xl font-bold')
            
            with ui.card().classes('w-full'):
                ui.label('Настройка пороговых значений').classes('text-lg font-bold mb-4')
                
                # Пороги мощности
                with ui.row().classes('w-full gap-4'):
                    ui.label('Максимальная мощность (кВт):').classes('w-1/3')
                    max_power = ui.number('', value=1000.0).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_threshold('max_power', max_power.value)).classes('bg-blue-500')
                
                # Пороги тока
                with ui.row().classes('w-full gap-4'):
                    ui.label('Максимальный ток (А):').classes('w-1/3')
                    max_current = ui.number('', value=100.0).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_threshold('max_current', max_current.value)).classes('bg-blue-500')
                
                # Пороги напряжения
                with ui.row().classes('w-full gap-4'):
                    ui.label('Минимальное напряжение (В):').classes('w-1/3')
                    min_voltage = ui.number('', value=200.0).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_threshold('min_voltage', min_voltage.value)).classes('bg-blue-500')
                
                with ui.row().classes('w-full gap-4'):
                    ui.label('Максимальное напряжение (В):').classes('w-1/3')
                    max_voltage = ui.number('', value=250.0).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_threshold('max_voltage', max_voltage.value)).classes('bg-blue-500')
            
            # Пороги по устройствам
            with ui.card().classes('w-full'):
                ui.label('Индивидуальные пороги по устройствам').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    device_select = ui.select(['Счетчик Меркурий 1', 'ПЛК ОВЕН 1'], label='Устройство').classes('w-1/3')
                    parameter_select = ui.select(['Мощность', 'Ток', 'Напряжение'], label='Параметр').classes('w-1/3')
                    threshold_value = ui.number('Значение').classes('w-1/3')
                
                ui.button('Установить индивидуальный порог', on_click=lambda: self.set_device_threshold(
                    device_select.value, parameter_select.value, threshold_value.value
                )).classes('bg-orange-500')
    
    async def render_system_management(self):
        """Управление системой"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Системные настройки').classes('text-xl font-bold')
            
            # Настройки сбора данных
            with ui.card().classes('w-full'):
                ui.label('Настройки сбора данных').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    ui.label('Интервал сбора данных (сек):').classes('w-1/3')
                    collection_interval = ui.number('', value=5).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_system_setting('collection_interval', collection_interval.value)).classes('bg-blue-500')
                
                with ui.row().classes('w-full gap-4'):
                    ui.label('Таймаут подключения (сек):').classes('w-1/3')
                    connection_timeout = ui.number('', value=10).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_system_setting('connection_timeout', connection_timeout.value)).classes('bg-blue-500')
            
            # Настройки базы данных
            with ui.card().classes('w-full'):
                ui.label('Настройки базы данных').classes('text-lg font-bold mb-4')
                
                with ui.row().classes('w-full gap-4'):
                    ui.label('Период хранения данных (дни):').classes('w-1/3')
                    retention_period = ui.number('', value=365).classes('w-1/3')
                    ui.button('Сохранить', on_click=lambda: self.save_system_setting('retention_period', retention_period.value)).classes('bg-blue-500')
                
                ui.button('Очистить старые данные', on_click=self.cleanup_old_data).classes('bg-red-500 mt-4')
            
            # Системная информация
            with ui.card().classes('w-full'):
                ui.label('Системная информация').classes('text-lg font-bold mb-4')
                
                with ui.column().classes('w-full gap-2'):
                    ui.label('Версия системы: 1.0.0').classes('text-sm')
                    ui.label('Время работы: 2 дня 5 часов').classes('text-sm')
                    ui.label('Использование памяти: 45%').classes('text-sm')
                    ui.label('Использование диска: 23%').classes('text-sm')
                    ui.label('Активных подключений: 2').classes('text-sm')
                
                with ui.row().classes('w-full gap-4 mt-4'):
                    ui.button('Перезапустить систему', on_click=self.restart_system).classes('bg-orange-500')
                    ui.button('Экспорт конфигурации', on_click=self.export_config).classes('bg-green-500')
                    ui.button('Импорт конфигурации', on_click=self.import_config).classes('bg-blue-500')
    
    def add_device(self, name, ip, port, unit_id, device_type):
        """Добавление нового устройства"""
        if not all([name, ip, port, unit_id]):
            ui.notify('Заполните все поля', type='negative')
            return
        
        # В реальной системе здесь будет сохранение в БД
        ui.notify(f'Устройство {name} добавлено', type='positive')
        logger.info(f"Добавлено устройство: {name} ({ip}:{port})")
    
    def add_user(self, username, password, role):
        """Добавление нового пользователя"""
        if not all([username, password, role]):
            ui.notify('Заполните все поля', type='negative')
            return
        
        # Хеширование пароля
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # В реальной системе здесь будет сохранение в БД
        ui.notify(f'Пользователь {username} добавлен', type='positive')
        logger.info(f"Добавлен пользователь: {username} с ролью {role}")
    
    def save_threshold(self, threshold_type, value):
        """Сохранение порогового значения"""
        if value is None:
            ui.notify('Введите значение', type='negative')
            return
        
        # В реальной системе здесь будет сохранение в конфигурацию
        ui.notify(f'Пороговое значение {threshold_type} сохранено: {value}', type='positive')
        logger.info(f"Сохранено пороговое значение {threshold_type}: {value}")
    
    def set_device_threshold(self, device, parameter, value):
        """Установка индивидуального порога для устройства"""
        if not all([device, parameter, value]):
            ui.notify('Заполните все поля', type='negative')
            return
        
        ui.notify(f'Индивидуальный порог для {device} установлен', type='positive')
        logger.info(f"Установлен индивидуальный порог для {device}: {parameter} = {value}")
    
    def save_system_setting(self, setting, value):
        """Сохранение системной настройки"""
        if value is None:
            ui.notify('Введите значение', type='negative')
            return
        
        ui.notify(f'Настройка {setting} сохранена: {value}', type='positive')
        logger.info(f"Сохранена системная настройка {setting}: {value}")
    
    def cleanup_old_data(self):
        """Очистка старых данных"""
        ui.notify('Очистка старых данных запущена', type='positive')
        logger.info("Запущена очистка старых данных")
    
    def restart_system(self):
        """Перезапуск системы"""
        ui.notify('Система будет перезапущена через 10 секунд', type='warning')
        logger.info("Запрошен перезапуск системы")
    
    def export_config(self):
        """Экспорт конфигурации"""
        # В реальной системе здесь будет генерация файла конфигурации
        config_data = {
            'devices': [],
            'thresholds': {},
            'system_settings': {}
        }
        
        import json
        config_json = json.dumps(config_data, indent=2, ensure_ascii=False)
        ui.download(config_json.encode(), 'system_config.json')
        ui.notify('Конфигурация экспортирована', type='positive')
    
    def import_config(self):
        """Импорт конфигурации"""
        ui.notify('Функция импорта конфигурации в разработке', type='info')
