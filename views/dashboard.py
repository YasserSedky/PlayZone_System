"""
لوحة التحكم الرئيسية
Main Dashboard
"""

import sys
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMenuBar, QStatusBar, QToolBar, QSplitter, QTabWidget,
    QMessageBox, QProgressBar, QGroupBox, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QAction, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# سيتم استيراد المكونات محلياً لتجنب مشاكل الاستيراد

class DashboardWindow(QMainWindow):
    """نافذة لوحة التحكم الرئيسية"""
    
    # إشارات
    logout_requested = Signal()
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        print(f"✅ تم إنشاء DashboardWindow للمستخدم: {current_user.get('username', '')}")
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("لوحة التحكم - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1000, 700)
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 16px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
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
                background-color: #f5f5f5;
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
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # عنوان الصفحة
        self.title_label = QLabel("🎮 لوحة التحكم | PlayZone Management System")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB; margin-bottom: 20px;")
        main_layout.addWidget(self.title_label)

        # عنوان الصفحة
        self.title_label = QLabel("TEST VER 1.0")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB; margin-bottom: 20px;")
        main_layout.addWidget(self.title_label)
        
        # معلومات النظام
        info_label = QLabel("KemetDevs - All Rights Reserved | Tel : 0100 763 5462")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        main_layout.addWidget(info_label)
        
        # تبويبات النظام
        self.create_tabs(main_layout)
        
        
        # تطبيق الصلاحيات
        self.apply_permissions()
    
    def create_tabs(self, parent_layout):
        """إنشاء تبويبات النظام"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # تبويب إدارة الورديات - أول تبويب
        try:
            from views.simple_shift_management import SimpleShiftManagementWindow
            self.shift_management = SimpleShiftManagementWindow(self.current_user)
            self.tab_widget.addTab(self.shift_management, "⏰ إدارة الورديات")
        except Exception as e:
            print(f"خطأ في تحميل إدارة الورديات: {e}")
            # إنشاء تبويب بديل
            shift_tab = QWidget()
            shift_tab.setStyleSheet("background-color: white;")
            shift_layout = QVBoxLayout(shift_tab)
            shift_label = QLabel("خطأ في تحميل إدارة الورديات")
            shift_label.setAlignment(Qt.AlignCenter)
            shift_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            shift_layout.addWidget(shift_label)
            self.tab_widget.addTab(shift_tab, "⏰ إدارة الورديات")
        
        # تبويب إدارة الكاشيرات (للمدير فقط)
        try:
            from utils.permissions import can_manage_cashiers
            if can_manage_cashiers(self.current_user.get('role', '')):
                from views.cashier_management import CashierManagementWindow
                self.cashier_management = CashierManagementWindow(self.current_user)
                self.tab_widget.addTab(self.cashier_management, "👥 إدارة الكاشيرات")
            else:
                # إنشاء تبويب مخفي للكاشير
                cashier_tab = QWidget()
                cashier_tab.setStyleSheet("background-color: white;")
                cashier_layout = QVBoxLayout(cashier_tab)
                cashier_label = QLabel("ليس لديك صلاحية لإدارة الكاشيرات")
                cashier_label.setAlignment(Qt.AlignCenter)
                cashier_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
                cashier_layout.addWidget(cashier_label)
                # لا نضيف التبويب للكاشير
        except Exception as e:
            print(f"خطأ في تحميل إدارة الكاشيرات: {e}")
        
        # تبويب إدارة الأجهزة
        try:
            from views.device_management import DeviceManagementWindow
            self.device_management = DeviceManagementWindow(self.current_user)
            self.tab_widget.addTab(self.device_management, "🎮 إدارة الأجهزة")
        except Exception as e:
            print(f"خطأ في تحميل إدارة الأجهزة: {e}")
            # إنشاء تبويب بديل
            device_tab = QWidget()
            device_tab.setStyleSheet("background-color: white;")
            device_layout = QVBoxLayout(device_tab)
            device_label = QLabel("إدارة الأجهزة - خطأ في التحميل")
            device_label.setAlignment(Qt.AlignCenter)
            device_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            device_layout.addWidget(device_label)
            self.tab_widget.addTab(device_tab, "🎮 إدارة الأجهزة")
        
        # تبويب إدارة الفواتير
        try:
            from views.invoice_management import InvoiceManagementWindow
            self.invoice_management = InvoiceManagementWindow(self.current_user)
            self.tab_widget.addTab(self.invoice_management, "📄 الفواتير")
        except Exception as e:
            print(f"خطأ في تحميل إدارة الفواتير: {e}")
            # إنشاء تبويب بديل
            invoice_tab = QWidget()
            invoice_tab.setStyleSheet("background-color: white;")
            invoice_layout = QVBoxLayout(invoice_tab)
            invoice_label = QLabel("إدارة الفواتير - خطأ في التحميل")
            invoice_label.setAlignment(Qt.AlignCenter)
            invoice_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            invoice_layout.addWidget(invoice_label)
            self.tab_widget.addTab(invoice_tab, "📄 الفواتير")
        
        # تبويب إدارة العملاء
        try:
            from views.customer_management import CustomerManagementWindow
            self.customer_management = CustomerManagementWindow(self.current_user)
            self.tab_widget.addTab(self.customer_management, "👥 العملاء")
        except Exception as e:
            print(f"خطأ في تحميل إدارة العملاء: {e}")
            # إنشاء تبويب بديل
            customer_tab = QWidget()
            customer_tab.setStyleSheet("background-color: white;")
            customer_layout = QVBoxLayout(customer_tab)
            customer_label = QLabel("إدارة العملاء - خطأ في التحميل")
            customer_label.setAlignment(Qt.AlignCenter)
            customer_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            customer_layout.addWidget(customer_label)
            self.tab_widget.addTab(customer_tab, "👥 العملاء")
        
        # تبويب إدارة المصروفات
        try:
            from views.expense_management import ExpenseManagementWindow
            self.expense_management = ExpenseManagementWindow(self.current_user)
            self.tab_widget.addTab(self.expense_management, "💰 المصروفات")
        except Exception as e:
            print(f"خطأ في تحميل إدارة المصروفات: {e}")
            # إنشاء تبويب بديل
            expense_tab = QWidget()
            expense_tab.setStyleSheet("background-color: white;")
            expense_layout = QVBoxLayout(expense_tab)
            expense_label = QLabel("إدارة المصروفات - خطأ في التحميل")
            expense_label.setAlignment(Qt.AlignCenter)
            expense_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            expense_layout.addWidget(expense_label)
            self.tab_widget.addTab(expense_tab, "💰 المصروفات")
        
        
        # تبويب إدارة المخزون
        try:
            from views.inventory_management import InventoryManagementWindow
            self.inventory_management = InventoryManagementWindow(self.current_user)
            self.tab_widget.addTab(self.inventory_management, "📦 المخزون")
        except Exception as e:
            print(f"خطأ في تحميل إدارة المخزون: {e}")
            # إنشاء تبويب بديل
            inventory_tab = QWidget()
            inventory_tab.setStyleSheet("background-color: white;")
            inventory_layout = QVBoxLayout(inventory_tab)
            inventory_label = QLabel("إدارة المخزون - خطأ في التحميل")
            inventory_label.setAlignment(Qt.AlignCenter)
            inventory_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            inventory_layout.addWidget(inventory_label)
            self.tab_widget.addTab(inventory_tab, "📦 المخزون")
        
        # تبويب التقارير
        try:
            from .reports_view import ReportsViewWindow
            self.reports_view = ReportsViewWindow(self.current_user)
            self.tab_widget.addTab(self.reports_view, "📊 التقارير")
        except Exception as e:
            print(f"⚠️ خطأ في تحميل قسم التقارير: {e}")
            # إنشاء تبويب بديل في حالة فشل التحميل
            self.reports_tab = QWidget()
            self.reports_tab.setStyleSheet("background-color: white;")
            reports_layout = QVBoxLayout(self.reports_tab)
            reports_label = QLabel("التقارير والإحصائيات - خطأ في التحميل")
            reports_label.setAlignment(Qt.AlignCenter)
            reports_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
            reports_layout.addWidget(reports_label)
            self.tab_widget.addTab(self.reports_tab, "📊 التقارير")
        
        # تبويب الإداريات (للمدير فقط) - بجانب التقارير
        if self.current_user.get('role', '') == 'admin':
            try:
                from views.administration_view import AdministrationView
                self.administration_view = AdministrationView(self.current_user)
                self.tab_widget.addTab(self.administration_view, "🏢 الإداريات")
                print("✅ تم تحميل تبويب الإداريات بنجاح")
            except Exception as e:
                print(f"❌ خطأ في تحميل الإداريات: {e}")
                import traceback
                traceback.print_exc()
        
        # تبويب الإعدادات (للمدير فقط)
        try:
            from utils.permissions import can_manage_cashiers
            if can_manage_cashiers(self.current_user.get('role', '')):
                from .settings_window import SettingsWindow
                self.settings_window = SettingsWindow(self.current_user)
                self.tab_widget.addTab(self.settings_window, "⚙️ الإعدادات")
            else:
                # إنشاء تبويب مخفي للكاشير
                settings_tab = QWidget()
                settings_tab.setStyleSheet("background-color: white;")
                settings_layout = QVBoxLayout(settings_tab)
                settings_label = QLabel("ليس لديك صلاحية للوصول إلى الإعدادات")
                settings_label.setAlignment(Qt.AlignCenter)
                settings_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
                settings_layout.addWidget(settings_label)
                # لا نضيف التبويب للكاشير
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
        
        parent_layout.addWidget(self.tab_widget)
    
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
            self.move(200, 200)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        # ربط إشارة تسجيل الخروج من إدارة الكاشيرات
        if hasattr(self, 'cashier_management'):
            self.cashier_management.logout_requested.connect(self.handle_logout)
        
        
        # ربط إشارة بدء وردية جديدة من إدارة الورديات
        if hasattr(self, 'shift_management'):
            self.shift_management.shift_started.connect(self.handle_shift_started)
    
    
    def handle_shift_started(self, shift_data):
        """معالج بدء وردية جديدة"""
        try:
            # تحديث بيانات الفواتير والمصروفات
            if hasattr(self, 'invoice_management'):
                self.invoice_management.load_invoices()
            
            if hasattr(self, 'expense_management'):
                self.expense_management.load_expenses()
            
            print("تم تحديث بيانات الفواتير والمصروفات بعد بدء وردية جديدة")
            
        except Exception as e:
            print(f"خطأ في تحديث البيانات بعد بدء الوردية: {e}")
    
    def switch_cashier(self, new_cashier):
        """التبديل التلقائي للكاشير"""
        try:
            # تحديث المستخدم الحالي
            self.current_user = new_cashier
            
            # تحديث شريط الحالة
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"المستخدم الحالي: {new_cashier.get('username', '')} - {new_cashier.get('full_name', '')}")
            
            # تحديث جميع الواجهات التي تعتمد على المستخدم الحالي
            if hasattr(self, 'device_panel'):
                self.device_panel.current_user = new_cashier
            
            if hasattr(self, 'invoice_management'):
                self.invoice_management.current_user = new_cashier
            
            if hasattr(self, 'expense_management'):
                self.expense_management.current_user = new_cashier
            
            if hasattr(self, 'customer_management'):
                self.customer_management.current_user = new_cashier
            
            print(f"تم التبديل التلقائي للكاشير: {new_cashier.get('username')}")
            
        except Exception as e:
            print(f"خطأ في التبديل التلقائي للكاشير: {e}")
    
    def setup_menu_bar(self):
        """إعداد شريط القوائم"""
        menubar = self.menuBar()
        
        # قائمة الملف
        file_menu = menubar.addMenu("الملف")
        
        # إعدادات
        settings_action = QAction("الإعدادات", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        
        # قائمة الأجهزة
        devices_menu = menubar.addMenu("الأجهزة")
        
        # إدارة الأجهزة
        manage_devices_action = QAction("إدارة الأجهزة", self)
        manage_devices_action.triggered.connect(self.show_device_management)
        devices_menu.addAction(manage_devices_action)
        
        # قائمة الفواتير
        invoices_menu = menubar.addMenu("الفواتير")
        
        # عرض الفواتير
        view_invoices_action = QAction("عرض الفواتير", self)
        view_invoices_action.triggered.connect(self.show_invoices)
        invoices_menu.addAction(view_invoices_action)
        
        # قائمة العملاء
        customers_menu = menubar.addMenu("العملاء")
        
        # إدارة العملاء
        manage_customers_action = QAction("إدارة العملاء", self)
        manage_customers_action.triggered.connect(self.show_customer_management)
        customers_menu.addAction(manage_customers_action)
        
        # قائمة التقارير
        reports_menu = menubar.addMenu("التقارير")
        
        # عرض التقارير
        view_reports_action = QAction("عرض التقارير", self)
        view_reports_action.triggered.connect(self.show_reports)
        reports_menu.addAction(view_reports_action)
        
        # قائمة المساعدة
        help_menu = menubar.addMenu("المساعدة")
        
        # حول التطبيق
        about_action = QAction("حول التطبيق", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = QToolBar("الأدوات الرئيسية")
        self.addToolBar(toolbar)
        
        # زر إدارة الأجهزة
        devices_action = QAction("الأجهزة", self)
        devices_action.triggered.connect(self.show_device_management)
        toolbar.addAction(devices_action)
        
        # زر الفواتير
        invoices_action = QAction("الفواتير", self)
        invoices_action.triggered.connect(self.show_invoices)
        toolbar.addAction(invoices_action)
        
        # زر العملاء
        customers_action = QAction("العملاء", self)
        customers_action.triggered.connect(self.show_customer_management)
        toolbar.addAction(customers_action)
        
        # زر حالة الجلسات
        sessions_action = QAction("⏸️ حالة الجلسات", self)
        sessions_action.triggered.connect(self.show_sessions_status)
        toolbar.addAction(sessions_action)
        
        toolbar.addSeparator()
        
        # زر التقارير
        reports_action = QAction("التقارير", self)
        reports_action.triggered.connect(self.show_reports)
        toolbar.addAction(reports_action)
        
        # زر الإعدادات
        settings_action = QAction("الإعدادات", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
    
    def setup_central_widget(self):
        """إعداد الـ widget المركزي"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # إنشاء الـ splitter الرئيسي
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # الجانب الأيسر - الإحصائيات السريعة
        self.create_stats_panel(main_splitter)
        
        # الجانب الأيمن - الأجهزة والتنبيهات
        self.create_right_panel(main_splitter)
        
        # تعيين نسب الـ splitter
        main_splitter.setSizes([400, 800])
    
    def create_stats_panel(self, parent):
        """إنشاء لوحة الإحصائيات"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(15)
        
        # عنوان اللوحة
        title_label = QLabel("الإحصائيات السريعة")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2E86AB;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }
        """)
        stats_layout.addWidget(title_label)
        
        # إحصائيات الإيرادات
        self.create_revenue_stats(stats_layout)
        
        # إحصائيات الأجهزة
        self.create_device_stats(stats_layout)
        
        # إحصائيات المنتجات
        self.create_product_stats(stats_layout)
        
        # إحصائيات العملاء
        self.create_customer_stats(stats_layout)
        
        parent.addWidget(stats_widget)
    
    def create_revenue_stats(self, parent_layout):
        """إنشاء إحصائيات الإيرادات"""
        revenue_group = QGroupBox("الإيرادات")
        revenue_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        revenue_layout = QGridLayout(revenue_group)
        
        # الإيرادات اليومية
        self.daily_revenue_label = QLabel("0.00 ج.م")
        self.daily_revenue_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #27ae60;
                padding: 5px;
            }
        """)
        revenue_layout.addWidget(QLabel("اليوم:"), 0, 0)
        revenue_layout.addWidget(self.daily_revenue_label, 0, 1)
        
        # الإيرادات الأسبوعية
        self.weekly_revenue_label = QLabel("0.00 ج.م")
        self.weekly_revenue_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #3498db;
                padding: 5px;
            }
        """)
        revenue_layout.addWidget(QLabel("هذا الأسبوع:"), 1, 0)
        revenue_layout.addWidget(self.weekly_revenue_label, 1, 1)
        
        # الإيرادات الشهرية
        self.monthly_revenue_label = QLabel("0.00 ج.م")
        self.monthly_revenue_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                padding: 5px;
            }
        """)
        revenue_layout.addWidget(QLabel("هذا الشهر:"), 2, 0)
        revenue_layout.addWidget(self.monthly_revenue_label, 2, 1)
        
        parent_layout.addWidget(revenue_group)
    
    def create_device_stats(self, parent_layout):
        """إنشاء إحصائيات الأجهزة"""
        device_group = QGroupBox("الأجهزة")
        device_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        device_layout = QGridLayout(device_group)
        
        # إجمالي الأجهزة
        self.total_devices_label = QLabel("0")
        self.total_devices_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                padding: 5px;
            }
        """)
        device_layout.addWidget(QLabel("إجمالي الأجهزة:"), 0, 0)
        device_layout.addWidget(self.total_devices_label, 0, 1)
        
        # الأجهزة المتاحة
        self.available_devices_label = QLabel("0")
        self.available_devices_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #27ae60;
                padding: 5px;
            }
        """)
        device_layout.addWidget(QLabel("متاحة:"), 1, 0)
        device_layout.addWidget(self.available_devices_label, 1, 1)
        
        # الأجهزة المشغولة
        self.occupied_devices_label = QLabel("0")
        self.occupied_devices_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                padding: 5px;
            }
        """)
        device_layout.addWidget(QLabel("مشغولة:"), 2, 0)
        device_layout.addWidget(self.occupied_devices_label, 2, 1)
        
        parent_layout.addWidget(device_group)
    
    def create_product_stats(self, parent_layout):
        """إنشاء إحصائيات المنتجات"""
        product_group = QGroupBox("المخزون")
        product_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        product_layout = QGridLayout(product_group)
        
        # إجمالي المنتجات
        self.total_products_label = QLabel("0")
        self.total_products_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                padding: 5px;
            }
        """)
        product_layout.addWidget(QLabel("إجمالي المنتجات:"), 0, 0)
        product_layout.addWidget(self.total_products_label, 0, 1)
        
        # المنتجات نافدة المخزون
        self.out_of_stock_label = QLabel("0")
        self.out_of_stock_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                padding: 5px;
            }
        """)
        product_layout.addWidget(QLabel("نافدة المخزون:"), 1, 0)
        product_layout.addWidget(self.out_of_stock_label, 1, 1)
        
        # المنتجات ذات المخزون المنخفض
        self.low_stock_label = QLabel("0")
        self.low_stock_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #f39c12;
                padding: 5px;
            }
        """)
        product_layout.addWidget(QLabel("مخزون منخفض:"), 2, 0)
        product_layout.addWidget(self.low_stock_label, 2, 1)
        
        parent_layout.addWidget(product_group)
    
    def create_customer_stats(self, parent_layout):
        """إنشاء إحصائيات العملاء"""
        customer_group = QGroupBox("العملاء")
        customer_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        customer_layout = QGridLayout(customer_group)
        
        # إجمالي العملاء
        self.total_customers_label = QLabel("0")
        self.total_customers_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2E86AB;
                padding: 5px;
            }
        """)
        customer_layout.addWidget(QLabel("إجمالي العملاء:"), 0, 0)
        customer_layout.addWidget(self.total_customers_label, 0, 1)
        
        # إجمالي الرصيد
        self.total_balance_label = QLabel("0.00 ج.م")
        self.total_balance_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #27ae60;
                padding: 5px;
            }
        """)
        customer_layout.addWidget(QLabel("إجمالي الرصيد:"), 1, 0)
        customer_layout.addWidget(self.total_balance_label, 1, 1)
        
        parent_layout.addWidget(customer_group)
    
    def create_right_panel(self, parent):
        """إنشاء اللوحة اليمنى"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        
        # عنوان اللوحة
        title_label = QLabel("الأجهزة والتنبيهات")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2E86AB;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }
        """)
        right_layout.addWidget(title_label)
        
        # إنشاء الـ tab widget
        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        # تبويب الأجهزة
        self.create_devices_tab()
        
        # تبويب التنبيهات
        self.create_notifications_tab()
        
        # تبويب الجلسات النشطة
        self.create_active_sessions_tab()
        
        parent.addWidget(right_widget)
    
    def create_devices_tab(self):
        """إنشاء تبويب الأجهزة"""
        devices_widget = QWidget()
        devices_layout = QVBoxLayout(devices_widget)
        
        # عنوان التبويب
        devices_title = QLabel("حالة الأجهزة")
        devices_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
        """)
        devices_layout.addWidget(devices_title)
        
        # منطقة عرض الأجهزة
        self.devices_scroll = QScrollArea()
        self.devices_scroll.setWidgetResizable(True)
        self.devices_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
        """)
        
        self.devices_container = QWidget()
        self.devices_layout = QGridLayout(self.devices_container)
        self.devices_layout.setSpacing(10)
        
        self.devices_scroll.setWidget(self.devices_container)
        devices_layout.addWidget(self.devices_scroll)
        
        self.tab_widget.addTab(devices_widget, "الأجهزة")
    
    def create_notifications_tab(self):
        """إنشاء تبويب التنبيهات"""
        notifications_widget = QWidget()
        notifications_layout = QVBoxLayout(notifications_widget)
        
        # عنوان التبويب
        notifications_title = QLabel("التنبيهات والإشعارات")
        notifications_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
        """)
        notifications_layout.addWidget(notifications_title)
        
        # منطقة التنبيهات
        self.notifications_scroll = QScrollArea()
        self.notifications_scroll.setWidgetResizable(True)
        self.notifications_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
        """)
        
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setSpacing(5)
        
        self.notifications_scroll.setWidget(self.notifications_container)
        notifications_layout.addWidget(self.notifications_scroll)
        
        self.tab_widget.addTab(notifications_widget, "التنبيهات")
    
    def create_active_sessions_tab(self):
        """إنشاء تبويب الجلسات النشطة"""
        sessions_widget = QWidget()
        sessions_layout = QVBoxLayout(sessions_widget)
        
        # عنوان التبويب
        sessions_title = QLabel("الجلسات النشطة")
        sessions_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
        """)
        sessions_layout.addWidget(sessions_title)
        
        # منطقة الجلسات النشطة
        self.sessions_scroll = QScrollArea()
        self.sessions_scroll.setWidgetResizable(True)
        self.sessions_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
        """)
        
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(5)
        
        self.sessions_scroll.setWidget(self.sessions_container)
        sessions_layout.addWidget(self.sessions_scroll)
        
        self.tab_widget.addTab(sessions_widget, "الجلسات النشطة")
    
    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # معلومات المستخدم
        user_info = f"المستخدم: {self.current_user.get('username', '')} ({self.current_user.get('role', '')})"
        self.status_bar.showMessage(user_info)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # الوقت الحالي
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
    
    def setup_layout(self):
        """إعداد التخطيط"""
        # تطبيق التخطيط RTL إذا كان مفعلاً
        if self.app_config.get('ui.rtl_support', True):
            self.setLayoutDirection(Qt.RightToLeft)
    
    def apply_settings(self):
        """تطبيق الإعدادات"""
        try:
            # إعداد حجم النافذة
            window_width = self.app_config.get('ui.window_width', 1200)
            window_height = self.app_config.get('ui.window_height', 800)
            self.resize(window_width, window_height)
            
            # إعداد الخط
            font_family = self.app_config.get('ui.font_family', 'Arial')
            font_size = self.app_config.get('ui.font_size', 12)
            font = QFont(font_family, font_size)
            self.setFont(font)
            
        except Exception as e:
            pass
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        pass
    
    def setup_timers(self):
        """إعداد التايمرات"""
        # تايمر تحديث البيانات
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_dashboard_data)
        self.data_timer.start(30000)  # كل 30 ثانية
        
        # تايمر تحديث الوقت
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # كل ثانية
        
        # تايمر التنبيهات
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(60000)  # كل دقيقة
    
    def load_dashboard_data(self):
        """تحميل بيانات لوحة التحكم"""
        try:
            self.update_dashboard_data()
            self.update_devices_display()
            self.update_active_sessions()
            self.update_notifications()
            
        except Exception as e:
            pass
    
    def update_dashboard_data(self):
        """تحديث بيانات لوحة التحكم"""
        try:
            # تحديث الإحصائيات
            self.update_revenue_stats()
            self.update_device_stats()
            self.update_product_stats()
            self.update_customer_stats()
            
        except Exception as e:
            pass
    
    def update_revenue_stats(self):
        """تحديث إحصائيات الإيرادات"""
        try:
            # الإيرادات اليومية
            today = datetime.now().date()
            daily_stats = self.invoice_model.get_invoice_stats(
                start_date=datetime.combine(today, datetime.min.time()),
                end_date=datetime.combine(today, datetime.max.time())
            )
            daily_revenue = daily_stats.get('total_revenue', 0)
            self.daily_revenue_label.setText(format_currency(daily_revenue))
            
            # الإيرادات الأسبوعية
            week_start = today - timedelta(days=today.weekday())
            weekly_stats = self.invoice_model.get_invoice_stats(
                start_date=datetime.combine(week_start, datetime.min.time()),
                end_date=datetime.now()
            )
            weekly_revenue = weekly_stats.get('total_revenue', 0)
            self.weekly_revenue_label.setText(format_currency(weekly_revenue))
            
            # الإيرادات الشهرية
            month_start = today.replace(day=1)
            monthly_stats = self.invoice_model.get_invoice_stats(
                start_date=datetime.combine(month_start, datetime.min.time()),
                end_date=datetime.now()
            )
            monthly_revenue = monthly_stats.get('total_revenue', 0)
            self.monthly_revenue_label.setText(format_currency(monthly_revenue))
            
        except Exception as e:
            pass
    
    def update_device_stats(self):
        """تحديث إحصائيات الأجهزة"""
        try:
            device_stats = self.device_model.get_device_stats()
            
            self.total_devices_label.setText(str(device_stats.get('total_devices', 0)))
            self.available_devices_label.setText(str(device_stats.get('available_devices', 0)))
            self.occupied_devices_label.setText(str(device_stats.get('occupied_devices', 0)))
            
        except Exception as e:
            pass
    
    def update_product_stats(self):
        """تحديث إحصائيات المنتجات"""
        try:
            product_stats = self.product_model.get_product_stats()
            
            self.total_products_label.setText(str(product_stats.get('total_products', 0)))
            self.out_of_stock_label.setText(str(product_stats.get('out_of_stock', 0)))
            self.low_stock_label.setText(str(product_stats.get('low_stock', 0)))
            
        except Exception as e:
            pass
    
    def update_customer_stats(self):
        """تحديث إحصائيات العملاء"""
        try:
            from models.customer_model import CustomerModel
            customer_model = CustomerModel()
            customer_stats = customer_model.get_customer_stats()
            
            self.total_customers_label.setText(str(customer_stats.get('total_customers', 0)))
            self.total_balance_label.setText(format_currency(customer_stats.get('total_balance', 0)))
            
        except Exception as e:
            pass
    
    def update_devices_display(self):
        """تحديث عرض الأجهزة"""
        try:
            # مسح الأجهزة الحالية
            for i in reversed(range(self.devices_layout.count())):
                self.devices_layout.itemAt(i).widget().setParent(None)
            
            # الحصول على الأجهزة
            devices = self.device_model.get_all_devices()
            
            # عرض الأجهزة
            row = 0
            col = 0
            for device in devices:
                device_widget = self.create_device_widget(device)
                self.devices_layout.addWidget(device_widget, row, col)
                
                col += 1
                if col >= 3:  # 3 أجهزة في كل صف
                    col = 0
                    row += 1
            
        except Exception as e:
            pass
    
    def create_device_widget(self, device):
        """إنشاء widget للجهاز"""
        device_frame = QFrame()
        device_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                background: white;
            }
        """)
        
        device_layout = QVBoxLayout(device_frame)
        
        # اسم الجهاز
        name_label = QLabel(device['name'])
        name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        device_layout.addWidget(name_label)
        
        # نوع الجهاز
        type_label = QLabel(f"النوع: {device['type']}")
        type_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
            }
        """)
        device_layout.addWidget(type_label)
        
        # حالة الجهاز
        status = device['status']
        status_label = QLabel(f"الحالة: {status}")
        
        if status == 'available':
            status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #27ae60;
                    font-weight: bold;
                }
            """)
        elif status == 'occupied':
            status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #e74c3c;
                    font-weight: bold;
                }
            """)
        else:
            status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #f39c12;
                    font-weight: bold;
                }
            """)
        
        device_layout.addWidget(status_label)
        
        # السعر
        price_label = QLabel(f"السعر: {format_currency(device['price_single'])}")
        price_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #2E86AB;
                font-weight: bold;
            }
        """)
        device_layout.addWidget(price_label)
        
        return device_frame
    
    def update_active_sessions(self):
        """تحديث الجلسات النشطة"""
        try:
            # مسح الجلسات الحالية
            for i in reversed(range(self.sessions_layout.count())):
                self.sessions_layout.itemAt(i).widget().setParent(None)
            
            # الحصول على الجلسات النشطة
            active_invoices = self.invoice_model.get_active_invoices()
            
            # عرض الجلسات النشطة
            for invoice in active_invoices:
                session_widget = self.create_session_widget(invoice)
                self.sessions_layout.addWidget(session_widget)
            
        except Exception as e:
            pass
    
    def create_session_widget(self, invoice):
        """إنشاء widget للجلسة"""
        session_frame = QFrame()
        session_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                background: #f8f9fa;
            }
        """)
        
        session_layout = QVBoxLayout(session_frame)
        
        # معلومات الجلسة
        device_name = invoice.get('device_name', 'غير محدد')
        start_time = format_time(invoice['start_time'], 'short')
        
        info_label = QLabel(f"{device_name} - بدأت: {start_time}")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #333;
                font-weight: bold;
            }
        """)
        session_layout.addWidget(info_label)
        
        # الكاشير
        cashier_name = invoice.get('cashier_open_name', 'غير محدد')
        cashier_label = QLabel(f"الكاشير: {cashier_name}")
        cashier_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
            }
        """)
        session_layout.addWidget(cashier_label)
        
        return session_frame
    
    def update_notifications(self):
        """تحديث التنبيهات"""
        try:
            # مسح التنبيهات الحالية
            for i in reversed(range(self.notifications_layout.count())):
                self.notifications_layout.itemAt(i).widget().setParent(None)
            
            # الحصول على التنبيهات
            notifications = self.notification_manager.get_notification_history(10)
            
            # عرض التنبيهات
            for notification in notifications:
                notification_widget = self.create_notification_widget(notification)
                self.notifications_layout.addWidget(notification_widget)
            
        except Exception as e:
            pass
    
    def create_notification_widget(self, notification):
        """إنشاء widget للتنبيه"""
        notification_frame = QFrame()
        notification_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                background: white;
            }
        """)
        
        notification_layout = QVBoxLayout(notification_frame)
        
        # عنوان التنبيه
        title_label = QLabel(notification.get('title', ''))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #333;
            }
        """)
        notification_layout.addWidget(title_label)
        
        # رسالة التنبيه
        message_label = QLabel(notification.get('message', ''))
        message_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
            }
        """)
        notification_layout.addWidget(message_label)
        
        # وقت التنبيه
        timestamp = notification.get('timestamp', datetime.now())
        time_label = QLabel(format_time(timestamp, 'short'))
        time_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #999;
            }
        """)
        notification_layout.addWidget(time_label)
        
        return notification_frame
    
    def update_time(self):
        """تحديث الوقت"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.setText(current_time)
        except Exception as e:
            pass
    
    def check_notifications(self):
        """التحقق من التنبيهات"""
        try:
            # التحقق من انتهاء الجلسات
            self.check_session_timeouts()
            
            # التحقق من المخزون المنخفض
            self.check_low_stock()
            
        except Exception as e:
            pass
    
    def check_session_timeouts(self):
        """التحقق من انتهاء وقت الجلسات"""
        try:
            # يمكن إضافة منطق التحقق من انتهاء الجلسات هنا
            pass
        except Exception as e:
            pass
    
    def check_low_stock(self):
        """التحقق من المخزون المنخفض"""
        try:
            low_stock_products = self.product_model.get_low_stock_products()
            
            for product in low_stock_products:
                self.notification_manager.show_low_stock_alert(
                    product['name'],
                    product['stock_quantity'],
                    product['min_stock_level']
                )
                
        except Exception as e:
            pass
    
    def show_device_management(self):
        """عرض إدارة الأجهزة"""
        try:
            # يمكن إضافة منطق عرض إدارة الأجهزة هنا
            pass
        except Exception as e:
            pass
    
    def show_invoices(self):
        """عرض الفواتير"""
        try:
            # يمكن إضافة منطق عرض الفواتير هنا
            pass
        except Exception as e:
            pass
    
    def show_customer_management(self):
        """عرض إدارة العملاء"""
        try:
            # يمكن إضافة منطق عرض إدارة العملاء هنا
            pass
        except Exception as e:
            pass
    
    def show_sessions_status(self):
        """عرض حالة الجلسات"""
        try:
            from utils.session_manager import SessionManager
            session_manager = SessionManager()
            status = session_manager.get_sessions_status()
            
            # إنشاء نافذة عرض حالة الجلسات
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("حالة الجلسات")
            dialog.setModal(True)
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # عنوان النافذة
            title_label = QLabel("📊 حالة الجلسات في النظام")
            title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # معلومات عامة
            info_label = QLabel(f"الجلسات النشطة: {status['active_count']} | الجلسات الموقوفة: {status['paused_count']}")
            info_label.setStyleSheet("font-size: 14px; color: #34495e; margin: 5px;")
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)
            
            # جدول الجلسات النشطة
            if status['active_sessions']:
                active_label = QLabel("🟢 الجلسات النشطة:")
                active_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60; margin: 10px 5px 5px 5px;")
                layout.addWidget(active_label)
                
                active_table = QTableWidget()
                active_table.setColumnCount(5)
                active_table.setHorizontalHeaderLabels(["الجهاز", "الكاشير", "نوع التسعيرة", "السعر", "وقت البداية"])
                
                active_table.setRowCount(len(status['active_sessions']))
                for i, session in enumerate(status['active_sessions']):
                    active_table.setItem(i, 0, QTableWidgetItem(session.get('device_name', 'غير محدد')))
                    active_table.setItem(i, 1, QTableWidgetItem(session.get('cashier_name', 'غير محدد')))
                    active_table.setItem(i, 2, QTableWidgetItem(session.get('pricing_type', 'غير محدد')))
                    active_table.setItem(i, 3, QTableWidgetItem(f"{session.get('session_price', 0):.2f} ج.م"))
                    start_time = session.get('start_time', '')
                    if start_time:
                        from datetime import datetime
                        if isinstance(start_time, str):
                            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        active_table.setItem(i, 4, QTableWidgetItem(start_time.strftime("%Y-%m-%d %H:%M:%S")))
                    else:
                        active_table.setItem(i, 4, QTableWidgetItem("غير محدد"))
                
                active_table.resizeColumnsToContents()
                layout.addWidget(active_table)
            
            # جدول الجلسات الموقوفة
            if status['paused_sessions']:
                paused_label = QLabel("⏸️ الجلسات الموقوفة:")
                paused_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12; margin: 10px 5px 5px 5px;")
                layout.addWidget(paused_label)
                
                paused_table = QTableWidget()
                paused_table.setColumnCount(5)
                paused_table.setHorizontalHeaderLabels(["الجهاز", "الكاشير", "نوع التسعيرة", "السعر", "وقت البداية"])
                
                paused_table.setRowCount(len(status['paused_sessions']))
                for i, session in enumerate(status['paused_sessions']):
                    paused_table.setItem(i, 0, QTableWidgetItem(session.get('device_name', 'غير محدد')))
                    paused_table.setItem(i, 1, QTableWidgetItem(session.get('cashier_name', 'غير محدد')))
                    paused_table.setItem(i, 2, QTableWidgetItem(session.get('pricing_type', 'غير محدد')))
                    paused_table.setItem(i, 3, QTableWidgetItem(f"{session.get('session_price', 0):.2f} ج.م"))
                    start_time = session.get('start_time', '')
                    if start_time:
                        from datetime import datetime
                        if isinstance(start_time, str):
                            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        paused_table.setItem(i, 4, QTableWidgetItem(start_time.strftime("%Y-%m-%d %H:%M:%S")))
                    else:
                        paused_table.setItem(i, 4, QTableWidgetItem("غير محدد"))
                
                paused_table.resizeColumnsToContents()
                layout.addWidget(paused_table)
            
            # أزرار التحكم
            buttons_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("🔄 تحديث")
            refresh_btn.clicked.connect(lambda: self.show_sessions_status())
            buttons_layout.addWidget(refresh_btn)
            
            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"خطأ في عرض حالة الجلسات: {e}")
            self.show_error_message(f"خطأ في عرض حالة الجلسات: {str(e)}")
    
    def show_reports(self):
        """عرض التقارير"""
        try:
            # يمكن إضافة منطق عرض التقارير هنا
            pass
        except Exception as e:
            pass
    
    def show_settings(self):
        """عرض الإعدادات"""
        try:
            # يمكن إضافة منطق عرض الإعدادات هنا
            pass
        except Exception as e:
            pass
    
    def show_about(self):
        """عرض معلومات التطبيق"""
        try:
            about_text = f"""
            <h3>نظام إدارة محل بلايستيشن</h3>
            <p><b>الإصدار:</b> {self.app_config.get('app.version', '1.0.0')}</p>
            <p><b>المطور:</b> {self.app_config.get('app.author', 'PS System Team')}</p>
            <p><b>المستخدم الحالي:</b> {self.current_user.get('username', '')}</p>
            <p><b>الدور:</b> {self.current_user.get('role', '')}</p>
            <p>نظام إدارة شامل لمحلات البلايستيشن والمشروبات والمأكولات</p>
            """
            
            msg_box = QMessageBox()
            msg_box.setWindowTitle("حول التطبيق")
            msg_box.setText(about_text)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.exec()
            
        except Exception as e:
            pass
    
    def handle_logout(self):
        """معالج تسجيل الخروج"""
        try:
            reply = QMessageBox.question(
                self,
                "تسجيل الخروج",
                "هل أنت متأكد من تسجيل الخروج؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.logout_requested.emit()
                
        except Exception as e:
            pass
    
    def apply_permissions(self):
        """تطبيق الصلاحيات على واجهة المستخدم"""
        try:
            from utils.permissions import (
                check_permission, Permission, can_manage_cashiers,
                can_access_reports, can_manage_system
            )
            
            user_role = self.current_user.get('role', '')
            
            # إخفاء/إظهار التبويبات حسب الصلاحيات
            for i in range(self.tab_widget.count()):
                tab_text = self.tab_widget.tabText(i)
                
                # إخفاء تبويب التقارير إذا لم يكن لديه صلاحية
                if "التقارير" in tab_text and not can_access_reports(user_role):
                    self.tab_widget.setTabVisible(i, False)
                
                # إخفاء تبويب إعدادات النظام إذا لم يكن لديه صلاحية
                if "الإعدادات" in tab_text and not can_manage_system(user_role):
                    self.tab_widget.setTabVisible(i, False)
            
            # تحديث عنوان النافذة ليشمل الدور
            role_display = "مدير" if user_role == "admin" else "كاشير"
            self.setWindowTitle(f"لوحة التحكم - {self.current_user.get('username', '')} ({role_display})")
            
            print(f"✅ تم تطبيق الصلاحيات للمستخدم: {self.current_user.get('username', '')} - الدور: {role_display}")
            
        except Exception as e:
            print(f"خطأ في تطبيق الصلاحيات: {e}")
    
    def closeEvent(self, event):
        """معالج إغلاق النافذة"""
        try:
            reply = QMessageBox.question(
                self,
                "إغلاق التطبيق",
                "هل أنت متأكد من إغلاق التطبيق؟\nسيتم إيقاف جميع الجلسات النشطة تلقائياً.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # إيقاف جميع الجلسات النشطة
                self.pause_all_sessions_on_shutdown()
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            event.accept()
    
    def pause_all_sessions_on_shutdown(self):
        """إيقاف جميع الجلسات عند إغلاق التطبيق"""
        try:
            from utils.session_manager import SessionManager
            session_manager = SessionManager()
            result = session_manager.pause_all_active_sessions()
            
            if result['success']:
                if result['paused_count'] > 0:
                    logger.info(f"تم إيقاف {result['paused_count']} جلسة عند إغلاق التطبيق")
                    # عرض رسالة للمستخدم
                    self.show_info_message(f"تم إيقاف {result['paused_count']} جلسة نشطة.\nسيتم استئنافها عند فتح التطبيق مرة أخرى.")
                else:
                    logger.info("لا توجد جلسات نشطة لإيقافها")
            else:
                logger.error(f"فشل في إيقاف الجلسات: {result['message']}")
                self.show_error_message(f"تحذير: {result['message']}")
                
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسات عند إغلاق التطبيق: {e}")
            self.show_error_message(f"تحذير: خطأ في إيقاف الجلسات")
    
    def show_info_message(self, message: str):
        """عرض رسالة معلومات"""
        try:
            from PySide6.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("معلومات")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        except Exception as e:
            logger.error(f"خطأ في عرض رسالة المعلومات: {e}")
    
    def show_error_message(self, message: str):
        """عرض رسالة خطأ"""
        try:
            from PySide6.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("خطأ")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        except Exception as e:
            logger.error(f"خطأ في عرض رسالة الخطأ: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = DashboardWindow(test_user)
    window.show()
    sys.exit(app.exec())
