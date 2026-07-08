"""
واجهة إدارة العملاء
Customer Management Interface
"""

import sys
import os
from datetime import datetime
from decimal import Decimal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.customer_model import CustomerModel
from utils.helpers import format_currency, format_phone, validate_phone
from utils.security import hash_password
from utils.notifications import show_success, show_error

class CustomerCard(QFrame):
    """كارت العميل"""
    
    # إشارات
    customer_clicked = Signal(dict)  # بيانات العميل
    
    def __init__(self, customer_data):
        super().__init__()
        self.customer_data = customer_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(165, 155)  # حجم مطابق للأجهزة
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
        """)
        
        # التخطيط الرئيسي
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # اسم العميل
        self.name_label = QLabel(self.customer_data.get('name', 'عميل'))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.name_label)
        
        # رقم الهاتف
        self.phone_label = QLabel(self.customer_data.get('phone', 'غير محدد'))
        self.phone_label.setAlignment(Qt.AlignCenter)
        self.phone_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.phone_label)
        
        # الرصيد
        self.balance_label = QLabel("")
        self.balance_label.setAlignment(Qt.AlignCenter)
        self.balance_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        layout.addWidget(self.balance_label)
        
        # حالة الرصيد
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.status_label)
        
        # معلومات إضافية
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 8px;")
        layout.addWidget(self.info_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
    
    def update_display(self):
        """تحديث عرض الكارت"""
        # تحديث الرصيد
        balance = self.customer_data.get('balance', 0)
        print(f"تحديث عرض الكارت للعميل {self.customer_data.get('name', 'غير محدد')} - الرصيد: {balance}")
        self.balance_label.setText(f"💰 {balance} جنيه")
        
        # تحديث حالة الرصيد واللون
        if balance >= 100:
            self.status_label.setText("رصيد عالي")
            self.info_label.setText("انقر للتفاصيل")
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
            """)
        elif balance >= 10:
            self.status_label.setText("رصيد متوسط")
            self.info_label.setText("انقر للتفاصيل")
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #f39c12;
                    color: white;
                    border: 2px solid #e67e22;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setText("رصيد منخفض")
            self.info_label.setText("يحتاج شحن")
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #e74c3c;
                    color: white;
                    border: 2px solid #c0392b;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
    
    def mousePressEvent(self, event):
        """معالج الضغط على الكارت"""
        if event.button() == Qt.LeftButton:
            self.customer_clicked.emit(self.customer_data)
    
    def update_customer_data(self, new_data):
        """تحديث بيانات العميل"""
        self.customer_data.update(new_data)
        self.update_display()

