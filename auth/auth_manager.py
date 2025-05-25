"""
Менеджер авторизации и аутентификации
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_sessions = {}  # session_id -> user_data
        self.session_timeout = timedelta(hours=8)  # 8 часов
        self._initialized = False

    async def initialize(self):
        """Инициализация менеджера авторизации"""
        if not self._initialized:
            # Убеждаемся что база данных инициализирована
            if not hasattr(self.db_manager, 'pool') or not self.db_manager.pool:
                await self.db_manager.initialize()
            self._initialized = True
            logger.info("AuthManager инициализирован")

    async def _ensure_initialized(self):
        """Убеждаемся что менеджер инициализирован"""
        if not self._initialized:
            await self.initialize()
    
    def generate_salt(self) -> str:
        """Генерация соли для пароля"""
        return secrets.token_hex(16)
    
    def hash_password(self, password: str, salt: str) -> str:
        """Хеширование пароля с солью"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация пользователя"""
        try:
            await self._ensure_initialized()
            
            # Получение пользователя из БД
            sql = '''
                SELECT 
                    user_id,
                    user_username,
                    user_full_name,
                    user_email,
                    user_role,
                    user_salt,
                    is_active,
                    failed_login_attempts,
                    locked_until
                FROM users
                WHERE user_username = %s AND is_active = TRUE
            '''
            
            async with self.db_manager.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if cursor is None:
                        logger.error("Не удалось создать курсор")
                    try:
                        await cursor.execute(sql, (username,))
                    except Exception as e:
                        logger.error(f"Ошибка выполнения SQL запроса: {e}")
                    user = await cursor.fetchone()
                    
                    if not user:
                        logger.warning(f"Попытка входа с несуществующим пользователем: {username}")
                        return None
                    
                    user_id, user_username, user_full_name, user_email, user_role, user_salt, is_active, failed_attempts, locked_until = user
                    
                    # Проверка блокировки аккаунта
                    if locked_until and locked_until > datetime.now():
                        logger.warning(f"Попытка входа заблокированным пользователем: {username}")
                        return None
                    
                    # Проверка пароля
                    password_hash = self.hash_password(password, user_salt)
                    
                    sql_check = '''
                        SELECT user_id FROM users 
                        WHERE user_username = %s AND user_password = %s
                    '''
                    
                    await cursor.execute(sql_check, (username, password_hash))
                    password_match = await cursor.fetchone()
                    
                    if password_match:
                        # Успешный вход - сброс счетчика неудачных попыток
                        await cursor.execute(
                            '''UPDATE users SET 
                               last_login = NOW(), 
                               failed_login_attempts = 0,
                               locked_until = NULL
                               WHERE user_id = %s''',
                            (user_id,)
                        )
                        
                        logger.info(f"Успешный вход пользователя: {username}")
                        
                        return {
                            'user_id': user_id,
                            'username': user_username,
                            'full_name': user_full_name,
                            'email': user_email,
                            'role': user_role,
                            'login_time': datetime.now()
                        }
                    else:
                        # Неудачная попытка входа
                        new_failed_attempts = failed_attempts + 1
                        
                        # Блокировка после 5 неудачных попыток
                        if new_failed_attempts >= 5:
                            lock_until = datetime.now() + timedelta(minutes=30)
                            await cursor.execute(
                                '''UPDATE users SET 
                                   failed_login_attempts = %s,
                                   locked_until = %s
                                   WHERE user_id = %s''',
                                (new_failed_attempts, lock_until, user_id)
                            )
                            logger.warning(f"Аккаунт {username} заблокирован на 30 минут")
                        else:
                            await cursor.execute(
                                '''UPDATE users SET failed_login_attempts = %s WHERE user_id = %s''',
                                (new_failed_attempts, user_id)
                            )
                        
                        logger.warning(f"Неудачная попытка входа: {username} (попытка {new_failed_attempts})")
                        return None
        
        except Exception as e:
            logger.error(f"Ошибка аутентификации пользователя {username}: {e}")
            return None
    
    def create_session(self, user_data: Dict[str, Any]) -> str:
        """Создание сессии пользователя"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            **user_data,
            'session_id': session_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        self.active_sessions[session_id] = session_data
        
        logger.info(f"Создана сессия для пользователя {user_data['username']}: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных сессии"""
        if not session_id or session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        # Проверка времени жизни сессии
        if datetime.now() - session_data['last_activity'] > self.session_timeout:
            self.destroy_session(session_id)
            return None
        
        # Обновление времени последней активности
        session_data['last_activity'] = datetime.now()
        return session_data
    
    def destroy_session(self, session_id: str):
        """Уничтожение сессии"""
        if session_id in self.active_sessions:
            username = self.active_sessions[session_id].get('username', 'Unknown')
            del self.active_sessions[session_id]
            logger.info(f"Сессия пользователя {username} завершена: {session_id}")
    
    def check_permission(self, session_data: Dict[str, Any], required_role: str) -> bool:
        """Проверка прав доступа"""
        if not session_data:
            return False
        
        user_role = session_data.get('role')
        
        # Иерархия ролей: admin > operator > viewer
        role_hierarchy = {
            'admin': 3,
            'operator': 2,
            'viewer': 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def cleanup_expired_sessions(self):
        """Очистка истекших сессий"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if current_time - session_data['last_activity'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.destroy_session(session_id)
        
        if expired_sessions:
            logger.info(f"Очищено {len(expired_sessions)} истекших сессий")
    
    async def create_user(self, username: str, password: str, full_name: str, 
                         email: str, role: str = 'viewer') -> bool:
        """Создание нового пользователя"""
        try:
            await self._ensure_initialized()
            
            if not self.db_manager.pool:
                logger.error("Пул подключений к базе данных не инициализирован")
                return False
            salt = self.generate_salt()
            password_hash = self.hash_password(password, salt)
            
            sql = '''
                INSERT INTO users (user_username, user_password, user_full_name, 
                                 user_email, user_role, user_salt)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            
            async with self.db_manager.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, (username, password_hash, full_name, email, role, salt))
            
            logger.info(f"Создан новый пользователь: {username} с ролью {role}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {username}: {e}")
            return False
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Изменение пароля пользователя"""
        try:
            await self._ensure_initialized()
            
            if not self.db_manager.pool:
                logger.error("Пул подключений к базе данных не инициализирован")
                return False
            # Получение текущих данных пользователя
            sql = 'SELECT user_salt, user_password FROM users WHERE user_id = %s'
            
            async with self.db_manager.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, (user_id,))
                    result = await cursor.fetchone()
                    
                    if not result:
                        return False
                    
                    current_salt, current_password_hash = result
                    
                    # Проверка старого пароля
                    old_password_hash = self.hash_password(old_password, current_salt)
                    if old_password_hash != current_password_hash:
                        return False
                    
                    # Установка нового пароля
                    new_salt = self.generate_salt()
                    new_password_hash = self.hash_password(new_password, new_salt)
                    
                    await cursor.execute(
                        'UPDATE users SET user_password = %s, user_salt = %s WHERE user_id = %s',
                        (new_password_hash, new_salt, user_id)
                    )
            
            logger.info(f"Пароль изменен для пользователя ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка изменения пароля для пользователя {user_id}: {e}")
            return False
