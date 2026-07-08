"""
واجهة إدارة الكاشيرات
Cashier Management Interface
"""

import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_model import UserModel
from controllers.auth_controller import AuthController
from utils.permissions import can_manage_cashiers, can_change_passwords
from utils.security import hash_password, verify_password
from utils.notifications import show_success, show_error, show_warning
import logging

logger = logging.getLogger(__name__)

class CashierCard(QFrame):
    """كارت الكاشير"""
    
    # إشارات
    cashier_clicked = Signal(dict)  # بيانات الكاشير
    edit_requested = Signal(dict)   # طلب تعديل
    delete_requested = Signal(dict) # طلب حذف
    
    def __init__(self, cashier_data):
        super().__init__()
        self.cashier_data = cashier_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(345, 440)  # حجم أكبر لملء الصف بالكامل
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border-radius: 10px;
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px;
                font-size: 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # التخطيط الرئيسي
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # هوامش أكبر للحجم الأكبر
        layout.setSpacing(16)  # مسافات أكبر بين العناصر
        
        # عنوان الكارت
        self.title_label = QLabel("كاشير")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # اسم المستخدم
        self.username_label = QLabel("")
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.username_label)
        
        # الاسم الكامل
        self.fullname_label = QLabel("")
        self.fullname_label.setAlignment(Qt.AlignCenter)
        self.fullname_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.fullname_label)
        
        # رقم الهاتف
        self.phone_label = QLabel("")
        self.phone_label.setAlignment(Qt.AlignCenter)
        self.phone_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.phone_label)
        
        # حالة الحساب
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # آخر تسجيل دخول
        self.last_login_label = QLabel("")
        self.last_login_label.setAlignment(Qt.AlignCenter)
        self.last_login_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.last_login_label)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("تعديل")
        self.edit_btn.setStyleSheet("background-color: #f39c12;")
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setStyleSheet("background-color: #e74c3c;")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        buttons_layout.addWidget(self.delete_btn)
        
        layout.addLayout(buttons_layout)
    
    def update_display(self):
        """تحديث عرض الكارت"""
        username = self.cashier_data.get('username', 'غير محدد')
        full_name = self.cashier_data.get('full_name', '')
        phone = self.cashier_data.get('phone', '')
        enabled = self.cashier_data.get('enabled', True)
        last_login = self.cashier_data.get('last_login')
        
        # تحديث البيانات
        self.username_label.setText(f"المستخدم: {username}")
        self.fullname_label.setText(f"الاسم: {full_name if full_name else 'غير محدد'}")
        self.phone_label.setText(f"الهاتف: {phone if phone else 'غير محدد'}")
        
        # تحديث الحالة
        if enabled:
            self.status_label.setText("نشط")
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #27ae60;
                    color: white;
                    border: 2px solid #229954;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 5px;
                    font-size: 12px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
        else:
            self.status_label.setText("معطل")
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #95a5a6;
                    color: white;
                    border: 2px solid #7f8c8d;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 5px;
                    font-size: 12px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
        
        # تحديث آخر تسجيل دخول
        if last_login:
            try:
                if isinstance(last_login, str):
                    last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                self.last_login_label.setText(f"آخر دخول: {last_login.strftime('%Y-%m-%d %H:%M')}")
            except:
                self.last_login_label.setText("آخر دخول: غير محدد")
        else:
            self.last_login_label.setText("آخر دخول: لم يسجل دخول")
    
    def on_edit_clicked(self):
        """معالج النقر على تعديل"""
        self.edit_requested.emit(self.cashier_data)
    
    def on_delete_clicked(self):
        """معالج النقر على حذف"""
        self.delete_requested.emit(self.cashier_data)
    
    def mousePressEvent(self, event):
        """معالج الضغط على الكارت"""
        if event.button() == Qt.LeftButton:
            self.cashier_clicked.emit(self.cashier_data)