class CustomerManagementWindow(QMainWindow):
    """نافذة إدارة العملاء"""
    
    # إشارات
    customer_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.customer_model = CustomerModel()
        self.customer_cards = {}
        self.customer_tabs = {}
        self.setup_ui()
        self.setup_connections()
        self.load_customers()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة العملاء - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1400, 900)
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
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # إنشاء منطقة التمرير الرئيسية
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # شريط الأدوات
        self.create_toolbar(main_layout)
        
        # تبويبات العملاء
        self.create_customer_tabs(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("👥 إدارة العملاء")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px; 
                font-weight: bold; 
                color: #2c3e50;
                padding: 10px;
                background-color: white;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
            }
        """)
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # حقل البحث
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالاسم أو رقم الهاتف...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)
        self.search_input.textChanged.connect(self.search_customers)
        search_layout.addWidget(self.search_input)
        
        toolbar_layout.addLayout(search_layout)
        toolbar_layout.addSpacing(20)
        
        # أزرار التحكم
        self.add_customer_btn = QPushButton("➕ إضافة عميل")
        self.add_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.add_customer_btn.clicked.connect(self.add_customer)
        toolbar_layout.addWidget(self.add_customer_btn)
        
        self.topup_btn = QPushButton("💰 شحن رصيد")
        self.topup_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        self.topup_btn.clicked.connect(self.topup_balance)
        toolbar_layout.addWidget(self.topup_btn)
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_customers)
        toolbar_layout.addWidget(self.refresh_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_customer_tabs(self, parent_layout):
        """إنشاء تبويبات العملاء"""
        # تبويبات العملاء
        self.customer_tab_widget = QTabWidget()
        
        # تبويب العملاء ذوي الرصيد العالي
        self.high_balance_tab = self.create_customer_tab("high_balance")
        self.customer_tab_widget.addTab(self.high_balance_tab, "💰 رصيد عالي (100+)")
        self.customer_tabs['high_balance'] = self.high_balance_tab
        
        # تبويب العملاء ذوي الرصيد المتوسط
        self.medium_balance_tab = self.create_customer_tab("medium_balance")
        self.customer_tab_widget.addTab(self.medium_balance_tab, "⚖️ رصيد متوسط (10-100)")
        self.customer_tabs['medium_balance'] = self.medium_balance_tab
        
        # تبويب العملاء ذوي الرصيد المنخفض
        self.low_balance_tab = self.create_customer_tab("low_balance")
        self.customer_tab_widget.addTab(self.low_balance_tab, "⚠️ رصيد منخفض (<10)")
        self.customer_tabs['low_balance'] = self.low_balance_tab
        
        # تبويب جميع العملاء
        self.all_customers_tab = self.create_customer_tab("all")
        self.customer_tab_widget.addTab(self.all_customers_tab, "👥 جميع العملاء")
        self.customer_tabs['all'] = self.all_customers_tab
        
        parent_layout.addWidget(self.customer_tab_widget)
    
    def create_customer_tab(self, customer_type):
        """إنشاء تبويب للعملاء"""
        # إنشاء الـ widget الرئيسي للتبويب
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(10)
        
        # عنوان التبويب مع إحصائيات
        title_layout = QHBoxLayout()
        
        title_label = QLabel(f"عملاء {customer_type}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_layout.addWidget(title_label)
        
        # عداد العملاء
        count_label = QLabel("0 عميل")
        count_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 10px;")
        count_label.setAlignment(Qt.AlignRight)
        title_layout.addWidget(count_label)
        
        tab_layout.addLayout(title_layout)
        
        # منطقة التمرير للعملاء
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # الـ widget المحتوي للعملاء
        customers_widget = QWidget()
        customers_layout = QGridLayout(customers_widget)
        customers_layout.setSpacing(8)  # مسافة أقل لتناسب 8 كروت
        customers_layout.setContentsMargins(8, 8, 8, 8)  # هوامش أقل
        customers_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # بدء من أعلى الصفحة
        
        # رسالة ترحيبية عند عدم وجود عملاء
        welcome_label = QLabel("👥 مرحباً بك في قسم إدارة العملاء\n\nيمكنك إضافة عملاء جدد من خلال زر 'إضافة عميل' في الأعلى")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                padding: 40px;
                text-align: center;
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                margin: 20px;
            }
        """)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setWordWrap(True)
        customers_layout.addWidget(welcome_label, 0, 0, 1, 8)  # يمتد عبر 8 أعمدة
        
        # تخزين التخطيط للاستخدام لاحقاً
        tab_widget.customers_layout = customers_layout
        tab_widget.customer_type = customer_type
        tab_widget.count_label = count_label
        
        scroll_area.setWidget(customers_widget)
        tab_layout.addWidget(scroll_area)
        
        return tab_widget
    
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات العملاء")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات العملاء
        self.total_customers_label = QLabel("إجمالي العملاء: 0")
        self.total_customers_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_customers_label)
        
        self.high_balance_label = QLabel("رصيد عالي: 0")
        self.high_balance_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.high_balance_label)
        
        self.medium_balance_label = QLabel("رصيد متوسط: 0")
        self.medium_balance_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(self.medium_balance_label)
        
        self.low_balance_label = QLabel("رصيد منخفض: 0")
        self.low_balance_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.low_balance_label)
        
        self.total_balance_label = QLabel("إجمالي الرصيد: 0 جنيه")
        self.total_balance_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.total_balance_label)
        
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
    
    def search_customers(self):
        """البحث في العملاء"""
        try:
            search_term = self.search_input.text().strip().lower()
            
            # تصفية الكروت المرئية
            for customer_type, tab in self.customer_tabs.items():
                for i in range(tab.customers_layout.count()):
                    item = tab.customers_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, CustomerCard):
                            customer_name = widget.customer_data.get('name', '').lower()
                            customer_phone = widget.customer_data.get('phone', '').lower()
                            
                            if search_term and search_term not in customer_name and search_term not in customer_phone:
                                widget.setVisible(False)
                            else:
                                widget.setVisible(True)
                        elif hasattr(widget, 'text') and "مرحباً بك" in widget.text():
                            # إخفاء رسالة الترحيب أثناء البحث
                            widget.setVisible(False)
            
        except Exception as e:
            print(f"خطأ في البحث: {e}")
    
    def load_customers(self):
        """تحميل العملاء"""
        try:
            print("بدء تحميل العملاء")
            
            # مسح العملاء الموجودة من جميع التبويبات
            for customer_type, tab in self.customer_tabs.items():
                for i in reversed(range(tab.customers_layout.count())):
                    item = tab.customers_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        # الحفاظ على رسالة الترحيب
                        if not (hasattr(widget, 'text') and "مرحباً بك" in widget.text()):
                            widget.setParent(None)
            
            self.customer_cards.clear()
            print("تم مسح الكروت الموجودة")
            
            # تحميل العملاء من قاعدة البيانات
            print("جاري تحميل العملاء من قاعدة البيانات")
            customers = self.customer_model.get_all_customers()
            print(f"تم تحميل {len(customers)} عميل من قاعدة البيانات")
            
            # تحويل البيانات لتتوافق مع التنسيق المطلوب
            formatted_customers = []
            for customer in customers:
                formatted_customer = {
                    'phone': customer['phone'],
                    'name': customer['name'],
                    'balance': float(customer['balance'])  # استخدام float بدلاً من Decimal
                }
                formatted_customers.append(formatted_customer)
                print(f"تم تنسيق العميل: {formatted_customer['name']} - الرصيد: {formatted_customer['balance']}")
            
            # توزيع العملاء على التبويبات
            customers_by_type = {
                'high_balance': [],
                'medium_balance': [],
                'low_balance': [],
                'all': formatted_customers
            }
            
            for customer in formatted_customers:
                balance = customer['balance']
                if balance >= 100:
                    customers_by_type['high_balance'].append(customer)
                elif balance >= 10:
                    customers_by_type['medium_balance'].append(customer)
                else:
                    customers_by_type['low_balance'].append(customer)
            
            # إنشاء كروت العملاء لكل تبويب
            for customer_type, customers_list in customers_by_type.items():
                if customer_type in self.customer_tabs:
                    tab = self.customer_tabs[customer_type]
                    self.create_customer_cards_for_tab(tab, customers_list)
            
            # تحديث الإحصائيات
            self.update_stats(formatted_customers)
            
        except Exception as e:
            print(f"Error loading customers: {e}")
            show_error(f"خطأ في تحميل العملاء: {e}")
    
    def create_customer_cards_for_tab(self, tab, customers):
        """إنشاء كروت العملاء لتبويب محدد"""
        # إخفاء رسالة الترحيب إذا كان هناك عملاء
        welcome_widget = tab.customers_layout.itemAtPosition(0, 0)
        if welcome_widget:
            welcome_label = welcome_widget.widget()
            if welcome_label and "مرحباً بك" in welcome_label.text():
                welcome_label.setVisible(len(customers) == 0)
        
        row = 1 if len(customers) > 0 else 0  # البدء من الصف الثاني إذا كان هناك عملاء
        col = 0
        max_cols = 8  # 8 كروت في الصف الواحد
        
        # تحديث عداد العملاء
        if hasattr(tab, 'count_label'):
            count = len(customers)
            if count == 0:
                tab.count_label.setText("لا يوجد عملاء")
                tab.count_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-style: italic;")
            else:
                tab.count_label.setText(f"{count} عميل")
                tab.count_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        
        for customer in customers:
            card = CustomerCard(customer)
            card.customer_clicked.connect(self.on_customer_clicked)
            self.customer_cards[customer['phone']] = card
            
            tab.customers_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def update_stats(self, customers):
        """تحديث الإحصائيات"""
        total = len(customers)
        high_balance = len([c for c in customers if c['balance'] >= 100])
        medium_balance = len([c for c in customers if 10 <= c['balance'] < 100])
        low_balance = len([c for c in customers if c['balance'] < 10])
        total_balance = sum(c['balance'] for c in customers)
        
        self.total_customers_label.setText(f"إجمالي العملاء: {total}")
        self.high_balance_label.setText(f"رصيد عالي: {high_balance}")
        self.medium_balance_label.setText(f"رصيد متوسط: {medium_balance}")
        self.low_balance_label.setText(f"رصيد منخفض: {low_balance}")
        self.total_balance_label.setText(f"إجمالي الرصيد: {total_balance} جنيه")
    
    def on_customer_clicked(self, customer_data):
        """معالج النقر على العميل"""
        print(f"تم النقر على العميل: {customer_data['name']}")
        self.customer_selected.emit(customer_data)
        
        # عرض نافذة تفاصيل العميل
        self.show_customer_details(customer_data)
    
    def show_customer_details(self, customer_data):
        """عرض نافذة تفاصيل العميل"""
        dialog = CustomerDetailsDialog(customer_data, self.current_user)
        dialog.exec()
    
    def add_customer(self):
        """إضافة عميل جديد"""
        # التحقق من وجود وردية نشطة
        from utils.shift_validation import validate_shift_required
        if not validate_shift_required(self):
            return
        
        dialog = AddCustomerDialog()
        if dialog.exec() == QDialog.Accepted:
            customer_data = dialog.get_customer_data()
            
            # التحقق من صحة البيانات
            if not self.validate_customer_data(customer_data):
                return
            
            try:
                # إضافة العميل إلى قاعدة البيانات
                success = self.customer_model.create_customer(
                    phone=customer_data['phone'],
                    name=customer_data['name'],
                    password=customer_data['password'],
                    initial_balance=Decimal(str(customer_data['initial_balance'])),
                    cashier_id=self.current_user['id']
                )
                
                if success:
                    show_success(f"تم إضافة العميل {customer_data['name']} بنجاح")
                    self.load_customers()
                    if hasattr(self, 'search_input'):
                        self.search_input.clear()
                    
                    # إشعار واجهة الفواتير بتحديث البيانات
                    self.notify_invoice_refresh()
                else:
                    show_error("فشل في إضافة العميل. تحقق من البيانات أو جرب مرة أخرى.")
                    
            except Exception as e:
                show_error(f"خطأ في إضافة العميل: {str(e)}")
    
    def validate_customer_data(self, customer_data):
        """التحقق من صحة بيانات العميل"""
        # التحقق من الحقول المطلوبة
        if not customer_data['phone'].strip():
            show_error("رقم الهاتف مطلوب")
            return False
        
        if not customer_data['name'].strip():
            show_error("اسم العميل مطلوب")
            return False
        
        if not customer_data['password'].strip():
            show_error("كلمة المرور مطلوبة")
            return False
        
        # التحقق من تأكيد كلمة المرور
        if customer_data['password'] != customer_data['confirm_password']:
            show_error("كلمات المرور غير متطابقة")
            return False
        
        # التحقق من صحة رقم الهاتف
        if not validate_phone(customer_data['phone']):
            show_error("رقم الهاتف غير صحيح. يجب أن يبدأ بـ 01 ويحتوي على 11 رقم")
            return False
        
        # التحقق من عدم وجود العميل
        existing_customer = self.customer_model.get_customer_by_phone(customer_data['phone'])
        if existing_customer:
            show_error("رقم الهاتف مسجل مسبقاً")
            return False
        
        return True
    
    def topup_balance(self):
        """شحن رصيد عميل"""
        # التحقق من وجود وردية نشطة
        from utils.shift_validation import validate_shift_required
        if not validate_shift_required(self):
            return
        
        print("بدء عملية شحن الرصيد")
        dialog = TopupBalanceDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            topup_data = dialog.get_topup_data()
            print(f"بيانات الشحن: {topup_data}")
            
            try:
                # التحقق من وجود العميل
                print(f"البحث عن العميل برقم الهاتف: {topup_data['phone']}")
                customer = self.customer_model.get_customer_by_phone(topup_data['phone'])
                if not customer:
                    print("العميل غير موجود")
                    show_error("العميل غير موجود")
                    return
                
                print(f"تم العثور على العميل: {customer['name']} - الرصيد الحالي: {customer['balance']}")
                
                # شحن الرصيد
                print(f"جاري شحن {topup_data['amount']} للعميل {customer['name']}")
                success = self.customer_model.update_customer_balance(
                    phone=topup_data['phone'],
                    amount=Decimal(str(topup_data['amount'])),
                    operation='add',
                    cashier_id=self.current_user['id'],
                    notes=topup_data['notes']
                )
                
                print(f"نتيجة شحن الرصيد: {success}")
                
                if success:
                    show_success(f"تم شحن {format_currency(topup_data['amount'])} للعميل {customer['name']}")
                    
                    # تحديث فوري للكروت الموجودة
                    print("جاري تحديث الكروت الموجودة")
                    if topup_data['phone'] in self.customer_cards:
                        card = self.customer_cards[topup_data['phone']]
                        # الحصول على البيانات المحدثة من قاعدة البيانات
                        updated_customer = self.customer_model.get_customer_by_phone(topup_data['phone'])
                        if updated_customer:
                            print(f"الرصيد المحدث: {updated_customer['balance']}")
                            card.customer_data['balance'] = updated_customer['balance']
                            card.update_display()
                            print("تم تحديث الكارت")
                    
                    # إعادة تحميل جميع العملاء
                    print("جاري إعادة تحميل جميع العملاء")
                    self.load_customers()
                    print("تم إعادة تحميل جميع العملاء")
                    
                    # إشعار واجهة الفواتير بتحديث البيانات
                    self.notify_invoice_refresh()
                else:
                    print("فشل في شحن الرصيد")
                    show_error("فشل في شحن الرصيد")
                    
            except Exception as e:
                print(f"خطأ في شحن الرصيد: {e}")
                import traceback
                traceback.print_exc()
                show_error(f"خطأ في شحن الرصيد: {str(e)}")
    
    
    def notify_invoice_refresh(self):
        """إشعار واجهة الفواتير بتحديث البيانات"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم العثور على نافذة إدارة الفواتير وتحديثها")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في تحديث واجهة الفواتير: {e}")
    
    def start_timer(self):
        """بدء التايمر لتحديث العملاء"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_customers_status)
        self.timer.start(60000)  # كل دقيقة
    
    def update_customers_status(self):
        """تحديث حالة العملاء"""
        for card in self.customer_cards.values():
            card.update_display()

