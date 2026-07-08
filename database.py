"""
نظام إدارة محل بلايستيشن - إدارة قاعدة البيانات
Database Management for PlayStation Shop Management System
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict, Any, Tuple
import threading
import time
import shutil

# إعداد نظام السجلات مع RotatingFileHandler
# الحد الأقصى: 5 ميجابايت، عدد النسخ الاحتياطية: 5 ملفات
db_log_handler = RotatingFileHandler(
    'ps_system.log',
    maxBytes=5 * 1024 * 1024,  # 5 ميجابايت
    backupCount=5,  # 5 نسخ احتياطية
    encoding='utf-8'
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        db_log_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات الرئيسي"""
    
    def __init__(self, config_file: str = "config/database_config.json"):
        self.config_file = config_file
        self.connection = None
        self.cursor = None
        self.lock = threading.Lock()
        self.config = self._load_config()
        self._connect()
        
    def _load_config(self) -> Dict[str, Any]:
        """تحميل إعدادات قاعدة البيانات"""
        default_config = {
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
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # دمج الإعدادات الافتراضية مع المحملة
                    default_config.update(config)
            else:
                # إنشاء ملف الإعدادات الافتراضي
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                logger.info(f"تم إنشاء ملف الإعدادات الافتراضي: {self.config_file}")
                
        except Exception as e:
            logger.error(f"خطأ في تحميل إعدادات قاعدة البيانات: {e}")
            
        return default_config
    
    def _convert_mysql_to_sqlite(self, query: str) -> str:
        """تحويل MySQL syntax إلى SQLite syntax"""
        try:
            import re
            
            # تحويل AUTO_INCREMENT إلى INTEGER PRIMARY KEY AUTOINCREMENT
            query = re.sub(r'INT\s+AUTO_INCREMENT\s+PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', query)
            
            # تحويل ENUM إلى TEXT مع CHECK constraint
            enum_pattern = r"ENUM\s*\([^)]+\)"
            query = re.sub(enum_pattern, 'TEXT', query)
            
            # تحويل TIMESTAMP إلى DATETIME
            query = query.replace('TIMESTAMP', 'DATETIME')
            
            # تحويل DEFAULT CURRENT_TIMESTAMP
            query = query.replace('DEFAULT CURRENT_TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP')
            
            # تحويل DEFAULT CURRENT_DATETIME
            query = query.replace('DEFAULT CURRENT_DATETIME', 'DEFAULT CURRENT_TIMESTAMP')
            
            # تحويل ON UPDATE CURRENT_TIMESTAMP
            query = query.replace('ON UPDATE CURRENT_TIMESTAMP', '')
            query = query.replace('ON UPDATE CURRENT_DATETIME', '')
            
            # تحويل BOOLEAN إلى INTEGER
            query = query.replace('BOOLEAN', 'INTEGER')
            
            # تحويل TRUE/FALSE إلى 1/0
            query = query.replace('DEFAULT TRUE', 'DEFAULT 1')
            query = query.replace('DEFAULT FALSE', 'DEFAULT 0')
            
            # إزالة ENGINE و CHARSET
            query = re.sub(r'ENGINE=\w+[^;]*', '', query)
            query = re.sub(r'DEFAULT CHARSET=\w+[^;]*', '', query)
            query = re.sub(r'COLLATE=\w+[^;]*', '', query)
            
            # إزالة INDEX definitions (سيتم إنشاؤها منفصلة)
            query = re.sub(r',\s*INDEX\s+\w+\s*\([^)]+\)', '', query)
            
            # إزالة FOREIGN KEY constraints (سيتم إنشاؤها منفصلة)
            query = re.sub(r',\s*FOREIGN KEY\s+\([^)]+\)\s+REFERENCES\s+\w+\([^)]+\)\s+ON DELETE\s+\w+', '', query)
            
            return query
            
        except Exception as e:
            logger.error(f"خطأ في تحويل MySQL إلى SQLite: {e}")
            return query
    
    def _connect(self) -> bool:
        """إنشاء اتصال بقاعدة البيانات"""
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # استخدام SQLite
                db_path = self.config['sqlite']['database_path']
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                self.connection = sqlite3.connect(
                    db_path,
                    check_same_thread=False,
                    timeout=30.0,
                    isolation_level=None  # تفعيل autocommit mode للحصول على أحدث البيانات فوراً
                )
                self.connection.row_factory = sqlite3.Row  # للحصول على نتائج كـ dictionary
                self.cursor = self.connection.cursor()
                
                # تفعيل المفاتيح الخارجية
                self.cursor.execute("PRAGMA foreign_keys = ON")
                # إضافة PRAGMA لتحسين الأداء والاستجابة
                self.cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging للقراءة السريعة
                self.cursor.execute("PRAGMA synchronous = NORMAL")  # التوازن بين الأمان والسرعة
                
                logger.info(f"تم الاتصال بقاعدة البيانات SQLite بنجاح: {db_path}")
                return True
            else:
                # استخدام MySQL (للتوافق مع الإصدارات القديمة)
                import mysql.connector
                from mysql.connector import Error
                
                mysql_config = self.config['mysql']
                self.connection = mysql.connector.connect(
                    host=mysql_config['host'],
                    port=mysql_config['port'],
                    database=mysql_config['database'],
                    user=mysql_config['user'],
                    password=mysql_config['password'],
                    charset=mysql_config['charset'],
                    collation=mysql_config['collation'],
                    autocommit=mysql_config['autocommit'],
                    connection_timeout=mysql_config['connection_timeout']
                )
                
                if self.connection.is_connected():
                    self.cursor = self.connection.cursor(dictionary=True, buffered=True)
                    logger.info("تم الاتصال بقاعدة البيانات MySQL بنجاح")
                    return True
                
        except Exception as e:
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            return False
            
        return False
    
    def reconnect(self) -> bool:
        """إعادة الاتصال بقاعدة البيانات"""
        try:
            if self.connection:
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    self.connection.close()
                else:
                    if hasattr(self.connection, 'is_connected') and self.connection.is_connected():
                        self.connection.close()
            return self._connect()
        except Exception as e:
            logger.error(f"خطأ في إعادة الاتصال: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch: bool = True) -> Optional[List[Dict]]:
        """تنفيذ استعلام قاعدة البيانات"""
        with self.lock:
            try:
                logger.info(f"تنفيذ استعلام: {query}")
                logger.info(f"المعاملات: {params}")
                logger.info(f"fetch: {fetch}")
                
                # التحقق من الاتصال
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    if not self.connection:
                        if not self.reconnect():
                            raise Exception("فشل في إعادة الاتصال بقاعدة البيانات")
                else:
                    if not self.connection or not self.connection.is_connected():
                        if not self.reconnect():
                            raise Exception("فشل في إعادة الاتصال بقاعدة البيانات")
                
                # تحويل MySQL syntax إلى SQLite syntax
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    query = self._convert_mysql_to_sqlite(query)
                
                if params is not None:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                
                if fetch:
                    result = self.cursor.fetchall()
                    # تحويل النتائج إلى dictionary
                    if self.config.get('database_type', 'sqlite') == 'sqlite':
                        result = [dict(row) for row in result]
                    logger.info(f"نتيجة الاستعلام: {result}")
                    return result
                else:
                    # ⭐⭐⭐ EXE FIX: commit صريح حتى مع autocommit mode ⭐⭐⭐
                    # في autocommit mode (isolation_level=None)، التغييرات تُحفظ تلقائياً
                    # لكن نضيف commit صريح للتأكد المطلق في exe
                    try:
                        self.connection.commit()
                        logger.debug("✅ تم عمل commit صريح للتحديث")
                    except Exception as commit_error:
                        # في حالة autocommit mode، قد يفشل commit لكن التغييرات محفوظة
                        logger.debug(f"⚠️ commit فشل (قد يكون autocommit نشط): {commit_error}")
                    
                    result = self.cursor.lastrowid if self.cursor.lastrowid else True
                    logger.info(f"نتيجة التحديث: {result}")
                    return result
                    
            except Exception as e:
                logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
                logger.error(f"الاستعلام: {query}")
                logger.error(f"المعاملات: {params}")
                if self.connection:
                    try:
                        self.connection.rollback()
                    except:
                        pass  # في autocommit mode، rollback قد لا يعمل
                raise e
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """تنفيذ استعلام متعدد"""
        with self.lock:
            try:
                # التحقق من الاتصال
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    if not self.connection:
                        if not self.reconnect():
                            raise Exception("فشل في إعادة الاتصال بقاعدة البيانات")
                else:
                    if not self.connection or not self.connection.is_connected():
                        if not self.reconnect():
                            raise Exception("فشل في إعادة الاتصال بقاعدة البيانات")
                
                # تحويل MySQL syntax إلى SQLite syntax
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    query = self._convert_mysql_to_sqlite(query)
                
                self.cursor.executemany(query, params_list)
                self.connection.commit()
                return True
                
            except Exception as e:
                logger.error(f"خطأ في تنفيذ الاستعلام المتعدد: {e}")
                if self.connection:
                    self.connection.rollback()
                raise e
    
    def create_tables(self) -> bool:
        """إنشاء جداول قاعدة البيانات"""
        try:
            # جدول المستخدمين
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL DEFAULT 'cashier' CHECK (role IN ('admin', 'cashier')),
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT UNIQUE,
                email TEXT,
                password_hash TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_by INTEGER,
                last_login TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # جدول الأجهزة
            devices_table = """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('PS', 'PC', 'PingPong', 'Billiard')),
                price_single REAL NOT NULL DEFAULT 0.00,
                price_multi REAL NOT NULL DEFAULT 0.00,
                status TEXT DEFAULT 'available' CHECK (status IN ('available', 'busy', 'maintenance', 'disabled')),
                current_session_id INTEGER NULL,
                current_invoice_id INTEGER NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            
            # جدول الورديات
            shifts_table = """
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cashier_id INTEGER NOT NULL,
                shift_name TEXT DEFAULT '',
                start_time TEXT NOT NULL,
                end_time TEXT NULL,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cashier_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
            
            # جدول الجلسات الجديد
            sessions_table = """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                cashier_id INTEGER NOT NULL,
                shift_id INTEGER NOT NULL,
                pricing_type TEXT NOT NULL CHECK (pricing_type IN ('single', 'multi')),
                session_price REAL NOT NULL DEFAULT 0.00,
                time_type TEXT NOT NULL DEFAULT 'fixed' CHECK (time_type IN ('fixed', 'open')),
                duration_minutes INTEGER NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NULL,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'paused')),
                is_paused INTEGER DEFAULT 0,
                paused_at TEXT NULL,
                total_paused_duration INTEGER DEFAULT 0,
                customer_phone TEXT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                FOREIGN KEY (cashier_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE
            )
            """
            
            # جدول تتبع التسعيرة المتقدمة
            pricing_segments_table = """
            CREATE TABLE IF NOT EXISTS pricing_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                pricing_type TEXT NOT NULL CHECK (pricing_type IN ('single', 'multi')),
                session_price REAL NOT NULL DEFAULT 0.00,
                start_time TEXT NOT NULL,
                end_time TEXT NULL,
                duration_seconds INTEGER DEFAULT 0,
                paused_duration_seconds INTEGER DEFAULT 0,
                actual_duration_seconds INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.00,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """
            
            # جدول الفواتير
            invoices_table = """
            CREATE TABLE IF NOT EXISTS invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device_id INT NOT NULL,
                session_id INT NULL,
                cashier_open INT NOT NULL,
                cashier_close INT NULL,
                shift_id INT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NULL,
                pricing_type ENUM('single', 'multi', 'mixed') NOT NULL,
                session_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                products_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                customer_phone VARCHAR(20) NULL,
                paid_by ENUM('cash', 'customer_balance') DEFAULT 'cash',
                created_by INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_by INT NULL,
                modified_at TIMESTAMP NULL,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                FOREIGN KEY (cashier_open) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (cashier_close) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (modified_by) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_device (device_id),
                INDEX idx_session (session_id),
                INDEX idx_cashier_open (cashier_open),
                INDEX idx_cashier_close (cashier_close),
                INDEX idx_shift (shift_id),
                INDEX idx_start_time (start_time),
                INDEX idx_end_time (end_time),
                INDEX idx_customer_phone (customer_phone),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول المنتجات
            products_table = """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock_quantity INT NOT NULL DEFAULT 0,
                category ENUM('drink', 'food') NOT NULL,
                min_stock_level INT DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_stock (stock_quantity),
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول العملاء
            customers_table = """
            CREATE TABLE IF NOT EXISTS customers (
                phone VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_balance (balance)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول المصروفات
            expenses_table = """
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(10,2) NOT NULL,
                reason VARCHAR(255) NOT NULL,
                cashier_id INT NOT NULL,
                shift_id INT NOT NULL,
                date_time DATETIME NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cashier_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE,
                INDEX idx_cashier (cashier_id),
                INDEX idx_shift (shift_id),
                INDEX idx_date_time (date_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول سجل التدقيق
            audit_log_table = """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NOT NULL,
                action VARCHAR(50) NOT NULL,
                performed_by INT NOT NULL,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason VARCHAR(255),
                old_value JSON,
                new_value JSON,
                FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_entity (entity_type, entity_id),
                INDEX idx_performed_by (performed_by),
                INDEX idx_performed_at (performed_at),
                INDEX idx_action (action)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول تفاصيل الفواتير (المنتجات المباعة)
            invoice_items_table = """
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                INDEX idx_invoice (invoice_id),
                INDEX idx_product (product_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول معاملات العملاء
            customer_transactions_table = """
            CREATE TABLE IF NOT EXISTS customer_transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_phone VARCHAR(20) NOT NULL,
                operation ENUM('add', 'subtract') NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                old_balance DECIMAL(10,2) NOT NULL,
                new_balance DECIMAL(10,2) NOT NULL,
                cashier_id INT NOT NULL,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_phone) REFERENCES customers(phone) ON DELETE CASCADE,
                FOREIGN KEY (cashier_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_customer_phone (customer_phone),
                INDEX idx_cashier (cashier_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول منتجات الجلسات
            session_products_table = """
            CREATE TABLE IF NOT EXISTS session_products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                INDEX idx_session (session_id),
                INDEX idx_product (product_id),
                INDEX idx_added_at (added_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # جدول صلاحيات المستخدمين
            user_permissions_table = """
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_key TEXT NOT NULL,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                granted_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(user_id, permission_key)
            )
            """
            
            # جدول الموظفين
            employees_table = """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                national_id TEXT UNIQUE,
                address TEXT,
                position TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                monthly_salary REAL NOT NULL DEFAULT 0.00,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # جدول سلف الموظفين
            employee_advances_table = """
            CREATE TABLE IF NOT EXISTS employee_advances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                reason TEXT,
                paid_back INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # جدول خصومات الموظفين
            employee_deductions_table = """
            CREATE TABLE IF NOT EXISTS employee_deductions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                reason TEXT NOT NULL,
                deduction_type TEXT DEFAULT 'other' CHECK (deduction_type IN ('absence', 'lateness', 'damage', 'other')),
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # جدول ساعات العمل الإضافية
            employee_overtime_table = """
            CREATE TABLE IF NOT EXISTS employee_overtime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                hours REAL NOT NULL,
                hourly_rate REAL NOT NULL,
                total_amount REAL NOT NULL,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # جدول سجل رواتب الموظفين
            employee_salary_records_table = """
            CREATE TABLE IF NOT EXISTS employee_salary_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                base_salary REAL NOT NULL,
                overtime_amount REAL DEFAULT 0.00,
                advances_amount REAL DEFAULT 0.00,
                deductions_amount REAL DEFAULT 0.00,
                net_salary REAL NOT NULL,
                payment_date TEXT,
                paid INTEGER DEFAULT 0,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(employee_id, month, year)
            )
            """
            
            # جدول المصاريف الإدارية
            administrative_expenses_table = """
            CREATE TABLE IF NOT EXISTS administrative_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_type TEXT NOT NULL CHECK (expense_type IN ('rent', 'electricity', 'water', 'gas', 'internet', 'phone', 'maintenance', 'taxes', 'fees', 'insurance', 'other')),
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurrence_period TEXT CHECK (recurrence_period IN ('monthly', 'quarterly', 'yearly') OR recurrence_period IS NULL),
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """
            
            # تنفيذ إنشاء الجداول
            tables = [
                users_table,
                devices_table,
                shifts_table,
                sessions_table,
                pricing_segments_table,
                invoices_table,
                products_table,
                customers_table,
                expenses_table,
                audit_log_table,
                invoice_items_table,
                customer_transactions_table,
                session_products_table,
                user_permissions_table,
                employees_table,
                employee_advances_table,
                employee_deductions_table,
                employee_overtime_table,
                employee_salary_records_table,
                administrative_expenses_table
            ]
            
            for table_sql in tables:
                self.execute_query(table_sql, fetch=False)
            
            logger.info("تم إنشاء جميع جداول قاعدة البيانات بنجاح")
            
            # إنشاء المستخدم الافتراضي
            self._create_default_admin()
            
            # إدراج بيانات تجريبية - معطل
            # self._insert_sample_data()
            
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء جداول قاعدة البيانات: {e}")
            return False
    
    def update_database_schema(self) -> bool:
        """تحديث هيكل قاعدة البيانات"""
        try:
            logger.info("بدء تحديث هيكل قاعدة البيانات...")
            
            # التحقق من وجود الأعمدة الجديدة في جدول المستخدمين
            columns_to_add = [
                ("full_name", "VARCHAR(100)"),
                ("email", "VARCHAR(100)"),
                ("is_active", "BOOLEAN DEFAULT TRUE"),
                ("notes", "TEXT"),
                ("created_by", "INT")
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    # التحقق من وجود العمود
                    result = self.execute_query(
                        f"PRAGMA table_info(users)",
                        fetch=True
                    )
                    
                    column_exists = any(col['name'] == column_name for col in result)
                    
                    if not column_exists:
                        # إضافة العمود
                        self.execute_query(
                            f"ALTER TABLE users ADD COLUMN {column_name} {column_type}",
                            fetch=False
                        )
                        logger.info(f"تم إضافة العمود {column_name} إلى جدول users")
                    
                except Exception as e:
                    logger.warning(f"خطأ في إضافة العمود {column_name}: {e}")
                    continue
            
            # تحديث جدول الأجهزة لدعم الجلسات الجديدة
            try:
                # التحقق من وجود العمود current_session_id
                result = self.execute_query(
                    "PRAGMA table_info(devices)",
                    fetch=True
                )
                
                session_id_exists = any(col['name'] == 'current_session_id' for col in result)
                
                if not session_id_exists:
                    # إضافة العمود
                    self.execute_query(
                        "ALTER TABLE devices ADD COLUMN current_session_id INT NULL",
                        fetch=False
                    )
                    logger.info("تم إضافة العمود current_session_id إلى جدول devices")
                
                # تحديث حالة الأجهزة من 'occupied' إلى 'busy'
                self.execute_query(
                    "UPDATE devices SET status = 'busy' WHERE status = 'occupied'",
                    fetch=False
                )
                logger.info("تم تحديث حالة الأجهزة من 'occupied' إلى 'busy'")
                
            except Exception as e:
                logger.warning(f"خطأ في تحديث جدول الأجهزة: {e}")
            
            # تحديث جدول الجلسات لدعم الوظائف الجديدة
            try:
                # التحقق من وجود الأعمدة الجديدة في جدول الجلسات
                result = self.execute_query(
                    "PRAGMA table_info(sessions)",
                    fetch=True
                )
                
                session_columns_to_add = [
                    ("is_paused", "INTEGER DEFAULT 0"),
                    ("paused_at", "DATETIME NULL"),
                    ("total_paused_duration", "INTEGER DEFAULT 0")
                ]
                
                for column_name, column_type in session_columns_to_add:
                    column_exists = any(col['name'] == column_name for col in result)
                    
                    if not column_exists:
                        # إضافة العمود
                        self.execute_query(
                            f"ALTER TABLE sessions ADD COLUMN {column_name} {column_type}",
                            fetch=False
                        )
                        logger.info(f"تم إضافة العمود {column_name} إلى جدول sessions")
                
                # إضافة فهرس للعمود الجديد
                try:
                    self.execute_query(
                        "CREATE INDEX IF NOT EXISTS idx_is_paused ON sessions(is_paused)",
                        fetch=False
                    )
                except Exception as e:
                    logger.warning(f"خطأ في إضافة فهرس is_paused: {e}")
                
            except Exception as e:
                logger.warning(f"خطأ في تحديث جدول الجلسات: {e}")
            
            # إضافة الفهارس الجديدة
            try:
                self.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_is_active ON users(is_active)",
                    fetch=False
                )
                self.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_current_session ON devices(current_session_id)",
                    fetch=False
                )
            except Exception as e:
                logger.warning(f"خطأ في إضافة الفهارس: {e}")
            
            logger.info("تم تحديث هيكل قاعدة البيانات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديث هيكل قاعدة البيانات: {e}")
            return False
    
    def _create_default_admin(self):
        """إنشاء المستخدم الافتراضي (المدير)"""
        try:
            # التحقق من وجود مدير
            admin_exists = self.execute_query(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            )
            
            if not admin_exists:
                try:
                    from utils.security import hash_password
                    password_hash = hash_password('admin123')
                except Exception as import_error:
                    logger.error(f"خطأ في استيراد hash_password: {import_error}")
                    # استخدام hashlib كبديل
                    import hashlib
                    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
                
                # إنشاء مدير افتراضي
                result = self.execute_query(
                    """INSERT INTO users (role, username, phone, password_hash, enabled) 
                       VALUES (?, ?, ?, ?, ?)""",
                    ('admin', 'admin', '01234567890', password_hash, 1),
                    fetch=False
                )
                
                if result:
                    logger.info("تم إنشاء المستخدم الافتراضي (admin/admin123)")
                else:
                    logger.error("فشل في إنشاء المستخدم الافتراضي")
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء المستخدم الافتراضي: {e}")
            import traceback
            traceback.print_exc()
    
    def _insert_sample_data(self):
        """إدراج بيانات تجريبية"""
        try:
            # التحقق من وجود بيانات
            devices_count = self.execute_query("SELECT COUNT(*) as count FROM devices")
            if devices_count and devices_count[0]['count'] > 0:
                logger.info("البيانات التجريبية موجودة بالفعل")
                return
            
            # تم حذف البيانات التجريبية للأجهزة
            # sample_devices = []
            
            # إدراج منتجات تجريبية
            sample_products = [
                ('كوكا كولا', 5.00, 50, 'drink'),
                ('بيبسي', 5.00, 50, 'drink'),
                ('مياه معدنية', 2.00, 100, 'drink'),
                ('عصير برتقال', 8.00, 30, 'drink'),
                ('شيبس', 3.00, 40, 'food'),
                ('شوكولاتة', 4.00, 25, 'food'),
                ('ساندويتش', 15.00, 20, 'food'),
                ('بيتزا صغيرة', 25.00, 15, 'food'),
            ]
            
            for product in sample_products:
                result = self.execute_query(
                    """INSERT INTO products (name, price, stock_quantity, category) 
                       VALUES (?, ?, ?, ?)""",
                    product,
                    fetch=False
                )
                if not result:
                    logger.error(f"فشل في إدراج المنتج: {product[0]}")
            
            logger.info("تم إدراج البيانات التجريبية بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ في إدراج البيانات التجريبية: {e}")
            import traceback
            traceback.print_exc()
    
    def backup_database(self, backup_path: str = None) -> bool:
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            if not backup_path:
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    backup_path = f"{backup_dir}/ps_system_backup_{timestamp}.db"
                else:
                    backup_path = f"{backup_dir}/ps_system_backup_{timestamp}.sql"
            
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # نسخ ملف SQLite
                source_path = self.config['sqlite']['database_path']
                if os.path.exists(source_path):
                    shutil.copy2(source_path, backup_path)
                    logger.info(f"تم إنشاء النسخة الاحتياطية SQLite: {backup_path}")
                    return True
                else:
                    logger.error(f"ملف قاعدة البيانات غير موجود: {source_path}")
                    return False
            else:
                # استخدام mysqldump لإنشاء النسخة الاحتياطية
                import subprocess
                
                mysql_config = self.config['mysql']
                cmd = [
                    'mysqldump',
                    f'--host={mysql_config["host"]}',
                    f'--port={mysql_config["port"]}',
                    f'--user={mysql_config["user"]}',
                    f'--password={mysql_config["password"]}',
                    '--single-transaction',
                    '--routines',
                    '--triggers',
                    '--events',
                    mysql_config['database']
                ]
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                
                if result.returncode == 0:
                    logger.info(f"تم إنشاء النسخة الاحتياطية MySQL: {backup_path}")
                    return True
                else:
                    logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {result.stderr}")
                    return False
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                # نسخ ملف SQLite
                target_path = self.config['sqlite']['database_path']
                if os.path.exists(backup_path):
                    # إغلاق الاتصال الحالي
                    if self.connection:
                        self.connection.close()
                    
                    # نسخ الملف
                    shutil.copy2(backup_path, target_path)
                    
                    # إعادة الاتصال
                    self._connect()
                    
                    logger.info(f"تم استعادة قاعدة البيانات SQLite من: {backup_path}")
                    return True
                else:
                    logger.error(f"ملف النسخة الاحتياطية غير موجود: {backup_path}")
                    return False
            else:
                # استخدام mysql لاستعادة النسخة الاحتياطية
                import subprocess
                
                mysql_config = self.config['mysql']
                cmd = [
                    'mysql',
                    f'--host={mysql_config["host"]}',
                    f'--port={mysql_config["port"]}',
                    f'--user={mysql_config["user"]}',
                    f'--password={mysql_config["password"]}',
                    mysql_config['database']
                ]
                
                with open(backup_path, 'r', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
                
                if result.returncode == 0:
                    logger.info(f"تم استعادة قاعدة البيانات MySQL من: {backup_path}")
                    return True
                else:
                    logger.error(f"خطأ في استعادة قاعدة البيانات: {result.stderr}")
                    return False
                
        except Exception as e:
            logger.error(f"خطأ في استعادة قاعدة البيانات: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """الحصول على حالة الاتصال"""
        try:
            if self.config.get('database_type', 'sqlite') == 'sqlite':
                if self.connection:
                    return {
                        'connected': True,
                        'database_type': 'SQLite',
                        'database_path': self.config['sqlite']['database_path'],
                        'server_version': sqlite3.sqlite_version
                    }
                else:
                    return {'connected': False, 'database_type': 'SQLite'}
            else:
                if self.connection and self.connection.is_connected():
                    mysql_config = self.config['mysql']
                    return {
                        'connected': True,
                        'database_type': 'MySQL',
                        'host': mysql_config['host'],
                        'database': mysql_config['database'],
                        'user': mysql_config['user'],
                        'server_version': self.connection.get_server_info()
                    }
                else:
                    return {'connected': False, 'database_type': 'MySQL'}
        except Exception as e:
            logger.error(f"خطأ في الحصول على حالة الاتصال: {e}")
            return {'connected': False, 'error': str(e)}
    
    def close_connection(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                if self.config.get('database_type', 'sqlite') == 'sqlite':
                    self.connection.close()
                else:
                    if hasattr(self.connection, 'is_connected') and self.connection.is_connected():
                        self.connection.close()
            logger.info("تم إغلاق الاتصال بقاعدة البيانات")
        except Exception as e:
            logger.error(f"خطأ في إغلاق الاتصال: {e}")
    
    def __del__(self):
        """إغلاق الاتصال عند حذف الكائن"""
        self.close_connection()

# إنشاء مثيل عام لمدير قاعدة البيانات
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """الحصول على مثيل مدير قاعدة البيانات"""
    return db_manager

def init_database() -> bool:
    """تهيئة قاعدة البيانات"""
    try:
        db = get_db_manager()
        # إنشاء الجداول
        if db.create_tables():
            # تحديث هيكل قاعدة البيانات
            db.update_database_schema()
            return True
        return False
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return False

if __name__ == "__main__":
    # اختبار الاتصال وإنشاء الجداول
    if init_database():
        print("تم تهيئة قاعدة البيانات بنجاح")
    else:
        print("فشل في تهيئة قاعدة البيانات")
