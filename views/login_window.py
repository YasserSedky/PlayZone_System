"""
نافذة تسجيل الدخول
Login Window
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox, QCheckBox,
    QSpacerItem, QSizePolicy, QApplication, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_model import UserModel
from utils.security import hash_password, verify_password
from utils.notifications import show_error, show_success
from config import get_app_config

class LoginWindow(QMainWindow):
    """نافذة تسجيل الدخول"""
    
    # إشارات
    login_successful = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.app_config = get_app_config()
        self.setup_ui()
        self.setup_connections()
        self.setup_animations()
        self.load_users()  # تحميل المستخدمين عند بدء التطبيق
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تسجيل الدخول - نظام إدارة محل بلايستيشن")
        self.setFixedSize(450, 350)  # حجم أصغر وأكثر احترافية
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #4CAF50;
                border-radius: 15px;
                background-color: white;
                selection-background-color: #4CAF50;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 18px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QCheckBox {
                font-size: 16px;
                color: #666;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(25)
        
        # إضافة مساحة في الأعلى
        main_layout.addStretch(1)
        
        # نموذج تسجيل الدخول
        self.create_login_form(main_layout)
        
        # إضافة مساحة في الأسفل
        main_layout.addStretch(1)
    
    def load_users(self):
        """تحميل المستخدمين في القائمة المنسدلة"""
        try:
            # مسح القائمة الحالية
            self.username_combo.clear()
            
            # جلب جميع المستخدمين المفعلين
            users = self.user_model.get_all_users()
            enabled_users = [user for user in users if user.get('enabled', True)]
            
            if not enabled_users:
                self.username_combo.addItem("لا يوجد مستخدمين", None)
                return
            
            # إضافة المستخدمين إلى القائمة
            for user in enabled_users:
                role = user.get('role', '')
                if role == 'admin':
                    role_text = "مدير"
                elif role == 'developer':
                    role_text = "مطور"
                else:
                    role_text = "كاشير"
                display_text = f"{user.get('username', 'غير محدد')} ({role_text})"
                self.username_combo.addItem(display_text, user)
            
            # تحديث القائمة حسب نوع المستخدم المحدد
            self.on_user_type_changed()
            
        except Exception as e:
            print(f"خطأ في تحميل المستخدمين: {e}")
            self.username_combo.addItem("خطأ في تحميل المستخدمين", None)
    
    def on_user_type_changed(self):
        """عند تغيير نوع المستخدم"""
        try:
            selected_role = self.user_type_combo.currentData()
            current_user = self.username_combo.currentData()
            
            # مسح القائمة
            self.username_combo.clear()
            
            # جلب المستخدمين حسب النوع المحدد
            users = self.user_model.get_users_by_role(selected_role)
            enabled_users = [user for user in users if user.get('enabled', True)]
            
            if not enabled_users:
                if selected_role == 'admin':
                    role_text = "مدير"
                elif selected_role == 'developer':
                    role_text = "مطور"
                else:
                    role_text = "كاشير"
                self.username_combo.addItem(f"لا يوجد {role_text} مفعل", None)
                return
            
            # إضافة المستخدمين إلى القائمة
            for user in enabled_users:
                role = user.get('role', '')
                if role == 'admin':
                    role_text = "مدير"
                elif role == 'developer':
                    role_text = "مطور"
                else:
                    role_text = "كاشير"
                display_text = f"{user.get('username', 'غير محدد')} ({role_text})"
                self.username_combo.addItem(display_text, user)
            
        except Exception as e:
            print(f"خطأ في تحديث قائمة المستخدمين: {e}")
    
    def create_logo_section(self, parent_layout):
        """إنشاء قسم الشعار"""
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # عنوان التطبيق
        title_label = QLabel("نظام إدارة محل بلايستيشن")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin: 10px;
            }
        """)
        
        # وصف التطبيق
        subtitle_label = QLabel("إدارة شاملة للأجهزة والفواتير والعملاء")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                margin: 5px;
            }
        """)
        
        logo_layout.addWidget(title_label)
        logo_layout.addWidget(subtitle_label)
        
        parent_layout.addWidget(logo_frame)
    
    def create_login_form(self, parent_layout):
        """إنشاء نموذج تسجيل الدخول الاحترافي"""
        # حقل نوع المستخدم
        self.user_type_combo = QComboBox()
        self.user_type_combo.addItem("مدير", "admin")
        self.user_type_combo.addItem("كاشير", "cashier")
        self.user_type_combo.addItem("مطور", "developer")
        self.user_type_combo.currentTextChanged.connect(self.on_user_type_changed)
        parent_layout.addWidget(self.user_type_combo)
        
        # حقل اختيار المستخدم
        self.username_combo = QComboBox()
        parent_layout.addWidget(self.username_combo)
        
        # حقل كلمة المرور
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        parent_layout.addWidget(self.password_input)
        
        # زر تسجيل الدخول
        self.login_button = QPushButton("تسجيل الدخول")
        parent_layout.addWidget(self.login_button)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: white; font-size: 14px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
        self.error_label.hide()
        parent_layout.addWidget(self.error_label)
    
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        try:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception as e:
            # في حالة فشل التوسيط، استخدم موضع افتراضي
            self.move(300, 300)
    
    def create_app_info(self, parent_layout):
        """إنشاء معلومات التطبيق"""
        info_label = QLabel("© 2024 نظام إدارة محل بلايستيشن")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 20px;")
        parent_layout.addWidget(info_label)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.login_button.clicked.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # إعداد التايمر لإخفاء رسالة الخطأ
        self.error_timer = QTimer(self)
        self.error_timer.timeout.connect(self.hide_error)
        self.error_timer.setSingleShot(True)
    
    def setup_animations(self):
        """إعداد الرسوم المتحركة"""
        # رسوم متحركة بسيطة للظهور
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
    
    def showEvent(self, event):
        """معالج حدث العرض"""
        super().showEvent(event)
        self.fade_animation.start()
        self.password_input.setFocus()
    
    def handle_login(self):
        """معالج تسجيل الدخول"""
        try:
            selected_user = self.username_combo.currentData()
            password = self.password_input.text().strip()
            
            # التحقق من الحقول المطلوبة
            if not selected_user:
                self.show_error("يرجى اختيار مستخدم من القائمة")
                return
            
            if not password:
                self.show_error("يرجى إدخال كلمة المرور")
                return
            
            # تعطيل زر تسجيل الدخول
            self.login_button.setEnabled(False)
            self.login_button.setText("جاري التحقق...")
            
            # التحقق من كلمة المرور
            if verify_password(password, selected_user['password_hash']):
                # التحقق من حالة الحساب
                if not selected_user.get('enabled', True):
                    self.show_error("الحساب معطل، يرجى التواصل مع المدير")
                    self.reset_login_button()
                    return
                
                # تسجيل الدخول بنجاح
                self.show_success("تم تسجيل الدخول بنجاح")
                
                # إرسال إشارة النجاح
                self.login_successful.emit(selected_user)
            else:
                self.show_error("كلمة المرور غير صحيحة")
                
        except Exception as e:
            self.show_error(f"خطأ في تسجيل الدخول: {str(e)}")
            
        finally:
            # إعادة تفعيل زر تسجيل الدخول
            self.reset_login_button()
    
    def reset_login_button(self):
        """إعادة تعيين زر تسجيل الدخول"""
        self.login_button.setEnabled(True)
        self.login_button.setText("تسجيل الدخول")
    
    def show_error(self, message: str):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.show()
        self.error_timer.start(5000)  # إخفاء بعد 5 ثوان
    
    def show_success(self, message: str):
        """عرض رسالة نجاح"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: #51cf66; font-size: 14px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.show()
        self.error_timer.start(3000)  # إخفاء بعد 3 ثوان
    
    def hide_error(self):
        """إخفاء رسالة الخطأ"""
        self.error_label.hide()
        self.error_label.setStyleSheet("color: white; font-size: 14px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
    
    def shake_animation(self):
        """رسوم متحركة للاهتزاز"""
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            
            animation = QPropertyAnimation(self, b"pos")
            animation.setDuration(100)
            animation.setLoopCount(3)
            animation.setKeyValueAt(0, self.pos())
            animation.setKeyValueAt(0.5, self.pos() + self.rect().topLeft() + self.rect().topLeft() * 0.1)
            animation.setKeyValueAt(1, self.pos())
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            animation.start()
            
        except Exception as e:
            pass  # تجاهل الأخطاء في الرسوم المتحركة
    
    def save_login_info(self, username: str):
        """حفظ معلومات تسجيل الدخول"""
        try:
            # يمكن إضافة منطق حفظ معلومات تسجيل الدخول هنا
            pass
        except Exception as e:
            pass
    
    def load_saved_login_info(self):
        """تحميل معلومات تسجيل الدخول المحفوظة"""
        try:
            # يمكن إضافة منطق تحميل معلومات تسجيل الدخول هنا
            pass
        except Exception as e:
            pass
    
    def keyPressEvent(self, event):
        """معالج الضغط على المفاتيح"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_login()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """معالج الضغط على الماوس للتحريك"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """معالج حركة الماوس للتحريك"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def closeEvent(self, event):
        """معالج إغلاق النافذة"""
        try:
            # إضافة أي منطق تنظيف مطلوب هنا
            event.accept()
        except Exception as e:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
