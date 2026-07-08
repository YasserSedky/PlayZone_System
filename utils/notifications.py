"""
نظام الإشعارات
Notifications System
"""

import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def show_success(message: str, title: str = "نجح") -> None:
    """عرض رسالة نجاح"""
    try:
        print(f"✅ {title}: {message}")
        logger.info(f"Success: {message}")
    except Exception as e:
        logger.error(f"خطأ في عرض رسالة النجاح: {e}")

def show_error(message: str, title: str = "خطأ") -> None:
    """عرض رسالة خطأ"""
    try:
        print(f"❌ {title}: {message}")
        logger.error(f"Error: {message}")
    except Exception as e:
        logger.error(f"خطأ في عرض رسالة الخطأ: {e}")

def show_warning(message: str, title: str = "تحذير") -> None:
    """عرض رسالة تحذير"""
    try:
        print(f"⚠️ {title}: {message}")
        logger.warning(f"Warning: {message}")
    except Exception as e:
        logger.error(f"خطأ في عرض رسالة التحذير: {e}")

def show_info(message: str, title: str = "معلومات") -> None:
    """عرض رسالة معلومات"""
    try:
        print(f"ℹ️ {title}: {message}")
        logger.info(f"Info: {message}")
    except Exception as e:
        logger.error(f"خطأ في عرض رسالة المعلومات: {e}")

def show_loading(message: str = "جاري التحميل...") -> None:
    """عرض رسالة تحميل"""
    try:
        print(f"⏳ {message}")
    except Exception as e:
        logger.error(f"خطأ في عرض رسالة التحميل: {e}")

def show_progress(current: int, total: int, message: str = "التقدم") -> None:
    """عرض شريط التقدم"""
    try:
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r📊 {message}: |{bar}| {current}/{total} ({percentage:.1f}%)", end='', flush=True)
        
        if current >= total:
            print()  # سطر جديد عند الانتهاء
            
    except Exception as e:
        logger.error(f"خطأ في عرض شريط التقدم: {e}")

def show_table(data: list, headers: list, title: str = "الجدول") -> None:
    """عرض البيانات في شكل جدول"""
    try:
        if not data or not headers:
            print(f"📋 {title}: لا توجد بيانات")
            return
        
        print(f"\n📋 {title}")
        print("=" * 80)
        
        # طباعة العناوين
        header_row = " | ".join(f"{header:^15}" for header in headers)
        print(header_row)
        print("-" * 80)
        
        # طباعة البيانات
        for row in data:
            if isinstance(row, dict):
                row_data = [str(row.get(header, ""))[:15] for header in headers]
            else:
                row_data = [str(item)[:15] for item in row]
            
            data_row = " | ".join(f"{item:^15}" for item in row_data)
            print(data_row)
        
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"خطأ في عرض الجدول: {e}")

def show_separator(char: str = "=", length: int = 50) -> None:
    """عرض فاصل"""
    try:
        print(char * length)
    except Exception as e:
        logger.error(f"خطأ في عرض الفاصل: {e}")

