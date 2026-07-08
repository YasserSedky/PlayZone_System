"""
أدوات إعادة تشغيل البرنامج التلقائي
Auto Restart Utilities
"""

import sys
import os
import subprocess
import json
from typing import Optional, Dict, Any
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import QTimer


def save_auto_login_data(cashier_id: int, username: str, role: str):
    """حفظ بيانات تسجيل الدخول التلقائي"""
    try:
        auto_login_data = {
            'cashier_id': cashier_id,
            'username': username,
            'role': role,
            'timestamp': str(datetime.now()),
            'auto_login': True
        }
        
        # حفظ البيانات في ملف مؤقت
        temp_file = os.path.join(os.path.dirname(__file__), '..', 'temp_auto_login.json')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(auto_login_data, f, ensure_ascii=False, indent=2)
        
        print(f"تم حفظ بيانات تسجيل الدخول التلقائي للكاشير {username}")
        return True
        
    except Exception as e:
        print(f"خطأ في حفظ بيانات تسجيل الدخول التلقائي: {e}")
        return False


def load_auto_login_data() -> Optional[Dict[str, Any]]:
    """تحميل بيانات تسجيل الدخول التلقائي"""
    try:
        temp_file = os.path.join(os.path.dirname(__file__), '..', 'temp_auto_login.json')
        
        if not os.path.exists(temp_file):
            return None
        
        with open(temp_file, 'r', encoding='utf-8') as f:
            auto_login_data = json.load(f)
        
        # التحقق من صحة البيانات
        if not auto_login_data.get('auto_login'):
            return None
        
        # حذف الملف بعد القراءة
        os.remove(temp_file)
        
        print(f"تم تحميل بيانات تسجيل الدخول التلقائي للكاشير {auto_login_data.get('username')}")
        return auto_login_data
        
    except Exception as e:
        print(f"خطأ في تحميل بيانات تسجيل الدخول التلقائي: {e}")
        return None


def restart_application_with_auto_login(cashier_id: int, username: str, role: str, parent_widget=None):
    """إعادة تشغيل البرنامج مع تسجيل دخول تلقائي"""
    try:
        # حفظ بيانات تسجيل الدخول التلقائي
        if not save_auto_login_data(cashier_id, username, role):
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "خطأ",
                    "فشل في حفظ بيانات تسجيل الدخول التلقائي"
                )
            return False
        
        # إظهار رسالة للمستخدم
        if parent_widget:
            QMessageBox.information(
                parent_widget,
                "إعادة تشغيل البرنامج",
                f"سيتم إعادة تشغيل البرنامج على حساب الكاشير: {username}\n\n"
                "يرجى الانتظار..."
            )
        
        # إعادة تشغيل البرنامج
        restart_application()
        return True
        
    except Exception as e:
        print(f"خطأ في إعادة تشغيل البرنامج: {e}")
        if parent_widget:
            QMessageBox.critical(
                parent_widget,
                "خطأ",
                f"فشل في إعادة تشغيل البرنامج: {str(e)}"
            )
        return False


def restart_application():
    """إعادة تشغيل البرنامج"""
    try:
        # الحصول على مسار البرنامج الحالي
        current_script = sys.argv[0]
        
        print(f"إعادة تشغيل البرنامج: {current_script}")
        
        # إعادة تشغيل البرنامج
        if sys.platform == "win32":
            # Windows - استخدام batch file لإعادة التشغيل
            batch_content = f'''@echo off
timeout /t 2 /nobreak >nul
start "" "{sys.executable}" "{current_script}" {" ".join(sys.argv[1:])}
del "%~f0"
'''
            batch_file = os.path.join(os.path.dirname(__file__), '..', 'restart_temp.bat')
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # تشغيل batch file
            subprocess.Popen([batch_file], shell=True)
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي بعد تأخير قصير
            import threading
            import time
            
            def delayed_exit():
                time.sleep(3)  # انتظار 3 ثوان
                import os
                os._exit(0)
            
            exit_thread = threading.Thread(target=delayed_exit)
            exit_thread.daemon = True
            exit_thread.start()
            
        else:
            # Linux/Mac
            subprocess.Popen([sys.executable, current_script] + sys.argv[1:])
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي
            import os
            os._exit(0)
        
    except Exception as e:
        print(f"خطأ في إعادة تشغيل البرنامج: {e}")
        # في حالة الفشل، إغلاق البرنامج بقوة
        import os
        os._exit(1)


