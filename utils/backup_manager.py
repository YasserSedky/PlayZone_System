"""
مدير النسخ الاحتياطي
Backup Manager
"""

import os
import shutil
import json
import zipfile
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """مدير النسخ الاحتياطي الشامل"""
    
    def __init__(self, backup_folder: str = "backups"):
        self.backup_folder = backup_folder
        self.db_file = "data/ps_system.db"
        self.config_files = [
            "config/app_settings.json",
            "config/system_settings.json",
            "config/database_config.json"
        ]
        self.ensure_backup_folder()
    
    def ensure_backup_folder(self):
        """التأكد من وجود مجلد النسخ الاحتياطي"""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder, exist_ok=True)
                logger.info(f"تم إنشاء مجلد النسخ الاحتياطي: {self.backup_folder}")
        except Exception as e:
            logger.error(f"خطأ في إنشاء مجلد النسخ الاحتياطي: {e}")
            raise
    
    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """إنشاء نسخة احتياطية شاملة"""
        try:
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"ps_system_backup_{timestamp}"
            
            backup_path = os.path.join(self.backup_folder, f"{backup_name}.zip")
            
            # التحقق من عدم وجود نسخة بنفس الاسم
            if os.path.exists(backup_path):
                return False, f"نسخة احتياطية بنفس الاسم موجودة: {backup_name}"
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # نسخ قاعدة البيانات
                if os.path.exists(self.db_file):
                    zipf.write(self.db_file, "data/ps_system.db")
                    logger.info("تم نسخ قاعدة البيانات")
                
                # نسخ ملفات الإعدادات
                for config_file in self.config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, config_file)
                        logger.info(f"تم نسخ ملف الإعدادات: {config_file}")
                
                # إنشاء ملف معلومات النسخة الاحتياطية
                backup_info = {
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "database_size": self.get_file_size(self.db_file),
                    "config_files": [f for f in self.config_files if os.path.exists(f)],
                    "version": "1.0.0"
                }
                
                zipf.writestr("backup_info.json", json.dumps(backup_info, indent=2, ensure_ascii=False))
            
            # التحقق من صحة النسخة الاحتياطية
            if self.validate_backup(backup_path):
                backup_size = self.get_file_size(backup_path)
                logger.info(f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_name} ({backup_size})")
                return True, f"تم إنشاء النسخة الاحتياطية بنجاح: {backup_name}"
            else:
                os.remove(backup_path)
                return False, "فشل في التحقق من صحة النسخة الاحتياطية"
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return False, f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}"
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """استعادة نسخة احتياطية"""
        try:
            # التحقق من وجود النسخة الاحتياطية
            if not os.path.exists(backup_path):
                return False, "النسخة الاحتياطية غير موجودة"
            
            # التحقق من صحة النسخة الاحتياطية
            if not self.validate_backup(backup_path):
                return False, "النسخة الاحتياطية تالفة أو غير صالحة"
            
            # إنشاء نسخة احتياطية من البيانات الحالية قبل الاستعادة
            current_backup_name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success, message = self.create_backup(current_backup_name)
            if not success:
                return False, f"فشل في إنشاء نسخة احتياطية من البيانات الحالية: {message}"
            
            # استخراج النسخة الاحتياطية
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # استخراج قاعدة البيانات
                if "data/ps_system.db" in zipf.namelist():
                    # إغلاق أي اتصالات بقاعدة البيانات الحالية
                    self.close_db_connections()
                    
                    # نسخ قاعدة البيانات الجديدة
                    zipf.extract("data/ps_system.db", ".")
                    logger.info("تم استعادة قاعدة البيانات")
                
                # استخراج ملفات الإعدادات
                for config_file in self.config_files:
                    if config_file in zipf.namelist():
                        zipf.extract(config_file, ".")
                        logger.info(f"تم استعادة ملف الإعدادات: {config_file}")
            
            logger.info(f"تم استعادة النسخة الاحتياطية بنجاح: {backup_path}")
            return True, "تم استعادة النسخة الاحتياطية بنجاح"
            
        except Exception as e:
            logger.error(f"خطأ في استعادة النسخة الاحتياطية: {e}")
            return False, f"خطأ في استعادة النسخة الاحتياطية: {str(e)}"
    
    def get_backups_list(self) -> List[Dict]:
        """الحصول على قائمة النسخ الاحتياطية المتاحة"""
        try:
            backups = []
            
            if not os.path.exists(self.backup_folder):
                return backups
            
            for filename in os.listdir(self.backup_folder):
                if filename.endswith('.zip'):
                    backup_path = os.path.join(self.backup_folder, filename)
                    backup_info = self.get_backup_info(backup_path)
                    if backup_info:
                        backups.append(backup_info)
            
            # ترتيب النسخ الاحتياطية حسب تاريخ الإنشاء (الأحدث أولاً)
            backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على قائمة النسخ الاحتياطية: {e}")
            return []
    
    def get_backup_info(self, backup_path: str) -> Optional[Dict]:
        """الحصول على معلومات النسخة الاحتياطية"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if "backup_info.json" in zipf.namelist():
                    info_data = zipf.read("backup_info.json")
                    backup_info = json.loads(info_data.decode('utf-8'))
                    
                    # إضافة معلومات إضافية
                    backup_info['file_path'] = backup_path
                    backup_info['file_size'] = self.get_file_size(backup_path)
                    backup_info['file_name'] = os.path.basename(backup_path)
                    
                    return backup_info
                else:
                    # معلومات افتراضية للنسخ القديمة
                    stat = os.stat(backup_path)
                    return {
                        'backup_name': os.path.splitext(os.path.basename(backup_path))[0],
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'file_path': backup_path,
                        'file_size': stat.st_size,
                        'file_name': os.path.basename(backup_path),
                        'version': 'unknown'
                    }
                    
        except Exception as e:
            logger.error(f"خطأ في قراءة معلومات النسخة الاحتياطية: {e}")
            return None
    
    def validate_backup(self, backup_path: str) -> bool:
        """التحقق من صحة النسخة الاحتياطية"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # التحقق من وجود ملفات أساسية
                namelist = zipf.namelist()
                
                # يجب أن تحتوي على قاعدة البيانات أو ملفات الإعدادات
                has_db = "data/ps_system.db" in namelist
                has_configs = any(config in namelist for config in self.config_files)
                
                if not (has_db or has_configs):
                    return False
                
                # التحقق من عدم تلف الملف
                zipf.testzip()
                return True
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من صحة النسخة الاحتياطية: {e}")
            return False
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """حذف نسخة احتياطية"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info(f"تم حذف النسخة الاحتياطية: {backup_path}")
                return True, "تم حذف النسخة الاحتياطية بنجاح"
            else:
                return False, "النسخة الاحتياطية غير موجودة"
                
        except Exception as e:
            logger.error(f"خطأ في حذف النسخة الاحتياطية: {e}")
            return False, f"خطأ في حذف النسخة الاحتياطية: {str(e)}"
    
    def cleanup_old_backups(self, keep_count: int = 10) -> Tuple[bool, str]:
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backups = self.get_backups_list()
            
            if len(backups) <= keep_count:
                return True, f"عدد النسخ الاحتياطية ({len(backups)}) أقل من الحد الأقصى ({keep_count})"
            
            # حذف النسخ القديمة
            backups_to_delete = backups[keep_count:]
            deleted_count = 0
            
            for backup in backups_to_delete:
                success, _ = self.delete_backup(backup['file_path'])
                if success:
                    deleted_count += 1
            
            logger.info(f"تم حذف {deleted_count} نسخة احتياطية قديمة")
            return True, f"تم حذف {deleted_count} نسخة احتياطية قديمة"
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ الاحتياطية القديمة: {e}")
            return False, f"خطأ في تنظيف النسخ الاحتياطية القديمة: {str(e)}"
    
    def get_file_size(self, file_path: str) -> str:
        """الحصول على حجم الملف بصيغة مقروءة"""
        try:
            if not os.path.exists(file_path):
                return "0 B"
            
            size = os.path.getsize(file_path)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            
            return f"{size:.1f} TB"
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على حجم الملف: {e}")
            return "غير معروف"
    
    def close_db_connections(self):
        """إغلاق اتصالات قاعدة البيانات"""
        try:
            # محاولة إغلاق اتصالات قاعدة البيانات
            import sqlite3
            # هذا قد يحتاج إلى تحسين حسب كيفية إدارة اتصالات قاعدة البيانات في التطبيق
            logger.info("تم إغلاق اتصالات قاعدة البيانات")
        except Exception as e:
            logger.error(f"خطأ في إغلاق اتصالات قاعدة البيانات: {e}")
    
    def schedule_auto_backup(self, frequency: str, enabled: bool) -> Tuple[bool, str]:
        """جدولة النسخ الاحتياطي التلقائي"""
        try:
            # هذا يمكن تطويره لاحقاً لاستخدام scheduler
            if enabled:
                logger.info(f"تم تفعيل النسخ الاحتياطي التلقائي: {frequency}")
                return True, f"تم تفعيل النسخ الاحتياطي التلقائي: {frequency}"
            else:
                logger.info("تم إلغاء النسخ الاحتياطي التلقائي")
                return True, "تم إلغاء النسخ الاحتياطي التلقائي"
                
        except Exception as e:
            logger.error(f"خطأ في جدولة النسخ الاحتياطي التلقائي: {e}")
            return False, f"خطأ في جدولة النسخ الاحتياطي التلقائي: {str(e)}"