class CustomerDetailsDialog(QDialog):
    """نافذة تفاصيل العميل"""
    
    def __init__(self, customer_data, current_user):
        super().__init__()
        self.customer_data = customer_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle(f"تفاصيل العميل - {self.customer_data['name']}")
        self.setFixedSize(650, 580)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 10px;
            }
            QTabWidget::pane {
                border: none;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 10px;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.8);
                padding: 15px 25px;
                margin: 5px;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
            }
            QTabBar::tab:hover {
                background-color: rgba(255, 255, 255, 0.9);
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #357a38);
            }
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border: none;
                border-radius: 15px;
                gridline-color: rgba(0, 0, 0, 0.1);
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: rgba(76, 175, 80, 0.3);
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            }
            QTableWidget::item:selected {
                background-color: rgba(76, 175, 80, 0.2);
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #333;
                padding: 15px 10px;
                border: none;
                border-right: 1px solid rgba(0, 0, 0, 0.1);
                font-weight: bold;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل العميل - {self.customer_data['name']}")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات التفاصيل
        tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_info_tab = QWidget()
        basic_layout = QVBoxLayout(basic_info_tab)
        basic_layout.setContentsMargins(30, 30, 30, 30)
        basic_layout.setSpacing(25)
        
        # معلومات العميل مع تصميم محسن وأصغر
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
        
        # الاسم
        name_label = QLabel("الاسم:")
        name_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        name_value = QLabel(self.customer_data.get('name', 'غير محدد'))
        name_value.setStyleSheet("color: #333; font-size: 14px; background-color: rgba(102, 126, 234, 0.1); padding: 8px 12px; border-radius: 10px; margin-bottom: 10px; min-height: 20px;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(name_value)
        
        # رقم الهاتف
        phone_label = QLabel("رقم الهاتف:")
        phone_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        phone_value = QLabel(self.customer_data.get('phone', 'غير محدد'))
        phone_value.setStyleSheet("color: #333; font-size: 14px; background-color: rgba(102, 126, 234, 0.1); padding: 8px 12px; border-radius: 10px; margin-bottom: 10px; min-height: 20px;")
        info_layout.addWidget(phone_label)
        info_layout.addWidget(phone_value)
        
        # الرصيد الحالي
        balance_label = QLabel("الرصيد الحالي:")
        balance_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        balance_value = QLabel(f"{self.customer_data.get('balance', 0)} جنيه")
        balance_value.setStyleSheet("color: #333; font-size: 14px; background-color: rgba(76, 175, 80, 0.1); padding: 8px 12px; border-radius: 10px; margin-bottom: 10px; min-height: 20px;")
        info_layout.addWidget(balance_label)
        info_layout.addWidget(balance_value)
        
        basic_layout.addWidget(info_frame)
        basic_layout.addStretch()
        
        tab_widget.addTab(basic_info_tab, "المعلومات الأساسية")
        
        # تبويب المعاملات
        transactions_tab = QWidget()
        transactions_layout = QVBoxLayout(transactions_tab)
        transactions_layout.setContentsMargins(30, 30, 30, 30)
        transactions_layout.setSpacing(20)
        
        # عنوان تبويب المعاملات
        transactions_title = QLabel("معاملات العميل")
        transactions_title.setStyleSheet("color: #667eea; font-size: 20px; font-weight: bold; margin-bottom: 15px;")
        transactions_layout.addWidget(transactions_title)
        
        # جدول المعاملات
        self.transactions_table = QTableWidget()
        transactions_table = self.transactions_table
        transactions_table.setColumnCount(6)
        transactions_table.setHorizontalHeaderLabels(["التاريخ", "العملية", "المبلغ", "الرصيد القديم", "الرصيد الجديد", "الكاشير"])
        
        # تحميل المعاملات الحقيقية من قاعدة البيانات
        self.load_customer_transactions(transactions_table)
        
        transactions_table.horizontalHeader().setStretchLastSection(True)
        transactions_table.setAlternatingRowColors(True)
        transactions_table.setSelectionBehavior(QTableWidget.SelectRows)
        transactions_table.setSortingEnabled(True)
        
        transactions_layout.addWidget(transactions_table)
        
        tab_widget.addTab(transactions_tab, "المعاملات")
        
        layout.addWidget(tab_widget)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # زر شحن الرصيد
        topup_btn = QPushButton("شحن رصيد")
        topup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        topup_btn.clicked.connect(self.charge_customer_balance)
        button_layout.addWidget(topup_btn)
        
        # زر تعديل المعلومات
        edit_btn = QPushButton("تعديل المعلومات")
        edit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #21618c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #21618c, stop: 1 #1b4f72);
            }
        """)
        edit_btn.clicked.connect(self.edit_customer_info)
        button_layout.addWidget(edit_btn)
        
        # زر حذف العميل
        delete_btn = QPushButton("حذف العميل")
        delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #a93226, stop: 1 #922b21);
            }
        """)
        delete_btn.clicked.connect(self.delete_customer)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        # زر إغلاق
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6e);
            }
        """)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_customer_transactions(self, transactions_table):
        """تحميل معاملات العميل"""
        try:
            from models.customer_model import CustomerModel
            customer_model = CustomerModel()
            
            transactions = customer_model.get_customer_transactions(self.customer_data['phone'])
            
            transactions_table.setRowCount(len(transactions))
            
            for row, transaction in enumerate(transactions):
                # التاريخ
                if transaction['timestamp']:
                    if isinstance(transaction['timestamp'], str):
                        date_str = transaction['timestamp'][:16]  # أخذ أول 16 حرف (YYYY-MM-DD HH:MM)
                    else:
                        date_str = transaction['timestamp'].strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = 'غير محدد'
                transactions_table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # العملية
                operation = "إضافة" if transaction['operation'] == 'add' else "خصم"
                transactions_table.setItem(row, 1, QTableWidgetItem(operation))
                
                # المبلغ
                amount_str = f"{transaction['amount']} جنيه"
                transactions_table.setItem(row, 2, QTableWidgetItem(amount_str))
                
                # الرصيد القديم
                old_balance_str = f"{transaction['old_balance']} جنيه"
                transactions_table.setItem(row, 3, QTableWidgetItem(old_balance_str))
                
                # الرصيد الجديد
                new_balance_str = f"{transaction['new_balance']} جنيه"
                transactions_table.setItem(row, 4, QTableWidgetItem(new_balance_str))
                
                # الكاشير
                cashier_name = transaction.get('cashier_name', 'غير محدد')
                transactions_table.setItem(row, 5, QTableWidgetItem(cashier_name))
            
        except Exception as e:
            print(f"Error loading customer transactions: {e}")
            transactions_table.setRowCount(0)
    
    def edit_customer_info(self):
        """تعديل معلومات العميل"""
        try:
            dialog = EditCustomerDialog(self.customer_data)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_customer_data()
                
                # التحقق من صحة البيانات
                if not self.validate_edit_data(updated_data):
                    return
                
                # تحديث العميل في قاعدة البيانات
                from models.customer_model import CustomerModel
                customer_model = CustomerModel()
                
                success = customer_model.update_customer(
                    phone=self.customer_data['phone'],
                    new_name=updated_data['name'],
                    new_password=updated_data['password'] if updated_data['password'] else None
                )
                
                if success:
                    from utils.notifications import show_success
                    show_success("تم تحديث معلومات العميل بنجاح")
                    
                    # تحديث البيانات المحلية
                    self.customer_data['name'] = updated_data['name']
                    
                    # إغلاق النافذة وإعادة فتحها لتحديث البيانات
                    self.accept()
                    new_dialog = CustomerDetailsDialog(self.customer_data, self.current_user)
                    new_dialog.exec()
                else:
                    from utils.notifications import show_error
                    show_error("فشل في تحديث معلومات العميل")
                    
        except Exception as e:
            print(f"Error editing customer: {e}")
            from utils.notifications import show_error
            show_error(f"خطأ في تعديل العميل: {str(e)}")
    
    def delete_customer(self):
        """حذف العميل"""
        try:
            from PySide6.QtWidgets import QMessageBox
            from utils.notifications import show_success, show_error
            
            # تأكيد الحذف
            reply = QMessageBox.question(
                self, 
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف العميل {self.customer_data['name']}؟\nسيتم حذف جميع المعاملات المرتبطة به.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from models.customer_model import CustomerModel
                customer_model = CustomerModel()
                
                success = customer_model.delete_customer(self.customer_data['phone'])
                
                if success:
                    show_success("تم حذف العميل بنجاح")
                    self.accept()  # إغلاق نافذة التفاصيل
                else:
                    show_error("فشل في حذف العميل")
                    
        except Exception as e:
            print(f"Error deleting customer: {e}")
            from utils.notifications import show_error
            show_error(f"خطأ في حذف العميل: {str(e)}")
    
    def validate_edit_data(self, customer_data):
        """التحقق من صحة بيانات التعديل"""
        from utils.notifications import show_error
        
        # التحقق من الحقول المطلوبة
        if not customer_data['name'].strip():
            show_error("اسم العميل مطلوب")
            return False
        
        # التحقق من كلمة المرور إذا تم إدخالها
        if customer_data['password']:
            if len(customer_data['password']) < 6:
                show_error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return False
            
            if customer_data['password'] != customer_data['confirm_password']:
                show_error("كلمة المرور وتأكيدها غير متطابقتين")
                return False
        
        return True
    
    def charge_customer_balance(self):
        """شحن رصيد العميل من نافذة التفاصيل"""
        # التحقق من وجود وردية نشطة
        from utils.shift_validation import validate_shift_required
        if not validate_shift_required(self):
            return
        
        try:
            print("بدء شحن الرصيد من نافذة التفاصيل")
            dialog = TopupBalanceDialog(self.current_user, self.customer_data['phone'])
            if dialog.exec() == QDialog.Accepted:
                topup_data = dialog.get_topup_data()
                print(f"بيانات الشحن من نافذة التفاصيل: {topup_data}")
                
                # التحقق من وجود العميل
                from models.customer_model import CustomerModel
                customer_model = CustomerModel()
                customer = customer_model.get_customer_by_phone(topup_data['phone'])
                
                if not customer:
                    print("العميل غير موجود في نافذة التفاصيل")
                    from utils.notifications import show_error
                    show_error("العميل غير موجود")
                    return
                
                print(f"تم العثور على العميل في نافذة التفاصيل: {customer['name']} - الرصيد الحالي: {customer['balance']}")
                
                # شحن الرصيد
                print(f"جاري شحن {topup_data['amount']} للعميل {customer['name']} من نافذة التفاصيل")
                success = customer_model.update_customer_balance(
                    phone=topup_data['phone'],
                    amount=Decimal(str(topup_data['amount'])),
                    operation='add',
                    cashier_id=self.current_user['id'],
                    notes=topup_data['notes']
                )
                
                print(f"نتيجة شحن الرصيد من نافذة التفاصيل: {success}")
                
                if success:
                    from utils.notifications import show_success, format_currency
                    show_success(f"تم شحن {format_currency(topup_data['amount'])} للعميل {customer['name']}")
                    
                    # الحصول على بيانات العميل المحدثة من قاعدة البيانات
                    print("جاري الحصول على البيانات المحدثة من قاعدة البيانات")
                    updated_customer = customer_model.get_customer_by_phone(topup_data['phone'])
                    if updated_customer:
                        print(f"الرصيد المحدث من نافذة التفاصيل: {updated_customer['balance']}")
                        self.customer_data['balance'] = updated_customer['balance']
                        # تحديث عرض الرصيد في الواجهة
                        print("جاري تحديث عرض الرصيد في الواجهة")
                        self.update_balance_display()
                    
                    # تحديث المعاملات
                    print("جاري تحديث المعاملات")
                    self.load_customer_transactions(self.transactions_table)
                    
                    # إشعار واجهة الفواتير بتحديث البيانات
                    self.notify_invoice_refresh()
                else:
                    print("فشل في شحن الرصيد من نافذة التفاصيل")
                    from utils.notifications import show_error
                    show_error("فشل في شحن الرصيد")
                    
        except Exception as e:
            print(f"Error charging balance: {e}")
            from utils.notifications import show_error
            show_error(f"خطأ في شحن الرصيد: {str(e)}")
    
    def update_balance_display(self):
        """تحديث عرض الرصيد في الواجهة"""
        try:
            print(f"جاري تحديث عرض الرصيد في الواجهة - الرصيد: {self.customer_data.get('balance', 0)}")
            
            # تحديث الرصيد في تبويب المعلومات الأساسية
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QTabWidget):
                    for j in range(widget.count()):
                        tab = widget.widget(j)
                        if tab and hasattr(tab, 'layout'):
                            layout = tab.layout()
                            if layout and isinstance(layout, QFormLayout):
                                # البحث عن صف الرصيد وتحديثه
                                for k in range(layout.rowCount()):
                                    label = layout.itemAt(k, QFormLayout.LabelRole).widget()
                                    if label and "الرصيد الحالي" in label.text():
                                        value_widget = layout.itemAt(k, QFormLayout.FieldRole).widget()
                                        if value_widget and isinstance(value_widget, QLabel):
                                            new_text = f"{self.customer_data.get('balance', 0)} جنيه"
                                            print(f"تحديث نص الرصيد إلى: {new_text}")
                                            value_widget.setText(new_text)
                                            break
                    break
            print("تم تحديث عرض الرصيد في الواجهة")
        except Exception as e:
            print(f"خطأ في تحديث عرض الرصيد: {e}")
            import traceback
            traceback.print_exc()
    
    def notify_invoice_refresh(self):
        """إشعار واجهة الفواتير بتحديث البيانات"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم العثور على نافذة إدارة الفواتير وتحديثها")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في تحديث واجهة الفواتير: {e}")