def schedule_restart_with_auto_login(cashier_id: int, username: str, role: str, 
                                   delay_ms: int = 2000, parent_widget=None):
    """جدولة إعادة تشغيل البرنامج مع تأخير"""
    try:
        print(f"بدء جدولة إعادة التشغيل للكاشير: {username}")
        
        # حفظ بيانات تسجيل الدخول التلقائي
        if not save_auto_login_data(cashier_id, username, role):
            print("فشل في حفظ بيانات تسجيل الدخول التلقائي")
            return False
        
        print(f"تم حفظ بيانات تسجيل الدخول التلقائي للكاشير: {username}")
        
        # إعادة التشغيل البسيطة
        simple_restart()
        
        return True
        
    except Exception as e:
        print(f"خطأ في إعادة تشغيل البرنامج: {e}")
        return False


def restart_with_delay():
    """إعادة تشغيل البرنامج مع تأخير قصير"""
    try:
        import threading
        import time
        
        def delayed_restart():
            time.sleep(1)  # انتظار ثانية واحدة
            force_restart_application()
        
        # تشغيل إعادة التشغيل في thread منفصل
        restart_thread = threading.Thread(target=delayed_restart)
        restart_thread.daemon = True
        restart_thread.start()
        
        return True
        
    except Exception as e:
        print(f"خطأ في إعادة التشغيل مع التأخير: {e}")
        return False


def simple_restart():
    """إعادة تشغيل بسيطة"""
    try:
        # الحصول على مسار البرنامج الحالي
        current_script = sys.argv[0]
        
        print(f"إعادة تشغيل بسيطة: {current_script}")
        
        if sys.platform == "win32":
            # Windows - استخدام start مباشرة
            import subprocess
            import os
            
            # بدء البرنامج الجديد
            subprocess.Popen([
                "start", "", sys.executable, current_script
            ] + sys.argv[1:], shell=True)
            
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي
            os._exit(0)
            
        else:
            # Linux/Mac
            subprocess.Popen([sys.executable, current_script] + sys.argv[1:])
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي
            import os
            os._exit(0)
        
    except Exception as e:
        print(f"خطأ في إعادة التشغيل البسيطة: {e}")
        import os
        os._exit(1)


def force_restart_application():
    """إعادة تشغيل البرنامج بقوة"""
    try:
        # الحصول على مسار البرنامج الحالي
        current_script = sys.argv[0]
        
        print(f"إعادة تشغيل البرنامج بقوة: {current_script}")
        
        if sys.platform == "win32":
            # Windows - استخدام طريقة مختلفة
            import subprocess
            import os
            
            # إنشاء ملف batch لإعادة التشغيل
            batch_content = f'''@echo off
start "" "{sys.executable}" "{current_script}" {" ".join(sys.argv[1:])}
'''
            batch_file = os.path.join(os.path.dirname(__file__), '..', 'restart_now.bat')
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # تشغيل batch file
            subprocess.Popen([batch_file], shell=True)
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي
            os._exit(0)
            
        else:
            # Linux/Mac
            subprocess.Popen([sys.executable, current_script] + sys.argv[1:])
            print("تم بدء البرنامج الجديد")
            
            # إغلاق البرنامج الحالي
            import os
            os._exit(0)
        
    except Exception as e:
        print(f"خطأ في إعادة تشغيل البرنامج: {e}")
        import os
        os._exit(1)


# إضافة استيراد datetime
from datetime import datetime
