"""
لوحة إدارة الأجهزة
Device Management Panel
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.device_model import DeviceModel
from models.invoice_model import InvoiceModel
from models.user_model import UserModel
from utils.helpers import format_currency, format_time
from utils.notifications import show_success, show_error

class DevicePanelWindow(QMainWindow):
    """نافذة إدارة الأجهزة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.device_model = DeviceModel()
        self.invoice_model = InvoiceModel()
        self.user_model = UserModel()
        self.setup_ui()
        self.load_devices()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الأجهزة - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1000, 700)
        
        # الـ widget المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # عنوان النافذة
        title_label = QLabel("إدارة الأجهزة")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2E86AB;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # إنشاء الـ tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # تبويب عرض الأجهزة
        self.create_devices_tab()
        
        # تبويب إضافة جهاز جديد
        self.create_add_device_tab()
        
        # تبويب الجلسات النشطة
        self.create_active_sessions_tab()
    
    def create_devices_tab(self):
        """إنشاء تبويب عرض الأجهزة"""
        devices_widget = QWidget()
        devices_layout = QVBoxLayout(devices_widget)
        
        # أزرار التحكم
        controls_layout = QHBoxLayout()
        
        # عرض الكاشير الحالي
        self.current_cashier_label = QLabel(f"الكاشير الحالي: {self.current_user.get('full_name', self.current_user.get('username', 'غير محدد'))}")
        self.current_cashier_label.setStyleSheet("font-size: 14px; color: #2E86AB; font-weight: bold; padding: 5px;")
        controls_layout.addWidget(self.current_cashier_label)
        
        controls_layout.addStretch()
        
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_devices)
        controls_layout.addWidget(refresh_btn)
        
        devices_layout.addLayout(controls_layout)
        
        # جدول الأجهزة
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(6)
        self.devices_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم", "النوع", "السعر (عزاب)", "السعر (متعدد)", "الحالة"
        ])
        
        # إعداد الجدول
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        devices_layout.addWidget(self.devices_table)
        
        self.tab_widget.addTab(devices_widget, "الأجهزة")
    
    def create_add_device_tab(self):
        """إنشاء تبويب إضافة جهاز جديد"""
        add_widget = QWidget()
        add_layout = QVBoxLayout(add_widget)
        
        # نموذج إضافة الجهاز
        form_group = QGroupBox("إضافة جهاز جديد")
        form_layout = QGridLayout(form_group)
        
        # اسم الجهاز
        form_layout.addWidget(QLabel("اسم الجهاز:"), 0, 0)
        self.device_name_input = QLineEdit()
        form_layout.addWidget(self.device_name_input, 0, 1)
        
        # نوع الجهاز
        form_layout.addWidget(QLabel("نوع الجهاز:"), 1, 0)
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItems(["PS", "PC", "PingPong", "Billiard"])
        form_layout.addWidget(self.device_type_combo, 1, 1)
        
        # سعر العزاب
        form_layout.addWidget(QLabel("سعر العزاب:"), 2, 0)
        self.price_single_input = QDoubleSpinBox()
        self.price_single_input.setRange(0, 1000)
        self.price_single_input.setDecimals(2)
        form_layout.addWidget(self.price_single_input, 2, 1)
        
        # سعر المتعددين
        form_layout.addWidget(QLabel("سعر المتعددين:"), 3, 0)
        self.price_multi_input = QDoubleSpinBox()
        self.price_multi_input.setRange(0, 1000)
        self.price_multi_input.setDecimals(2)
        form_layout.addWidget(self.price_multi_input, 3, 1)
        
        add_layout.addWidget(form_group)
        
        # زر الإضافة
        add_btn = QPushButton("إضافة الجهاز")
        add_btn.clicked.connect(self.add_device)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
        """)
        add_layout.addWidget(add_btn)
        
        add_layout.addStretch()
        
        self.tab_widget.addTab(add_widget, "إضافة جهاز")
    
    def create_active_sessions_tab(self):
        """إنشاء تبويب الجلسات النشطة"""
        sessions_widget = QWidget()
        sessions_layout = QVBoxLayout(sessions_widget)
        
        # جدول الجلسات النشطة
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(5)
        self.sessions_table.setHorizontalHeaderLabels([
            "الجهاز", "الكاشير", "وقت البداية", "المدة", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.sessions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        sessions_layout.addWidget(self.sessions_table)
        
        self.tab_widget.addTab(sessions_widget, "الجلسات النشطة")
    
    def load_devices(self):
        """تحميل الأجهزة"""
        try:
            devices = self.device_model.get_all_devices()
            
            self.devices_table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                self.devices_table.setItem(row, 0, QTableWidgetItem(str(device['id'])))
                self.devices_table.setItem(row, 1, QTableWidgetItem(device['name']))
                self.devices_table.setItem(row, 2, QTableWidgetItem(device['type']))
                self.devices_table.setItem(row, 3, QTableWidgetItem(format_currency(device['price_single'])))
                self.devices_table.setItem(row, 4, QTableWidgetItem(format_currency(device['price_multi'])))
                self.devices_table.setItem(row, 5, QTableWidgetItem(device['status']))
            
            # تحديث الجلسات النشطة
            self.load_active_sessions()
            
        except Exception as e:
            show_error(f"خطأ في تحميل الأجهزة: {str(e)}")
    
    def load_active_sessions(self):
        """تحميل الجلسات النشطة"""
        try:
            active_invoices = self.invoice_model.get_active_invoices()
            
            self.sessions_table.setRowCount(len(active_invoices))
            
            for row, invoice in enumerate(active_invoices):
                self.sessions_table.setItem(row, 0, QTableWidgetItem(invoice.get('device_name', '')))
                self.sessions_table.setItem(row, 1, QTableWidgetItem(invoice.get('cashier_open_name', '')))
                self.sessions_table.setItem(row, 2, QTableWidgetItem(format_time(invoice['start_time'], 'short')))
                
                # حساب المدة
                from datetime import datetime
                duration = datetime.now() - invoice['start_time']
                duration_str = f"{int(duration.total_seconds() / 60)} دقيقة"
                self.sessions_table.setItem(row, 3, QTableWidgetItem(duration_str))
                
                # زر الإجراءات
                action_btn = QPushButton("إغلاق الجلسة")
                action_btn.clicked.connect(lambda checked, inv_id=invoice['id']: self.close_session(inv_id))
                self.sessions_table.setCellWidget(row, 4, action_btn)
            
        except Exception as e:
            show_error(f"خطأ في تحميل الجلسات النشطة: {str(e)}")
    
    def add_device(self):
        """إضافة جهاز جديد"""
        try:
            name = self.device_name_input.text().strip()
            device_type = self.device_type_combo.currentText()
            price_single = self.price_single_input.value()
            price_multi = self.price_multi_input.value()
            
            if not name:
                show_error("يرجى إدخال اسم الجهاز")
                return
            
            if price_single <= 0 or price_multi <= 0:
                show_error("يرجى إدخال أسعار صحيحة")
                return
            
            # إضافة الجهاز
            device_id = self.device_model.create_device(
                name=name,
                device_type=device_type,
                price_single=price_single,
                price_multi=price_multi
            )
            
            if device_id:
                show_success("تم إضافة الجهاز بنجاح")
                self.clear_form()
                self.load_devices()
            else:
                show_error("فشل في إضافة الجهاز")
                
        except Exception as e:
            show_error(f"خطأ في إضافة الجهاز: {str(e)}")
    
    def close_session(self, invoice_id):
        """إغلاق الجلسة"""
        try:
            reply = QMessageBox.question(
                self,
                "إغلاق الجلسة",
                "هل أنت متأكد من إغلاق هذه الجلسة؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # استخدام DeviceController لإغلاق الجلسة
                from controllers.device_controller import DeviceController
                device_controller = DeviceController(self.current_user)
                
                result = device_controller.close_session(invoice_id)
                
                if result['success']:
                    show_success(result['message'])
                    self.load_active_sessions()
                    # إشعار واجهة الفواتير بتحديث البيانات
                    self.notify_invoice_refresh()
                else:
                    show_error(result['message'])
                    
        except Exception as e:
            show_error(f"خطأ في إغلاق الجلسة: {str(e)}")
    
    def notify_invoice_refresh(self):
        """إشعار واجهة الفواتير بتحديث البيانات"""
        try:
            # البحث عن واجهة الفواتير في لوحة التحكم
            parent = self.parent()
            while parent:
                if hasattr(parent, 'invoice_management'):
                    parent.invoice_management.load_invoices()
                    print("تم تحديث واجهة الفواتير")
                    break
                parent = parent.parent()
        except Exception as e:
            print(f"خطأ في تحديث واجهة الفواتير: {e}")
    
    
    def clear_form(self):
        """مسح النموذج"""
        self.device_name_input.clear()
        self.device_type_combo.setCurrentIndex(0)
        self.price_single_input.setValue(0)
        self.price_multi_input.setValue(0)




if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = DevicePanelWindow(test_user)
    window.show()
    sys.exit(app.exec())
