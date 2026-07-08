"""
نافذة تسجيل دخول الورديات
Shift Login Window
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox, QComboBox,
    QSpacerItem, QSizePolicy, QApplication, QDialog, QFormLayout,
    QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.shift_controller import ShiftController
from utils.notifications import show_error, show_success

class ShiftLoginWindow(QMainWindow):
    """نافذة تسجيل دخول الورديات"""
    
    # إشارات
    shift_login_successful = Signal(dict)  # بيانات الوردية
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.shift_controller = ShiftController()
        self.setup_ui()
        self.setup_connections()
        self.load_shift_templates()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تسجيل دخول الوردية - نظام إدارة محل بلايستيشن")
        self.setFixedSize(500, 400)
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                padding: 15px;
                border: 3px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                background-color: white;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #4CAF50;
                border-width: 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                border-radius: 8px;
                font-weight: bold;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTextEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # عنوان التطبيق
        title_label = QLabel("⏰ تسجيل دخول الوردية")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # معلومات الكاشير
        cashier_label = QLabel(f"الكاشير: {self.current_user.get('username', 'غير محدد')}")
        cashier_label.setAlignment(Qt.AlignCenter)
        cashier_label.setStyleSheet("font-size: 16px; color: #666; margin-bottom: 20px;")
        main_layout.addWidget(cashier_label)
        
        # نموذج تسجيل دخول الوردية
        self.create_shift_login_form(main_layout)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px; margin-top: 10px;")
        self.error_label.hide()
        main_layout.addWidget(self.error_label)
    
    def create_shift_login_form(self, parent_layout):
        """إنشاء نموذج تسجيل دخول الوردية"""
        # حقل اختيار الوردية
        shift_label = QLabel("الوردية:")
        shift_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        parent_layout.addWidget(shift_label)
        
        self.shift_combo = QComboBox()
        self.shift_combo.setPlaceholderText("اختر الوردية")
        parent_layout.addWidget(self.shift_combo)
        
        # حقل كلمة المرور
        password_label = QLabel("كلمة مرور الوردية:")
        password_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        parent_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة مرور الوردية")
        self.password_input.setEchoMode(QLineEdit.Password)
        parent_layout.addWidget(self.password_input)
        
        # حقل الملاحظات
        notes_label = QLabel("ملاحظات (اختياري):")
        notes_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        parent_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات حول الوردية...")
        parent_layout.addWidget(self.notes_input)
        
        # زر تسجيل الدخول
        self.login_button = QPushButton("تسجيل دخول الوردية")
        parent_layout.addWidget(self.login_button)
    
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        try:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception as e:
            self.move(300, 300)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.login_button.clicked.connect(self.handle_shift_login)
        self.password_input.returnPressed.connect(self.handle_shift_login)
        
        # إعداد التايمر لإخفاء رسالة الخطأ
        self.error_timer = QTimer(self)
        self.error_timer.timeout.connect(self.hide_error)
        self.error_timer.setSingleShot(True)
    
    def load_shift_templates(self):
        """تحميل قوالب الورديات المتاحة"""
        try:
            templates = self.shift_controller.get_shift_templates(active_only=True)
            
            self.shift_combo.clear()
            for template in templates:
                self.shift_combo.addItem(template['name'], template)
                
        except Exception as e:
            print(f"خطأ في تحميل قوالب الورديات: {e}")
            self.show_error("خطأ في تحميل قوالب الورديات")
    
    def handle_shift_login(self):
        """معالج تسجيل دخول الوردية"""
        try:
            # التحقق من الحقول المطلوبة
            if self.shift_combo.currentIndex() == -1:
                self.show_error("يرجى اختيار وردية")
                return
            
            password = self.password_input.text().strip()
            if not password:
                self.show_error("يرجى إدخال كلمة مرور الوردية")
                return
            
            # تعطيل زر تسجيل الدخول
            self.login_button.setEnabled(False)
            self.login_button.setText("جاري تسجيل الدخول...")
            
            # الحصول على بيانات القالب المختار
            template_data = self.shift_combo.currentData()
            shift_name = template_data['name']
            notes = self.notes_input.toPlainText().strip()
            
            # تسجيل دخول الوردية
            result = self.shift_controller.login_to_shift(
                shift_name=shift_name,
                password=password,
                cashier_id=self.current_user['id'],
                notes=notes
            )
            
            if result['success']:
                # تسجيل الدخول بنجاح
                self.show_success(result['message'])
                
                # إرسال إشارة النجاح
                self.shift_login_successful.emit(result['shift_data'])
                
                # إغلاق النافذة بعد ثانيتين
                QTimer.singleShot(2000, self.close)
                
            else:
                self.show_error(result['message'])
                
        except Exception as e:
            self.show_error(f"خطأ في تسجيل دخول الوردية: {str(e)}")
            
        finally:
            # إعادة تفعيل زر تسجيل الدخول
            self.login_button.setEnabled(True)
            self.login_button.setText("تسجيل دخول الوردية")
    
    def show_error(self, message: str):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: red; font-size: 12px; margin-top: 10px;")
        self.error_label.show()
        self.error_timer.start(5000)  # إخفاء بعد 5 ثوان
    
    def show_success(self, message: str):
        """عرض رسالة نجاح"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: green; font-size: 12px; margin-top: 10px;")
        self.error_label.show()
        self.error_timer.start(3000)  # إخفاء بعد 3 ثوان
    
    def hide_error(self):
        """إخفاء رسالة الخطأ"""
        self.error_label.hide()
        self.error_label.setStyleSheet("color: red; font-size: 12px; margin-top: 10px;")
    
    def keyPressEvent(self, event):
        """معالج الضغط على المفاتيح"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_shift_login()
        else:
            super().keyPressEvent(event)

class ShiftLoginDialog(QDialog):
    """نافذة حوار تسجيل دخول الوردية"""
    
    # إشارات
    shift_login_successful = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.shift_controller = ShiftController()
        self.setup_ui()
        self.load_shift_templates()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تسجيل دخول إلى وردية")
        self.setFixedSize(450, 350)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("تسجيل دخول إلى وردية")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الكاشير
        cashier_label = QLabel(f"الكاشير: {self.current_user.get('username', 'غير محدد')}")
        cashier_label.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(cashier_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اختيار الوردية
        self.shift_combo = QComboBox()
        self.shift_combo.setPlaceholderText("اختر الوردية")
        form_layout.addRow("الوردية:", self.shift_combo)
        
        # كلمة المرور
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("كلمة مرور الوردية")
        form_layout.addRow("كلمة المرور:", self.password_input)
        
        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_shift_templates(self):
        """تحميل قوالب الورديات المتاحة"""
        try:
            templates = self.shift_controller.get_shift_templates(active_only=True)
            
            self.shift_combo.clear()
            for template in templates:
                self.shift_combo.addItem(template['name'], template)
                
        except Exception as e:
            print(f"خطأ في تحميل قوالب الورديات: {e}")
    
    def accept(self):
        """التحقق من البيانات وتسجيل الدخول"""
        if self.shift_combo.currentIndex() == -1:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار وردية")
            return
        
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال كلمة المرور")
            return
        
        try:
            # الحصول على بيانات القالب المختار
            template_data = self.shift_combo.currentData()
            shift_name = template_data['name']
            notes = self.notes_input.toPlainText().strip()
            
            # تسجيل دخول الوردية
            result = self.shift_controller.login_to_shift(
                shift_name=shift_name,
                password=password,
                cashier_id=self.current_user['id'],
                notes=notes
            )
            
            if result['success']:
                QMessageBox.information(self, "نجح", result['message'])
                self.shift_login_successful.emit(result['shift_data'])
                super().accept()
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تسجيل الدخول: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # بيانات تجريبية للاختبار
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    window = ShiftLoginWindow(test_user)
    window.show()
    sys.exit(app.exec())
