"""
مسجل الأخطاء المحسن
Enhanced Error Logger
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QApplication

class ErrorLogger:
    """مسجل الأخطاء المحسن"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """إعداد نظام التسجيل"""
        # إعداد مسجل الأخطاء مع RotatingFileHandler
        # الحد الأقصى: 5 ميجابايت، عدد النسخ الاحتياطية: 5 ملفات
        error_handler = RotatingFileHandler(
            'error_log.txt',
            maxBytes=5 * 1024 * 1024,  # 5 ميجابايت
            backupCount=5,  # 5 نسخ احتياطية
            encoding='utf-8'
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                error_handler,
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # إعداد مسجل خاص للأخطاء الحرجة مع RotatingFileHandler
        self.critical_logger = logging.getLogger('critical_errors')
        critical_handler = RotatingFileHandler(
            'critical_errors.txt',
            maxBytes=5 * 1024 * 1024,  # 5 ميجابايت
            backupCount=5,  # 5 نسخ احتياطية
            encoding='utf-8'
        )
        critical_handler.setLevel(logging.ERROR)
        critical_formatter = logging.Formatter('%(asctime)s - CRITICAL - %(message)s')
        critical_handler.setFormatter(critical_formatter)
        self.critical_logger.addHandler(critical_handler)
    
    def log_error(self, error, context=""):
        """تسجيل خطأ عادي"""
        error_msg = f"خطأ في {context}: {str(error)}"
        logging.error(error_msg)
    
    def log_critical_error(self, error, context=""):
        """تسجيل خطأ حرج"""
        error_details = traceback.format_exc()
        critical_msg = f"خطأ حرج في {context}: {str(error)}\nالتفاصيل: {error_details}"
        
        self.critical_logger.error(critical_msg)
        
        # محاولة عرض رسالة للمستخدم
        try:
            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None, 
                    "خطأ حرج", 
                    f"حدث خطأ حرج في النظام:\n{str(error)}\n\nتم تسجيل التفاصيل في ملف السجل."
                )
        except Exception:
            # في حالة فشل عرض الرسالة، طباعة في الكونسول
            print(f"خطأ حرج: {critical_msg}")
    
    def log_session_error(self, session_id, error, operation=""):
        """تسجيل خطأ متعلق بالجلسة"""
        error_msg = f"خطأ في الجلسة {session_id} - العملية: {operation} - الخطأ: {str(error)}"
        logging.error(error_msg)
    
    def log_payment_error(self, session_id, error, operation=""):
        """تسجيل خطأ متعلق بالدفع"""
        error_msg = f"خطأ في الدفع - الجلسة: {session_id} - العملية: {operation} - الخطأ: {str(error)}"
        logging.error(error_msg)

# إنشاء مثيل عام لمسجل الأخطاء
error_logger = ErrorLogger()

def safe_execute(func, *args, **kwargs):
    """تنفيذ دالة بشكل آمن مع معالجة الأخطاء"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_logger.log_critical_error(e, f"تنفيذ الدالة {func.__name__}")
        return None

def safe_session_operation(operation_name):
    """ديكوراتور لعمليات الجلسة الآمنة"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                session_id = args[0] if args else "غير محدد"
                error_logger.log_session_error(session_id, e, operation_name)
                return {
                    'success': False,
                    'message': f'حدث خطأ في {operation_name}: {str(e)}'
                }
        return wrapper
    return decorator

def safe_payment_operation(operation_name):
    """ديكوراتور لعمليات الدفع الآمنة"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                session_id = kwargs.get('session_id', 'غير محدد')
                error_logger.log_payment_error(session_id, e, operation_name)
                return {
                    'success': False,
                    'message': f'حدث خطأ في {operation_name}: {str(e)}'
                }
        return wrapper
    return decorator
