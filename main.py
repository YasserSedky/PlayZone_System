"""
نظام إدارة محل بلايستيشن - الملف الرئيسي
PlayStation Shop Management System - Main File
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# إعداد الترميز للنصوص العربية
if sys.platform == "win32":
    import codecs
    # التحقق من وجود sys.stdout و sys.stderr قبل محاولة استخدامهما
    if sys.stdout is not None:
        try:
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        except (AttributeError, OSError):
            # تجاهل الخطأ إذا لم يكن بالإمكان فصل stdout
            pass
    
    if sys.stderr is not None:
        try:
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except (AttributeError, OSError):
            # تجاهل الخطأ إذا لم يكن بالإمكان فصل stderr
            pass
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QPixmap, QFont, QIcon

# إضافة مسار المشروع إلى Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# استيراد المكونات الأساسية
# سيتم استيراد database محلياً
# سيتم استيراد المكونات محلياً لتجنب مشاكل الاستيراد
# سيتم استيراد LoginWindow محلياً في show_login_window
# سيتم استيراد DashboardWindow محلياً

# إعداد نظام السجلات
def setup_logging():
    """إعداد نظام السجلات"""
    try:
        # إنشاء مجلد السجلات
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # إعداد التنسيق
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # إعداد الملف الرئيسي للسجلات مع RotatingFileHandler
        # الحد الأقصى: 5 ميجابايت، عدد النسخ الاحتياطية: 5 ملفات
        log_file = f'{log_dir}/ps_system_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 ميجابايت
            backupCount=5,  # 5 نسخ احتياطية
            encoding='utf-8'
        )
        
        handlers = [file_handler]
        
        # إضافة StreamHandler فقط إذا كان sys.stdout متوفراً
        if sys.stdout is not None:
            handlers.append(logging.StreamHandler(sys.stdout))
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers
        )
        
        # إعداد مستوى السجلات حسب الإعدادات
        try:
            from config import get_app_config
            app_config = get_app_config()
            debug_mode = app_config.get('development.debug_mode', False)
            if debug_mode:
                logging.getLogger().setLevel(logging.DEBUG)
        except:
            pass  # تجاهل إذا فشل الاستيراد
        
        logger = logging.getLogger(__name__)
        logger.info("تم إعداد نظام السجلات بنجاح")
        
    except Exception as e:
        print(f"خطأ في إعداد نظام السجلات: {e}")

class SplashScreen(QSplashScreen):
    """شاشة البداية"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة شاشة البداية"""
        try:
            # إنشاء pixmap للشاشة
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.darkBlue)
            
            self.setPixmap(pixmap)
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            
            # إعداد النص
            self.showMessage(
                "جاري تحميل نظام إدارة محل بلايستيشن...",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.white
            )
            
        except Exception as e:
            logging.error(f"خطأ في إعداد شاشة البداية: {e}")

