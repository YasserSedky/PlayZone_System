"""
مدير النسخ الاحتياطي التلقائي
Automatic Backup Scheduler
"""

import os
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class AutoBackupScheduler:
    """مدير النسخ الاحتياطي التلقائي"""
    
    def __init__(self, backup_manager, callback: Optional[Callable] = None):
        self.backup_manager = backup_manager
        self.callback = callback
        self.scheduler_thread = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.frequency = "شهرياً"  # افتراضي
        self.enabled = False
        self.last_backup_date = None
        
        # تحميل آخر تاريخ نسخة احتياطية
        self.load_last_backup_date()
    
    def start_scheduler(self, frequency: str = "شهرياً", enabled: bool = True):
        """بدء جدولة النسخ الاحتياطي التلقائي"""
        try:
            self.frequency = frequency
            self.enabled = enabled
            
            if not enabled:
                self.stop_scheduler()
                logger.info("تم إلغاء النسخ الاحتياطي التلقائي")
                return True, "تم إلغاء النسخ الاحتياطي التلقائي"
            
            # إيقاف الجدولة السابقة إذا كانت تعمل
            self.stop_scheduler()
            
            # بدء الجدولة الجديدة
            self.stop_event.clear()
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            logger.info(f"تم بدء النسخ الاحتياطي التلقائي: {frequency}")
            return True, f"تم تفعيل النسخ الاحتياطي التلقائي: {frequency}"
            
        except Exception as e:
            logger.error(f"خطأ في بدء جدولة النسخ الاحتياطي: {e}")
            return False, f"خطأ في بدء جدولة النسخ الاحتياطي: {str(e)}"
    
    def stop_scheduler(self):
        """إيقاف جدولة النسخ الاحتياطي التلقائي"""
        try:
            self.is_running = False
            self.stop_event.set()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("تم إيقاف النسخ الاحتياطي التلقائي")
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف جدولة النسخ الاحتياطي: {e}")
    
    def _scheduler_loop(self):
        """حلقة الجدولة الرئيسية"""
        logger.info("بدء حلقة جدولة النسخ الاحتياطي التلقائي")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # التحقق من الحاجة لإنشاء نسخة احتياطية
                if self._should_create_backup():
                    self._create_automatic_backup()
                
                # انتظار دقيقة واحدة قبل التحقق مرة أخرى
                self.stop_event.wait(60)  # انتظار 60 ثانية
                
            except Exception as e:
                logger.error(f"خطأ في حلقة جدولة النسخ الاحتياطي: {e}")
                time.sleep(60)  # انتظار دقيقة في حالة الخطأ
        
        logger.info("انتهاء حلقة جدولة النسخ الاحتياطي التلقائي")
    
    def _should_create_backup(self) -> bool:
        """التحقق من الحاجة لإنشاء نسخة احتياطية"""
        try:
            if not self.enabled:
                return False
            
            now = datetime.now()
            
            # التحقق من النسخ الشهرية
            if self.frequency == "شهرياً":
                return self._should_create_monthly_backup(now)
            elif self.frequency == "أسبوعياً":
                return self._should_create_weekly_backup(now)
            elif self.frequency == "يومياً":
                return self._should_create_daily_backup(now)
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الحاجة للنسخة الاحتياطية: {e}")
            return False
    
    def _should_create_monthly_backup(self, now: datetime) -> bool:
        """التحقق من الحاجة لنسخة احتياطية شهرية"""
        try:
            # إذا لم تكن هناك نسخة احتياطية سابقة، أنشئ واحدة
            if self.last_backup_date is None:
                return True
            
            # التحقق من أن اليوم هو أول يوم في الشهر
            if now.day != 1:
                return False
            
            # التحقق من أن آخر نسخة احتياطية لم تكن في نفس الشهر
            if (self.last_backup_date.year == now.year and 
                self.last_backup_date.month == now.month):
                return False
            
            # التحقق من أن الوقت مناسب (مثلاً الساعة 2 صباحاً)
            if now.hour < 2:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من النسخة الشهرية: {e}")
            return False
    
    def _should_create_weekly_backup(self, now: datetime) -> bool:
        """التحقق من الحاجة لنسخة احتياطية أسبوعية"""
        try:
            if self.last_backup_date is None:
                return True
            
            # التحقق من أن اليوم هو الأحد (بداية الأسبوع)
            if now.weekday() != 6:  # الأحد = 6
                return False
            
            # التحقق من أن آخر نسخة احتياطية لم تكن في نفس الأسبوع
            days_diff = (now - self.last_backup_date).days
            if days_diff < 7:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من النسخة الأسبوعية: {e}")
            return False
    
    def _should_create_daily_backup(self, now: datetime) -> bool:
        """التحقق من الحاجة لنسخة احتياطية يومية"""
        try:
            if self.last_backup_date is None:
                return True
            
            # التحقق من أن آخر نسخة احتياطية لم تكن اليوم
            if (self.last_backup_date.year == now.year and 
                self.last_backup_date.month == now.month and 
                self.last_backup_date.day == now.day):
                return False
            
            # التحقق من أن الوقت مناسب (مثلاً الساعة 3 صباحاً)
            if now.hour < 3:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من النسخة اليومية: {e}")
            return False
    
    def _create_automatic_backup(self):
        """إنشاء نسخة احتياطية تلقائية"""
        try:
            logger.info("بدء إنشاء نسخة احتياطية تلقائية")
            
            # إنشاء اسم النسخة الاحتياطية
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"auto_backup_{self.frequency}_{timestamp}"
            
            # إنشاء النسخة الاحتياطية
            success, message = self.backup_manager.create_backup(backup_name)
            
            if success:
                # تحديث آخر تاريخ نسخة احتياطية
                self.last_backup_date = datetime.now()
                self.save_last_backup_date()
                
                logger.info(f"تم إنشاء النسخة الاحتياطية التلقائية بنجاح: {backup_name}")
                
                # استدعاء callback إذا كان موجوداً
                if self.callback:
                    self.callback(True, f"تم إنشاء نسخة احتياطية تلقائية: {backup_name}")
            else:
                logger.error(f"فشل في إنشاء النسخة الاحتياطية التلقائية: {message}")
                
                # استدعاء callback إذا كان موجوداً
                if self.callback:
                    self.callback(False, f"فشل في إنشاء النسخة الاحتياطية التلقائية: {message}")
                    
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية التلقائية: {e}")
            if self.callback:
                self.callback(False, f"خطأ في إنشاء النسخة الاحتياطية التلقائية: {str(e)}")
    
    def load_last_backup_date(self):
        """تحميل آخر تاريخ نسخة احتياطية"""
        try:
            backup_info_file = os.path.join(self.backup_manager.backup_folder, "last_backup_info.json")
            
            if os.path.exists(backup_info_file):
                import json
                with open(backup_info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'last_backup_date' in data:
                        self.last_backup_date = datetime.fromisoformat(data['last_backup_date'])
                        logger.info(f"تم تحميل آخر تاريخ نسخة احتياطية: {self.last_backup_date}")
            
        except Exception as e:
            logger.error(f"خطأ في تحميل آخر تاريخ نسخة احتياطية: {e}")
    
    def save_last_backup_date(self):
        """حفظ آخر تاريخ نسخة احتياطية"""
        try:
            backup_info_file = os.path.join(self.backup_manager.backup_folder, "last_backup_info.json")
            
            data = {
                'last_backup_date': self.last_backup_date.isoformat(),
                'frequency': self.frequency,
                'enabled': self.enabled
            }
            
            import json
            with open(backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"تم حفظ آخر تاريخ نسخة احتياطية: {self.last_backup_date}")
            
        except Exception as e:
            logger.error(f"خطأ في حفظ آخر تاريخ نسخة احتياطية: {e}")
    
    def get_status(self) -> dict:
        """الحصول على حالة الجدولة"""
        return {
            'enabled': self.enabled,
            'frequency': self.frequency,
            'is_running': self.is_running,
            'last_backup_date': self.last_backup_date.isoformat() if self.last_backup_date else None
        }
    
    def force_backup(self) -> tuple:
        """إجبار إنشاء نسخة احتياطية"""
        try:
            logger.info("بدء إنشاء نسخة احتياطية إجبارية")
            self._create_automatic_backup()
            return True, "تم إنشاء النسخة الاحتياطية الإجبارية بنجاح"
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية الإجبارية: {e}")
            return False, f"خطأ في إنشاء النسخة الاحتياطية الإجبارية: {str(e)}"
