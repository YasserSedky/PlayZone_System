"""
إعدادات التطبيق
Application Configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AppConfig:
    """إعدادات التطبيق"""
    
    def __init__(self, config_file: str = "config/app_settings.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """تحميل الإعدادات الافتراضية"""
        return {
            "app_name": "نظام إدارة محل بلايستيشن",
            "app_version": "2.0.0",
            "language": "ar",
            "currency": "EGP",
            "currency_symbol": "ج.م",
            "enable_shift_management": True,
            "enable_audit_log": True
        }
    
    def _load_config(self):
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"تم تحميل إعدادات التطبيق من: {self.config_file}")
            else:
                self.save_config()
                logger.info(f"تم إنشاء ملف إعدادات التطبيق الافتراضي: {self.config_file}")
                
        except Exception as e:
            logger.error(f"خطأ في تحميل إعدادات التطبيق: {e}")
    
    def save_config(self) -> bool:
        """حفظ الإعدادات في الملف"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"تم حفظ إعدادات التطبيق في: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حفظ إعدادات التطبيق: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """تعيين قيمة إعداد"""
        try:
            self.config[key] = value
            logger.info(f"تم تعيين إعداد التطبيق {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تعيين الإعداد {key}: {e}")
            return False

# إنشاء مثيل عام لإعدادات التطبيق
app_config = AppConfig()

def get_app_config() -> AppConfig:
    """الحصول على مثيل إعدادات التطبيق"""
    return app_config

def get_database_config():
    """الحصول على إعدادات قاعدة البيانات"""
    try:
        from config.database_config import get_database_config as get_db_config
        return get_db_config()
    except:
        return None