"""
Скрипт установки и настройки системы
"""
import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error

def install_requirements():
    """Установка зависимостей"""
    print("Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Зависимости установлены успешно")
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка установки зависимостей: {e}")
        return False
    return True

def create_database():
    """Создание базы данных"""
    print("Создание базы данных...")
    
    # Параметры подключения (настройте под вашу систему)
    host = input("Введите хост MySQL (по умолчанию localhost): ") or "localhost"
    port = input("Введите порт MySQL (по умолчанию 3306): ") or "3306"
    username = input("Введите имя пользователя MySQL: ")
    password = input("Введите пароль MySQL: ")
    
    try:
        # Подключение к MySQL
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            user=username,
            password=password
        )
        
        cursor = connection.cursor()
        
        # Создание базы данных
        cursor.execute("CREATE DATABASE IF NOT EXISTS energy_monitoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✓ База данных создана успешно")
        
        # Создание пользователя для приложения (опционально)
        app_user = input("Создать отдельного пользователя для приложения? (y/n): ")
        if app_user.lower() == 'y':
            app_username = input("Имя пользователя приложения: ")
            app_password = input("Пароль пользователя приложения: ")
            
            cursor.execute(f"CREATE USER IF NOT EXISTS '{app_username}'@'%' IDENTIFIED BY '{app_password}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON energy_monitoring.* TO '{app_username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"✓ Пользователь {app_username} создан")
        
        cursor.close()
        connection.close()
        
        # Обновление конфигурации
        update_config(host, port, username if app_user.lower() != 'y' else app_username, 
                     password if app_user.lower() != 'y' else app_password)
        
    except Error as e:
        print(f"✗ Ошибка создания базы данных: {e}")
        return False
    
    return True

def update_config(host, port, username, password):
    """Обновление конфигурации"""
    config_content = f'''"""
Конфигурация системы (автоматически сгенерирована)
"""
import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ModbusDevice:
    name: str
    ip_address: str
    port: int
    unit_id: int
    device_type: str

@dataclass
class DatabaseConfig:
    host: str = '{host}'
    port: int = {port}
    database: str = 'energy_monitoring'
    username: str = '{username}'
    password: str = '{password}'

class Settings:
    def __init__(self):
        self.COLLECTION_INTERVAL = 5
        self.DATABASE = DatabaseConfig()
        
        # Настройте ваши устройства здесь
        self.MODBUS_DEVICES = [
            ModbusDevice(
                name="Счетчик Меркурий 1",
                ip_address="192.168.1.100",
                port=502,
                unit_id=1,
                device_type="meter"
            ),
            ModbusDevice(
                name="ПЛК ОВЕН 1",
                ip_address="192.168.1.101",
                port=502,
                unit_id=2,
                device_type="plc"
            )
        ]
        
        self.THRESHOLDS = {{
            'max_power': 1000.0,
            'max_current': 100.0,
            'min_voltage': 200.0,
            'max_voltage': 250.0
        }}
        
        self.MERCURY_REGISTERS = {{
            'active_power': 0x0000,
            'reactive_power': 0x0002,
            'voltage_l1': 0x0004,
            'voltage_l2': 0x0006,
            'voltage_l3': 0x0008,
            'current_l1': 0x000A,
            'current_l2': 0x000C,
            'current_l3': 0x000E
        }}
        
        self.OVEN_REGISTERS = {{
            'equipment_status': 0x0100,
            'discrete_inputs': 0x0200
        }}
'''
    
    with open('config/settings.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✓ Конфигурация обновлена")

def create_directories():
    """Создание необходимых директорий"""
    directories = [
        'config',
        'database',
        'data_collection',
        'data_processing',
        'analysis',
        'web_interface',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✓ Директории созданы")

def create_service_file():
    """Создание файла службы для systemd (Linux)"""
    if sys.platform.startswith('linux'):
        service_content = f'''[Unit]
Description=Energy Monitoring System
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
        
        try:
            with open('/tmp/energy-monitoring.service', 'w') as f:
                f.write(service_content)
            
            print("✓ Файл службы создан в /tmp/energy-monitoring.service")
            print("  Для установки выполните:")
            print("  sudo cp /tmp/energy-monitoring.service /etc/systemd/system/")
            print("  sudo systemctl enable energy-monitoring")
            print("  sudo systemctl start energy-monitoring")
        except Exception as e:
            print(f"⚠ Не удалось создать файл службы: {e}")

def main():
    """Основная функция установки"""
    print("=== Установка системы мониторинга энергопотребления ===")
    print()
    
    # Создание директорий
    create_directories()
    
    # Установка зависимостей
    if not install_requirements():
        print("Установка прервана из-за ошибок")
        return
    
    # Настройка базы данных
    setup_db = input("Настроить базу данных? (y/n): ")
    if setup_db.lower() == 'y':
        if not create_database():
            print("Установка прервана из-за ошибок БД")
            return
    
    # Создание службы
    create_service = input("Создать файл службы для автозапуска? (y/n): ")
    if create_service.lower() == 'y':
        create_service_file()
    
    print()
    print("=== Установка завершена ===")
    print("Для запуска системы выполните: python main.py")
    print("Веб-интерфейс будет доступен по адресу: http://localhost:8080")
    print()
    print("Не забудьте:")
    print("1. Настроить IP-адреса устройств в config/settings.py")
    print("2. Проверить подключение к устройствам Modbus")
    print("3. Настроить пороговые значения в веб-интерфейсе")

if __name__ == "__main__":
    main()