def show_timestamp() -> None:
    """عرض الطابع الزمني"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕒 الوقت: {timestamp}")
    except Exception as e:
        logger.error(f"خطأ في عرض الطابع الزمني: {e}")

def show_system_info() -> None:
    """عرض معلومات النظام"""
    try:
        import platform
        import sys
        
        print("\n💻 معلومات النظام:")
        print(f"   النظام: {platform.system()} {platform.release()}")
        print(f"   المعالج: {platform.processor()}")
        print(f"   Python: {sys.version}")
        print(f"   المسار: {os.getcwd()}")
        
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات النظام: {e}")

def show_database_info() -> None:
    """عرض معلومات قاعدة البيانات"""
    try:
        from database import get_db_manager
        
        db = get_db_manager()
        status = db.get_connection_status()
        
        print("\n🗄️ معلومات قاعدة البيانات:")
        if status.get('connected'):
            print(f"   الحالة: متصل ✅")
            print(f"   النوع: {status.get('database_type', 'غير محدد')}")
            if 'database_path' in status:
                print(f"   المسار: {status['database_path']}")
            if 'host' in status:
                print(f"   الخادم: {status['host']}")
                print(f"   قاعدة البيانات: {status.get('database', 'غير محدد')}")
        else:
            print(f"   الحالة: غير متصل ❌")
            if 'error' in status:
                print(f"   الخطأ: {status['error']}")
                
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات قاعدة البيانات: {e}")

def show_shift_info() -> None:
    """عرض معلومات الورديات"""
    try:
        from controllers.shift_controller import ShiftController
        
        shift_controller = ShiftController()
        templates = shift_controller.get_shift_templates()
        today_shifts = shift_controller.get_today_shifts()
        
        print("\n⏰ معلومات الورديات:")
        print(f"   قوالب الورديات: {len(templates)}")
        print(f"   ورديات اليوم: {len(today_shifts)}")
        
        if templates:
            print("   القوالب المتاحة:")
            for template in templates[:3]:  # عرض أول 3 قوالب فقط
                print(f"     - {template['name']}")
        
        if today_shifts:
            print("   ورديات اليوم:")
            for shift in today_shifts[:3]:  # عرض أول 3 ورديات فقط
                status = "نشطة" if not shift.get('end_time') else "منتهية"
                print(f"     - {shift.get('shift_name', 'غير محدد')} ({status})")
                
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات الورديات: {e}")

def show_user_info() -> None:
    """عرض معلومات المستخدمين"""
    try:
        from models.user_model import UserModel
        
        user_model = UserModel()
        stats = user_model.get_user_stats()
        
        print("\n👥 معلومات المستخدمين:")
        print(f"   إجمالي المستخدمين: {stats.get('total_users', 0)}")
        print(f"   المديرين: {stats.get('admins', 0)}")
        print(f"   الكاشيرز: {stats.get('cashiers', 0)}")
        print(f"   المفعلين: {stats.get('enabled_users', 0)}")
        
        if stats.get('last_login'):
            print(f"   آخر تسجيل دخول: {stats['last_login']}")
                
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات المستخدمين: {e}")

def show_full_system_status() -> None:
    """عرض الحالة الكاملة للنظام"""
    try:
        print("\n" + "="*60)
        print("📊 حالة النظام الكاملة")
        print("="*60)
        
        show_timestamp()
        show_system_info()
        show_database_info()
        show_shift_info()
        show_user_info()
        
        print("\n" + "="*60)
        
    except Exception as e:
        logger.error(f"خطأ في عرض حالة النظام: {e}")

def clear_screen() -> None:
    """مسح الشاشة"""
    try:
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception as e:
        logger.error(f"خطأ في مسح الشاشة: {e}")

def pause(message: str = "اضغط Enter للمتابعة...") -> None:
    """إيقاف مؤقت"""
    try:
        input(f"\n⏸️ {message}")
    except Exception as e:
        logger.error(f"خطأ في الإيقاف المؤقت: {e}")

def confirm(message: str = "هل تريد المتابعة؟") -> bool:
    """طلب تأكيد من المستخدم"""
    try:
        response = input(f"❓ {message} (y/n): ").lower().strip()
        return response in ['y', 'yes', 'نعم', 'ن']
    except Exception as e:
        logger.error(f"خطأ في طلب التأكيد: {e}")
        return False

def get_user_input(message: str, default: str = "") -> str:
    """الحصول على إدخال من المستخدم"""
    try:
        if default:
            response = input(f"📝 {message} (افتراضي: {default}): ").strip()
            return response if response else default
        else:
            return input(f"📝 {message}: ").strip()
    except Exception as e:
        logger.error(f"خطأ في الحصول على إدخال المستخدم: {e}")
        return default

def show_menu(options: list, title: str = "القائمة") -> int:
    """عرض قائمة خيارات"""
    try:
        print(f"\n📋 {title}:")
        print("-" * 40)
        
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        print("-" * 40)
        
        while True:
            try:
                choice = int(input("اختر رقم الخيار: "))
                if 1 <= choice <= len(options):
                    return choice
                else:
                    show_error(f"يرجى اختيار رقم بين 1 و {len(options)}")
            except ValueError:
                show_error("يرجى إدخال رقم صحيح")
                
    except Exception as e:
        logger.error(f"خطأ في عرض القائمة: {e}")
        return 0

def show_countdown(seconds: int, message: str = "الانتظار") -> None:
    """عرض عداد تنازلي"""
    try:
        import time
        
        for i in range(seconds, 0, -1):
            print(f"\r⏳ {message}: {i} ثانية", end='', flush=True)
            time.sleep(1)
        
        print(f"\r✅ {message}: انتهى!     ")
        
    except Exception as e:
        logger.error(f"خطأ في العداد التنازلي: {e}")

# دوال مساعدة للإشعارات المتقدمة
class NotificationManager:
    """مدير الإشعارات"""
    
    def __init__(self):
        self.notifications = []
        self.max_notifications = 100
    
    def add_notification(self, message: str, level: str = "info", timestamp: Optional[datetime] = None) -> None:
        """إضافة إشعار جديد"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            notification = {
                'message': message,
                'level': level,
                'timestamp': timestamp
            }
            
            self.notifications.append(notification)
            
            # الاحتفاظ بحد أقصى من الإشعارات
            if len(self.notifications) > self.max_notifications:
                self.notifications = self.notifications[-self.max_notifications:]
            
            # عرض الإشعار
            if level == "success":
                show_success(message)
            elif level == "error":
                show_error(message)
            elif level == "warning":
                show_warning(message)
            else:
                show_info(message)
                
        except Exception as e:
            logger.error(f"خطأ في إضافة الإشعار: {e}")
    
    def get_notifications(self, level: Optional[str] = None, limit: int = 10) -> list:
        """الحصول على الإشعارات"""
        try:
            notifications = self.notifications
            
            if level:
                notifications = [n for n in notifications if n['level'] == level]
            
            return notifications[-limit:] if limit > 0 else notifications
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الإشعارات: {e}")
            return []
    
    def clear_notifications(self) -> None:
        """مسح جميع الإشعارات"""
        try:
            self.notifications.clear()
            show_info("تم مسح جميع الإشعارات")
        except Exception as e:
            logger.error(f"خطأ في مسح الإشعارات: {e}")

# إنشاء مثيل عام لمدير الإشعارات
notification_manager = NotificationManager()

# دوال مختصرة للاستخدام السريع
def notify_success(message: str) -> None:
    """إشعار نجاح سريع"""
    notification_manager.add_notification(message, "success")

def notify_error(message: str) -> None:
    """إشعار خطأ سريع"""
    notification_manager.add_notification(message, "error")

def notify_warning(message: str) -> None:
    """إشعار تحذير سريع"""
    notification_manager.add_notification(message, "warning")

def notify_info(message: str) -> None:
    """إشعار معلومات سريع"""
    notification_manager.add_notification(message, "info")