"""
إعدادات قاعدة البيانات
Database Configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """إعدادات قاعدة البيانات"""
    
    def __init__(self, config_file: str = "config/database_config.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """تحميل الإعدادات الافتراضية لقاعدة البيانات"""
        return {
            "database_type": "sqlite",
            "sqlite": {
                "database_path": "data/ps_system.db",
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "backup_retention_days": 30
            },
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "database": "ps_system",
                "user": "root",
                "password": "",
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "autocommit": True,
                "connection_timeout": 60,
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "backup_retention_days": 30,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": False,
                "ssl_disabled": True,
                "ssl_verify_cert": False,
                "ssl_verify_identity": False
            }
        }
    
    def _load_config(self):
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"تم تحميل إعدادات قاعدة البيانات من: {self.config_file}")
            else:
                self.save_config()
                logger.info(f"تم إنشاء ملف إعدادات قاعدة البيانات الافتراضي: {self.config_file}")
                
        except Exception as e:
            logger.error(f"خطأ في تحميل إعدادات قاعدة البيانات: {e}")
    
    def save_config(self) -> bool:
        """حفظ الإعدادات في الملف"""
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"تم حفظ إعدادات قاعدة البيانات في: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حفظ إعدادات قاعدة البيانات: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """تعيين قيمة إعداد"""
        try:
            self.config[key] = value
            logger.info(f"تم تعيين إعداد قاعدة البيانات {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تعيين إعداد قاعدة البيانات: {e}")
            return False
    
    def get_connection_string(self) -> str:
        """الحصول على سلسلة الاتصال"""
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                return f"sqlite:///{self.config['sqlite']['database_path']}"
            else:
                mysql_config = self.config['mysql']
                return f"mysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
        except Exception as e:
            logger.error(f"خطأ في إنشاء سلسلة الاتصال: {e}")
            return ""
    
    def get_connection_params(self) -> Dict[str, Any]:
        """الحصول على معاملات الاتصال"""
        if self.config.get('database_type', 'sqlite') == 'sqlite':
            return {
                'database_path': self.config['sqlite']['database_path']
            }
        else:
            mysql_config = self.config['mysql']
            return {
                'host': mysql_config['host'],
                'port': mysql_config['port'],
                'database': mysql_config['database'],
                'user': mysql_config['user'],
                'password': mysql_config['password'],
                'charset': mysql_config['charset'],
                'collation': mysql_config['collation'],
                'autocommit': mysql_config['autocommit'],
                'connection_timeout': mysql_config['connection_timeout']
            }
    
    def validate_config(self) -> Dict[str, Any]:
        """التحقق من صحة إعدادات قاعدة البيانات"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # التحقق من SQLite
                sqlite_config = self.config.get('sqlite', {})
                if not sqlite_config.get('database_path'):
                    validation_result['errors'].append("مسار قاعدة البيانات SQLite مطلوب")
                    validation_result['valid'] = False
                
                # التحقق من إعدادات النسخ الاحتياطي
                if sqlite_config.get('backup_enabled'):
                    backup_interval = sqlite_config.get('backup_interval_hours', 0)
                    if backup_interval <= 0:
                        validation_result['warnings'].append("فترة النسخ الاحتياطي غير صحيحة")
                    
                    retention_days = sqlite_config.get('backup_retention_days', 0)
                    if retention_days <= 0:
                        validation_result['warnings'].append("فترة الاحتفاظ بالنسخ الاحتياطية غير صحيحة")
            else:
                # التحقق من MySQL
                mysql_config = self.config.get('mysql', {})
                required_fields = ['host', 'port', 'database', 'user']
                for field in required_fields:
                    if not mysql_config.get(field):
                        validation_result['errors'].append(f"الحقل {field} مطلوب")
                        validation_result['valid'] = False
                
                # التحقق من المنفذ
                port = mysql_config.get('port', 0)
                if not isinstance(port, int) or port <= 0 or port > 65535:
                    validation_result['errors'].append("رقم المنفذ غير صحيح")
                    validation_result['valid'] = False
                
                # التحقق من timeout
                timeout = mysql_config.get('connection_timeout', 0)
                if not isinstance(timeout, int) or timeout <= 0:
                    validation_result['warnings'].append("مهلة الاتصال غير صحيحة")
                
                # التحقق من إعدادات النسخ الاحتياطي
                if mysql_config.get('backup_enabled'):
                    backup_interval = mysql_config.get('backup_interval_hours', 0)
                    if backup_interval <= 0:
                        validation_result['warnings'].append("فترة النسخ الاحتياطي غير صحيحة")
                    
                    retention_days = mysql_config.get('backup_retention_days', 0)
                    if retention_days <= 0:
                        validation_result['warnings'].append("فترة الاحتفاظ بالنسخ الاحتياطية غير صحيحة")
                
                # التحقق من إعدادات pool
                pool_size = mysql_config.get('pool_size', 0)
                if pool_size <= 0:
                    validation_result['warnings'].append("حجم pool غير صحيح")
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من إعدادات قاعدة البيانات: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append("خطأ في التحقق من الإعدادات")
        
        return validation_result
    
    def test_connection(self) -> Dict[str, Any]:
        """اختبار الاتصال بقاعدة البيانات"""
        test_result = {
            'success': False,
            'message': '',
            'connection_time': 0
        }
        
        try:
            import time
            
            start_time = time.time()
            
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # اختبار SQLite
                import sqlite3
                import os
                
                db_path = self.config['sqlite']['database_path']
                db_dir = os.path.dirname(db_path)
                
                # إنشاء المجلد إذا لم يكن موجوداً
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                # اختبار الاتصال
                connection = sqlite3.connect(db_path, timeout=30.0)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                connection.close()
                
                test_result['success'] = True
                test_result['message'] = "تم الاتصال بقاعدة البيانات SQLite بنجاح"
                test_result['connection_time'] = time.time() - start_time
                
            else:
                # اختبار MySQL
                import mysql.connector
                
                mysql_config = self.config['mysql']
                connection = mysql.connector.connect(
                    host=mysql_config['host'],
                    port=mysql_config['port'],
                    user=mysql_config['user'],
                    password=mysql_config['password'],
                    connection_timeout=mysql_config['connection_timeout']
                )
                
                if connection.is_connected():
                    test_result['success'] = True
                    test_result['message'] = "تم الاتصال بقاعدة البيانات MySQL بنجاح"
                    test_result['connection_time'] = time.time() - start_time
                    
                    # اختبار قاعدة البيانات
                    cursor = connection.cursor()
                    cursor.execute(f"USE {mysql_config['database']}")
                    cursor.close()
                    
                    connection.close()
                else:
                    test_result['message'] = "فشل في الاتصال"
                
        except Exception as e:
            test_result['message'] = f"خطأ في الاتصال: {e}"
        
        return test_result
    
    def create_database(self) -> bool:
        """إنشاء قاعدة البيانات إذا لم تكن موجودة"""
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # إنشاء مجلد قاعدة البيانات SQLite
                import os
                db_path = self.config['sqlite']['database_path']
                db_dir = os.path.dirname(db_path)
                
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"تم إنشاء مجلد قاعدة البيانات: {db_dir}")
                
                # إنشاء ملف قاعدة البيانات إذا لم يكن موجوداً
                if not os.path.exists(db_path):
                    import sqlite3
                    connection = sqlite3.connect(db_path)
                    connection.close()
                    logger.info(f"تم إنشاء قاعدة البيانات SQLite: {db_path}")
                
                return True
            else:
                # إنشاء قاعدة البيانات MySQL
                import mysql.connector
                
                mysql_config = self.config['mysql']
                # الاتصال بدون تحديد قاعدة البيانات
                connection = mysql.connector.connect(
                    host=mysql_config['host'],
                    port=mysql_config['port'],
                    user=mysql_config['user'],
                    password=mysql_config['password']
                )
                
                cursor = connection.cursor()
                
                # إنشاء قاعدة البيانات
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']} CHARACTER SET {mysql_config['charset']} COLLATE {mysql_config['collation']}")
                
                cursor.close()
                connection.close()
                
                logger.info(f"تم إنشاء قاعدة البيانات MySQL: {mysql_config['database']}")
                return True
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء قاعدة البيانات: {e}")
            return False
    
    def get_backup_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات النسخ الاحتياطي"""
        if self.config.get('database_type', 'sqlite') == 'sqlite':
            sqlite_config = self.config.get('sqlite', {})
            return {
                'enabled': sqlite_config.get('backup_enabled', True),
                'interval_hours': sqlite_config.get('backup_interval_hours', 24),
                'retention_days': sqlite_config.get('backup_retention_days', 30)
            }
        else:
            mysql_config = self.config.get('mysql', {})
            return {
                'enabled': mysql_config.get('backup_enabled', True),
                'interval_hours': mysql_config.get('backup_interval_hours', 24),
                'retention_days': mysql_config.get('backup_retention_days', 30)
            }
    
    def get_pool_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات pool الاتصالات"""
        if self.config.get('database_type', 'sqlite') == 'sqlite':
            # SQLite لا يحتاج pool settings
            return {}
        else:
            mysql_config = self.config.get('mysql', {})
            return {
                'pool_size': mysql_config.get('pool_size', 10),
                'max_overflow': mysql_config.get('max_overflow', 20),
                'pool_timeout': mysql_config.get('pool_timeout', 30),
                'pool_recycle': mysql_config.get('pool_recycle', 3600)
            }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """تحديث إعدادات قاعدة البيانات"""
        try:
            self.config.update(new_config)
            return self.save_config()
        except Exception as e:
            logger.error(f"خطأ في تحديث إعدادات قاعدة البيانات: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """إعادة تعيين الإعدادات إلى الافتراضية"""
        try:
            self.config = self._load_default_config()
            return self.save_config()
        except Exception as e:
            logger.error(f"خطأ في إعادة تعيين إعدادات قاعدة البيانات: {e}")
            return False

# إنشاء مثيل عام لإعدادات قاعدة البيانات
database_config = DatabaseConfig()

def get_database_config() -> DatabaseConfig:
    """الحصول على مثيل إعدادات قاعدة البيانات"""
    return database_config
