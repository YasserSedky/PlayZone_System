"""
واجهة التقارير الشاملة
Comprehensive Reports View
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QMessageBox, QGroupBox,
    QTabWidget, QDateEdit, QTextEdit, QProgressBar, QScrollArea,
    QSplitter, QSpinBox, QCheckBox, QSlider
)
from PySide6.QtCore import Qt, Signal, QDate, QThread, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon, QPainter, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.report_controller import ReportController
from utils.helpers import format_currency, format_time
from utils.notifications import show_success, show_error

class ReportGenerationThread(QThread):
    """خيط إنشاء التقارير"""
    report_ready = Signal(dict)
    progress_updated = Signal(int)
    
    def __init__(self, controller, report_type, params):
        super().__init__()
        self.controller = controller
        self.report_type = report_type
        self.params = params
    
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            if self.report_type == 'revenue':
                result = self.controller.get_revenue_report(**self.params)
            elif self.report_type == 'profit':
                result = self.controller.get_profit_report(**self.params)
            elif self.report_type == 'device':
                result = self.controller.get_device_report(**self.params)
            elif self.report_type == 'product':
                result = self.controller.get_product_report(**self.params)
            elif self.report_type == 'expense':
                result = self.controller.get_expense_report(**self.params)
            elif self.report_type == 'customer':
                result = self.controller.get_customer_report(**self.params)
            elif self.report_type == 'shift':
                result = self.controller.get_shift_report(**self.params)
            # elif self.report_type == 'kpi_dashboard':  # تم حذف مؤشرات الأداء
            #     result = self.controller.get_kpi_dashboard(**self.params)
            else:
                result = {'success': False, 'message': 'نوع التقرير غير صحيح'}
            
            self.progress_updated.emit(100)
            self.report_ready.emit(result)
            
        except Exception as e:
            self.report_ready.emit({'success': False, 'message': str(e)})

class ReportsViewWindow(QMainWindow):
    """نافذة التقارير الشاملة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.controller = ReportController(current_user)
        self.current_report_data = None
        self.report_thread = None
        
        self.setup_ui()
        self.load_initial_data()
    
    def closeEvent(self, event):
        """إغلاق النافذة وإنهاء الخيوط"""
        try:
            if self.report_thread and self.report_thread.isRunning():
                self.report_thread.terminate()
                self.report_thread.wait(3000)  # انتظار 3 ثوان
        except Exception as e:
            print(f"خطأ في إنهاء الخيط: {e}")
        
        event.accept()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("التقارير والإحصائيات - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1400, 900)
        
        # إنشاء منطقة التمرير الرئيسية
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # الـ widget المركزي
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # عنوان النافذة
        self.create_header(main_layout)
        
        # إنشاء الـ tab widget
        self.create_tabs(main_layout)
    
    def create_header(self, parent_layout):
        """إنشاء رأس الصفحة"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2E86AB;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("📊 التقارير والإحصائيات")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # معلومات المستخدم
        user_info = QLabel(f"المستخدم: {self.current_user.get('username', '')}")
        user_info.setStyleSheet("color: white; font-size: 12px;")
        header_layout.addWidget(user_info)
        
        parent_layout.addWidget(header_frame)
    
    def create_tabs(self, parent_layout):
        """إنشاء تبويبات التقارير"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
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
        
        # إنشاء التبويبات
        self.create_revenue_tab()
        self.create_profit_tab()
        self.create_device_tab()
        self.create_product_tab()
        self.create_expense_tab()
        self.create_customer_tab()
        self.create_shift_tab()
        self.create_invoices_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_filter_controls(self, parent_layout):
        """إنشاء أدوات التصفية"""
        filter_group = QGroupBox("تصفية التقارير")
        filter_group.setStyleSheet("""
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
        
        filter_layout = QGridLayout(filter_group)
        
        # التاريخ من
        filter_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate().addDays(-30))
        self.start_date_input.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date_input, 0, 1)
        
        # التاريخ إلى
        filter_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date_input, 0, 3)
        
        # أزرار سريعة للفترات
        period_layout = QHBoxLayout()
        
        today_btn = QPushButton("اليوم")
        today_btn.clicked.connect(lambda: self.set_period('today'))
        period_layout.addWidget(today_btn)
        
        week_btn = QPushButton("هذا الأسبوع")
        week_btn.clicked.connect(lambda: self.set_period('week'))
        period_layout.addWidget(week_btn)
        
        month_btn = QPushButton("هذا الشهر")
        month_btn.clicked.connect(lambda: self.set_period('month'))
        period_layout.addWidget(month_btn)
        
        year_btn = QPushButton("هذا العام")
        year_btn.clicked.connect(lambda: self.set_period('year'))
        period_layout.addWidget(year_btn)
        
        filter_layout.addLayout(period_layout, 1, 0, 1, 4)
        
        # زر تحديث
        refresh_btn = QPushButton("🔄 تحديث البيانات")
        # refresh_btn.clicked.connect(self.refresh_kpi_data)  # تم حذف مؤشرات الأداء
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        filter_layout.addWidget(refresh_btn, 2, 0, 1, 2)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        filter_layout.addWidget(self.progress_bar, 2, 2, 1, 2)
        
        parent_layout.addWidget(filter_group)
    
    
    
    def create_revenue_tab(self):
        """إنشاء تبويب تقارير الإيرادات"""
        revenue_widget = QWidget()
        revenue_layout = QVBoxLayout(revenue_widget)
        
        # أدوات التصفية
        self.create_revenue_filters(revenue_layout)
        
        # بطاقات إجمالي الإيرادات
        self.create_revenue_summary_cards(revenue_layout)
        
        # تبويب الإيرادات اليومية
        daily_widget = QWidget()
        daily_layout = QVBoxLayout(daily_widget)
        
        self.daily_revenue_table = QTableWidget()
        self.daily_revenue_table.setColumnCount(4)
        self.daily_revenue_table.setHorizontalHeaderLabels([
            "التاريخ", "عدد الفواتير", "الإيرادات", "متوسط الفاتورة"
        ])
        daily_layout.addWidget(self.daily_revenue_table)
        
        revenue_layout.addWidget(daily_widget)
        
        self.tab_widget.addTab(revenue_widget, "💰 تقارير الإيرادات")
    
    def create_profit_tab(self):
        """إنشاء تبويب تقارير الأرباح"""
        profit_widget = QWidget()
        profit_layout = QVBoxLayout(profit_widget)
        
        # أدوات التصفية
        self.create_profit_filters(profit_layout)
        
        # بطاقات إجمالي الأرباح
        self.create_profit_summary_cards(profit_layout)
        
        # تبويبات فرعية للإيرادات والمصروفات
        profit_tabs = QTabWidget()
        
        # تبويب الإيرادات اليومية
        revenue_widget = QWidget()
        revenue_layout = QVBoxLayout(revenue_widget)
        
        self.profit_revenue_table = QTableWidget()
        self.profit_revenue_table.setColumnCount(4)
        self.profit_revenue_table.setHorizontalHeaderLabels([
            "التاريخ", "عدد الفواتير", "الإيرادات", "متوسط الفاتورة"
        ])
        revenue_layout.addWidget(self.profit_revenue_table)
        
        profit_tabs.addTab(revenue_widget, "الإيرادات اليومية")
        
        # تبويب المصروفات اليومية
        expense_widget = QWidget()
        expense_layout = QVBoxLayout(expense_widget)
        
        self.profit_expense_table = QTableWidget()
        self.profit_expense_table.setColumnCount(4)
        self.profit_expense_table.setHorizontalHeaderLabels([
            "التاريخ", "عدد المصروفات", "إجمالي المصروفات", "متوسط المصروف"
        ])
        expense_layout.addWidget(self.profit_expense_table)
        
        profit_tabs.addTab(expense_widget, "المصروفات اليومية")
        
        profit_layout.addWidget(profit_tabs)
        
        self.tab_widget.addTab(profit_widget, "📈 تقارير الأرباح")
    
    def create_device_tab(self):
        """إنشاء تبويب تقارير الأجهزة"""
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        
        # أدوات التصفية
        self.create_device_filters(device_layout)
        
        # جدول أداء الأجهزة
        self.device_performance_table = QTableWidget()
        self.device_performance_table.setColumnCount(6)
        self.device_performance_table.setHorizontalHeaderLabels([
            "اسم الجهاز", "النوع", "عدد الجلسات", "الإيرادات", "متوسط الجلسة", "وقت الاستخدام"
        ])
        
        device_layout.addWidget(self.device_performance_table)
        
        self.tab_widget.addTab(device_widget, "🎮 تقارير الأجهزة")
    
    def create_product_tab(self):
        """إنشاء تبويب تقارير المنتجات"""
        product_widget = QWidget()
        product_layout = QVBoxLayout(product_widget)
        
        # أدوات التصفية
        self.create_product_filters(product_layout)
        
        # إضافة بطاقات الإجماليات
        self.create_product_summary_cards(product_layout)
        
        # إنشاء التبويبات الفرعية
        product_tabs = QTabWidget()
        
        # تبويب مبيعات المنتجات
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)
        
        self.product_sales_table = QTableWidget()
        self.product_sales_table.setColumnCount(5)
        self.product_sales_table.setHorizontalHeaderLabels([
            "اسم المنتج", "الفئة", "الكمية المباعة", "الإيرادات", "متوسط السعر"
        ])
        sales_layout.addWidget(self.product_sales_table)
        
        product_tabs.addTab(sales_widget, "مبيعات المنتجات")
        
        # تبويب حالة المخزون
        stock_widget = QWidget()
        stock_layout = QVBoxLayout(stock_widget)
        
        self.stock_status_table = QTableWidget()
        self.stock_status_table.setColumnCount(4)
        self.stock_status_table.setHorizontalHeaderLabels([
            "اسم المنتج", "المخزون الحالي", "الحد الأدنى", "الحالة"
        ])
        stock_layout.addWidget(self.stock_status_table)
        
        product_tabs.addTab(stock_widget, "حالة المخزون")
        
        product_layout.addWidget(product_tabs)
        
        self.tab_widget.addTab(product_widget, "🛒 تقارير المنتجات")
    
    def create_expense_tab(self):
        """إنشاء تبويب تقارير المصروفات"""
        expense_widget = QWidget()
        expense_layout = QVBoxLayout(expense_widget)
        
        # أدوات التصفية
        self.create_expense_filters(expense_layout)
        
        # إضافة بطاقات الإجماليات
        self.create_expense_summary_cards(expense_layout)
        
        # جدول المصروفات
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(5)
        self.expense_table.setHorizontalHeaderLabels([
            "التاريخ", "المبلغ", "السبب", "الكاشير", "الوردية"
        ])
        
        expense_layout.addWidget(self.expense_table)
        
        self.tab_widget.addTab(expense_widget, "💸 تقارير المصروفات")
    
    def create_customer_tab(self):
        """إنشاء تبويب تقارير العملاء"""
        customer_widget = QWidget()
        customer_layout = QVBoxLayout(customer_widget)
        
        # أدوات التصفية
        self.create_customer_filters(customer_layout)
        
        # إنشاء التبويبات الفرعية
        customer_tabs = QTabWidget()
        
        # تبويب إحصائيات العملاء
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        self.customer_stats_table = QTableWidget()
        self.customer_stats_table.setColumnCount(3)
        self.customer_stats_table.setHorizontalHeaderLabels([
            "المؤشر", "القيمة", "التفاصيل"
        ])
        stats_layout.addWidget(self.customer_stats_table)
        
        customer_tabs.addTab(stats_widget, "إحصائيات العملاء")
        
        # تبويب العملاء الأكثر رصيداً
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        self.top_customers_table = QTableWidget()
        self.top_customers_table.setColumnCount(4)
        self.top_customers_table.setHorizontalHeaderLabels([
            "اسم العميل", "رقم الهاتف", "الرصيد", "تاريخ التسجيل"
        ])
        top_layout.addWidget(self.top_customers_table)
        
        customer_tabs.addTab(top_widget, "العملاء")
        
        customer_layout.addWidget(customer_tabs)
        
        self.tab_widget.addTab(customer_widget, "👥 تقارير العملاء")
    
    
    def create_shift_tab(self):
        """إنشاء تبويب تقارير الورديات"""
        shift_widget = QWidget()
        shift_layout = QVBoxLayout(shift_widget)
        
        # أدوات التصفية
        self.create_shift_filters(shift_layout)
        
        # جدول الورديات
        self.shift_table = QTableWidget()
        self.shift_table.setColumnCount(6)
        self.shift_table.setHorizontalHeaderLabels([
            "اسم الوردية", "الكاشير", "وقت البداية", "وقت النهاية", "الإيرادات", "المصروفات"
        ])
        
        shift_layout.addWidget(self.shift_table)
        
        self.tab_widget.addTab(shift_widget, "🕐 تقارير الورديات")
    
    
    def create_invoices_tab(self):
        """إنشاء تبويب تقارير الفواتير"""
        invoices_widget = QWidget()
        invoices_layout = QVBoxLayout(invoices_widget)
        
        # أدوات التصفية للفواتير
        self.create_invoice_filters(invoices_layout)
        
        # تحميل بيانات الفلاتر
        self.load_invoice_references()
        
        # أزرار التحكم
        self.create_invoice_controls(invoices_layout)
        
        # بطاقات الإجمالي
        self.create_invoice_summary_cards(invoices_layout)
        
        # جدول الفواتير
        self.create_invoices_table(invoices_layout)
        
        self.tab_widget.addTab(invoices_widget, "🧾 الفواتير")
        
        # تحميل الفواتير تلقائياً عند فتح التبويب
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def create_invoice_filters(self, parent_layout):
        """إنشاء أدوات تصفية الفواتير"""
        filter_group = QGroupBox("تصفية الفواتير")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
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
        filter_layout = QGridLayout(filter_group)
        
        # تاريخ البداية
        filter_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.invoice_start_date = QDateEdit()
        self.invoice_start_date.setDate(QDate.currentDate().addDays(-7))
        self.invoice_start_date.setCalendarPopup(True)
        self.invoice_start_date.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        filter_layout.addWidget(self.invoice_start_date, 0, 1)
        
        # تاريخ النهاية
        filter_layout.addWidget(QLabel("إلى تاريخ:"), 1, 0)
        self.invoice_end_date = QDateEdit()
        self.invoice_end_date.setDate(QDate.currentDate())
        self.invoice_end_date.setCalendarPopup(True)
        self.invoice_end_date.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        filter_layout.addWidget(self.invoice_end_date, 1, 1)
        
        # الجهاز
        filter_layout.addWidget(QLabel("الجهاز:"), 2, 0)
        self.invoice_device_combo = QComboBox()
        filter_layout.addWidget(self.invoice_device_combo, 2, 1)
        
        # الكاشير
        filter_layout.addWidget(QLabel("الكاشير:"), 3, 0)
        self.invoice_cashier_combo = QComboBox()
        filter_layout.addWidget(self.invoice_cashier_combo, 3, 1)
        
        parent_layout.addWidget(filter_group)
    
    def create_invoice_summary_cards(self, parent_layout):
        """إنشاء بطاقات إجمالي الفواتير"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        summary_layout.setSpacing(20)
        
        # بطاقة إجمالي الفواتير
        self.invoice_total_card = self.create_summary_card("إجمالي الفواتير", "0", "فاتورة", "#3498db")
        summary_layout.addWidget(self.invoice_total_card)
        
        # بطاقة إجمالي المبلغ
        self.invoice_amount_card = self.create_summary_card("إجمالي المبلغ", "0", "جنيه", "#27ae60")
        summary_layout.addWidget(self.invoice_amount_card)
        
        # بطاقة متوسط الفاتورة
        self.invoice_avg_card = self.create_summary_card("متوسط الفاتورة", "0", "جنيه", "#e67e22")
        summary_layout.addWidget(self.invoice_avg_card)
        
        # بطاقة فواتير خدمة العملاء
        self.customer_service_card = self.create_summary_card("فواتير خدمة العملاء", "0", "فاتورة", "#9b59b6")
        summary_layout.addWidget(self.customer_service_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_invoice_controls(self, parent_layout):
        """إنشاء أزرار التحكم للفواتير"""
        controls_layout = QHBoxLayout()
        
        # زر فلترة
        filter_btn = QPushButton("🔍 فلترة")
        filter_btn.clicked.connect(self.load_invoices)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(filter_btn)
        
        # زر عرض جميع الفواتير
        all_invoices_btn = QPushButton("📋 جميع الفواتير")
        all_invoices_btn.clicked.connect(self.load_all_invoices)
        all_invoices_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        controls_layout.addWidget(all_invoices_btn)
        
        controls_layout.addStretch()
        parent_layout.addLayout(controls_layout)
    
    def create_invoices_table(self, parent_layout):
        """إنشاء جدول الفواتير"""
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(11)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "الجهاز", "كاشير الفتح", "كاشير الإغلاق", "وقت البداية", 
            "وقت النهاية", "المدة", "المبلغ", "تفاصيل التسعيرة", "الحالة", "طريقة الدفع"
        ])
        
        # إعداد الجدول
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # ربط النقر على الجدول بعرض تفاصيل الفاتورة
        self.invoices_table.itemClicked.connect(self.on_invoice_clicked)
        
        parent_layout.addWidget(self.invoices_table)
    
    
    # ============ إنشاء أدوات التصفية ============
    
    def create_date_filters(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المشتركة"""
        # نوع الفترة
        parent_layout.addWidget(QLabel("الفترة الزمنية:"), start_row, 0)
        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems([
            "اليوم", "أمس", "هذا الأسبوع", "الأسبوع الماضي", 
            "هذا الشهر", "الشهر الماضي", "هذا العام", "العام الماضي", "فترة مخصصة"
        ])
        self.period_type_combo.currentTextChanged.connect(self.on_period_changed)
        parent_layout.addWidget(self.period_type_combo, start_row, 1)
        
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row + 1, 0)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate().addDays(-7))
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.start_date_input, start_row + 1, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 2, 0)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.end_date_input, start_row + 2, 1)
        
        # أزرار سريعة للفترات
        quick_buttons_layout = QHBoxLayout()
        
        today_btn = QPushButton("اليوم")
        today_btn.clicked.connect(lambda: self.set_period("اليوم"))
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        quick_buttons_layout.addWidget(today_btn)
        
        week_btn = QPushButton("هذا الأسبوع")
        week_btn.clicked.connect(lambda: self.set_period("هذا الأسبوع"))
        week_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        quick_buttons_layout.addWidget(week_btn)
        
        month_btn = QPushButton("هذا الشهر")
        month_btn.clicked.connect(lambda: self.set_period("هذا الشهر"))
        month_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        quick_buttons_layout.addWidget(month_btn)
        
        parent_layout.addLayout(quick_buttons_layout, start_row + 3, 0, 1, 2)
    
    def create_simple_date_filters(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.device_start_date_input = QDateEdit()
        self.device_start_date_input.setDate(QDate.currentDate())
        self.device_start_date_input.setCalendarPopup(True)
        self.device_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.device_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.device_end_date_input = QDateEdit()
        self.device_end_date_input.setDate(QDate.currentDate())
        self.device_end_date_input.setCalendarPopup(True)
        self.device_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.device_end_date_input, start_row + 1, 1)
    
    def create_simple_date_filters_for_products(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للمنتجات (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.product_start_date_input = QDateEdit()
        self.product_start_date_input.setDate(QDate.currentDate())
        self.product_start_date_input.setCalendarPopup(True)
        self.product_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.product_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.product_end_date_input = QDateEdit()
        self.product_end_date_input.setDate(QDate.currentDate())
        self.product_end_date_input.setCalendarPopup(True)
        self.product_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.product_end_date_input, start_row + 1, 1)
    
    def create_simple_date_filters_for_expenses(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للمصروفات (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.expense_start_date_input = QDateEdit()
        self.expense_start_date_input.setDate(QDate.currentDate())
        self.expense_start_date_input.setCalendarPopup(True)
        self.expense_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.expense_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.expense_end_date_input = QDateEdit()
        self.expense_end_date_input.setDate(QDate.currentDate())
        self.expense_end_date_input.setCalendarPopup(True)
        self.expense_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.expense_end_date_input, start_row + 1, 1)
    
    def create_simple_date_filters_for_customers(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للعملاء (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.customer_start_date_input = QDateEdit()
        self.customer_start_date_input.setDate(QDate.currentDate())
        self.customer_start_date_input.setCalendarPopup(True)
        self.customer_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.customer_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.customer_end_date_input = QDateEdit()
        self.customer_end_date_input.setDate(QDate.currentDate())
        self.customer_end_date_input.setCalendarPopup(True)
        self.customer_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.customer_end_date_input, start_row + 1, 1)
    
    def create_simple_date_filters_for_revenue(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للإيرادات (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.revenue_start_date_input = QDateEdit()
        self.revenue_start_date_input.setDate(QDate.currentDate())
        self.revenue_start_date_input.setCalendarPopup(True)
        self.revenue_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.revenue_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.revenue_end_date_input = QDateEdit()
        self.revenue_end_date_input.setDate(QDate.currentDate())
        self.revenue_end_date_input.setCalendarPopup(True)
        self.revenue_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.revenue_end_date_input, start_row + 1, 1)
        
        # زر فلترة
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_revenue_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        parent_layout.addWidget(filter_btn, start_row + 2, 0, 1, 2)
    
    def create_simple_date_filters_for_profit(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للأرباح (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.profit_start_date_input = QDateEdit()
        self.profit_start_date_input.setDate(QDate.currentDate())
        self.profit_start_date_input.setCalendarPopup(True)
        self.profit_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.profit_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.profit_end_date_input = QDateEdit()
        self.profit_end_date_input.setDate(QDate.currentDate())
        self.profit_end_date_input.setCalendarPopup(True)
        self.profit_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.profit_end_date_input, start_row + 1, 1)
        
        # زر فلترة
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_profit_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        parent_layout.addWidget(filter_btn, start_row + 2, 0, 1, 2)
    
    def create_simple_date_filters_for_shifts(self, parent_layout, start_row):
        """إنشاء فلاتر التاريخ المبسطة للورديات (بدون أزرار الفترات)"""
        # تاريخ البداية
        parent_layout.addWidget(QLabel("من تاريخ:"), start_row, 0)
        self.shift_start_date_input = QDateEdit()
        self.shift_start_date_input.setDate(QDate.currentDate())
        self.shift_start_date_input.setCalendarPopup(True)
        self.shift_start_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.shift_start_date_input, start_row, 1)
        
        # تاريخ النهاية
        parent_layout.addWidget(QLabel("إلى تاريخ:"), start_row + 1, 0)
        self.shift_end_date_input = QDateEdit()
        self.shift_end_date_input.setDate(QDate.currentDate())
        self.shift_end_date_input.setCalendarPopup(True)
        self.shift_end_date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
            }
        """)
        parent_layout.addWidget(self.shift_end_date_input, start_row + 1, 1)
    
    
    
    def create_revenue_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير الإيرادات"""
        filter_group = QGroupBox("تصفية تقارير الإيرادات")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
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
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة
        self.create_simple_date_filters_for_revenue(filter_layout, 0)
        
        parent_layout.addWidget(filter_group)
    
    def create_profit_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير الأرباح"""
        filter_group = QGroupBox("تصفية تقارير الأرباح")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
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
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة
        self.create_simple_date_filters_for_profit(filter_layout, 0)
        
        parent_layout.addWidget(filter_group)
    
    def create_revenue_summary_cards(self, parent_layout):
        """إنشاء بطاقات إجمالي الإيرادات"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        summary_layout.setSpacing(20)
        
        # بطاقة إجمالي الإيرادات
        self.revenue_total_card = self.create_summary_card("إجمالي الإيرادات", "0", "جنيه", "#27ae60")
        summary_layout.addWidget(self.revenue_total_card)
        
        # بطاقة عدد الفواتير
        self.revenue_invoices_card = self.create_summary_card("عدد الفواتير", "0", "فاتورة", "#3498db")
        summary_layout.addWidget(self.revenue_invoices_card)
        
        # بطاقة متوسط الفاتورة
        self.revenue_avg_card = self.create_summary_card("متوسط الفاتورة", "0", "جنيه", "#e67e22")
        summary_layout.addWidget(self.revenue_avg_card)
        
        # بطاقة إيرادات الجلسات
        self.revenue_sessions_card = self.create_summary_card("إيرادات الجلسات", "0", "جنيه", "#9b59b6")
        summary_layout.addWidget(self.revenue_sessions_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_profit_summary_cards(self, parent_layout):
        """إنشاء بطاقات إجمالي الأرباح"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        summary_layout.setSpacing(20)
        
        # بطاقة إجمالي الإيرادات
        self.profit_revenue_card = self.create_summary_card("إجمالي الإيرادات", "0", "جنيه", "#27ae60")
        summary_layout.addWidget(self.profit_revenue_card)
        
        # بطاقة إجمالي المصروفات
        self.profit_expense_card = self.create_summary_card("إجمالي المصروفات", "0", "جنيه", "#e74c3c")
        summary_layout.addWidget(self.profit_expense_card)
        
        # بطاقة صافي الربح
        self.profit_net_card = self.create_summary_card("صافي الربح", "0", "جنيه", "#2ecc71")
        summary_layout.addWidget(self.profit_net_card)
        
        # بطاقة عدد الفواتير
        self.profit_invoices_card = self.create_summary_card("عدد الفواتير", "0", "فاتورة", "#3498db")
        summary_layout.addWidget(self.profit_invoices_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_device_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير الأجهزة"""
        filter_group = QGroupBox("تصفية تقارير الأجهزة")
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة (بدون أزرار الفترات)
        self.create_simple_date_filters(filter_layout, 0)
        
        # نوع الجهاز
        filter_layout.addWidget(QLabel("نوع الجهاز:"), 2, 0)
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItem("جميع الأنواع", "")
        
        # تحميل أنواع الأجهزة من قاعدة البيانات
        try:
            from models.device_model import DeviceModel
            device_model = DeviceModel()
            devices = device_model.get_all_devices()
            device_types = list(set([d['type'] for d in devices if d.get('type')]))
            for device_type in sorted(device_types):
                self.device_type_combo.addItem(device_type, device_type)
        except Exception as e:
            # print(f"خطأ في تحميل أنواع الأجهزة: {e}")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            # القيم الافتراضية في حالة الخطأ
            self.device_type_combo.addItems(["PS", "PC", "PingPong", "Billiard"])
        
        filter_layout.addWidget(self.device_type_combo, 2, 1)
        
        # زر فلترة البيانات
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_device_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        filter_layout.addWidget(filter_btn, 2, 2)
        
        parent_layout.addWidget(filter_group)
    
    def create_product_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير المنتجات"""
        filter_group = QGroupBox("تصفية تقارير المنتجات")
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة (بدون أزرار الفترات)
        self.create_simple_date_filters_for_products(filter_layout, 0)
        
        # فئة المنتج
        filter_layout.addWidget(QLabel("فئة المنتج:"), 2, 0)
        self.product_category_combo = QComboBox()
        self.product_category_combo.addItem("جميع الفئات", "")
        
        # تحميل فئات المنتجات من قاعدة البيانات
        try:
            from models.product_model import ProductModel
            product_model = ProductModel()
            products = product_model.get_all_products()
            categories = list(set([p['category'] for p in products if p.get('category')]))
            for category in sorted(categories):
                self.product_category_combo.addItem(category, category)
        except Exception as e:
            # print(f"خطأ في تحميل فئات المنتجات: {e}")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            # القيم الافتراضية في حالة الخطأ
            self.product_category_combo.addItems(["drink", "food"])
        
        filter_layout.addWidget(self.product_category_combo, 2, 1)
        
        # زر فلترة البيانات
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_product_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        filter_layout.addWidget(filter_btn, 2, 2)
        
        parent_layout.addWidget(filter_group)
    
    def create_product_summary_cards(self, parent_layout):
        """إنشاء بطاقات إجماليات المنتجات"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        # بطاقة إجمالي الكمية المباعة
        self.total_quantity_card = self.create_summary_card("📦 إجمالي الكمية المباعة", "0", "قطعة", "#3498db")
        summary_layout.addWidget(self.total_quantity_card)
        
        # بطاقة إجمالي الإيرادات
        self.total_revenue_card = self.create_summary_card("💰 إجمالي الإيرادات", "0.00", "ج.م", "#27ae60")
        summary_layout.addWidget(self.total_revenue_card)
        
        # بطاقة عدد المنتجات المباعة
        self.products_sold_card = self.create_summary_card("🛒 المنتجات المباعة", "0", "منتج", "#e74c3c")
        summary_layout.addWidget(self.products_sold_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_summary_card(self, title, value, unit, color):
        """إنشاء بطاقة ملخص"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                min-width: 150px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px;")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("value")
        card_layout.addWidget(value_label)
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("font-size: 10px;")
        unit_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(unit_label)
        
        return card
    
    def create_expense_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير المصروفات"""
        filter_group = QGroupBox("تصفية تقارير المصروفات")
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة (بدون أزرار الفترات)
        self.create_simple_date_filters_for_expenses(filter_layout, 0)
        
        # الكاشير
        filter_layout.addWidget(QLabel("الكاشير:"), 2, 0)
        self.expense_cashier_combo = QComboBox()
        self.expense_cashier_combo.addItem("جميع الكاشيرز", "")
        filter_layout.addWidget(self.expense_cashier_combo, 2, 1)
        
        # زر فلترة البيانات
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_expense_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        filter_layout.addWidget(filter_btn, 2, 2)
        
        parent_layout.addWidget(filter_group)
    
    def create_expense_summary_cards(self, parent_layout):
        """إنشاء بطاقات إجماليات المصروفات"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        # بطاقة إجمالي المصروفات
        self.total_expense_card = self.create_summary_card("💰 إجمالي المصروفات", "0.00", "ج.م", "#e74c3c")
        summary_layout.addWidget(self.total_expense_card)
        
        # بطاقة عدد المصروفات
        self.expense_count_card = self.create_summary_card("📊 عدد المصروفات", "0", "مصروف", "#f39c12")
        summary_layout.addWidget(self.expense_count_card)
        
        # بطاقة متوسط المصروف
        self.avg_expense_card = self.create_summary_card("📈 متوسط المصروف", "0.00", "ج.م", "#9b59b6")
        summary_layout.addWidget(self.avg_expense_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_customer_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير العملاء"""
        filter_group = QGroupBox("تصفية تقارير العملاء")
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة (بدون أزرار الفترات)
        self.create_simple_date_filters_for_customers(filter_layout, 0)
        
        # زر فلترة البيانات
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_customer_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        filter_layout.addWidget(filter_btn, 2, 0)
        
        parent_layout.addWidget(filter_group)
    
    
    def create_shift_filters(self, parent_layout):
        """إنشاء أدوات تصفية تقارير الورديات"""
        filter_group = QGroupBox("تصفية تقارير الورديات")
        filter_layout = QGridLayout(filter_group)
        
        # فلاتر التاريخ المبسطة (بدون أزرار الفترات)
        self.create_simple_date_filters_for_shifts(filter_layout, 0)
        
        # الكاشير
        filter_layout.addWidget(QLabel("الكاشير:"), 2, 0)
        self.shift_cashier_combo = QComboBox()
        self.shift_cashier_combo.addItem("جميع الكاشيرز", "")
        filter_layout.addWidget(self.shift_cashier_combo, 2, 1)
        
        # زر فلترة البيانات
        filter_btn = QPushButton("🔍 فلترة البيانات")
        filter_btn.clicked.connect(self.generate_shift_report)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        filter_layout.addWidget(filter_btn, 2, 2)
        
        parent_layout.addWidget(filter_group)
    
    
    # ============ وظائف مساعدة ============
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل قائمة الكاشيرز
            self.load_cashier_list()
            
            # تم حذف مؤشرات الأداء
            
        except Exception as e:
            show_error(f"خطأ في تحميل البيانات الأولية: {str(e)}")
    
    def load_cashier_list(self):
        """تحميل قائمة الكاشيرز"""
        try:
            # تحميل قائمة الكاشيرز من قاعدة البيانات
            from models.user_model import UserModel
            user_model = UserModel()
            cashiers = user_model.get_cashiers()
            
            # تحديث قوائم الكاشيرز
            self.expense_cashier_combo.clear()
            self.expense_cashier_combo.addItem("جميع الكاشيرز", "")
            
            self.shift_cashier_combo.clear()
            self.shift_cashier_combo.addItem("جميع الكاشيرز", "")
            
            for cashier in cashiers:
                self.expense_cashier_combo.addItem(cashier['username'], cashier['id'])
                self.shift_cashier_combo.addItem(cashier['username'], cashier['id'])
                
        except Exception as e:
            pass
    
    
    # ============ وظائف إنشاء التقارير ============
    
    def generate_revenue_report(self):
        """إنشاء تقرير الإيرادات"""
        try:
            start_date = self.revenue_start_date_input.date().toPython()
            end_date = self.revenue_end_date_input.date().toPython()
            
            # إنهاء الخيط السابق إذا كان موجوداً
            if self.report_thread and self.report_thread.isRunning():
                self.report_thread.terminate()
                self.report_thread.wait()
            
            # إنشاء خيط لتوليد التقرير
            self.report_thread = ReportGenerationThread(
                self.controller,
                'revenue',
                {
                    'start_date': start_date,
                    'end_date': end_date,
                    'report_type': 'daily'
                }
            )
            self.report_thread.report_ready.connect(self.display_revenue_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير الإيرادات: {str(e)}")
    
    def generate_profit_report(self):
        """إنشاء تقرير الأرباح"""
        try:
            start_date = self.profit_start_date_input.date().toPython()
            end_date = self.profit_end_date_input.date().toPython()
            
            # إنهاء الخيط السابق إذا كان موجوداً
            if self.report_thread and self.report_thread.isRunning():
                self.report_thread.terminate()
                self.report_thread.wait()
            
            # إنشاء خيط لتوليد التقرير
            self.report_thread = ReportGenerationThread(
                self.controller,
                'profit',
                {
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            self.report_thread.report_ready.connect(self.display_profit_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير الأرباح: {str(e)}")
    
    def generate_device_report(self):
        """إنشاء تقرير الأجهزة"""
        try:
            start_date = self.device_start_date_input.date().toPython()
            end_date = self.device_end_date_input.date().toPython()
            device_type = self.device_type_combo.currentData()
            
            self.report_thread = ReportGenerationThread(
                self.controller,
                'device',
                {
                    'start_date': start_date,
                    'end_date': end_date,
                    'device_type': device_type
                }
            )
            self.report_thread.report_ready.connect(self.display_device_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير الأجهزة: {str(e)}")
    
    def generate_product_report(self):
        """إنشاء تقرير المنتجات"""
        try:
            start_date = self.product_start_date_input.date().toPython()
            end_date = self.product_end_date_input.date().toPython()
            category = self.product_category_combo.currentData()
            
            self.report_thread = ReportGenerationThread(
                self.controller,
                'product',
                {
                    'start_date': start_date,
                    'end_date': end_date,
                    'category': category
                }
            )
            self.report_thread.report_ready.connect(self.display_product_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير المنتجات: {str(e)}")
    
    def generate_expense_report(self):
        """إنشاء تقرير المصروفات"""
        try:
            start_date = self.expense_start_date_input.date().toPython()
            end_date = self.expense_end_date_input.date().toPython()
            cashier_id = self.expense_cashier_combo.currentData()
            
            self.report_thread = ReportGenerationThread(
                self.controller,
                'expense',
                {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cashier_id': cashier_id
                }
            )
            self.report_thread.report_ready.connect(self.display_expense_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير المصروفات: {str(e)}")
    
    def generate_customer_report(self):
        """إنشاء تقرير العملاء"""
        try:
            start_date = self.customer_start_date_input.date().toPython()
            end_date = self.customer_end_date_input.date().toPython()
            
            self.report_thread = ReportGenerationThread(
                self.controller,
                'customer',
                {
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            self.report_thread.report_ready.connect(self.display_customer_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير العملاء: {str(e)}")
    
    
    def generate_shift_report(self):
        """إنشاء تقرير الورديات"""
        try:
            start_date = self.shift_start_date_input.date().toPython()
            end_date = self.shift_end_date_input.date().toPython()
            cashier_id = self.shift_cashier_combo.currentData()
            
            self.report_thread = ReportGenerationThread(
                self.controller,
                'shift',
                {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cashier_id': cashier_id
                }
            )
            self.report_thread.report_ready.connect(self.display_shift_report)
            self.report_thread.start()
            
        except Exception as e:
            show_error(f"خطأ في إنشاء تقرير الورديات: {str(e)}")
    
    
    # ============ وظائف عرض التقارير ============
    
    def display_revenue_report(self, result):
        """عرض تقرير الإيرادات"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                
                # تحديث بطاقات إجمالي الإيرادات
                self.update_revenue_summary_cards(data)
                
                # عرض الإيرادات اليومية
                if 'daily_revenue' in data:
                    daily_data = data['daily_revenue']
                    self.populate_daily_revenue_table(daily_data)
                
                show_success("تم إنشاء تقرير الإيرادات بنجاح")
            else:
                show_error(f"خطأ في تقرير الإيرادات: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير الإيرادات: {str(e)}")
    
    def update_revenue_summary_cards(self, data):
        """تحديث بطاقات إجمالي الإيرادات"""
        try:
            # حساب الإحصائيات من البيانات
            summary_data = data.get('summary', {})
            daily_data = data.get('daily_revenue', [])
            
            # إجمالي الإيرادات
            total_revenue = summary_data.get('total_revenue', 0)
            if not total_revenue and daily_data:
                total_revenue = sum(day.get('total_revenue', 0) for day in daily_data)
            
            # عدد الفواتير
            total_invoices = summary_data.get('total_invoices', 0)
            if not total_invoices and daily_data:
                total_invoices = sum(day.get('invoice_count', 0) for day in daily_data)
            
            # متوسط الفاتورة
            avg_invoice = total_revenue / total_invoices if total_invoices > 0 else 0
            
            # إيرادات الجلسات - نحسبها من البيانات اليومية
            session_revenue = summary_data.get('session_revenue', 0)
            if not session_revenue and daily_data:
                # نحتاج للحصول على إيرادات الجلسات من قاعدة البيانات
                session_revenue = self.calculate_session_revenue_from_daily_data(daily_data)
            
            # تحديث البطاقات
            self.update_summary_card(self.revenue_total_card, f"{total_revenue:.2f}")
            self.update_summary_card(self.revenue_invoices_card, total_invoices)
            self.update_summary_card(self.revenue_avg_card, f"{avg_invoice:.2f}")
            self.update_summary_card(self.revenue_sessions_card, f"{session_revenue:.2f}")
            
        except Exception as e:
            print(f"خطأ في تحديث بطاقات إجمالي الإيرادات: {e}")
    
    def calculate_session_revenue_from_daily_data(self, daily_data):
        """حساب إيرادات الجلسات من البيانات اليومية"""
        try:
            # نحتاج للحصول على إيرادات الجلسات من قاعدة البيانات
            from models.report_model import ReportModel
            report_model = ReportModel()
            
            # الحصول على إجمالي إيرادات الجلسات للفترة
            start_date = None
            end_date = None
            
            if daily_data:
                # استخراج التواريخ من البيانات اليومية
                dates = [day.get('date') for day in daily_data if day.get('date')]
                if dates:
                    start_date = min(dates)
                    end_date = max(dates)
            
            if start_date and end_date:
                # الحصول على إيرادات الجلسات من قاعدة البيانات
                session_revenue_result = report_model.db.execute_query(
                    """SELECT COALESCE(SUM(session_price), 0) as session_revenue
                       FROM invoices 
                       WHERE DATE(start_time) BETWEEN ? AND ?""",
                    (start_date, end_date)
                )
                
                if session_revenue_result:
                    return session_revenue_result[0].get('session_revenue', 0)
            
            return 0
            
        except Exception as e:
            print(f"خطأ في حساب إيرادات الجلسات: {e}")
            return 0
    
    def display_profit_report(self, result):
        """عرض تقرير الأرباح"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                
                # تحديث بطاقات إجمالي الأرباح
                self.update_profit_summary_cards(data)
                
                # عرض الإيرادات اليومية
                if 'daily_revenue' in data:
                    daily_revenue = data['daily_revenue']
                    self.populate_profit_revenue_table(daily_revenue)
                
                # عرض المصروفات اليومية
                if 'daily_expenses' in data:
                    daily_expenses = data['daily_expenses']
                    self.populate_profit_expense_table(daily_expenses)
                
                show_success("تم إنشاء تقرير الأرباح بنجاح")
            else:
                show_error(f"خطأ في تقرير الأرباح: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير الأرباح: {str(e)}")
    
    def update_profit_summary_cards(self, data):
        """تحديث بطاقات إجمالي الأرباح"""
        try:
            summary_data = data.get('summary', {})
            
            # إجمالي الإيرادات
            total_revenue = summary_data.get('total_revenue', 0)
            
            # إجمالي المصروفات
            total_expenses = summary_data.get('total_expenses', 0)
            
            # صافي الربح
            net_profit = summary_data.get('net_profit', 0)
            
            # عدد الفواتير
            total_invoices = summary_data.get('total_invoices', 0)
            
            # تحديث البطاقات
            self.update_summary_card(self.profit_revenue_card, f"{total_revenue:.2f}")
            self.update_summary_card(self.profit_expense_card, f"{total_expenses:.2f}")
            self.update_summary_card(self.profit_net_card, f"{net_profit:.2f}")
            self.update_summary_card(self.profit_invoices_card, total_invoices)
            
        except Exception as e:
            print(f"خطأ في تحديث بطاقات إجمالي الأرباح: {e}")
    
    def populate_profit_revenue_table(self, revenue_data):
        """تعبئة جدول الإيرادات اليومية للأرباح"""
        try:
            self.profit_revenue_table.setRowCount(len(revenue_data))
            
            for row, day_data in enumerate(revenue_data):
                # التاريخ
                date_item = QTableWidgetItem(str(day_data.get('date', '')))
                self.profit_revenue_table.setItem(row, 0, date_item)
                
                # عدد الفواتير
                invoice_count_item = QTableWidgetItem(str(day_data.get('invoice_count', 0)))
                self.profit_revenue_table.setItem(row, 1, invoice_count_item)
                
                # الإيرادات
                revenue_item = QTableWidgetItem(f"{day_data.get('total_revenue', 0):.2f}")
                self.profit_revenue_table.setItem(row, 2, revenue_item)
                
                # متوسط الفاتورة
                avg_item = QTableWidgetItem(f"{day_data.get('avg_invoice_value', 0):.2f}")
                self.profit_revenue_table.setItem(row, 3, avg_item)
            
            # ضبط عرض الأعمدة
            self.profit_revenue_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"خطأ في تعبئة جدول الإيرادات اليومية: {e}")
    
    def populate_profit_expense_table(self, expense_data):
        """تعبئة جدول المصروفات اليومية للأرباح"""
        try:
            self.profit_expense_table.setRowCount(len(expense_data))
            
            for row, day_data in enumerate(expense_data):
                # التاريخ
                date_item = QTableWidgetItem(str(day_data.get('date', '')))
                self.profit_expense_table.setItem(row, 0, date_item)
                
                # عدد المصروفات
                expense_count_item = QTableWidgetItem(str(day_data.get('expense_count', 0)))
                self.profit_expense_table.setItem(row, 1, expense_count_item)
                
                # إجمالي المصروفات
                total_item = QTableWidgetItem(f"{day_data.get('total_amount', 0):.2f}")
                self.profit_expense_table.setItem(row, 2, total_item)
                
                # متوسط المصروف
                avg_item = QTableWidgetItem(f"{day_data.get('avg_amount', 0):.2f}")
                self.profit_expense_table.setItem(row, 3, avg_item)
            
            # ضبط عرض الأعمدة
            self.profit_expense_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"خطأ في تعبئة جدول المصروفات اليومية: {e}")
    
    def display_device_report(self, result):
        """عرض تقرير الأجهزة"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                performance_data = data.get('performance', [])
                
                self.populate_device_performance_table(performance_data)
                show_success("تم إنشاء تقرير الأجهزة بنجاح")
            else:
                show_error(f"خطأ في تقرير الأجهزة: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير الأجهزة: {str(e)}")
    
    def display_product_report(self, result):
        """عرض تقرير المنتجات"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                sales_data = data.get('sales', [])
                performance_data = data.get('performance', {})
                detailed_stock_data = data.get('detailed_stock', [])
                
                # تحديث بطاقات الإجماليات
                self.update_product_summary_cards(sales_data, performance_data)
                
                self.populate_product_sales_table(sales_data)
                self.populate_stock_status_table(detailed_stock_data)
                show_success("تم إنشاء تقرير المنتجات بنجاح")
            else:
                show_error(f"خطأ في تقرير المنتجات: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير المنتجات: {str(e)}")
    
    def update_product_summary_cards(self, sales_data, performance_data):
        """تحديث بطاقات إجماليات المنتجات"""
        try:
            # حساب إجمالي الكمية المباعة
            total_quantity = sum(item.get('quantity_sold', 0) for item in sales_data)
            
            # حساب إجمالي الإيرادات
            total_revenue = sum(item.get('revenue', 0) for item in sales_data)
            
            # حساب عدد المنتجات المباعة (المنتجات التي تم بيعها)
            products_sold = len([item for item in sales_data if item.get('quantity_sold', 0) > 0])
            
            # تحديث البطاقات
            self.update_summary_card(self.total_quantity_card, total_quantity)
            self.update_summary_card(self.total_revenue_card, total_revenue)
            self.update_summary_card(self.products_sold_card, products_sold)
            
        except Exception as e:
            # print(f"خطأ في تحديث بطاقات الإجماليات: {e}")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            pass
    
    def update_summary_card(self, card, value):
        """تحديث بطاقة ملخص"""
        try:
            value_label = card.findChild(QLabel, "value")
            if value_label:
                if isinstance(value, (int, float)):
                    if value >= 1000000:
                        formatted_value = f"{value/1000000:.1f}M"
                    elif value >= 1000:
                        formatted_value = f"{value/1000:.1f}K"
                    else:
                        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(int(value))
                else:
                    formatted_value = str(value)
                
                value_label.setText(formatted_value)
        except Exception as e:
            pass
    
    def display_expense_report(self, result):
        """عرض تقرير المصروفات"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                expenses = data.get('expenses', [])
                
                # تحديث بطاقات الإجماليات
                self.update_expense_summary_cards(expenses)
                
                self.populate_expense_table(expenses)
                show_success("تم إنشاء تقرير المصروفات بنجاح")
            else:
                show_error(f"خطأ في تقرير المصروفات: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير المصروفات: {str(e)}")
    
    def update_expense_summary_cards(self, expenses):
        """تحديث بطاقات إجماليات المصروفات"""
        try:
            # حساب إجمالي المصروفات
            total_expense = sum(expense.get('amount', 0) for expense in expenses)
            
            # حساب عدد المصروفات
            expense_count = len(expenses)
            
            # حساب متوسط المصروف
            avg_expense = total_expense / expense_count if expense_count > 0 else 0
            
            # تحديث البطاقات
            self.update_summary_card(self.total_expense_card, total_expense)
            self.update_summary_card(self.expense_count_card, expense_count)
            self.update_summary_card(self.avg_expense_card, avg_expense)
            
        except Exception as e:
            # print(f"خطأ في تحديث بطاقات الإجماليات: {e}")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            pass
    
    def display_customer_report(self, result):
        """عرض تقرير العملاء"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                stats = data.get('statistics', {})
                top_customers = data.get('top_customers', [])
                
                self.populate_customer_stats_table(stats)
                self.populate_top_customers_table(top_customers)
                show_success("تم إنشاء تقرير العملاء بنجاح")
            else:
                show_error(f"خطأ في تقرير العملاء: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير العملاء: {str(e)}")
    
    
    def display_shift_report(self, result):
        """عرض تقرير الورديات"""
        try:
            if result.get('success'):
                data = result.get('data', {})
                shifts = data.get('shifts', [])
                
                self.populate_shift_table(shifts)
                show_success("تم إنشاء تقرير الورديات بنجاح")
            else:
                show_error(f"خطأ في تقرير الورديات: {result.get('message', '')}")
                
        except Exception as e:
            show_error(f"خطأ في عرض تقرير الورديات: {str(e)}")
    
    
    # ============ وظائف ملء الجداول ============
    
    def populate_revenue_summary_table(self, summary_data):
        """ملء جدول ملخص الإيرادات"""
        try:
            # تنظيف البيانات
            total_revenue = float(summary_data.get('total_revenue', 0))
            session_revenue = float(summary_data.get('session_revenue', 0))
            products_revenue = float(summary_data.get('products_revenue', 0))
            total_invoices = int(summary_data.get('total_invoices', 0))
            avg_invoice = float(summary_data.get('avg_invoice_value', 0))
            
            # حساب النسب المئوية
            session_percentage = (session_revenue / max(total_revenue, 1) * 100) if total_revenue > 0 else 0
            products_percentage = (products_revenue / max(total_revenue, 1) * 100) if total_revenue > 0 else 0
            
            table_data = [
                ["إجمالي الإيرادات", format_currency(total_revenue), "100%", ""],
                ["إيرادات الجلسات", format_currency(session_revenue), f"{session_percentage:.1f}%", ""],
                ["إيرادات المنتجات", format_currency(products_revenue), f"{products_percentage:.1f}%", ""],
                ["عدد الفواتير", str(total_invoices), "", ""],
                ["متوسط الفاتورة", format_currency(avg_invoice), "", ""]
            ]
            
            self.revenue_summary_table.setRowCount(len(table_data))
            for row, data_row in enumerate(table_data):
                for col, value in enumerate(data_row):
                    # تنظيف النص من أي رموز غير مرغوب فيها
                    clean_value = str(value).strip().replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    
                    item = QTableWidgetItem(clean_value)
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # تنسيق خاص للقيم المالية
                    if col == 1 and value:  # عمود القيمة
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    
                    # تنسيق خاص للنسب
                    if col == 2 and value:  # عمود النسبة
                        item.setTextAlignment(Qt.AlignCenter)
                        if "%" in str(value):
                            item.setBackground(QColor(240, 248, 255))  # لون خفيف للنسب
                    
                    self.revenue_summary_table.setItem(row, col, item)
            
            # تحديث الجدول
            self.revenue_summary_table.resizeColumnsToContents()
            self.revenue_summary_table.resizeRowsToContents()
            
            # التأكد من أن الجدول مرئي
            self.revenue_summary_table.setVisible(True)
            
            # إجبار إعادة رسم الجدول
            self.revenue_summary_table.repaint()
            self.revenue_summary_table.update()
                    
        except Exception as e:
            print(f"خطأ في ملء جدول ملخص الإيرادات: {e}")
            # إنشاء جدول فارغ في حالة الخطأ
            self.revenue_summary_table.setRowCount(1)
            self.revenue_summary_table.setItem(0, 0, QTableWidgetItem("خطأ في تحميل البيانات"))
            pass
    
    def populate_daily_revenue_table(self, daily_data):
        """ملء جدول الإيرادات اليومية"""
        try:
            self.daily_revenue_table.setRowCount(len(daily_data))
            for row, data in enumerate(daily_data):
                self.daily_revenue_table.setItem(row, 0, QTableWidgetItem(str(data.get('date', ''))))
                self.daily_revenue_table.setItem(row, 1, QTableWidgetItem(str(data.get('invoice_count', 0))))
                self.daily_revenue_table.setItem(row, 2, QTableWidgetItem(format_currency(data.get('total_revenue', 0))))
                self.daily_revenue_table.setItem(row, 3, QTableWidgetItem(format_currency(data.get('avg_invoice_value', 0))))
                
        except Exception as e:
            pass
    
    def populate_device_performance_table(self, performance_data):
        """ملء جدول أداء الأجهزة"""
        try:
            self.device_performance_table.setRowCount(len(performance_data))
            for row, data in enumerate(performance_data):
                self.device_performance_table.setItem(row, 0, QTableWidgetItem(data.get('name', '')))
                self.device_performance_table.setItem(row, 1, QTableWidgetItem(data.get('type', '')))
                self.device_performance_table.setItem(row, 2, QTableWidgetItem(str(data.get('session_count', 0))))
                self.device_performance_table.setItem(row, 3, QTableWidgetItem(format_currency(data.get('total_revenue', 0))))
                self.device_performance_table.setItem(row, 4, QTableWidgetItem(format_currency(data.get('avg_revenue_per_session', 0))))
                self.device_performance_table.setItem(row, 5, QTableWidgetItem(f"{data.get('avg_session_minutes', 0):.1f} دقيقة"))
                
        except Exception as e:
            pass
    
    def populate_product_sales_table(self, sales_data):
        """ملء جدول مبيعات المنتجات"""
        try:
            self.product_sales_table.setRowCount(len(sales_data))
            for row, data in enumerate(sales_data):
                self.product_sales_table.setItem(row, 0, QTableWidgetItem(data.get('name', '')))
                self.product_sales_table.setItem(row, 1, QTableWidgetItem(data.get('category', '')))
                # استخدام quantity_sold بدلاً من total_sold
                quantity = data.get('quantity_sold', data.get('total_sold', 0))
                self.product_sales_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
                # استخدام revenue بدلاً من total_revenue
                revenue = data.get('revenue', data.get('total_revenue', 0))
                self.product_sales_table.setItem(row, 3, QTableWidgetItem(format_currency(revenue)))
                # استخدام avg_selling_price
                avg_price = data.get('avg_selling_price', 0)
                self.product_sales_table.setItem(row, 4, QTableWidgetItem(format_currency(avg_price)))
                
        except Exception as e:
            pass
    
    def populate_stock_status_table(self, stock_data):
        """ملء جدول حالة المخزون"""
        try:
            self.stock_status_table.setRowCount(len(stock_data))
            for row, data in enumerate(stock_data):
                # اسم المنتج
                product_name = data.get('name', 'غير محدد')
                self.stock_status_table.setItem(row, 0, QTableWidgetItem(product_name))
                
                # المخزون الحالي
                stock_quantity = data.get('stock_quantity', 0)
                self.stock_status_table.setItem(row, 1, QTableWidgetItem(str(stock_quantity)))
                
                # الحد الأدنى
                min_level = data.get('min_stock_level', 0)
                self.stock_status_table.setItem(row, 2, QTableWidgetItem(str(min_level)))
                
                # الحالة (استخدام الحالة المحسوبة من الدالة أو حسابها محلياً)
                status = data.get('status', '')
                if not status:
                    # حساب الحالة محلياً إذا لم تكن متوفرة
                    if stock_quantity == 0:
                        status = "نفد"
                    elif stock_quantity <= min_level:
                        status = "منخفض"
                    else:
                        status = "متوفر"
                
                # تعيين لون للحالة
                status_item = QTableWidgetItem(status)
                if status == "نفد":
                    status_item.setBackground(QColor(255, 200, 200))  # أحمر فاتح
                elif status == "منخفض":
                    status_item.setBackground(QColor(255, 255, 200))  # أصفر فاتح
                else:
                    status_item.setBackground(QColor(200, 255, 200))  # أخضر فاتح
                
                self.stock_status_table.setItem(row, 3, status_item)
                
        except Exception as e:
            pass
    
    def populate_expense_table(self, expenses):
        """ملء جدول المصروفات"""
        try:
            self.expense_table.setRowCount(len(expenses))
            for row, expense in enumerate(expenses):
                # تنسيق التاريخ والوقت
                date_time_str = expense.get('date_time', '')
                if date_time_str:
                    try:
                        from datetime import datetime
                        if isinstance(date_time_str, str):
                            # تحويل النص إلى datetime
                            if 'T' in date_time_str:
                                date_time = datetime.fromisoformat(date_time_str.replace('Z', '+00:00'))
                            else:
                                # تنسيق SQLite
                                date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            date_time = date_time_str
                        
                        formatted_date = date_time.strftime('%d/%m/%Y %H:%M')
                    except Exception as e:
                        formatted_date = str(date_time_str)
                else:
                    formatted_date = ''
                
                self.expense_table.setItem(row, 0, QTableWidgetItem(formatted_date))
                self.expense_table.setItem(row, 1, QTableWidgetItem(format_currency(expense.get('amount', 0))))
                self.expense_table.setItem(row, 2, QTableWidgetItem(expense.get('reason', '')))
                self.expense_table.setItem(row, 3, QTableWidgetItem(expense.get('cashier_name', '')))
                self.expense_table.setItem(row, 4, QTableWidgetItem(expense.get('shift_name', '')))
            
        except Exception as e:
            print(f"خطأ في ملء جدول المصروفات: {e}")
            pass
    
    def populate_customer_stats_table(self, stats):
        """ملء جدول إحصائيات العملاء"""
        try:
            table_data = [
                ["إجمالي العملاء", str(stats.get('total_customers', 0)), ""],
                ["إجمالي الرصيد", format_currency(stats.get('total_balance', 0)), ""],
                ["متوسط الرصيد", format_currency(stats.get('avg_balance', 0)), ""],
                ["أعلى رصيد", format_currency(stats.get('max_balance', 0)), ""],
                ["أقل رصيد", format_currency(stats.get('min_balance', 0)), ""]
            ]
            
            self.customer_stats_table.setRowCount(len(table_data))
            for row, data_row in enumerate(table_data):
                for col, value in enumerate(data_row):
                    self.customer_stats_table.setItem(row, col, QTableWidgetItem(str(value)))
            
        except Exception as e:
            pass
    
    def populate_top_customers_table(self, top_customers):
        """ملء جدول العملاء الأكثر رصيداً"""
        try:
            self.top_customers_table.setRowCount(len(top_customers))
            for row, customer in enumerate(top_customers):
                self.top_customers_table.setItem(row, 0, QTableWidgetItem(customer.get('name', '')))
                self.top_customers_table.setItem(row, 1, QTableWidgetItem(customer.get('phone', '')))
                self.top_customers_table.setItem(row, 2, QTableWidgetItem(format_currency(customer.get('balance', 0))))
                self.top_customers_table.setItem(row, 3, QTableWidgetItem(format_time(customer.get('created_at', ''), 'date')))
            
        except Exception as e:
            pass
    
    
    def populate_shift_table(self, shifts):
        """ملء جدول الورديات"""
        try:
            self.shift_table.setRowCount(len(shifts))
            for row, shift in enumerate(shifts):
                self.shift_table.setItem(row, 0, QTableWidgetItem(shift.get('shift_name', '')))
                self.shift_table.setItem(row, 1, QTableWidgetItem(shift.get('cashier_name', '')))
                self.shift_table.setItem(row, 2, QTableWidgetItem(format_time(shift.get('start_time', ''), 'short')))
                self.shift_table.setItem(row, 3, QTableWidgetItem(format_time(shift.get('end_time', ''), 'short')))
                self.shift_table.setItem(row, 4, QTableWidgetItem(format_currency(shift.get('total_revenue', 0))))
                self.shift_table.setItem(row, 5, QTableWidgetItem(format_currency(shift.get('total_expenses', 0))))
                
        except Exception as e:
            pass
    
    
    def on_tab_changed(self, index):
        """معالج تغيير التبويب"""
        try:
            tab_name = self.tab_widget.tabText(index)
            if tab_name == "🧾 الفواتير":
                # تحميل جميع الفواتير عند فتح تبويب الفواتير
                self.load_all_invoices()
        except Exception as e:
            print(f"خطأ في تغيير التبويب: {e}")
    
    # ============ دوال تبويب الفواتير ============
    
    
    def load_invoices(self):
        """تحميل الفواتير"""
        try:
            print("بدء تحميل الفواتير...")
            
            # الحصول على معايير التصفية
            start_date = self.invoice_start_date.date().toPython()
            end_date = self.invoice_end_date.date().toPython()
            device_id = self.invoice_device_combo.currentData()
            cashier_id = self.invoice_cashier_combo.currentData()
            
            print(f"معايير الفلترة:")
            print(f"  - التاريخ: {start_date} إلى {end_date}")
            print(f"  - الجهاز: {device_id}")
            print(f"  - الكاشير: {cashier_id}")
            
            # الحصول على الفواتير
            from models.invoice_model import InvoiceModel
            invoice_model = InvoiceModel()
            
            # تحديد نوع الاستعلام حسب المعايير
            if device_id == "customer_service":
                # فواتير خدمة العملاء (فواتير بدون جهاز)
                invoices = invoice_model.get_all_closed_invoices(start_date, end_date)
                invoices = [inv for inv in invoices if not inv.get('device_id') or inv.get('device_id') is None]
                
                # تصفية إضافية حسب الكاشير
                if cashier_id:
                    invoices = [inv for inv in invoices if inv.get('cashier_close') == cashier_id]
            else:
                # الفواتير العادية
                invoices = invoice_model.get_all_closed_invoices(start_date, end_date)
                
                # تصفية إضافية حسب الجهاز والكاشير
                if device_id:
                    invoices = [inv for inv in invoices if inv.get('device_id') == device_id]
                if cashier_id:
                    # فلترة حسب كاشير الإغلاق (cashier_close)
                    invoices = [inv for inv in invoices if inv.get('cashier_close') == cashier_id]
            
            print(f"تم العثور على {len(invoices)} فاتورة")
            
            # عرض الفواتير في الجدول
            self.populate_invoices_table(invoices)
            
            # تحديث بطاقات الإجمالي
            self.update_invoice_summary_cards(invoices)
            
            # عرض رسالة إعلامية إذا لم توجد فواتير
            if not invoices:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "لا توجد فواتير", 
                    f"لا توجد فواتير في الفترة المحددة ({start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')})")
            
        except Exception as e:
            print(f"خطأ في تحميل الفواتير: {e}")
            import traceback
            traceback.print_exc()
    
    def update_invoice_summary_cards(self, invoices):
        """تحديث بطاقات إجمالي الفواتير"""
        try:
            # حساب الإحصائيات
            total_invoices = len(invoices)
            total_amount = sum(invoice.get('total_amount', 0) for invoice in invoices)
            avg_amount = total_amount / total_invoices if total_invoices > 0 else 0
            
            # حساب فواتير خدمة العملاء (فواتير بدون جهاز)
            customer_service_invoices = len([inv for inv in invoices if not inv.get('device_id') or inv.get('device_id') is None])
            
            # تحديث البطاقات
            self.update_summary_card(self.invoice_total_card, total_invoices)
            self.update_summary_card(self.invoice_amount_card, f"{total_amount:.2f}")
            self.update_summary_card(self.invoice_avg_card, f"{avg_amount:.2f}")
            self.update_summary_card(self.customer_service_card, customer_service_invoices)
            
        except Exception as e:
            print(f"خطأ في تحديث بطاقات إجمالي الفواتير: {e}")
    
    def load_all_invoices(self):
        """تحميل جميع الفواتير المغلقة"""
        try:
            print("تحميل جميع الفواتير المغلقة...")
            from models.invoice_model import InvoiceModel
            invoice_model = InvoiceModel()
            
            # الحصول على جميع الفواتير المغلقة
            invoices = invoice_model.get_all_closed_invoices()
            print(f"تم العثور على {len(invoices)} فاتورة مغلقة")
            
            # عرض الفواتير في الجدول
            self.populate_invoices_table(invoices)
            
            # تحديث بطاقات الإجمالي
            self.update_invoice_summary_cards(invoices)
            
            # عرض رسالة إعلامية
            if invoices:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "تم التحميل", 
                    f"تم تحميل {len(invoices)} فاتورة مغلقة")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "لا توجد فواتير", 
                    "لا توجد فواتير مغلقة في قاعدة البيانات")
            
        except Exception as e:
            print(f"خطأ في تحميل جميع الفواتير: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في تحميل الفواتير:\n{str(e)}")
    
    def load_invoice_references(self):
        """تحميل قوائم المراجع للفواتير"""
        try:
            # تحميل قائمة الأجهزة
            from models.device_model import DeviceModel
            device_model = DeviceModel()
            devices = device_model.get_all_devices()
            
            # print(f"تم تحميل {len(devices)} جهاز")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            
            self.invoice_device_combo.clear()
            self.invoice_device_combo.addItem("جميع الأجهزة", "")
            self.invoice_device_combo.addItem("خدمة العملاء", "customer_service")
            for device in devices:
                self.invoice_device_combo.addItem(device['name'], device['id'])
                # print(f"تم إضافة جهاز: {device['name']} (ID: {device['id']})")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            
            # تحميل قائمة الكاشير
            from models.user_model import UserModel
            user_model = UserModel()
            users = user_model.get_all_users()
            
            # print(f"تم تحميل {len(users)} مستخدم")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            
            self.invoice_cashier_combo.clear()
            self.invoice_cashier_combo.addItem("جميع الكاشير", "")
            for user in users:
                self.invoice_cashier_combo.addItem(user['username'], user['id'])
                # print(f"تم إضافة مستخدم: {user['username']} (ID: {user['id']})")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
                
        except Exception as e:
            # print(f"خطأ في تحميل مراجع الفواتير: {e}")  # تم تعطيل الطباعة لتجنب مشاكل الترميز
            import traceback
            traceback.print_exc()
    
    def populate_invoices_table(self, invoices):
        """ملء جدول الفواتير"""
        try:
            self.invoices_table.setRowCount(len(invoices))
            
            for row, invoice in enumerate(invoices):
                self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice['id'])))
                self.invoices_table.setItem(row, 1, QTableWidgetItem(invoice.get('device_name', '')))
                self.invoices_table.setItem(row, 2, QTableWidgetItem(invoice.get('cashier_open_name', '')))
                self.invoices_table.setItem(row, 3, QTableWidgetItem(invoice.get('cashier_close_name', '')))
                
                # وقت البداية
                start_time = invoice['start_time']
                if isinstance(start_time, str):
                    from datetime import datetime
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                self.invoices_table.setItem(row, 4, QTableWidgetItem(start_time.strftime('%Y-%m-%d %H:%M')))
                
                # وقت النهاية
                end_time = invoice.get('end_time')
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    self.invoices_table.setItem(row, 5, QTableWidgetItem(end_time.strftime('%Y-%m-%d %H:%M')))
                else:
                    self.invoices_table.setItem(row, 5, QTableWidgetItem("نشطة"))
                
                # المدة
                if end_time:
                    duration = end_time - start_time
                    duration_str = f"{int(duration.total_seconds() / 60)} دقيقة"
                else:
                    from datetime import datetime
                    duration = datetime.now() - start_time
                    duration_str = f"{int(duration.total_seconds() / 60)} دقيقة"
                
                self.invoices_table.setItem(row, 6, QTableWidgetItem(duration_str))
                self.invoices_table.setItem(row, 7, QTableWidgetItem(format_currency(invoice['total_amount'])))
                
                # تفاصيل التسعيرة
                pricing_details = invoice.get('pricing_details', {})
                pricing_text = self.format_pricing_details_for_table(pricing_details)
                self.invoices_table.setItem(row, 8, QTableWidgetItem(pricing_text))
                
                # الحالة
                status = "مكتملة" if end_time else "نشطة"
                self.invoices_table.setItem(row, 9, QTableWidgetItem(status))
                
                # طريقة الدفع
                payment_method = invoice.get('paid_by', 'نقدي')
                if payment_method == 'cash':
                    payment_text = "نقدي"
                elif payment_method == 'customer_balance':
                    payment_text = "من حساب العميل"
                else:
                    payment_text = payment_method
                self.invoices_table.setItem(row, 10, QTableWidgetItem(payment_text))
            
        except Exception as e:
            print(f"خطأ في ملء جدول الفواتير: {e}")
    
    def format_pricing_details_for_table(self, pricing_details):
        """تنسيق تفاصيل التسعيرة للجدول"""
        try:
            if not pricing_details:
                return "غير متوفر"
            
            if pricing_details.get('has_advanced_pricing', False):
                single_cost = pricing_details.get('single_cost', 0)
                multi_cost = pricing_details.get('multi_cost', 0)
                
                if single_cost > 0 and multi_cost > 0:
                    return f"👤 {single_cost:.1f} + 👥 {multi_cost:.1f}"
                elif single_cost > 0:
                    return f"👤 {single_cost:.1f}"
                elif multi_cost > 0:
                    return f"👥 {multi_cost:.1f}"
                else:
                    return "لا توجد تكلفة"
            else:
                # ⭐ تسعيرة بسيطة - استخدام pricing_type_original للعرض الصحيح
                pricing_type_original = pricing_details.get('pricing_type_original', pricing_details.get('pricing_type', 'single'))
                if pricing_type_original == 'single':
                    return "👤 فردي"
                elif pricing_type_original == 'multi':
                    return "👥 جماعي"
                elif pricing_type_original == 'mixed':
                    return "👤👥 فردي / جماعي"
                else:
                    return "👤 فردي"  # افتراضي
                    
        except Exception as e:
            return "خطأ في التنسيق"
    
    def on_invoice_clicked(self, item):
        """عرض تفاصيل الفاتورة عند النقر عليها"""
        try:
            row = item.row()
            invoice_id = self.invoices_table.item(row, 0).text()
            
            # الحصول على تفاصيل الفاتورة
            from models.invoice_model import InvoiceModel
            invoice_model = InvoiceModel()
            invoice = invoice_model.get_invoice_by_id(int(invoice_id))
            
            if invoice:
                # عرض نافذة تفاصيل الفاتورة
                self.show_invoice_details_dialog(invoice)
            
        except Exception as e:
            print(f"خطأ في عرض تفاصيل الفاتورة: {e}")
            import traceback
            traceback.print_exc()
    
    def show_invoice_details_dialog(self, invoice):
        """عرض نافذة تفاصيل الفاتورة"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont
            
            # إنشاء النافذة
            dialog = QDialog(self)
            dialog.setWindowTitle(f"تفاصيل الفاتورة رقم {invoice['id']}")
            dialog.setModal(True)
            dialog.resize(800, 600)
            
            # التخطيط الرئيسي
            layout = QVBoxLayout(dialog)
            
            # العنوان
            title_label = QLabel(f"📋 تفاصيل الفاتورة رقم {invoice['id']}")
            title_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            """)
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # معلومات أساسية
            basic_group = QGroupBox("📋 المعلومات الأساسية")
            basic_layout = QFormLayout(basic_group)
            
            basic_layout.addRow("رقم الفاتورة:", QLabel(str(invoice['id'])))
            basic_layout.addRow("الجهاز:", QLabel(invoice.get('device_name', 'غير محدد')))
            basic_layout.addRow("كاشير الفتح:", QLabel(invoice.get('cashier_open_name', 'غير محدد')))
            basic_layout.addRow("كاشير الإغلاق:", QLabel(invoice.get('cashier_close_name', 'غير محدد')))
            
            # تنسيق التاريخ
            start_time = invoice['start_time']
            if isinstance(start_time, str):
                from datetime import datetime
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            basic_layout.addRow("وقت البداية:", QLabel(start_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            end_time = invoice.get('end_time')
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                basic_layout.addRow("وقت النهاية:", QLabel(end_time.strftime('%Y-%m-%d %H:%M:%S')))
            else:
                basic_layout.addRow("وقت النهاية:", QLabel("نشطة"))
            
            layout.addWidget(basic_group)
            
            # تفاصيل التسعيرة
            pricing_details = invoice.get('pricing_details', {})
            if pricing_details.get('has_advanced_pricing', False):
                pricing_group = QGroupBox("💰 تفاصيل التسعيرة المتقدمة")
                pricing_layout = QVBoxLayout(pricing_group)
                
                pricing_text = QTextEdit()
                pricing_text.setReadOnly(True)
                pricing_text.setMaximumHeight(150)
                
                single_cost = pricing_details.get('single_cost', 0)
                multi_cost = pricing_details.get('multi_cost', 0)
                single_hours = pricing_details.get('single_hours', 0)
                multi_hours = pricing_details.get('multi_hours', 0)
                
                pricing_content = ""
                if single_cost > 0 and multi_cost > 0:
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    
                    pricing_content = f"""👤 التسعيرة الفردية:
   الوقت: {single_h:02d}:{single_m:02d}:{single_s:02d}
   التكلفة: {format_currency(single_cost)}

👥 التسعيرة الجماعية:
   الوقت: {multi_h:02d}:{multi_m:02d}:{multi_s:02d}
   التكلفة: {format_currency(multi_cost)}

💰 المجموع: {format_currency(pricing_details.get('total_cost', 0))}"""
                elif single_cost > 0:
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    pricing_content = f"""👤 التسعيرة الفردية:
   الوقت: {single_h:02d}:{single_m:02d}:{single_s:02d}
   التكلفة: {format_currency(single_cost)}"""
                elif multi_cost > 0:
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    pricing_content = f"""👥 التسعيرة الجماعية:
   الوقت: {multi_h:02d}:{multi_m:02d}:{multi_s:02d}
   التكلفة: {format_currency(multi_cost)}"""
                
                pricing_text.setPlainText(pricing_content)
                pricing_layout.addWidget(pricing_text)
                layout.addWidget(pricing_group)
            else:
                # ⭐ تسعيرة بسيطة - استخدام pricing_type_original للعرض الصحيح
                pricing_type_original = pricing_details.get('pricing_type_original', pricing_details.get('pricing_type', 'single'))
                
                # ⭐ تحديد نص التسعيرة بناءً على النوع (مع دعم mixed)
                if pricing_type_original == 'single':
                    pricing_type_label = "👤 فردي"
                elif pricing_type_original == 'multi':
                    pricing_type_label = "👥 جماعي"
                elif pricing_type_original == 'mixed':
                    pricing_type_label = "👤👥 فردي / جماعي"
                else:
                    pricing_type_label = "👤 فردي"  # افتراضي
                
                basic_layout.addRow("نوع التسعيرة:", QLabel(pricing_type_label))
            
            # المبالغ
            amounts_group = QGroupBox("💵 المبالغ")
            amounts_layout = QFormLayout(amounts_group)
            
            amounts_layout.addRow("سعر الجلسة:", QLabel(format_currency(invoice.get('session_price', 0))))
            amounts_layout.addRow("إجمالي المنتجات:", QLabel(format_currency(invoice.get('products_total', 0))))
            amounts_layout.addRow("المبلغ الإجمالي:", QLabel(format_currency(invoice.get('total_amount', 0))))
            
            payment_method = invoice.get('paid_by', 'نقدي')
            if payment_method == 'cash':
                payment_text = "نقدي"
            elif payment_method == 'customer_balance':
                payment_text = "من حساب العميل"
            else:
                payment_text = payment_method
            amounts_layout.addRow("طريقة الدفع:", QLabel(payment_text))
            
            if invoice.get('customer_phone'):
                amounts_layout.addRow("هاتف العميل:", QLabel(invoice['customer_phone']))
            
            layout.addWidget(amounts_group)
            
            # منتجات الفاتورة
            products_group = QGroupBox("🛒 منتجات الفاتورة")
            products_layout = QVBoxLayout(products_group)
            
            # جلب منتجات الفاتورة
            from models.invoice_model import InvoiceModel
            invoice_model = InvoiceModel()
            products = invoice_model.get_invoice_products(invoice['id'])
            
            if products:
                products_table = QTableWidget()
                products_table.setColumnCount(4)
                products_table.setHorizontalHeaderLabels(["اسم المنتج", "الكمية", "سعر الوحدة", "الإجمالي"])
                
                products_table.setRowCount(len(products))
                for row, product in enumerate(products):
                    # استخدام product_name إذا كان متوفراً، وإلا name
                    product_name = product.get('product_name') or product.get('name', 'غير محدد')
                    quantity = product.get('quantity', 0)
                    
                    # تحديد السعر والإجمالي بناءً على نوع البيانات
                    if 'unit_price' in product and 'total_price' in product:
                        # بيانات من invoice_items
                        unit_price = product.get('unit_price', 0)
                        total_price = product.get('total_price', 0)
                    elif 'price' in product:
                        # بيانات من invoice_products
                        unit_price = product.get('price', 0)
                        total_price = unit_price * quantity
                    else:
                        # بيانات افتراضية
                        unit_price = 0
                        total_price = 0
                    
                    products_table.setItem(row, 0, QTableWidgetItem(product_name))
                    products_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
                    products_table.setItem(row, 2, QTableWidgetItem(format_currency(unit_price)))
                    products_table.setItem(row, 3, QTableWidgetItem(format_currency(total_price)))
                
                # إعداد الجدول
                header = products_table.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.Stretch)
                products_table.setMaximumHeight(200)
                
                products_layout.addWidget(products_table)
            else:
                no_products_label = QLabel("لا توجد منتجات في هذه الفاتورة")
                no_products_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                no_products_label.setAlignment(Qt.AlignCenter)
                products_layout.addWidget(no_products_label)
            
            layout.addWidget(products_group)
            
            # أزرار التحكم
            buttons_layout = QHBoxLayout()
            
            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            buttons_layout.addWidget(close_btn)
            
            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)
            
            # عرض النافذة
            dialog.exec()
            
        except Exception as e:
            print(f"خطأ في عرض نافذة تفاصيل الفاتورة: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في عرض تفاصيل الفاتورة:\n{str(e)}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = ReportsViewWindow(test_user)
    window.show()
    sys.exit(app.exec())