class EditCustomerDialog(QDialog):
    """نافذة تعديل معلومات العميل"""
    
    def __init__(self, customer_data):
        super().__init__()
        self.customer_data = customer_data
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("تعديل معلومات العميل")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
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
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QPushButton#cancel_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
            }
            QPushButton#cancel_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
            }
            QPushButton#cancel_btn:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6d);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("تعديل معلومات العميل")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # اسم العميل
        self.name_input = QLineEdit()
        self.name_input.setText(self.customer_data['name'])
        self.name_input.setPlaceholderText("اسم العميل")
        self.name_input.setMinimumHeight(45)
        layout.addWidget(self.name_input)
        
        # رقم الهاتف (غير قابل للتعديل)
        self.phone_label = QLabel(self.customer_data['phone'])
        self.phone_label.setStyleSheet("""
            color: #667eea;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(102, 126, 234, 0.1);
            padding: 15px 20px;
            border-radius: 25px;
            margin-top: 10px;
            margin-bottom: 10px;
            min-height: 25px;
            border: 2px solid rgba(102, 126, 234, 0.3);
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        self.phone_label.setMinimumHeight(45)
        layout.addWidget(self.phone_label)
        
        # كلمة المرور الجديدة
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور الجديدة (اترك فارغاً للحفاظ على كلمة المرور الحالية)")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)
        
        # تأكيد كلمة المرور
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setMinimumHeight(45)
        layout.addWidget(self.confirm_password_input)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("حفظ التغييرات")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # تعيين التركيز على حقل الاسم
        self.name_input.setFocus()
    
    def validate_and_accept(self):
        """التحقق من صحة البيانات وقبول النافذة"""
        try:
            # التحقق من الاسم
            name = self.name_input.text().strip()
            if not name:
                self.show_error("يرجى إدخال اسم العميل")
                return
            
            # التحقق من كلمة المرور إذا تم إدخالها
            password = self.password_input.text().strip()
            confirm_password = self.confirm_password_input.text().strip()
            
            if password and confirm_password:
                if password != confirm_password:
                    self.show_error("كلمة المرور وتأكيدها غير متطابقتين")
                    return
                if len(password) < 6:
                    self.show_error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    return
            elif password and not confirm_password:
                self.show_error("يرجى تأكيد كلمة المرور الجديدة")
                return
            elif confirm_password and not password:
                self.show_error("يرجى إدخال كلمة المرور الجديدة")
                return
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
            # قبول النافذة
            self.accept()
            
        except Exception as e:
            self.show_error(f"خطأ في التحقق من البيانات: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
        self.error_label.setStyleSheet("""
            color: #ff6b6b; 
            font-size: 14px; 
            background-color: rgba(255, 107, 107, 0.2); 
            padding: 15px; 
            border-radius: 15px;
            border: 2px solid rgba(255, 107, 107, 0.3);
        """)
    
    def get_customer_data(self):
        """الحصول على بيانات العميل المحدثة"""
        return {
            'name': self.name_input.text().strip(),
            'phone': self.customer_data['phone'],  # لا يتغير
            'password': self.password_input.text().strip(),
            'confirm_password': self.confirm_password_input.text().strip()
        }

class AddCustomerDialog(QDialog):
    """نافذة إضافة عميل جديد"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("إضافة عميل جديد")
        self.setFixedSize(550, 750)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
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
            QDoubleSpinBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QDoubleSpinBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("إضافة عميل جديد")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # اسم العميل
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل")
        self.name_input.setMinimumHeight(45)
        layout.addWidget(self.name_input)
        
        # رقم الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        self.phone_input.setMinimumHeight(45)
        layout.addWidget(self.phone_input)
        
        # كلمة المرور
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        layout.addWidget(self.password_input)
        
        # تأكيد كلمة المرور
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setMinimumHeight(45)
        layout.addWidget(self.confirm_password_input)
        
        # الرصيد الأولي
        self.initial_balance_input = QLineEdit()
        self.initial_balance_input.setPlaceholderText("الرصيد الأولي (جنيه)")
        self.initial_balance_input.setText("0")
        self.initial_balance_input.setMinimumHeight(45)
        layout.addWidget(self.initial_balance_input)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6e);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # التركيز على حقل الاسم
        self.name_input.setFocus()
    
    def get_customer_data(self):
        """الحصول على بيانات العميل"""
        try:
            initial_balance = float(self.initial_balance_input.text().strip())
        except ValueError:
            initial_balance = 0.0
            
        return {
            'name': self.name_input.text().strip(),
            'phone': self.phone_input.text().strip(),
            'password': self.password_input.text().strip(),
            'confirm_password': self.confirm_password_input.text().strip(),
            'initial_balance': initial_balance
        }