class CashierManagementWindow(QMainWindow):
    """نافذة إدارة الكاشيرات"""
    
    # إشارات
    cashier_selected = Signal(dict)
    logout_requested = Signal()
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.cashier_cards = {}
        self.user_model = UserModel()
        self.auth_controller = AuthController()
        self.setup_ui()
        self.setup_connections()
        self.load_cashiers()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الكاشيرات - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1500, 650)  # حجم مناسب للكروت الأكبر
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # شريط الأدوات
        self.create_toolbar(main_layout)
        
        # منطقة الكاشيرات
        self.create_cashiers_area(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("👥 إدارة الكاشيرات")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # أزرار التحكم
        self.add_cashier_btn = QPushButton("إضافة كاشير")
        self.add_cashier_btn.setStyleSheet("background-color: #27ae60;")
        self.add_cashier_btn.clicked.connect(self.add_cashier)
        toolbar_layout.addWidget(self.add_cashier_btn)
        
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.setStyleSheet("background-color: #f39c12;")
        self.refresh_btn.clicked.connect(self.load_cashiers)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # زر تسجيل الخروج
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setStyleSheet("background-color: #e74c3c;")
        self.logout_btn.clicked.connect(self.handle_logout)
        toolbar_layout.addWidget(self.logout_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_cashiers_area(self, parent_layout):
        """إنشاء منطقة الكاشيرات"""
        # مجموعة الكاشيرات
        cashiers_group = QGroupBox("الكاشيرات")
        cashiers_layout = QVBoxLayout(cashiers_group)
        
        # الـ widget المحتوي للكاشيرات
        self.cashiers_widget = QWidget()
        self.cashiers_layout = QHBoxLayout(self.cashiers_widget)  # تغيير إلى HBoxLayout للصف الواحد
        self.cashiers_layout.setSpacing(15)  # تقليل المسافة بين الكروت
        self.cashiers_layout.setContentsMargins(15, 15, 15, 15)  # تقليل الهوامش
        self.cashiers_layout.setAlignment(Qt.AlignTop)  # محاذاة في الأعلى
        
        cashiers_layout.addWidget(self.cashiers_widget)
        
        parent_layout.addWidget(cashiers_group)
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات الكاشيرات")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات الكاشيرات
        self.total_cashiers_label = QLabel("إجمالي الكاشيرات: 0")
        self.total_cashiers_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_cashiers_label)
        
        self.active_cashiers_label = QLabel("نشط: 0")
        self.active_cashiers_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.active_cashiers_label)
        
        self.inactive_cashiers_label = QLabel("معطل: 0")
        self.inactive_cashiers_label.setStyleSheet("font-size: 14px; color: #95a5a6; font-weight: bold;")
        stats_layout.addWidget(self.inactive_cashiers_label)
        
        parent_layout.addLayout(stats_layout)
    
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        try:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception as e:
            self.move(200, 200)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        pass
    
    def clear_cashiers_layout(self):
        """مسح جميع العناصر من تخطيط الكاشيرات"""
        try:
            while self.cashiers_layout.count():
                child = self.cashiers_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
                elif child.spacerItem():
                    # لا نحذف spacer items، سنحتفظ بها
                    pass
        except Exception as e:
            logger.error(f"خطأ في مسح تخطيط الكاشيرات: {e}")
    
    def load_cashiers(self):
        """تحميل الكاشيرات"""
        try:
            # مسح الكاشيرات الموجودة
            self.clear_cashiers_layout()
            
            self.cashier_cards.clear()
            
            # تحميل الكاشيرات من قاعدة البيانات
            cashiers = self.user_model.get_cashiers()
            
            # إنشاء كروت الكاشيرات في تخطيط صف واحد 4x1 (حد أقصى 4 كاشيرز)
            for cashier in cashiers:
                card = CashierCard(cashier)
                card.cashier_clicked.connect(self.on_cashier_clicked)
                card.edit_requested.connect(self.edit_cashier)
                card.delete_requested.connect(self.delete_cashier)
                self.cashier_cards[cashier['id']] = card
                
                # إضافة الكارت إلى التخطيط الأفقي
                self.cashiers_layout.addWidget(card)
            
            # إضافة مساحة مرنة في النهاية لدفع الكروت إلى اليسار
            self.cashiers_layout.addStretch()
            
            # تحديث الإحصائيات
            self.update_stats(cashiers)
            
            # طباعة للتأكد من التحميل
            print(f"تم تحميل {len(cashiers)} كاشير")
            
        except Exception as e:
            logger.error(f"خطأ في تحميل الكاشيرات: {e}")
            show_error("خطأ في تحميل الكاشيرات", str(e))
    
    def update_stats(self, cashiers):
        """تحديث الإحصائيات"""
        total = len(cashiers)
        active = len([c for c in cashiers if c.get('enabled', True)])
        inactive = total - active
        
        self.total_cashiers_label.setText(f"إجمالي الكاشيرات: {total}/4")
        self.active_cashiers_label.setText(f"نشط: {active}")
        self.inactive_cashiers_label.setText(f"معطل: {inactive}")
        
        # تحديث حالة زر إضافة كاشير
        if total >= 4:
            self.add_cashier_btn.setEnabled(False)
            self.add_cashier_btn.setText("حد أقصى (4/4)")
            self.add_cashier_btn.setStyleSheet("background-color: #95a5a6; color: white;")
        else:
            self.add_cashier_btn.setEnabled(True)
            self.add_cashier_btn.setText("إضافة كاشير")
            self.add_cashier_btn.setStyleSheet("background-color: #27ae60;")
    
    def on_cashier_clicked(self, cashier_data):
        """معالج النقر على الكاشير"""
        logger.info(f"تم النقر على الكاشير: {cashier_data['id']}")
        self.cashier_selected.emit(cashier_data)
        
        # عرض نافذة تفاصيل الكاشير
        self.show_cashier_details(cashier_data)
    
    def show_cashier_details(self, cashier_data):
        """عرض نافذة تفاصيل الكاشير"""
        dialog = CashierDetailsDialog(cashier_data, self.current_user)
        dialog.exec()
    
    def add_cashier(self):
        """إضافة كاشير جديد"""
        if not can_manage_cashiers(self.current_user.get('role', '')):
            show_error("خطأ في الصلاحيات", "ليس لديك صلاحية لإضافة كاشيرات")
            return
        
        # التحقق من الحد الأقصى للكاشيرات (4 كاشيرات)
        try:
            current_cashiers = self.user_model.get_cashiers()
            if len(current_cashiers) >= 4:
                show_error("حد أقصى للكاشيرات", "لا يمكن إضافة أكثر من 4 كاشيرات في النظام")
                return
        except Exception as e:
            print(f"خطأ في التحقق من عدد الكاشيرات: {e}")
        
        dialog = AddCashierDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            # إضافة الكاشير الجديد
            print("تم قبول إضافة الكاشير، جاري تحديث العرض...")
            self.load_cashiers()
            print("تم تحديث عرض الكاشيرات")
    
    def edit_cashier(self, cashier_data):
        """تعديل كاشير"""
        if not can_manage_cashiers(self.current_user.get('role', '')):
            show_error("خطأ في الصلاحيات", "ليس لديك صلاحية لتعديل الكاشيرات")
            return
        
        dialog = EditCashierDialog(cashier_data, self.current_user)
        if dialog.exec() == QDialog.Accepted:
            # تحديث الكاشير
            self.load_cashiers()
    
    def delete_cashier(self, cashier_data):
        """حذف كاشير"""
        if not can_manage_cashiers(self.current_user.get('role', '')):
            show_error("خطأ في الصلاحيات", "ليس لديك صلاحية لحذف الكاشيرات")
            return
        
        # تأكيد الحذف
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            f"هل أنت متأكد من حذف الكاشير '{cashier_data.get('username', '')}'؟\n\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.user_model.delete_user(cashier_data['id'])
                if success:
                    show_success("تم الحذف", f"تم حذف الكاشير '{cashier_data.get('username', '')}' بنجاح")
                    self.load_cashiers()
                else:
                    show_error("خطأ في الحذف", "فشل في حذف الكاشير")
            except Exception as e:
                logger.error(f"خطأ في حذف الكاشير: {e}")
                show_error("خطأ في الحذف", str(e))
    
    def handle_logout(self):
        """معالج تسجيل الخروج"""
        reply = QMessageBox.question(
            self,
            "تسجيل الخروج",
            "هل أنت متأكد من تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

class AddCashierDialog(QDialog):
    """نافذة إضافة كاشير جديد"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.user_model = UserModel()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إضافة كاشير جديد")
        self.setFixedSize(500, 650)
        self.setModal(True)
        
        # تطبيق الخلفية المتدرجة الحديثة
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 15px;
                font-size: 14px;
                color: #333;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 15px;
                font-size: 14px;
                color: #333;
            }
            QTextEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
            QCheckBox {
                color: #333;
                font-size: 14px;
                font-weight: bold;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #667eea;
                border-radius: 10px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("إضافة كاشير جديد")
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 25px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # حقول البيانات
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setMinimumHeight(45)
        layout.addWidget(self.username_input)
        
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("الاسم الكامل")
        self.fullname_input.setMinimumHeight(45)
        layout.addWidget(self.fullname_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        self.phone_input.setMinimumHeight(45)
        layout.addWidget(self.phone_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور")
        self.confirm_password_input.setMinimumHeight(45)
        layout.addWidget(self.confirm_password_input)
        
        # حالة الحساب
        self.enabled_checkbox = QCheckBox("الحساب نشط")
        self.enabled_checkbox.setChecked(True)
        layout.addWidget(self.enabled_checkbox)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ff6b6b;
            font-size: 14px;
            background-color: rgba(255, 107, 107, 0.2);
            padding: 15px;
            border-radius: 15px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)
        self.save_btn.clicked.connect(self.validate_and_accept)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
            QPushButton:pressed {
                background: #6c7b7d;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # تعيين التركيز الأولي
        self.username_input.setFocus()
    
    def validate_and_accept(self):
        """التحقق من البيانات وقبول النموذج"""
        # التحقق من البيانات
        username = self.username_input.text().strip()
        full_name = self.fullname_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        enabled = self.enabled_checkbox.isChecked()
        
        # التحقق من البيانات المطلوبة
        if not username:
            self.show_error("اسم المستخدم مطلوب")
            return
        
        if not password:
            self.show_error("كلمة المرور مطلوبة")
            return
        
        if password != confirm_password:
            self.show_error("كلمة المرور وتأكيدها غير متطابقتين")
            return
        
        if len(password) < 6:
            self.show_error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
            return
        
        # التحقق من توفر اسم المستخدم
        if not self.user_model.is_username_available(username):
            self.show_error("اسم المستخدم موجود بالفعل")
            return
        
        # التحقق من توفر رقم الهاتف
        if phone and not self.user_model.is_phone_available(phone):
            self.show_error("رقم الهاتف موجود بالفعل")
            return
        
        try:
            # إنشاء الكاشير
            user_data = {
                'username': username,
                'full_name': full_name,
                'phone': phone,
                'password': password,
                'role': 'cashier',
                'enabled': enabled,
                'created_by': self.current_user.get('id', 1)
            }
            
            user_id = self.user_model.create_user(user_data)
            
            if user_id:
                print(f"تم إنشاء الكاشير بنجاح مع ID: {user_id}")
                show_success("تم الإضافة", f"تم إنشاء كاشير '{username}' بنجاح")
                super().accept()
            else:
                print("فشل في إنشاء الكاشير - user_id is None")
                self.show_error("فشل في إنشاء الكاشير")
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الكاشير: {e}")
            self.show_error(str(e))
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()

class EditCashierDialog(QDialog):
    """نافذة تعديل كاشير"""
    
    def __init__(self, cashier_data, current_user):
        super().__init__()
        self.cashier_data = cashier_data
        self.current_user = current_user
        self.user_model = UserModel()
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تعديل كاشير")
        self.setFixedSize(600, 650)
        self.setModal(True)
        
        # تطبيق الخلفية المتدرجة الحديثة
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 15px;
                font-size: 14px;
                color: #333;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                padding: 15px;
                font-size: 14px;
                color: #333;
            }
            QTextEdit:focus {
                border-color: #667eea;
                background-color: white;
            }
            QCheckBox {
                color: #333;
                font-size: 14px;
                font-weight: bold;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #667eea;
                border-radius: 10px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.7);
                color: #333;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 10px;
            }
            QTabBar::tab:selected {
                background-color: #667eea;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: rgba(102, 126, 234, 0.8);
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("تعديل كاشير")
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 25px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات التعديل
        tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setContentsMargins(30, 30, 30, 30)
        basic_layout.setSpacing(20)
        
        # اسم المستخدم
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setMinimumHeight(45)
        basic_layout.addWidget(self.username_input)
        
        # الاسم الكامل
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("الاسم الكامل")
        self.fullname_input.setMinimumHeight(45)
        basic_layout.addWidget(self.fullname_input)
        
        # رقم الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        self.phone_input.setMinimumHeight(45)
        basic_layout.addWidget(self.phone_input)
        
        # حالة الحساب
        self.enabled_checkbox = QCheckBox("الحساب نشط")
        basic_layout.addWidget(self.enabled_checkbox)
        
        tab_widget.addTab(basic_tab, "المعلومات الأساسية")
        
        # تبويب تغيير كلمة المرور
        password_tab = QWidget()
        password_layout = QVBoxLayout(password_tab)
        password_layout.setContentsMargins(30, 30, 30, 30)
        password_layout.setSpacing(20)
        
        # كلمة المرور الجديدة
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("كلمة المرور الجديدة")
        self.new_password_input.setMinimumHeight(45)
        password_layout.addWidget(self.new_password_input)
        
        # تأكيد كلمة المرور
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        self.confirm_password_input.setMinimumHeight(45)
        password_layout.addWidget(self.confirm_password_input)
        
        # ملاحظة
        note_label = QLabel("اترك كلمة المرور فارغة إذا كنت لا تريد تغييرها")
        note_label.setStyleSheet("color: #7f8c8d; font-size: 12px; background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 10px;")
        password_layout.addWidget(note_label)
        
        tab_widget.addTab(password_tab, "تغيير كلمة المرور")
        
        layout.addWidget(tab_widget)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ff6b6b;
            font-size: 14px;
            background-color: rgba(255, 107, 107, 0.2);
            padding: 15px;
            border-radius: 15px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("حفظ التغييرات")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)
        self.save_btn.clicked.connect(self.validate_and_accept)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
            QPushButton:pressed {
                background: #6c7b7d;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # تعيين التركيز الأولي
        self.username_input.setFocus()
    
    def load_data(self):
        """تحميل بيانات الكاشير"""
        self.username_input.setText(self.cashier_data.get('username', ''))
        self.fullname_input.setText(self.cashier_data.get('full_name', ''))
        self.phone_input.setText(self.cashier_data.get('phone', ''))
        self.enabled_checkbox.setChecked(self.cashier_data.get('enabled', True))
    
    def validate_and_accept(self):
        """التحقق من البيانات وقبول النموذج"""
        # التحقق من البيانات
        username = self.username_input.text().strip()
        full_name = self.fullname_input.text().strip()
        phone = self.phone_input.text().strip()
        enabled = self.enabled_checkbox.isChecked()
        
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # التحقق من البيانات المطلوبة
        if not username:
            self.show_error("اسم المستخدم مطلوب")
            return
        
        # التحقق من كلمة المرور إذا تم إدخالها
        if new_password:
            if new_password != confirm_password:
                self.show_error("كلمة المرور وتأكيدها غير متطابقتين")
                return
            
            if len(new_password) < 6:
                self.show_error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
        
        # التحقق من توفر اسم المستخدم
        if not self.user_model.is_username_available(username, self.cashier_data['id']):
            self.show_error("اسم المستخدم موجود بالفعل")
            return
        
        # التحقق من توفر رقم الهاتف
        if phone and not self.user_model.is_phone_available(phone, self.cashier_data['id']):
            self.show_error("رقم الهاتف موجود بالفعل")
            return
        
        try:
            # تحديث البيانات الأساسية
            update_data = {
                'username': username,
                'full_name': full_name,
                'phone': phone,
                'enabled': enabled
            }
            
            # تحديث كلمة المرور إذا تم إدخالها
            if new_password:
                from utils.security import hash_password
                update_data['password_hash'] = hash_password(new_password)
            
            success = self.user_model.update_user(self.cashier_data['id'], **update_data)
            
            if success:
                show_success("تم التحديث", f"تم تحديث كاشير '{username}' بنجاح")
                super().accept()
            else:
                self.show_error("فشل في تحديث الكاشير")
                
        except Exception as e:
            logger.error(f"خطأ في تحديث الكاشير: {e}")
            self.show_error(str(e))
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()

class CashierDetailsDialog(QDialog):
    """نافذة تفاصيل الكاشير"""
    
    def __init__(self, cashier_data, current_user):
        super().__init__()
        self.cashier_data = cashier_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(f"تفاصيل الكاشير - {self.cashier_data.get('username', '')}")
        self.setFixedSize(650, 580)
        self.setModal(True)
        
        # تطبيق الخلفية المتدرجة الحديثة
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            QTabWidget::pane {
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.7);
                color: #333;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 10px;
            }
            QTabBar::tab:selected {
                background-color: #667eea;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: rgba(102, 126, 234, 0.8);
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل الكاشير - {self.cashier_data.get('username', '')}")
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 25px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات التفاصيل
        tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_info_tab = QWidget()
        basic_layout = QVBoxLayout(basic_info_tab)
        basic_layout.setContentsMargins(30, 30, 30, 30)
        basic_layout.setSpacing(20)
        
        # إطار المعلومات
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)
        
        # معلومات الكاشير
        cashier_info = [
            ("اسم المستخدم:", self.cashier_data.get('username', 'غير محدد')),
            ("الاسم الكامل:", self.cashier_data.get('full_name', 'غير محدد')),
            ("رقم الهاتف:", self.cashier_data.get('phone', 'غير محدد')),
            ("الدور:", "كاشير"),
            ("حالة الحساب:", "نشط" if self.cashier_data.get('enabled', True) else "معطل")
        ]
        
        for label_text, value_text in cashier_info:
            value_label = QLabel(value_text)
            value_label.setStyleSheet("""
                color: #333;
                font-size: 14px;
                background-color: rgba(102, 126, 234, 0.1);
                padding: 8px 12px;
                border-radius: 10px;
                margin-bottom: 10px;
                min-height: 20px;
            """)
            info_layout.addWidget(value_label)
        
        # تاريخ الإنشاء
        created_at = self.cashier_data.get('created_at')
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_label = QLabel(created_at.strftime('%Y-%m-%d %H:%M'))
                created_label.setStyleSheet("""
                    color: #333;
                    font-size: 14px;
                    background-color: rgba(102, 126, 234, 0.1);
                    padding: 8px 12px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    min-height: 20px;
                """)
                info_layout.addWidget(created_label)
            except:
                pass
        
        # آخر تسجيل دخول
        last_login = self.cashier_data.get('last_login')
        if last_login:
            try:
                if isinstance(last_login, str):
                    last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                last_login_label = QLabel(last_login.strftime('%Y-%m-%d %H:%M'))
                last_login_label.setStyleSheet("""
                    color: #333;
                    font-size: 14px;
                    background-color: rgba(102, 126, 234, 0.1);
                    padding: 8px 12px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    min-height: 20px;
                """)
                info_layout.addWidget(last_login_label)
            except:
                pass
        
        basic_layout.addWidget(info_frame)
        
        tab_widget.addTab(basic_info_tab, "المعلومات الأساسية")
        
        # تبويب الإحصائيات
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        stats_layout.setContentsMargins(30, 30, 30, 30)
        stats_layout.setSpacing(20)
        
        stats_label = QLabel("إحصائيات الكاشير - قيد التطوير")
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setStyleSheet("""
            font-size: 16px;
            color: #7f8c8d;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 20px;
            border-radius: 15px;
        """)
        stats_layout.addWidget(stats_label)
        
        tab_widget.addTab(stats_tab, "الإحصائيات")
        
        layout.addWidget(tab_widget)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.close_btn = QPushButton("إغلاق")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
            QPushButton:pressed {
                background: #6c7b7d;
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
