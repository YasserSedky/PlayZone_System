"""
مدير الإعدادات
Settings Manager
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SettingsManager:
    """مدير إعدادات النظام"""
    
    def __init__(self, settings_file: str = "config/system_settings.json"):
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    logger.info("تم تحميل الإعدادات بنجاح")
                    return settings
            else:
                logger.warning("ملف الإعدادات غير موجود، سيتم إنشاء إعدادات افتراضية")
                return self.get_default_settings()
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات: {e}")
            return self.get_default_settings()
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """حفظ الإعدادات في الملف"""
        try:
            if settings is not None:
                self.settings = settings
            
            # إنشاء مجلد الإعدادات إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            
            logger.info("تم حفظ الإعدادات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")
            return False
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """الحصول على إعداد محدد"""
        try:
            keys = key_path.split('.')
            value = self.settings
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الإعداد {key_path}: {e}")
            return default
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """تعيين إعداد محدد"""
        try:
            keys = key_path.split('.')
            current = self.settings
            
            # التنقل إلى المستوى قبل الأخير
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # تعيين القيمة
            current[keys[-1]] = value
            
            logger.info(f"تم تعيين الإعداد {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تعيين الإعداد {key_path}: {e}")
            return False
    
    def get_default_settings(self) -> Dict[str, Any]:
        """الحصول على الإعدادات الافتراضية"""
        return {
            "company": {
                "name": "مؤسسة الألعاب",
                "address": "",
                "phone": "",
                "email": ""
            },
            "ui": {
                "language": "العربية",
                "currency": "جنيه مصري (ج.م)",
                "date_format": "dd/mm/yyyy"
            },
            "backup": {
                "auto_backup": False,
                "frequency": "يومياً",
                "folder": "backups/"
            }
        }
    
    def get_company_name(self) -> str:
        """الحصول على اسم الشركة"""
        return self.get_setting("company.name", "مؤسسة الألعاب")
    
    def get_currency(self) -> str:
        """الحصول على العملة"""
        return self.get_setting("ui.currency", "جنيه مصري (ج.م)")
    

# إنشاء مثيل عام لمدير الإعدادات
settings_manager = SettingsManager()
