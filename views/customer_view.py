"""
عرض وإدارة العملاء
Customer View and Management
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QMessageBox, QGroupBox,
    QTabWidget, QDoubleSpinBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.customer_model import CustomerModel
from utils.helpers import format_currency, format_phone
from utils.notifications import show_success, show_error

class CustomerViewWindow(QMainWindow):
    """نافذة عرض وإدارة العملاء"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.customer_model = CustomerModel()
        self.setup_ui()
        self.load_customers()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة العملاء - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1000, 700)
        
        # الـ widget المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # عنوان النافذة
        title_label = QLabel("إدارة العملاء")
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
        
        # تبويب عرض العملاء
        self.create_customers_tab()
        
        # تبويب إضافة عميل جديد
        self.create_add_customer_tab()
        
        # تبويب شحن الرصيد
        self.create_balance_tab()
    
    def create_customers_tab(self):
        """إنشاء تبويب عرض العملاء"""
        customers_widget = QWidget()
        customers_layout = QVBoxLayout(customers_widget)
        
        # أدوات البحث
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("البحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("اسم العميل أو رقم الهاتف")
        self.search_input.textChanged.connect(self.search_customers)
        search_layout.addWidget(self.search_input)
        
        search_layout.addStretch()
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_customers)
        search_layout.addWidget(refresh_btn)
        
        customers_layout.addLayout(search_layout)
        
        # جدول العملاء
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([
            "رقم الهاتف", "الاسم", "الرصيد", "تاريخ الإنشاء", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        customers_layout.addWidget(self.customers_table)
        
        self.tab_widget.addTab(customers_widget, "العملاء")
    
    def create_add_customer_tab(self):
        """إنشاء تبويب إضافة عميل جديد"""
        add_widget = QWidget()
        add_layout = QVBoxLayout(add_widget)
        
        # نموذج إضافة العميل
        form_group = QGroupBox("إضافة عميل جديد")
        form_layout = QGridLayout(form_group)
        
        # رقم الهاتف
        form_layout.addWidget(QLabel("رقم الهاتف:"), 0, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("01xxxxxxxxx")
        form_layout.addWidget(self.phone_input, 0, 1)
        
        # اسم العميل
        form_layout.addWidget(QLabel("اسم العميل:"), 1, 0)
        self.name_input = QLineEdit()
        form_layout.addWidget(self.name_input, 1, 1)
        
        # كلمة المرور
        form_layout.addWidget(QLabel("كلمة المرور:"), 2, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_input, 2, 1)
        
        # الرصيد الابتدائي
        form_layout.addWidget(QLabel("الرصيد الابتدائي:"), 3, 0)
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(0, 10000)
        self.balance_input.setDecimals(2)
        form_layout.addWidget(self.balance_input, 3, 1)
        
        add_layout.addWidget(form_group)
        
        # زر الإضافة
        add_btn = QPushButton("إضافة العميل")
        add_btn.clicked.connect(self.add_customer)
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
        
        self.tab_widget.addTab(add_widget, "إضافة عميل")
    
    def create_balance_tab(self):
        """إنشاء تبويب شحن الرصيد"""
        balance_widget = QWidget()
        balance_layout = QVBoxLayout(balance_widget)
        
        # نموذج شحن الرصيد
        form_group = QGroupBox("شحن رصيد العميل")
        form_layout = QGridLayout(form_group)
        
        # رقم الهاتف
        form_layout.addWidget(QLabel("رقم الهاتف:"), 0, 0)
        self.charge_phone_input = QLineEdit()
        self.charge_phone_input.setPlaceholderText("01xxxxxxxxx")
        form_layout.addWidget(self.charge_phone_input, 0, 1)
        
        # زر البحث عن العميل
        find_btn = QPushButton("البحث عن العميل")
        find_btn.clicked.connect(self.find_customer)
        form_layout.addWidget(find_btn, 0, 2)
        
        # معلومات العميل
        self.customer_info_label = QLabel("")
        self.customer_info_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        form_layout.addWidget(self.customer_info_label, 1, 0, 1, 3)
        
        # مبلغ الشحن
        form_layout.addWidget(QLabel("مبلغ الشحن:"), 2, 0)
        self.charge_amount_input = QDoubleSpinBox()
        self.charge_amount_input.setRange(0, 10000)
        self.charge_amount_input.setDecimals(2)
        form_layout.addWidget(self.charge_amount_input, 2, 1)
        
        balance_layout.addWidget(form_group)
        
        # زر الشحن
        charge_btn = QPushButton("شحن الرصيد")
        charge_btn.clicked.connect(self.charge_balance)
        charge_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5dade2;
            }
        """)
        balance_layout.addWidget(charge_btn)
        
        balance_layout.addStretch()
        
        self.tab_widget.addTab(balance_widget, "شحن الرصيد")
    
    def load_customers(self):
        """تحميل العملاء"""
        try:
            customers = self.customer_model.get_all_customers()
            self.display_customers(customers)
            
        except Exception as e:
            show_error(f"خطأ في تحميل العملاء: {str(e)}")
    
    def display_customers(self, customers):
        """عرض العملاء في الجدول"""
        try:
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, QTableWidgetItem(format_phone(customer['phone'])))
                self.customers_table.setItem(row, 1, QTableWidgetItem(customer['name']))
                self.customers_table.setItem(row, 2, QTableWidgetItem(format_currency(customer['balance'])))
                self.customers_table.setItem(row, 3, QTableWidgetItem(str(customer['created_at'])))
                
                # زر الإجراءات
                actions_btn = QPushButton("عرض التفاصيل")
                actions_btn.clicked.connect(lambda checked, phone=customer['phone']: self.show_customer_details(phone))
                self.customers_table.setCellWidget(row, 4, actions_btn)
            
        except Exception as e:
            show_error(f"خطأ في عرض العملاء: {str(e)}")
    
    def search_customers(self):
        """البحث في العملاء"""
        try:
            search_term = self.search_input.text().strip()
            
            if search_term:
                customers = self.customer_model.search_customers(search_term)
            else:
                customers = self.customer_model.get_all_customers()
            
            self.display_customers(customers)
            
        except Exception as e:
            show_error(f"خطأ في البحث: {str(e)}")
    
    def add_customer(self):
        """إضافة عميل جديد"""
        try:
            phone = self.phone_input.text().strip()
            name = self.name_input.text().strip()
            password = self.password_input.text().strip()
            balance = self.balance_input.value()
            
            # التحقق من الحقول المطلوبة
            if not phone or not name or not password:
                show_error("يرجى ملء جميع الحقول المطلوبة")
                return
            
            # التحقق من صحة رقم الهاتف
            from utils.helpers import validate_phone
            if not validate_phone(phone):
                show_error("رقم الهاتف غير صحيح")
                return
            
            # التحقق من عدم وجود العميل
            if not self.customer_model.is_phone_available(phone):
                show_error("رقم الهاتف مسجل مسبقاً")
                return
            
            # تشفير كلمة المرور
            from utils.security import hash_password
            password_hash = hash_password(password)
            
            # إضافة العميل
            success = self.customer_model.create_customer(
                phone=phone,
                name=name,
                password_hash=password_hash,
                balance=balance
            )
            
            if success:
                show_success("تم إضافة العميل بنجاح")
                self.clear_add_form()
                self.load_customers()
            else:
                show_error("فشل في إضافة العميل")
                
        except Exception as e:
            show_error(f"خطأ في إضافة العميل: {str(e)}")
    
    def find_customer(self):
        """البحث عن العميل"""
        try:
            phone = self.charge_phone_input.text().strip()
            
            if not phone:
                show_error("يرجى إدخال رقم الهاتف")
                return
            
            customer = self.customer_model.get_customer_by_phone(phone)
            
            if customer:
                info_text = f"""
                <b>اسم العميل:</b> {customer['name']}<br>
                <b>رقم الهاتف:</b> {format_phone(customer['phone'])}<br>
                <b>الرصيد الحالي:</b> {format_currency(customer['balance'])}<br>
                <b>تاريخ الإنشاء:</b> {customer['created_at']}
                """
                self.customer_info_label.setText(info_text)
            else:
                self.customer_info_label.setText("العميل غير موجود")
                show_error("العميل غير موجود")
                
        except Exception as e:
            show_error(f"خطأ في البحث عن العميل: {str(e)}")
    
    def charge_balance(self):
        """شحن رصيد العميل"""
        try:
            phone = self.charge_phone_input.text().strip()
            amount = self.charge_amount_input.value()
            
            if not phone:
                show_error("يرجى إدخال رقم الهاتف")
                return
            
            if amount <= 0:
                show_error("يرجى إدخال مبلغ صحيح")
                return
            
            # التحقق من وجود العميل
            customer = self.customer_model.get_customer_by_phone(phone)
            if not customer:
                show_error("العميل غير موجود")
                return
            
            # شحن الرصيد
            success = self.customer_model.add_balance(phone, amount)
            
            if success:
                show_success(f"تم شحن {format_currency(amount)} للعميل {customer['name']}")
                self.charge_amount_input.setValue(0)
                self.find_customer()  # تحديث معلومات العميل
                self.load_customers()  # تحديث قائمة العملاء
            else:
                show_error("فشل في شحن الرصيد")
                
        except Exception as e:
            show_error(f"خطأ في شحن الرصيد: {str(e)}")
    
    def show_customer_details(self, phone):
        """عرض تفاصيل العميل"""
        try:
            customer = self.customer_model.get_customer_by_phone(phone)
            
            if customer:
                details_text = f"""
                <h3>تفاصيل العميل</h3>
                <p><b>الاسم:</b> {customer['name']}</p>
                <p><b>رقم الهاتف:</b> {format_phone(customer['phone'])}</p>
                <p><b>الرصيد الحالي:</b> {format_currency(customer['balance'])}</p>
                <p><b>تاريخ الإنشاء:</b> {customer['created_at']}</p>
                <p><b>آخر تحديث:</b> {customer['updated_at']}</p>
                """
                
                msg_box = QMessageBox()
                msg_box.setWindowTitle("تفاصيل العميل")
                msg_box.setText(details_text)
                msg_box.setIcon(QMessageBox.Information)
                msg_box.exec()
            else:
                show_error("العميل غير موجود")
                
        except Exception as e:
            show_error(f"خطأ في عرض تفاصيل العميل: {str(e)}")
    
    def clear_add_form(self):
        """مسح نموذج الإضافة"""
        self.phone_input.clear()
        self.name_input.clear()
        self.password_input.clear()
        self.balance_input.setValue(0)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = CustomerViewWindow(test_user)
    window.show()
    sys.exit(app.exec())