class PSApplication(QApplication):
    """التطبيق الرئيسي"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setup_application()
        self.current_user = None
        self.main_window = None
    
    def setup_application(self):
        """إعداد التطبيق"""
        try:
            # إعداد معلومات التطبيق
            app_config = get_app_config()
            
            self.setApplicationName(app_config.get('app.name', 'نظام إدارة محل بلايستيشن'))
            self.setApplicationVersion(app_config.get('app.version', '1.0.0'))
            self.setOrganizationName(app_config.get('app.author', 'PS System Team'))
            
            # إعداد الخط
            font_family = app_config.get('ui.font_family', 'Arial')
            font_size = app_config.get('ui.font_size', 12)
            
            font = QFont(font_family, font_size)
            self.setFont(font)
            
            # إعداد الأيقونة
            icon_path = self.get_icon_path("ps_icon.png")
            if icon_path and os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            
            # إعداد RTL
            if app_config.get('ui.rtl_support', True):
                self.setLayoutDirection(Qt.RightToLeft)
            
            logging.info("تم إعداد التطبيق بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في إعداد التطبيق: {e}")
    
    def get_icon_path(self, icon_name: str) -> str:
        """الحصول على مسار الأيقونة"""
        try:
            # البحث في مجلد resources
            resources_path = os.path.join(os.path.dirname(__file__), "resources", icon_name)
            if os.path.exists(resources_path):
                return resources_path
            
            # البحث في مجلد التطبيق
            app_path = os.path.join(os.path.dirname(__file__), icon_name)
            if os.path.exists(app_path):
                return app_path
            
            return ""
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على مسار الأيقونة: {e}")
            return ""
    
    def show_login_window(self):
        """عرض نافذة تسجيل الدخول"""
        try:
            print("محاولة عرض نافذة تسجيل الدخول...")
            
            # استيراد LoginWindow محلياً لتجنب مشاكل الاستيراد
            from views.login_window import LoginWindow
            
            print("تم استيراد LoginWindow بنجاح")
            
            self.login_window = LoginWindow()
            print(" تم إنشاء LoginWindow بنجاح")
            
            self.login_window.login_successful.connect(self.on_login_successful)
            print(" تم ربط الإشارات بنجاح")
            
            self.login_window.show()
            print(" تم استدعاء show() بنجاح")
            
            # التأكد من أن النافذة مرئية
            self.login_window.raise_()
            self.login_window.activateWindow()
            
            logging.info("تم عرض نافذة تسجيل الدخول بنجاح")
            print("🎉 نافذة تسجيل الدخول يجب أن تظهر الآن!")
            
        except Exception as e:
            logging.error(f"خطأ في عرض نافذة تسجيل الدخول: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"خطأ في عرض نافذة تسجيل الدخول:\n{e}")
    
    def on_login_successful(self, user_data):
        """معالج نجاح تسجيل الدخول"""
        try:
            print(f" تم تسجيل الدخول بنجاح للمستخدم: {user_data.get('username', '')}")
            self.current_user = user_data
            
            # إغلاق نافذة تسجيل الدخول
            if hasattr(self, 'login_window'):
                self.login_window.close()
                print(" تم إغلاق نافذة تسجيل الدخول")
            
            # عرض لوحة التحكم
            self.show_dashboard()
            
        except Exception as e:
            print(f" خطأ في معالج نجاح تسجيل الدخول: {e}")
            logging.error(f"خطأ في معالجة تسجيل الدخول: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"خطأ في تسجيل الدخول:\n{e}")
            self.show_error_message("خطأ في معالجة تسجيل الدخول")
    
    def show_dashboard_with_auto_login(self, auto_login_data):
        """عرض لوحة التحكم مع تسجيل دخول تلقائي"""
        try:
            print(f"تسجيل دخول تلقائي للكاشير: {auto_login_data.get('username')}")
            
            # إنشاء بيانات المستخدم
            user_data = {
                'id': auto_login_data.get('cashier_id'),
                'username': auto_login_data.get('username'),
                'role': auto_login_data.get('role'),
                'auto_login': True
            }
            
            self.current_user = user_data
            
            # عرض لوحة التحكم مباشرة
            self.show_dashboard()
            
            # إظهار رسالة ترحيب
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                None,
                "تسجيل دخول تلقائي",
                f"مرحباً {user_data['username']}!\n\n"
                "تم تسجيل دخولك تلقائياً بعد إعادة تشغيل البرنامج."
            )
            
        except Exception as e:
            print(f"خطأ في تسجيل الدخول التلقائي: {e}")
            logging.error(f"خطأ في تسجيل الدخول التلقائي: {e}")
            # في حالة الخطأ، عرض نافذة تسجيل الدخول العادية
            self.show_login_window()
    
    def show_dashboard(self):
        """عرض لوحة التحكم"""
        try:
            print(" محاولة عرض لوحة التحكم...")
            
            # استيراد DashboardWindow محلياً
            from views.dashboard import DashboardWindow
            
            print(" تم استيراد DashboardWindow")
            
            self.main_window = DashboardWindow(self.current_user)
            print(" تم إنشاء DashboardWindow")
            
            self.main_window.logout_requested.connect(self.on_logout_requested)
            print(" تم ربط إشارة تسجيل الخروج")
            
            self.main_window.show()
            print(" تم عرض لوحة التحكم")
            
            # التأكد من أن النافذة مرئية
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            print("🎉 لوحة التحكم يجب أن تظهر الآن!")
            
        except Exception as e:
            print(f" خطأ في عرض لوحة التحكم: {e}")
            logging.error(f"خطأ في عرض لوحة التحكم: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"خطأ في عرض لوحة التحكم:\n{e}")
    
    def on_logout_requested(self):
        """معالج طلب تسجيل الخروج"""
        try:
            # إغلاق النافذة الرئيسية
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            # مسح بيانات المستخدم
            self.current_user = None
            
            # عرض نافذة تسجيل الدخول مرة أخرى
            self.show_login_window()
            
        except Exception as e:
            logging.error(f"خطأ في معالجة تسجيل الخروج: {e}")
    
    def show_error_message(self, message: str):
        """عرض رسالة خطأ"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("خطأ")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            
        except Exception as e:
            logging.error(f"خطأ في عرض رسالة الخطأ: {e}")
    
    def show_info_message(self, message: str):
        """عرض رسالة معلومات"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("معلومات")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            
        except Exception as e:
            logging.error(f"خطأ في عرض رسالة المعلومات: {e}")
    
    def pause_all_sessions_on_shutdown(self):
        """إيقاف جميع الجلسات عند إغلاق التطبيق"""
        try:
            from utils.session_manager import SessionManager
            session_manager = SessionManager()
            result = session_manager.pause_all_active_sessions()
            
            if result['success']:
                if result['paused_count'] > 0:
                    logging.info(f"تم إيقاف {result['paused_count']} جلسة عند إغلاق التطبيق")
                else:
                    logging.info("لا توجد جلسات نشطة لإيقافها")
            else:
                logging.error(f"فشل في إيقاف الجلسات: {result['message']}")
                
        except Exception as e:
            logging.error(f"خطأ في إيقاف الجلسات عند إغلاق التطبيق: {e}")
    
    def closeEvent(self, event):
        """معالج إغلاق التطبيق"""
        try:
            # إيقاف جميع الجلسات النشطة
            self.pause_all_sessions_on_shutdown()
            
            # إغلاق التطبيق
            event.accept()
            
        except Exception as e:
            logging.error(f"خطأ في إغلاق التطبيق: {e}")
            event.accept()

def check_dependencies():
    """التحقق من المتطلبات"""
    try:
        print(" التحقق من المتطلبات...")
        required_modules = [
            'PySide6',
            'sqlite3',
            'decimal',
            'datetime',
            'json',
            'logging'
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            error_msg = f" المكتبات التالية مفقودة: {', '.join(missing_modules)}\n"
            error_msg += "يرجى تثبيت المتطلبات باستخدام: pip install -r requirements.txt"
            
            print(error_msg)
            return False
        
        print(" جميع المتطلبات متوفرة")
        return True
        
    except Exception as e:
        print(f"خطأ في التحقق من المتطلبات: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    try:
        # التحقق من المتطلبات (مبسط)
        print("التحقق من المتطلبات...")
        try:
            import PySide6
            import sqlite3
            print("جميع المتطلبات متوفرة")
        except ImportError as e:
            print(f"خطأ في المتطلبات: {e}")
            return 1
        
        # إعداد نظام السجلات
        print("إعداد نظام السجلات...")
        setup_logging()
        logger = logging.getLogger(__name__)
        
        print("تم إعداد نظام السجلات")
        logger.info("بدء تشغيل نظام إدارة محل بلايستيشن")
        
        # استيراد المكونات محلياً
        print("استيراد المكونات...")
        from config import get_app_config
        from database import init_database, get_db_manager
        print("تم استيراد المكونات")
        
        # إنشاء التطبيق
        print("إنشاء التطبيق...")
        app = PSApplication(sys.argv)
        print("تم إنشاء التطبيق")
        
        # إعداد QApplication للتعامل مع الـ threads
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # تهيئة قاعدة البيانات مباشرة (بدون شاشة البداية)
        print(" بدء تهيئة قاعدة البيانات...")
        try:
            # اختبار الاتصال بقاعدة البيانات
            print(" اختبار الاتصال بقاعدة البيانات...")
            db = get_db_manager()
            status = db.get_connection_status()
            
            if not status.get('connected'):
                print(f" فشل في الاتصال بقاعدة البيانات")
                app.show_error_message("فشل في الاتصال بقاعدة البيانات")
                return 1
            
            print(" تم الاتصال بقاعدة البيانات بنجاح")
            
            # تهيئة قاعدة البيانات
            print(" تهيئة قاعدة البيانات...")
            if not init_database():
                print(" فشل في تهيئة قاعدة البيانات")
                app.show_error_message("فشل في تهيئة قاعدة البيانات")
                return 1
            
            print(" تم تهيئة قاعدة البيانات بنجاح")
            logger.info("تم تهيئة قاعدة البيانات بنجاح")
            
            # استئناف الجلسات الموقوفة
            print(" استئناف الجلسات الموقوفة...")
            try:
                from utils.session_manager import SessionManager
                session_manager = SessionManager()
                result = session_manager.resume_paused_sessions()
                
                if result['success']:
                    if result['resumed_count'] > 0:
                        print(f" تم استئناف {result['resumed_count']} جلسة")
                        logger.info(f"تم استئناف {result['resumed_count']} جلسة عند بدء التطبيق")
                    else:
                        print(" لا توجد جلسات موقوفة للاستئناف")
                else:
                    print(f" تحذير: {result['message']}")
                    logger.warning(f"تحذير في استئناف الجلسات: {result['message']}")
                    
            except Exception as e:
                print(f" تحذير في استئناف الجلسات: {e}")
                logger.warning(f"تحذير في استئناف الجلسات: {e}")
            
        except Exception as e:
            print(f" خطأ في تهيئة قاعدة البيانات: {e}")
            logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            import traceback
            traceback.print_exc()
            app.show_error_message(f"خطأ في تهيئة قاعدة البيانات:\n{e}")
            return 1
        
        # التحقق من بصمة الجهاز أولاً
        print(" التحقق من بصمة الجهاز...")
        try:
            from utils.security import device_fingerprint
            
            device_result = device_fingerprint.initialize_device_protection()
            
            if not device_result['success']:
                print(f" خطأ في التحقق من الجهاز: {device_result.get('error', 'خطأ غير معروف')}")
                
                # عرض رسالة خطأ وإغلاق البرنامج
                error_msg = "🚫 خطأ في التحقق من الجهاز\n\n"
                
                if 'error' in device_result and 'تم نقل البرنامج' in device_result['error']:
                    error_msg += "تم نقل البرنامج إلى جهاز آخر!\n"
                    error_msg += "هذا البرنامج مربوط بجهاز معين ولا يمكن نقله.\n\n"
                    error_msg += "للاستفسار، يرجى التواصل مع فريق الدعم الفني."
                else:
                    error_msg += f"السبب: {device_result.get('error', 'خطأ غير معروف')}\n\n"
                    error_msg += "يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."
                
                app.show_error_message(error_msg)
                logger.error(f"فشل في التحقق من الجهاز: {device_result}")
                return 1
            
            if device_result.get('is_first_run'):
                print(" هذا هو التشغيل الأول للبرنامج على هذا الجهاز")
                logger.info("تم تسجيل الجهاز بنجاح - التشغيل الأول")
                
                # عرض رسالة ترحيب للجهاز الجديد
                welcome_msg = "🎉 مرحباً بك في نظام إدارة محل بلايستيشن\n\n"
                welcome_msg += "تم تسجيل هذا الجهاز بنجاح.\n"
                welcome_msg += "يمكنك الآن استخدام البرنامج بشكل طبيعي.\n\n"
                welcome_msg += "ملاحظة: هذا البرنامج مربوط بهذا الجهاز ولا يمكن نقله."
                
                app.show_info_message(welcome_msg)
            elif device_result.get('device_transferred'):
                print(" تم نقل البرنامج إلى جهاز جديد - مسموح حسب الإعدادات")
                logger.info("تم نقل البرنامج إلى جهاز جديد - مسموح حسب الإعدادات")
                
                # عرض رسالة تحذيرية
                transfer_msg = "⚠️ تحذير: تم نقل البرنامج\n\n"
                transfer_msg += "تم نقل البرنامج إلى جهاز جديد.\n"
                transfer_msg += "يُنصح بالتواصل مع الدعم الفني للتأكد من صحة العملية."
                
                app.show_info_message(transfer_msg)
            elif device_result.get('warning'):
                print(f" تحذير: {device_result['warning']}")
                logger.warning(f"تحذير من نقل الجهاز: {device_result['warning']}")
                
                # عرض رسالة تحذيرية
                warning_msg = "⚠️ تحذير\n\n"
                warning_msg += f"{device_result['warning']}\n\n"
                warning_msg += "إذا كان هذا خطأ، يرجى التواصل مع الدعم الفني."
                
                app.show_info_message(warning_msg)
            elif device_result.get('protection_disabled'):
                print(" نظام حماية الجهاز معطل")
                logger.info("نظام حماية الجهاز معطل")
            else:
                print(" الجهاز مسجل مسبقاً - التشغيل مسموح")
                logger.info("الجهاز مسجل مسبقاً - التشغيل مسموح")
                
        except Exception as e:
            print(f" خطأ في التحقق من بصمة الجهاز: {e}")
            logger.error(f"خطأ في التحقق من بصمة الجهاز: {e}")
            import traceback
            traceback.print_exc()
            
            # في حالة فشل التحقق من الجهاز، عرض رسالة خطأ
            app.show_error_message("خطأ في التحقق من الجهاز\nيرجى المحاولة مرة أخرى")
            return 1
        
        # التحقق من تسجيل الدخول التلقائي
        print(" التحقق من تسجيل الدخول التلقائي...")
        try:
            from utils.auto_restart import load_auto_login_data
            auto_login_data = load_auto_login_data()
            
            if auto_login_data:
                print(f" تم العثور على بيانات تسجيل دخول تلقائي للكاشير: {auto_login_data.get('username')}")
                # تسجيل الدخول التلقائي
                app.show_dashboard_with_auto_login(auto_login_data)
            else:
                # عرض نافذة تسجيل الدخول العادية
                print(" محاولة عرض نافذة تسجيل الدخول...")
                app.show_login_window()
                print(" تم استدعاء show_login_window")
                
        except Exception as e:
            print(f" خطأ في التحقق من تسجيل الدخول التلقائي: {e}")
            # عرض نافذة تسجيل الدخول العادية في حالة الخطأ
            app.show_login_window()
        
        # تشغيل التطبيق
        print(" بدء تشغيل التطبيق...")
        return app.exec()
        
    except Exception as e:
        logging.error(f"خطأ في الدالة الرئيسية: {e}")
        print(f"خطأ في تشغيل التطبيق: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
