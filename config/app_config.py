"""
إعدادات التطبيق العامة
General Application Settings
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AppConfig:
    """إعدادات التطبيق العامة"""
    
    def __init__(self, config_file: str = "config/app_settings.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """تحميل الإعدادات الافتراضية"""
        return {
            # إعدادات التطبيق العامة
            "app": {
                "name": "نظام إدارة محل بلايستيشن",
                "version": "1.0.0",
                "author": "PS System Team",
                "language": "ar",
                "theme": "default",
                "auto_save": True,
                "auto_save_interval": 300,  # 5 دقائق
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "backup_retention_days": 30
            },
            
            # إعدادات الواجهة
            "ui": {
                "window_width": 1200,
                "window_height": 800,
                "window_maximized": False,
                "font_family": "Arial",
                "font_size": 12,
                "rtl_support": True,
                "show_tooltips": True,
                "show_status_bar": True,
                "show_menu_bar": True,
                "auto_hide_sidebar": False,
                "sidebar_width": 250,
                "theme_color": "#2E86AB",
                "accent_color": "#A23B72"
            },
            
            # إعدادات العملة والمالية
            "currency": {
                "default_currency": "EGP",
                "currency_symbol": "ج.م",
                "decimal_places": 2,
                "thousands_separator": ",",
                "decimal_separator": ".",
                "show_currency_symbol": True,
                "currency_position": "after"  # before or after
            },
            
            # إعدادات الوقت والتاريخ
            "datetime": {
                "date_format": "%Y-%m-%d",
                "time_format": "%H:%M:%S",
                "datetime_format": "%Y-%m-%d %H:%M:%S",
                "timezone": "Africa/Cairo",
                "24_hour_format": True,
                "show_seconds": True
            },
            
            # إعدادات الأجهزة
            "devices": {
                "default_session_time": 60,  # دقيقة
                "max_session_time": 480,     # 8 ساعات
                "min_session_time": 15,      # 15 دقيقة
                "auto_close_sessions": True,
                "session_warning_time": 5,   # دقائق قبل انتهاء الجلسة
                "default_pricing_type": "single",
                "enable_multiplayer": True,
                "max_players_per_device": 4
            },
            
            # إعدادات المنتجات والمخزون
            "inventory": {
                "low_stock_threshold": 5,
                "auto_reorder": False,
                "reorder_quantity": 10,
                "track_expiry_dates": False,
                "expiry_warning_days": 7,
                "barcode_enabled": False,
                "auto_update_stock": True
            },
            
            # إعدادات العملاء
            "customers": {
                "require_phone_verification": False,
                "auto_create_customer": True,
                "default_customer_balance": 0.00,
                "max_customer_balance": 1000.00,
                "customer_discount_enabled": False,
                "default_discount_percentage": 0,
                "loyalty_points_enabled": False,
                "points_per_currency": 1
            },
            
            # إعدادات التقارير
            "reports": {
                "default_report_period": "daily",
                "auto_generate_reports": False,
                "report_retention_days": 365,
                "include_charts": True,
                "chart_colors": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E"],
                "export_formats": ["PDF", "Excel", "CSV"],
                "default_export_format": "PDF"
            },
            
            # إعدادات الطباعة
            "printing": {
                "printer_name": "",
                "paper_size": "A4",
                "orientation": "portrait",
                "margins": {
                    "top": 20,
                    "bottom": 20,
                    "left": 20,
                    "right": 20
                },
                "font_size": 10,
                "show_logo": True,
                "logo_path": "",
                "show_company_info": True,
                "company_name": "محل بلايستيشن",
                "company_address": "",
                "company_phone": "",
                "company_email": ""
            },
            
            # إعدادات التنبيهات
            "notifications": {
                "enabled": True,
                "sound_enabled": True,
                "popup_enabled": True,
                "email_notifications": False,
                "sms_notifications": False,
                "notification_duration": 5000,  # milliseconds
                "max_notifications": 100,
                "auto_clear_notifications": True,
                "clear_interval_hours": 24
            },
            
            # إعدادات الأمان
            "security": {
                "require_admin_password": True,
                "session_timeout_minutes": 30,
                "max_login_attempts": 3,
                "lockout_duration_minutes": 15,
                "password_min_length": 8,
                "require_strong_password": True,
                "audit_log_enabled": True,
                "audit_log_retention_days": 365,
                "encrypt_sensitive_data": True,
                "device_protection_enabled": True,
                "device_fingerprint_file": "config/device_fingerprint.json",
                "device_protection_key": "PS_DEVICE_PROTECTION_2024",
                "allow_device_transfer": False,
                "device_mismatch_action": "block"  # block, warn, allow
            },
            
            # إعدادات النسخ الاحتياطي
            "backup": {
                "enabled": True,
                "auto_backup": True,
                "backup_interval_hours": 24,
                "backup_time": "02:00",  # 2 AM
                "backup_location": "backups/",
                "retention_days": 30,
                "compress_backups": True,
                "encrypt_backups": False,
                "backup_database": True,
                "backup_files": True
            },
            
            # إعدادات الشبكة
            "network": {
                "enable_remote_access": False,
                "server_port": 8080,
                "max_connections": 10,
                "connection_timeout": 30,
                "enable_ssl": False,
                "ssl_certificate": "",
                "ssl_key": ""
            },
            
            # إعدادات التحديثات
            "updates": {
                "check_for_updates": True,
                "auto_update": False,
                "update_channel": "stable",  # stable, beta, alpha
                "last_update_check": None,
                "update_server_url": ""
            },
            
            # إعدادات التطوير
            "development": {
                "debug_mode": False,
                "log_level": "INFO",
                "log_file": "ps_system.log",
                "max_log_size_mb": 10,
                "log_retention_days": 30,
                "enable_profiling": False,
                "show_debug_info": False
            }
        }
    
    def _load_config(self):
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._merge_config(loaded_config)
                logger.info(f"تم تحميل الإعدادات من: {self.config_file}")
            else:
                self.save_config()
                logger.info(f"تم إنشاء ملف الإعدادات الافتراضي: {self.config_file}")
                
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات: {e}")
    
    def _merge_config(self, loaded_config: Dict[str, Any]):
        """دمج الإعدادات المحملة مع الافتراضية"""
        try:
            def merge_dict(default: Dict, loaded: Dict):
                for key, value in loaded.items():
                    if key in default:
                        if isinstance(default[key], dict) and isinstance(value, dict):
                            merge_dict(default[key], value)
                        else:
                            default[key] = value
                    else:
                        default[key] = value
            
            merge_dict(self.config, loaded_config)
            
        except Exception as e:
            logger.error(f"خطأ في دمج الإعدادات: {e}")
    
    def save_config(self) -> bool:
        """حفظ الإعدادات في الملف"""
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"تم حفظ الإعدادات في: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد"""
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الإعداد: {e}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """تعيين قيمة إعداد"""
        try:
            keys = key_path.split('.')
            config = self.config
            
            # التنقل إلى المفتاح الأخير
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # تعيين القيمة
            config[keys[-1]] = value
            
            logger.info(f"تم تعيين الإعداد {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تعيين الإعداد: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """إعادة تعيين الإعدادات إلى الافتراضية"""
        try:
            self.config = self._load_default_config()
            return self.save_config()
            
        except Exception as e:
            logger.error(f"خطأ في إعادة تعيين الإعدادات: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """تحديث الإعدادات"""
        try:
            self._merge_config(new_config)
            return self.save_config()
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الإعدادات: {e}")
            return False
    
    def export_config(self, export_file: str) -> bool:
        """تصدير الإعدادات"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"تم تصدير الإعدادات إلى: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تصدير الإعدادات: {e}")
            return False
    
    def import_config(self, import_file: str) -> bool:
        """استيراد الإعدادات"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self._merge_config(imported_config)
            return self.save_config()
            
        except Exception as e:
            logger.error(f"خطأ في استيراد الإعدادات: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """التحقق من صحة الإعدادات"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # التحقق من الإعدادات المالية
            currency_config = self.get('currency', {})
            if not currency_config.get('default_currency'):
                validation_result['errors'].append("العملة الافتراضية مطلوبة")
                validation_result['valid'] = False
            
            # التحقق من إعدادات الأجهزة
            devices_config = self.get('devices', {})
            if devices_config.get('max_session_time', 0) <= devices_config.get('min_session_time', 0):
                validation_result['errors'].append("الوقت الأقصى للجلسة يجب أن يكون أكبر من الأدنى")
                validation_result['valid'] = False
            
            # التحقق من إعدادات المخزون
            inventory_config = self.get('inventory', {})
            if inventory_config.get('low_stock_threshold', 0) < 0:
                validation_result['errors'].append("حد المخزون المنخفض يجب أن يكون موجب")
                validation_result['valid'] = False
            
            # التحقق من إعدادات الأمان
            security_config = self.get('security', {})
            if security_config.get('password_min_length', 0) < 6:
                validation_result['warnings'].append("طول كلمة المرور قصير جداً")
            
            # التحقق من إعدادات النسخ الاحتياطي
            backup_config = self.get('backup', {})
            if backup_config.get('enabled') and not backup_config.get('backup_location'):
                validation_result['warnings'].append("موقع النسخ الاحتياطي غير محدد")
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الإعدادات: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append("خطأ في التحقق من الإعدادات")
        
        return validation_result

# إنشاء مثيل عام لإعدادات التطبيق
app_config = AppConfig()

def get_app_config() -> AppConfig:
    """الحصول على مثيل إعدادات التطبيق"""
    return app_config
