"""
نافذة إنهاء الجلسة والحساب
Session Checkout Window
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QRadioButton, QButtonGroup, 
                               QLineEdit, QMessageBox, QGroupBox, QGridLayout,
                               QFrame, QSpacerItem, QSizePolicy, QTextEdit,
                               QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon
from decimal import Decimal
from datetime import datetime
from utils.helpers import format_currency
import logging

logger = logging.getLogger(__name__)

class SessionCheckoutWindow(QDialog):
    """نافذة إنهاء الجلسة والحساب"""
    
    # إشارة لإرسال نتيجة الدفع
    payment_completed = Signal(dict)
    
    def __init__(self, session_data, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.customer_data = None
        self.payment_method = 'cash'  # 'cash' أو 'customer_balance'
        self.total_amount = Decimal('0.00')
        self.customer_balance = Decimal('0.00')
        self.cash_amount = Decimal('0.00')
        self.customer_amount = Decimal('0.00')
        
        self.setup_ui()
        self.calculate_totals()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إنهاء الجلسة والحساب")
        self.setModal(True)
        self.setFixedSize(700, 800)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # عنوان النافذة
        title_label = QLabel("إنهاء الجلسة والحساب")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # إنشاء التبويبات
        self.setup_tabs(main_layout)
        
        # الأزرار
        self.setup_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def setup_tabs(self, layout):
        """إعداد التبويبات"""
        # إنشاء التبويبات
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5dade2;
                color: white;
            }
        """)
        
        # تبويبة معلومات الجلسة
        self.session_tab = QWidget()
        self.setup_session_tab()
        self.tab_widget.addTab(self.session_tab, "معلومات الجلسة")
        
        # تبويبة الدفع والحساب
        self.payment_tab = QWidget()
        self.setup_payment_tab()
        self.tab_widget.addTab(self.payment_tab, "الدفع والحساب")
        
        layout.addWidget(self.tab_widget)
    
    def setup_session_tab(self):
        """إعداد تبويبة معلومات الجلسة"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # معلومات الجلسة
        self.setup_session_info(layout)
        
        # تفاصيل الفاتورة
        self.setup_invoice_details(layout)
        
        self.session_tab.setLayout(layout)
    
    def setup_payment_tab(self):
        """إعداد تبويبة الدفع والحساب"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # خيارات الدفع
        self.setup_payment_options(layout)
        
        # معلومات العميل (مخفية في البداية)
        self.setup_customer_info(layout)
        
        # ملخص الدفع
        self.setup_payment_summary(layout)
        
        self.payment_tab.setLayout(layout)
        
    def setup_session_info(self, layout):
        """إعداد معلومات الجلسة"""
        session_group = QGroupBox("معلومات الجلسة")
        session_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        session_layout = QGridLayout()
        session_layout.setSpacing(10)
        
        # معلومات الجلسة
        session_info = [
            ("الجهاز:", self.session_data.get('device_name', 'غير محدد')),
            ("الكاشير:", self.session_data.get('cashier_name', 'غير محدد')),
            ("نوع التسعيرة:", self.session_data.get('pricing_type', 'غير محدد')),
            ("وقت البداية:", self.format_datetime(self.session_data.get('start_time'))),
            ("المدة المنقضية:", self.format_duration()),
            ("نوع الجلسة:", "وقت محدد" if self.session_data.get('time_type') == 'fixed' else "وقت مفتوح")
        ]
        
        for i, (label, value) in enumerate(session_info):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #34495e;")
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: #2c3e50;")
            
            session_layout.addWidget(label_widget, i, 0)
            session_layout.addWidget(value_widget, i, 1)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
    def setup_invoice_details(self, layout):
        """إعداد تفاصيل الفاتورة"""
        invoice_group = QGroupBox("تفاصيل الفاتورة")
        invoice_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        invoice_layout = QGridLayout()
        invoice_layout.setSpacing(10)
        
        # حساب تكلفة الجلسة
        session_cost = self.calculate_session_cost()
        products_total = self.calculate_products_total()
        self.total_amount = session_cost + products_total
        
        # تفاصيل الفاتورة
        invoice_details = [
            ("تكلفة الجلسة:", format_currency(session_cost)),
            ("إجمالي المنتجات:", format_currency(products_total)),
            ("المبلغ الإجمالي:", format_currency(self.total_amount))
        ]
        
        for i, (label, value) in enumerate(invoice_details):
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #34495e;")
            value_widget = QLabel(value)
            if i == len(invoice_details) - 1:  # المبلغ الإجمالي
                value_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
            else:
                value_widget.setStyleSheet("color: #2c3e50;")
            
            invoice_layout.addWidget(label_widget, i, 0)
            invoice_layout.addWidget(value_widget, i, 1)
        
        invoice_group.setLayout(invoice_layout)
        layout.addWidget(invoice_group)
        
    def setup_payment_options(self, layout):
        """إعداد خيارات الدفع"""
        payment_group = QGroupBox("خيارات الدفع")
        payment_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(15)
        
        # مجموعة أزرار الدفع
        self.payment_group = QButtonGroup()
        
        # خيار الدفع النقدي
        self.cash_radio = QRadioButton("الدفع نقداً")
        self.cash_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #27ae60;
                padding: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        self.cash_radio.setChecked(True)
        self.cash_radio.toggled.connect(self.on_payment_method_changed)
        self.payment_group.addButton(self.cash_radio, 0)
        payment_layout.addWidget(self.cash_radio)
        
        # خيار الدفع من حساب العميل
        self.customer_radio = QRadioButton("الدفع من حساب العميل")
        self.customer_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #3498db;
                padding: 10px;
            }
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        self.customer_radio.toggled.connect(self.on_payment_method_changed)
        self.payment_group.addButton(self.customer_radio, 1)
        payment_layout.addWidget(self.customer_radio)
        
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)
        
    def setup_customer_info(self, layout):
        """إعداد معلومات العميل"""
        self.customer_group = QGroupBox("معلومات العميل")
        self.customer_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        self.customer_group.setVisible(False)
        
        customer_layout = QGridLayout()
        customer_layout.setSpacing(10)
        
        # رقم الهاتف
        phone_label = QLabel("رقم الهاتف:")
        phone_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("أدخل رقم هاتف العميل")
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        customer_layout.addWidget(phone_label, 0, 0)
        customer_layout.addWidget(self.phone_input, 0, 1)
        
        # كلمة المرور
        password_label = QLabel("كلمة المرور:")
        password_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة مرور العميل")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        customer_layout.addWidget(password_label, 1, 0)
        customer_layout.addWidget(self.password_input, 1, 1)
        
        # زر التحقق من العميل
        self.verify_customer_btn = QPushButton("التحقق من العميل")
        self.verify_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.verify_customer_btn.clicked.connect(self.verify_customer)
        customer_layout.addWidget(self.verify_customer_btn, 2, 0, 1, 2)
        
        # معلومات العميل
        self.customer_info_label = QLabel("")
        self.customer_info_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-weight: bold;
                padding: 10px;
                background-color: #d5f4e6;
                border-radius: 5px;
                border: 1px solid #27ae60;
            }
        """)
        self.customer_info_label.setVisible(False)
        customer_layout.addWidget(self.customer_info_label, 3, 0, 1, 2)
        
        self.customer_group.setLayout(customer_layout)
        layout.addWidget(self.customer_group)
        
    def setup_payment_summary(self, layout):
        """إعداد ملخص الدفع"""
        self.summary_group = QGroupBox("ملخص الدفع")
        self.summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.summary_layout = QGridLayout()
        self.summary_layout.setSpacing(10)
        
        # المبلغ الإجمالي
        total_label = QLabel("المبلغ الإجمالي:")
        total_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.total_label = QLabel(format_currency(self.total_amount))
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        self.summary_layout.addWidget(total_label, 0, 0)
        self.summary_layout.addWidget(self.total_label, 0, 1)
        
        # المبلغ المدفوع نقداً
        self.cash_label = QLabel("المبلغ المدفوع نقداً:")
        self.cash_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.cash_amount_label = QLabel(format_currency(0))
        self.cash_amount_label.setStyleSheet("color: #27ae60;")
        self.summary_layout.addWidget(self.cash_label, 1, 0)
        self.summary_layout.addWidget(self.cash_amount_label, 1, 1)
        
        # المبلغ المدفوع من الحساب
        self.customer_label = QLabel("المبلغ المدفوع من الحساب:")
        self.customer_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.customer_amount_label = QLabel(format_currency(0))
        self.customer_amount_label.setStyleSheet("color: #3498db;")
        self.summary_layout.addWidget(self.customer_label, 2, 0)
        self.summary_layout.addWidget(self.customer_amount_label, 2, 1)
        
        # الرصيد المتبقي
        self.balance_label = QLabel("الرصيد المتبقي:")
        self.balance_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.balance_amount_label = QLabel(format_currency(0))
        self.balance_amount_label.setStyleSheet("color: #f39c12;")
        self.summary_layout.addWidget(self.balance_label, 3, 0)
        self.summary_layout.addWidget(self.balance_amount_label, 3, 1)
        
        self.summary_group.setLayout(self.summary_layout)
        layout.addWidget(self.summary_group)
        
    def setup_buttons(self, layout):
        """إعداد الأزرار"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # زر الإلغاء
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        # زر تأكيد الدفع
        self.confirm_btn = QPushButton("تأكيد الدفع")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.confirm_btn.clicked.connect(self.confirm_payment)
        buttons_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(buttons_layout)
        
    def calculate_totals(self):
        """حساب المجاميع"""
        # حساب تكلفة الجلسة
        session_cost = self.calculate_session_cost()
        products_total = self.calculate_products_total()
        self.total_amount = session_cost + products_total
        
        # تحديث الملخص
        self.update_payment_summary()
        
    def calculate_session_cost(self) -> Decimal:
        """حساب تكلفة الجلسة"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            cost_info = session_model.calculate_session_cost(self.session_data['id'])
            
            if cost_info:
                return Decimal(str(cost_info['total_cost']))
            else:
                # استخدام السعر الافتراضي
                return Decimal(str(self.session_data.get('session_price', 0)))
                
        except Exception as e:
            logger.error(f"خطأ في حساب تكلفة الجلسة: {e}")
            return Decimal(str(self.session_data.get('session_price', 0)))
    
    def calculate_products_total(self) -> Decimal:
        """حساب إجمالي المنتجات"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            products_total = session_model.get_session_products_total(self.session_data['id'])
            return Decimal(str(products_total))
            
        except Exception as e:
            logger.error(f"خطأ في حساب إجمالي المنتجات: {e}")
            return Decimal('0.00')
    
    def format_datetime(self, dt):
        """تنسيق التاريخ والوقت"""
        if dt:
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return "غير محدد"
    
    def format_duration(self):
        """تنسيق المدة"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            time_info = session_model.get_session_time_info(self.session_data['id'])
            
            if time_info:
                hours = time_info.get('elapsed_hours', 0)
                minutes = time_info.get('elapsed_minutes', 0)
                seconds = time_info.get('elapsed_seconds', 0)
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return "غير محدد"
                
        except Exception as e:
            logger.error(f"خطأ في تنسيق المدة: {e}")
            return "غير محدد"
    
    def on_payment_method_changed(self):
        """تغيير طريقة الدفع"""
        if self.cash_radio.isChecked():
            self.payment_method = 'cash'
            self.customer_group.setVisible(False)
            self.cash_amount = self.total_amount
            self.customer_amount = Decimal('0.00')
        else:
            self.payment_method = 'customer_balance'
            self.customer_group.setVisible(True)
            self.cash_amount = Decimal('0.00')
            self.customer_amount = Decimal('0.00')
        
        self.update_payment_summary()
    
    def verify_customer(self):
        """التحقق من العميل"""
        try:
            phone = self.phone_input.text().strip()
            password = self.password_input.text().strip()
            
            if not phone or not password:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال رقم الهاتف وكلمة المرور")
                return
            
            # التحقق من العميل
            from models.customer_model import CustomerModel
            customer_model = CustomerModel()
            customer = customer_model.authenticate_customer(phone, password)
            
            if customer:
                self.customer_data = customer
                self.customer_balance = Decimal(str(customer['balance']))
                
                # عرض معلومات العميل
                self.customer_info_label.setText(
                    f"العميل: {customer['name']}\n"
                    f"الرصيد الحالي: {format_currency(self.customer_balance)}"
                )
                self.customer_info_label.setVisible(True)
                
                # تحديث ملخص الدفع
                self.update_payment_summary()
                
                # التحقق من كفاية الرصيد
                if self.customer_balance >= self.total_amount:
                    # الرصيد كافي
                    self.customer_amount = self.total_amount
                    self.cash_amount = Decimal('0.00')
                    QMessageBox.information(
                        self, "نجح التحقق", 
                        f"الرصيد كافي للدفع\nالرصيد المتبقي: {format_currency(self.customer_balance - self.total_amount)}"
                    )
                else:
                    # الرصيد غير كافي - عرض خيارات
                    self.show_insufficient_balance_options()
                
            else:
                QMessageBox.warning(self, "خطأ", "رقم الهاتف أو كلمة المرور غير صحيحة")
                self.customer_data = None
                self.customer_info_label.setVisible(False)
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من العميل: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في التحقق من العميل: {str(e)}")
    
    def show_insufficient_balance_options(self):
        """عرض خيارات الرصيد غير الكافي"""
        msg = QMessageBox()
        msg.setWindowTitle("رصيد غير كافي")
        msg.setText(f"رصيد العميل ({format_currency(self.customer_balance)}) أقل من المبلغ المطلوب ({format_currency(self.total_amount)})")
        msg.setInformativeText("اختر طريقة الدفع:")
        
        # خيار 1: سحب كل الرصيد + الباقي نقداً
        option1_btn = msg.addButton("سحب كل الرصيد + الباقي نقداً", QMessageBox.ActionRole)
        
        # خيار 2: الدفع نقداً بالكامل
        option2_btn = msg.addButton("الدفع نقداً بالكامل", QMessageBox.ActionRole)
        
        # خيار 3: إلغاء
        cancel_btn = msg.addButton("إلغاء", QMessageBox.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == option1_btn:
            # سحب كل الرصيد + الباقي نقداً
            self.customer_amount = self.customer_balance
            self.cash_amount = self.total_amount - self.customer_balance
            QMessageBox.information(
                self, "تم التحديث", 
                f"سيتم سحب {format_currency(self.customer_amount)} من الحساب\n"
                f"والباقي {format_currency(self.cash_amount)} نقداً"
            )
        elif msg.clickedButton() == option2_btn:
            # الدفع نقداً بالكامل
            self.customer_amount = Decimal('0.00')
            self.cash_amount = self.total_amount
            QMessageBox.information(
                self, "تم التحديث", 
                f"سيتم الدفع نقداً بالكامل: {format_currency(self.cash_amount)}"
            )
        else:
            # إلغاء - إعادة تعيين
            self.customer_amount = Decimal('0.00')
            self.cash_amount = Decimal('0.00')
        
        self.update_payment_summary()
    
    def update_payment_summary(self):
        """تحديث ملخص الدفع"""
        # تحديث المبلغ الإجمالي
        self.total_label.setText(format_currency(self.total_amount))
        
        # تحديث المبلغ المدفوع نقداً
        self.cash_amount_label.setText(format_currency(self.cash_amount))
        
        # تحديث المبلغ المدفوع من الحساب
        self.customer_amount_label.setText(format_currency(self.customer_amount))
        
        # تحديث الرصيد المتبقي
        if self.customer_data:
            remaining_balance = self.customer_balance - self.customer_amount
            self.balance_amount_label.setText(format_currency(remaining_balance))
        else:
            self.balance_amount_label.setText(format_currency(0))
        
        # إظهار/إخفاء العناصر حسب طريقة الدفع
        if self.payment_method == 'cash':
            self.cash_label.setVisible(True)
            self.cash_amount_label.setVisible(True)
            self.customer_label.setVisible(False)
            self.customer_amount_label.setVisible(False)
            self.balance_label.setVisible(False)
            self.balance_amount_label.setVisible(False)
        else:
            self.cash_label.setVisible(True)
            self.cash_amount_label.setVisible(True)
            self.customer_label.setVisible(True)
            self.customer_amount_label.setVisible(True)
            self.balance_label.setVisible(True)
            self.balance_amount_label.setVisible(True)
    
    def confirm_payment(self):
        """تأكيد الدفع"""
        try:
            # التحقق من صحة البيانات
            if self.payment_method == 'customer_balance':
                if not self.customer_data:
                    QMessageBox.warning(self, "تحذير", "يرجى التحقق من العميل أولاً")
                    return
                
                if self.customer_amount + self.cash_amount != self.total_amount:
                    QMessageBox.warning(self, "تحذير", "المبلغ المدفوع لا يساوي المبلغ الإجمالي")
                    return
            
            # تأكيد الدفع
            reply = QMessageBox.question(
                self, "تأكيد الدفع", 
                f"هل أنت متأكد من تأكيد الدفع؟\n"
                f"المبلغ الإجمالي: {format_currency(self.total_amount)}\n"
                f"طريقة الدفع: {'نقداً' if self.payment_method == 'cash' else 'من حساب العميل'}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # إرسال نتيجة الدفع
                payment_result = {
                    'success': True,
                    'session_id': self.session_data['id'],
                    'total_amount': self.total_amount,
                    'payment_method': self.payment_method,
                    'cash_amount': self.cash_amount,
                    'customer_amount': self.customer_amount,
                    'customer_data': self.customer_data
                }
                
                self.payment_completed.emit(payment_result)
                self.accept()
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"خطأ في تأكيد الدفع: {error_details}")
            
            try:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ في تأكيد الدفع: {str(e)}")
            except Exception as msg_error:
                print(f"خطأ في عرض رسالة الخطأ: {msg_error}")
