"""
واجهة إدارة الورديات الاحترافية
Professional Shift Management Interface
"""

import sys
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar, QStackedWidget,
    QListWidget, QListWidgetItem, QCheckBox, QSpinBox,
    QDoubleSpinBox, QSlider, QProgressBar, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QLinearGradient

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.shift_controller import ShiftController
from utils.notifications import show_error, show_success

class ShiftDataWidget(QWidget):
    """ويدجت عرض بيانات الوردية"""
    
    # إشارات
    data_updated = Signal(dict)
    
    def __init__(self, cashier_id: int, shift_id: int = None):
        super().__init__()
        self.cashier_id = cashier_id
        self.shift_id = shift_id
        self.shift_controller = ShiftController()
        self.setup_ui()
        self.load_data()
        self.start_refresh_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # عنوان القسم
        title_label = QLabel("📊 بيانات الوردية الحالية")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(title_label)
        
        # إحصائيات سريعة
        self.create_stats_widgets(layout)
        
        # تبويبات البيانات
        self.create_tabs_widget(layout)
    
    def create_stats_widgets(self, parent_layout):
        """إنشاء ويدجت الإحصائيات"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # إجمالي الفواتير
        self.invoices_count_label = QLabel("0")
        self.invoices_count_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #27ae60;
            background-color: #d5f4e6;
            padding: 15px;
            border-radius: 8px;
            min-width: 80px;
            text-align: center;
        """)
        invoices_label = QLabel("فواتير")
        invoices_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        invoices_layout = QVBoxLayout()
        invoices_layout.addWidget(self.invoices_count_label)
        invoices_layout.addWidget(invoices_label)
        stats_layout.addLayout(invoices_layout)
        
        # إجمالي الإيرادات
        self.revenue_label = QLabel("0.00")
        self.revenue_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
            background-color: #d6eaf8;
            padding: 15px;
            border-radius: 8px;
            min-width: 80px;
            text-align: center;
        """)
        revenue_text_label = QLabel("إيرادات")
        revenue_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        revenue_layout = QVBoxLayout()
        revenue_layout.addWidget(self.revenue_label)
        revenue_layout.addWidget(revenue_text_label)
        stats_layout.addLayout(revenue_layout)
        
        # إجمالي المصروفات
        self.expenses_label = QLabel("0.00")
        self.expenses_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            background-color: #fadbd8;
            padding: 15px;
            border-radius: 8px;
            min-width: 80px;
            text-align: center;
        """)
        expenses_text_label = QLabel("مصروفات")
        expenses_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        expenses_layout = QVBoxLayout()
        expenses_layout.addWidget(self.expenses_label)
        expenses_layout.addWidget(expenses_text_label)
        stats_layout.addLayout(expenses_layout)
        
        # صافي الربح
        self.profit_label = QLabel("0.00")
        self.profit_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #8e44ad;
            background-color: #e8daef;
            padding: 15px;
            border-radius: 8px;
            min-width: 80px;
            text-align: center;
        """)
        profit_text_label = QLabel("صافي الربح")
        profit_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        profit_layout = QVBoxLayout()
        profit_layout.addWidget(self.profit_label)
        profit_layout.addWidget(profit_text_label)
        stats_layout.addLayout(profit_layout)
        
        parent_layout.addWidget(stats_frame)
    
    def create_tabs_widget(self, parent_layout):
        """إنشاء تبويبات البيانات"""
        self.tabs_widget = QTabWidget()
        self.tabs_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
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
        """)
        
        # تبويب الفواتير
        self.invoices_tab = self.create_invoices_tab()
        self.tabs_widget.addTab(self.invoices_tab, "📄 الفواتير")
        
        # تبويب المصروفات
        self.expenses_tab = self.create_expenses_tab()
        self.tabs_widget.addTab(self.expenses_tab, "💰 المصروفات")
        
        parent_layout.addWidget(self.tabs_widget)
    
    def create_invoices_tab(self):
        """إنشاء تبويب الفواتير"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # شريط أدوات الفواتير
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        
        # عداد الفواتير
        self.invoices_count_display = QLabel("0 فاتورة")
        self.invoices_count_display.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        toolbar_layout.addWidget(self.invoices_count_display)
        
        layout.addLayout(toolbar_layout)
        
        # جدول الفواتير
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "الجهاز", "المبلغ", "وقت البداية", "وقت النهاية", "الحالة"
        ])
        
        # إعداد الجدول
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoices_table.horizontalHeader().setStretchLastSection(True)
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.invoices_table)
        
        return tab_widget
    
    def create_expenses_tab(self):
        """إنشاء تبويب المصروفات"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # شريط أدوات المصروفات
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        refresh_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        
        # عداد المصروفات
        self.expenses_count_display = QLabel("0 مصروف")
        self.expenses_count_display.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        toolbar_layout.addWidget(self.expenses_count_display)
        
        layout.addLayout(toolbar_layout)
        
        # جدول المصروفات
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels([
            "رقم المصروف", "المبلغ", "السبب", "التاريخ", "الملاحظات"
        ])
        
        # إعداد الجدول
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.expenses_table.horizontalHeader().setStretchLastSection(True)
        self.expenses_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.expenses_table)
        
        return tab_widget
    
    def load_data(self):
        """تحميل بيانات الوردية"""
        try:
            # الحصول على بيانات الوردية
            shift_data = self.shift_controller.get_cashier_shift_data(self.cashier_id, self.shift_id)
            
            # تحديث الإحصائيات
            stats = shift_data.get('statistics', {})
            self.invoices_count_label.setText(str(stats.get('total_invoices', 0)))
            self.revenue_label.setText(f"{stats.get('total_revenue', 0):.2f}")
            self.expenses_label.setText(f"{stats.get('total_expense_amount', 0):.2f}")
            self.profit_label.setText(f"{stats.get('net_profit', 0):.2f}")
            
            # تحديث جداول البيانات
            self.update_invoices_table(shift_data.get('invoices', []))
            self.update_expenses_table(shift_data.get('expenses', []))
            
            # إرسال إشارة التحديث
            self.data_updated.emit(shift_data)
            
        except Exception as e:
            print(f"خطأ في تحميل بيانات الوردية: {e}")
    
    def update_invoices_table(self, invoices):
        """تحديث جدول الفواتير"""
        self.invoices_table.setRowCount(len(invoices))
        self.invoices_count_display.setText(f"{len(invoices)} فاتورة")
        
        for row, invoice in enumerate(invoices):
            # رقم الفاتورة
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice.get('id', ''))))
            
            # اسم الجهاز
            device_name = invoice.get('device_name', 'غير محدد')
            self.invoices_table.setItem(row, 1, QTableWidgetItem(device_name))
            
            # المبلغ
            amount = invoice.get('total_amount', 0)
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"{amount:.2f}"))
            
            # وقت البداية
            start_time = invoice.get('start_time', '')
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time_str = start_time.strftime('%H:%M')
            else:
                start_time_str = 'غير محدد'
            self.invoices_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            
            # وقت النهاية
            end_time = invoice.get('end_time', '')
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_time_str = end_time.strftime('%H:%M')
            else:
                end_time_str = 'نشطة'
            self.invoices_table.setItem(row, 4, QTableWidgetItem(end_time_str))
            
            # الحالة
            status = "مغلقة" if end_time else "نشطة"
            status_item = QTableWidgetItem(status)
            if status == "نشطة":
                status_item.setBackground(QColor("#d5f4e6"))
            else:
                status_item.setBackground(QColor("#fadbd8"))
            self.invoices_table.setItem(row, 5, status_item)
    
    def update_expenses_table(self, expenses):
        """تحديث جدول المصروفات"""
        self.expenses_table.setRowCount(len(expenses))
        self.expenses_count_display.setText(f"{len(expenses)} مصروف")
        
        for row, expense in enumerate(expenses):
            # رقم المصروف
            self.expenses_table.setItem(row, 0, QTableWidgetItem(str(expense.get('id', ''))))
            
            # المبلغ
            amount = expense.get('amount', 0)
            self.expenses_table.setItem(row, 1, QTableWidgetItem(f"{amount:.2f}"))
            
            # السبب
            reason = expense.get('reason', 'غير محدد')
            self.expenses_table.setItem(row, 2, QTableWidgetItem(reason))
            
            # التاريخ
            date_time = expense.get('date_time', '')
            if date_time:
                if isinstance(date_time, str):
                    date_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                date_str = date_time.strftime('%H:%M')
            else:
                date_str = 'غير محدد'
            self.expenses_table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # الملاحظات
            notes = expense.get('notes', '')
            self.expenses_table.setItem(row, 4, QTableWidgetItem(notes))
    
    def start_refresh_timer(self):
        """بدء تايمر التحديث التلقائي"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(30000)  # كل 30 ثانية

class ProfessionalShiftManagementWindow(QMainWindow):
    """نافذة إدارة الورديات الاحترافية"""
    
    # إشارات
    shift_started = Signal(dict)
    shift_ended = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.shift_controller = ShiftController()
        self.current_shift_data = None
        self.setup_ui()
        self.setup_connections()
        self.load_current_shift()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الورديات الاحترافية - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1400, 900)
        self.center_window()
        
        # إعداد الخلفية العامة
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # شريط العنوان
        self.create_header(main_layout)
        
        # منطقة المحتوى الرئيسية
        self.create_main_content(main_layout)
        
        # شريط الحالة
        self.create_status_bar()
    
    def create_header(self, parent_layout):
        """إنشاء شريط العنوان"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # عنوان الصفحة
        title_label = QLabel("⏰ إدارة الورديات الاحترافية")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
            background: none;
            border: none;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # معلومات المستخدم
        user_info = QLabel(f"المستخدم: {self.current_user.get('username', 'غير محدد')}")
        user_info.setStyleSheet("""
            font-size: 16px;
            color: white;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
        """)
        header_layout.addWidget(user_info)
        
        parent_layout.addWidget(header_frame)
    
    def create_main_content(self, parent_layout):
        """إنشاء المحتوى الرئيسي"""
        # استخدام QStackedWidget للتبديل بين الحالات
        self.content_stack = QStackedWidget()
        
        # صفحة عدم وجود وردية نشطة
        self.no_shift_page = self.create_no_shift_page()
        self.content_stack.addWidget(self.no_shift_page)
        
        # صفحة الوردية النشطة
        self.active_shift_page = self.create_active_shift_page()
        self.content_stack.addWidget(self.active_shift_page)
        
        parent_layout.addWidget(self.content_stack)
    
    def create_no_shift_page(self):
        """إنشاء صفحة عدم وجود وردية نشطة"""
        page_widget = QWidget()
        layout = QVBoxLayout(page_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # رسالة عدم وجود وردية
        no_shift_label = QLabel("لا توجد وردية نشطة")
        no_shift_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #7f8c8d;
            margin-bottom: 30px;
        """)
        no_shift_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(no_shift_label)
        
        # زر بدء وردية جديدة
        start_shift_btn = QPushButton("🚀 بدء وردية جديدة")
        start_shift_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                min-width: 200px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
            }
            QPushButton:pressed {
                background: #1e8449;
            }
        """)
        start_shift_btn.clicked.connect(self.start_new_shift)
        layout.addWidget(start_shift_btn, alignment=Qt.AlignCenter)
        
        return page_widget
    
    def create_active_shift_page(self):
        """إنشاء صفحة الوردية النشطة"""
        page_widget = QWidget()
        layout = QVBoxLayout(page_widget)
        
        # شريط معلومات الوردية
        self.create_shift_info_bar(layout)
        
        # منطقة البيانات
        self.shift_data_widget = ShiftDataWidget(
            self.current_user.get('id'), 
            self.current_shift_data.get('id') if self.current_shift_data else None
        )
        self.shift_data_widget.data_updated.connect(self.on_shift_data_updated)
        layout.addWidget(self.shift_data_widget)
        
        # شريط الأدوات السفلي
        self.create_bottom_toolbar(layout)
        
        return page_widget
    
    def create_shift_info_bar(self, parent_layout):
        """إنشاء شريط معلومات الوردية"""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        
        # معلومات الوردية
        self.shift_info_label = QLabel("معلومات الوردية")
        self.shift_info_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        info_layout.addWidget(self.shift_info_label)
        
        info_layout.addStretch()
        
        # زر إنهاء الوردية
        end_shift_btn = QPushButton("⏹️ إنهاء الوردية")
        end_shift_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        end_shift_btn.clicked.connect(self.end_current_shift)
        info_layout.addWidget(end_shift_btn)
        
        parent_layout.addWidget(info_frame)
    
    def create_bottom_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات السفلي"""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # زر تحديث البيانات
        refresh_btn = QPushButton("🔄 تحديث البيانات")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_shift_data)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        
        # معلومات آخر تحديث
        self.last_update_label = QLabel("آخر تحديث: --:--")
        self.last_update_label.setStyleSheet("color: white; font-size: 12px;")
        toolbar_layout.addWidget(self.last_update_label)
        
        parent_layout.addWidget(toolbar_frame)
    
    def create_status_bar(self):
        """إنشاء شريط الحالة"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # حالة الاتصال
        self.connection_status = QLabel("🟢 متصل")
        self.connection_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.status_bar.addWidget(self.connection_status)
        
        # حالة الوردية
        self.shift_status = QLabel("لا توجد وردية نشطة")
        self.shift_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.shift_status)
    
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
    
    def load_current_shift(self):
        """تحميل الوردية الحالية"""
        try:
            cashier_id = self.current_user.get('id')
            if not cashier_id:
                return
            
            # الحصول على الوردية النشطة
            active_shift = self.shift_controller.get_active_shift(cashier_id)
            
            if active_shift:
                self.current_shift_data = active_shift
                self.show_active_shift()
            else:
                self.current_shift_data = None
                self.show_no_shift()
                
        except Exception as e:
            print(f"خطأ في تحميل الوردية الحالية: {e}")
            self.show_no_shift()
    
    def show_active_shift(self):
        """عرض صفحة الوردية النشطة"""
        if self.current_shift_data:
            # تحديث معلومات الوردية
            start_time = self.current_shift_data.get('start_time')
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M')
            else:
                start_time_str = 'غير محدد'
            
            shift_name = self.current_shift_data.get('shift_name', 'وردية')
            self.shift_info_label.setText(f"{shift_name} - بدأت في: {start_time_str}")
            
            # تحديث شريط الحالة
            self.shift_status.setText(f"وردية نشطة: {shift_name}")
            self.shift_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # التبديل إلى صفحة الوردية النشطة
            self.content_stack.setCurrentWidget(self.active_shift_page)
    
    def show_no_shift(self):
        """عرض صفحة عدم وجود وردية"""
        # تحديث شريط الحالة
        self.shift_status.setText("لا توجد وردية نشطة")
        self.shift_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # التبديل إلى صفحة عدم وجود وردية
        self.content_stack.setCurrentWidget(self.no_shift_page)
    
    def start_new_shift(self):
        """بدء وردية جديدة"""
        dialog = StartShiftDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            try:
                cashier_id = dialog.get_cashier_id()
                shift_name = dialog.get_shift_name()
                notes = dialog.get_notes()
                
                # بدء الوردية مع تفريغ البيانات
                result = self.shift_controller.start_shift_with_clear_data(
                    cashier_id=cashier_id,
                    shift_name=shift_name,
                    notes=notes
                )
                
                if result['success']:
                    show_success("تم بدء الوردية", result['message'])
                    self.load_current_shift()
                    self.shift_started.emit(result.get('shift_data', {}))
                    
                    # إعادة تشغيل البرنامج مع تسجيل دخول تلقائي للكاشير الجديد
                    try:
                        from utils.auto_restart import schedule_restart_with_auto_login
                        from models.user_model import UserModel
                        
                        # الحصول على بيانات الكاشير الجديد
                        user_model = UserModel()
                        cashier_data = user_model.get_user_by_id(cashier_id)
                        
                        if cashier_data:
                            # جدولة إعادة التشغيل مع تأخير 2 ثانية
                            schedule_restart_with_auto_login(
                                cashier_id=cashier_id,
                                username=cashier_data['username'],
                                role=cashier_data['role'],
                                delay_ms=2000,
                                parent_widget=None
                            )
                            print(f"تم جدولة إعادة تشغيل البرنامج للكاشير {cashier_data['username']}")
                        else:
                            print(f"لم يتم العثور على بيانات الكاشير {cashier_id}")
                            
                    except Exception as restart_error:
                        print(f"خطأ في جدولة إعادة التشغيل: {restart_error}")
                else:
                    show_error("خطأ في بدء الوردية", result['message'])
                    
            except Exception as e:
                show_error("خطأ في بدء الوردية", str(e))
    
    def end_current_shift(self):
        """إنهاء الوردية الحالية"""
        if not self.current_shift_data:
            return
        
        dialog = EndShiftDialog(self.current_shift_data, self.current_user)
        if dialog.exec() == QDialog.Accepted:
            try:
                shift_id = self.current_shift_data['id']
                notes = dialog.get_notes()
                
                result = self.shift_controller.end_shift(shift_id, notes)
                
                if result['success']:
                    show_success("تم إنهاء الوردية", result['message'])
                    self.load_current_shift()
                    self.shift_ended.emit(self.current_shift_data)
                else:
                    show_error("خطأ في إنهاء الوردية", result['message'])
                    
            except Exception as e:
                show_error("خطأ في إنهاء الوردية", str(e))
    
    def refresh_shift_data(self):
        """تحديث بيانات الوردية"""
        if hasattr(self, 'shift_data_widget'):
            self.shift_data_widget.load_data()
            self.last_update_label.setText(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
    
    def on_shift_data_updated(self, data):
        """معالج تحديث بيانات الوردية"""
        self.last_update_label.setText(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

class StartShiftDialog(QDialog):
    """نافذة بدء وردية جديدة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("بدء وردية جديدة")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("🚀 بدء وردية جديدة")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اختيار الكاشير (للمدير فقط)
        from utils.permissions import check_permission, Permission
        if check_permission(self.current_user.get('role', ''), Permission.ADMIN_OVERRIDE):
            self.cashier_combo = QComboBox()
            self.cashier_combo.setStyleSheet("font-size: 14px; padding: 5px;")
            self.load_cashiers()
            form_layout.addRow("الكاشير:", self.cashier_combo)
        else:
            cashier_label = QLabel(f"{self.current_user.get('username', 'غير محدد')}")
            cashier_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            form_layout.addRow("الكاشير:", cashier_label)
            self.cashier_combo = None
        
        # اسم الوردية
        self.shift_name_input = QLineEdit()
        self.shift_name_input.setPlaceholderText("مثال: وردية صباحية")
        self.shift_name_input.setText(f"وردية {datetime.now().strftime('%Y-%m-%d')}")
        form_layout.addRow("اسم الوردية:", self.shift_name_input)
        
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
    
    def load_cashiers(self):
        """تحميل قائمة الكاشيرات"""
        try:
            from models.user_model import UserModel
            user_model = UserModel()
            cashiers = user_model.get_cashiers()
            
            self.cashier_combo.clear()
            for cashier in cashiers:
                if cashier.get('enabled', True):
                    display_name = f"{cashier.get('username', '')} - {cashier.get('full_name', '')}"
                    self.cashier_combo.addItem(display_name, cashier['id'])
            
            # تحديد الكاشير الحالي
            current_user_id = self.current_user.get('id')
            for i in range(self.cashier_combo.count()):
                if self.cashier_combo.itemData(i) == current_user_id:
                    self.cashier_combo.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            print(f"خطأ في تحميل الكاشيرات: {e}")
    
    def get_cashier_id(self):
        """الحصول على معرف الكاشير المختار"""
        if self.cashier_combo:
            return self.cashier_combo.currentData()
        else:
            return self.current_user.get('id')
    
    def get_shift_name(self):
        """الحصول على اسم الوردية"""
        return self.shift_name_input.text().strip()
    
    def get_notes(self):
        """الحصول على الملاحظات"""
        return self.notes_input.toPlainText().strip()

class EndShiftDialog(QDialog):
    """نافذة إنهاء وردية"""
    
    def __init__(self, shift_data, current_user):
        super().__init__()
        self.shift_data = shift_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إنهاء وردية")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("⏹️ إنهاء وردية")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الوردية
        shift_info = QLabel(f"الوردية رقم: {self.shift_data['id']}")
        shift_info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(shift_info)
        
        # وقت البداية
        start_time = self.shift_data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        start_time_label = QLabel(f"وقت البداية: {start_time.strftime('%Y-%m-%d %H:%M')}")
        start_time_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(start_time_label)
        
        # المدة الحالية
        duration = datetime.now() - start_time
        hours = int(duration.total_seconds() / 3600)
        minutes = int((duration.total_seconds() % 3600) / 60)
        duration_label = QLabel(f"المدة الحالية: {hours}س {minutes}د")
        duration_label.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(duration_label)
        
        # ملاحظات النهاية
        notes_label = QLabel("ملاحظات إنهاء الوردية (اختياري):")
        notes_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات حول إنهاء الوردية...")
        layout.addWidget(self.notes_input)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_notes(self):
        """الحصول على الملاحظات"""
        return self.notes_input.toPlainText().strip()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # بيانات تجريبية للاختبار
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = ProfessionalShiftManagementWindow(test_user)
    window.show()
    sys.exit(app.exec())