class TopupBalanceDialog(QDialog):
    """نافذة شحن رصيد العميل"""
    
    def __init__(self, current_user, default_phone=None):
        super().__init__()
        self.current_user = current_user
        self.default_phone = default_phone
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("شحن رصيد العميل")
        self.setFixedSize(550, 650)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
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
            QDoubleSpinBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QDoubleSpinBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QTextEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("شحن رصيد العميل")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # رقم هاتف العميل
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم هاتف العميل")
        self.phone_input.setMinimumHeight(45)
        if self.default_phone:
            self.phone_input.setText(self.default_phone)
        layout.addWidget(self.phone_input)
        
        # مبلغ الشحن
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("مبلغ الشحن (جنيه)")
        self.amount_input.setText("50")
        self.amount_input.setMinimumHeight(45)
        layout.addWidget(self.amount_input)
        
        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setMinimumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        layout.addWidget(self.notes_input)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("شحن الرصيد")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        self.save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6e);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # التركيز على حقل رقم الهاتف
        self.phone_input.setFocus()
    
    def validate_and_accept(self):
        """التحقق من البيانات وقبول النافذة"""
        phone = self.phone_input.text().strip()
        
        # تحويل المبلغ من نص إلى رقم
        try:
            amount = float(self.amount_input.text().strip())
        except ValueError:
            self.show_error("يرجى إدخال مبلغ صحيح للشحن")
            return
        
        if not phone:
            self.show_error("يرجى إدخال رقم هاتف العميل")
            return
        
        if amount <= 0:
            self.show_error("يرجى إدخال مبلغ صحيح للشحن")
            return
        
        self.accept()
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def get_topup_data(self):
        """الحصول على بيانات الشحن"""
        try:
            amount = float(self.amount_input.text().strip())
        except ValueError:
            amount = 0.0
            
        return {
            'phone': self.phone_input.text().strip(),
            'amount': amount,
            'notes': self.notes_input.toPlainText().strip()
        }
