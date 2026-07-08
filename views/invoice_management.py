"""
واجهة إدارة الفواتير
Invoice Management Interface
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar, QSpinBox, QDoubleSpinBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InvoiceCard(QFrame):
    """كارت الفاتورة"""
    
    # إشارات
    invoice_clicked = Signal(dict)  # بيانات الفاتورة
    
    def __init__(self, invoice_data):
        super().__init__()
        self.invoice_data = invoice_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(120, 140)  # حجم أصغر لتناسب 10 كروت كاملة في الصف
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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        
        # عنوان الفاتورة
        self.title_label = QLabel(f"#{self.invoice_data.get('id', 'N/A')}")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # اسم الجهاز
        self.device_label = QLabel("")
        self.device_label.setAlignment(Qt.AlignCenter)
        self.device_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.device_label)
        
        # الكاشير
        self.cashier_label = QLabel("")
        self.cashier_label.setAlignment(Qt.AlignCenter)
        self.cashier_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.cashier_label)
        
        # وقت البداية
        self.start_time_label = QLabel("")
        self.start_time_label.setAlignment(Qt.AlignCenter)
        self.start_time_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.start_time_label)
        
        # المبلغ الإجمالي
        self.total_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        layout.addWidget(self.total_label)
        
        # حالة الفاتورة
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
    
    def update_display(self):
        """تحديث عرض الكارت"""
        # تحديث اسم الجهاز
        device_name = self.invoice_data.get('device_name', 'غير محدد')
        self.device_label.setText(f"الجهاز: {device_name}")
        
        # تحديث الكاشير
        cashier_name = self.invoice_data.get('cashier_open_name', 'غير محدد')
        self.cashier_label.setText(f"الكاشير: {cashier_name}")
        
        # تحديث وقت البداية
        start_time = self.invoice_data.get('start_time')
        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            self.start_time_label.setText(f"البداية: {start_time.strftime('%H:%M')}")
        
        # ⭐ تحديث المبلغ الإجمالي مع تفاصيل التسعيرة - تم إصلاحه
        total_amount = self.invoice_data.get('total_amount', 0)
        pricing_details = self.invoice_data.get('pricing_details', {})
        pricing_type_original = self.invoice_data.get('pricing_type_original', 'single')  # ⭐ الأصلي من قاعدة البيانات
        
        if pricing_details.get('has_advanced_pricing', False):
            # تسعيرة متقدمة
            single_cost = pricing_details.get('single_cost', 0)
            multi_cost = pricing_details.get('multi_cost', 0)
            
            if single_cost > 0 and multi_cost > 0:
                # تسعيرة مختلطة
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👤 {single_cost:.1f} + 👥 {multi_cost:.1f}")
            elif single_cost > 0:
                # فردي فقط
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👤 فردي")
            elif multi_cost > 0:
                # جماعي فقط
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👥 جماعي")
            else:
                self.total_label.setText(f"المبلغ: {total_amount} جنيه")
        else:
            # ⭐ تسعيرة تقليدية - استخدام pricing_type_original للعرض الصحيح
            if pricing_type_original == 'single':
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👤 فردي")
            elif pricing_type_original == 'multi':
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👥 جماعي")
            elif pricing_type_original == 'mixed':
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👤👥 فردي / جماعي")
            else:
                self.total_label.setText(f"المبلغ: {total_amount} جنيه\n👤 فردي")
        
        # تحديث حالة الفاتورة
        end_time = self.invoice_data.get('end_time')
        if end_time:
            # فاتورة مغلقة
            self.status_label.setText("مغلقة")
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
            """)
        else:
            # فاتورة مفتوحة
            self.status_label.setText("مفتوحة")
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
    
    def mousePressEvent(self, event):
        """معالج الضغط على الكارت"""
        if event.button() == Qt.LeftButton:
            self.invoice_clicked.emit(self.invoice_data)

class InvoiceManagementWindow(QMainWindow):
    """نافذة إدارة الفواتير"""
    
    # إشارات
    invoice_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.invoice_cards = {}
        self.setup_ui()
        self.setup_connections()
        self.load_invoices()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الفواتير - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1200, 800)
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
        
        # منطقة الفلاتر - تم إزالتها
        # self.create_filters_area(main_layout)
        
        # منطقة الفواتير المغلقة
        self.create_invoices_area(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("📄 إدارة الفواتير")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # أزرار التحكم
        self.total_invoices_btn = QPushButton("إجمالي الفواتير")
        self.total_invoices_btn.setStyleSheet("background-color: #3498db;")
        self.total_invoices_btn.clicked.connect(self.show_total_invoices)
        toolbar_layout.addWidget(self.total_invoices_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    # تم إزالة دالة create_filters_area
    
    def create_invoices_area(self, parent_layout):
        """إنشاء منطقة الفواتير"""
        # مجموعة الفواتير
        invoices_group = QGroupBox("الفواتير المغلقة")
        invoices_layout = QVBoxLayout(invoices_group)
        
        # إنشاء جدول الفواتير
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels([
            "اسم الجهاز",
            "وقت وتاريخ البداية",
            "وقت وتاريخ الإغلاق", 
            "الكاشير (البداية)",
            "الكاشير (الإغلاق)",
            "إجمالي الفاتورة",
            "طريقة الدفع"
        ])
        
        # تنسيق الجدول
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoices_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.invoices_table.setSortingEnabled(True)
        
        # تنسيق رؤوس الأعمدة
        header = self.invoices_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # اسم الجهاز
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # وقت البداية
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # وقت الإغلاق
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # كاشير البداية
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # كاشير الإغلاق
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # إجمالي الفاتورة
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # طريقة الدفع
        
        # تنسيق الجدول
        self.invoices_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        # ربط إشارة النقر
        self.invoices_table.itemClicked.connect(self.on_invoice_row_clicked)
        
        invoices_layout.addWidget(self.invoices_table)
        parent_layout.addWidget(invoices_group)
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات الفواتير")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات الفواتير
        self.total_invoices_label = QLabel("إجمالي الفواتير: 0")
        self.total_invoices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_invoices_label)
        
        self.open_invoices_label = QLabel("مفتوحة: 0")
        self.open_invoices_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.open_invoices_label)
        
        self.closed_invoices_label = QLabel("مغلقة: 0")
        self.closed_invoices_label.setStyleSheet("font-size: 14px; color: #95a5a6; font-weight: bold;")
        stats_layout.addWidget(self.closed_invoices_label)
        
        self.total_revenue_label = QLabel("إجمالي الإيرادات: 0 جنيه")
        self.total_revenue_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.total_revenue_label)
        
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
    
    def refresh_invoices(self):
        """تحديث الفواتير"""
        try:
            self.load_invoices()
        except Exception as e:
            print(f"خطأ في تحديث الفواتير: {e}")
    
    def add_new_invoice(self, invoice_data):
        """إضافة فاتورة جديدة"""
        try:
            # تنسيق بيانات الفاتورة
            formatted_invoice = self.format_invoice_data(invoice_data)
            
            # إضافة السطر الجديد في المقدمة
            self.invoices_table.insertRow(0)
            
            # إضافة البيانات إلى الجدول
            self.invoices_table.setItem(0, 0, QTableWidgetItem(formatted_invoice.get('device_name', 'غير محدد')))
            
            # تنسيق وقت البدء
            start_time = formatted_invoice.get('start_time')
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_time_str = 'غير محدد'
            self.invoices_table.setItem(0, 1, QTableWidgetItem(start_time_str))
            
            # تنسيق وقت الإغلاق
            end_time = formatted_invoice.get('end_time')
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                end_time_str = 'غير محدد'
            self.invoices_table.setItem(0, 2, QTableWidgetItem(end_time_str))
            
            # كاشير البداية
            self.invoices_table.setItem(0, 3, QTableWidgetItem(formatted_invoice.get('cashier_open_name', 'غير محدد')))
            
            # كاشير الإغلاق
            self.invoices_table.setItem(0, 4, QTableWidgetItem(formatted_invoice.get('cashier_close_name', 'غير محدد')))
            
            # إجمالي الفاتورة
            total_amount = formatted_invoice.get('total_amount', 0)
            total_str = f"{float(total_amount):.2f} جنيه"
            self.invoices_table.setItem(0, 5, QTableWidgetItem(total_str))
            
            # طريقة الدفع
            payment_method = formatted_invoice.get('paid_by', 'نقداً')
            self.invoices_table.setItem(0, 6, QTableWidgetItem(payment_method))
            
            # حفظ بيانات الفاتورة الكاملة
            self.invoice_cards[invoice_data['id']] = formatted_invoice
            
            # تحديث الإحصائيات
            self.update_stats_from_cards()
            
        except Exception as e:
            print(f"خطأ في إضافة فاتورة جديدة: {e}")
    
    def update_stats_from_cards(self):
        """تحديث الإحصائيات من البيانات الموجودة"""
        try:
            total = len(self.invoice_cards)
            closed_invoices = len([invoice_data for invoice_data in self.invoice_cards.values() 
                                  if invoice_data.get('end_time')])
            total_revenue = sum(float(invoice_data.get('total_amount', 0)) 
                              for invoice_data in self.invoice_cards.values() 
                              if invoice_data.get('end_time'))
            
            self.total_invoices_label.setText(f"إجمالي الفواتير: {total}")
            self.open_invoices_label.setText(f"مفتوحة: 0")
            self.closed_invoices_label.setText(f"مغلقة: {closed_invoices}")
            self.total_revenue_label.setText(f"إجمالي الإيرادات: {total_revenue:.2f} جنيه")
            
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {e}")
    
    # تم إزالة دالة apply_filters
    
    def load_invoices(self):
        """تحميل فواتير الوردية الحالية فقط"""
        try:
            # مسح البيانات الموجودة في الجدول
            self.invoices_table.setRowCount(0)
            self.invoice_cards.clear()
            
            # مسح التخزين المؤقت في المتحكم
            try:
                from controllers.shift_controller import ShiftController
                shift_controller = ShiftController()
                # مسح التخزين المؤقت للوردية المشتركة
                keys_to_remove = [key for key in shift_controller.shift_data_cache.keys() if key.startswith("shared_")]
                for key in keys_to_remove:
                    del shift_controller.shift_data_cache[key]
            except Exception as e:
                print(f"خطأ في مسح التخزين المؤقت: {e}")
            
            # الحصول على فواتير الوردية المشتركة
            from controllers.shift_controller import ShiftController
            shift_controller = ShiftController()
            
            # الحصول على بيانات الوردية المشتركة
            shift_data = shift_controller.get_cashier_shift_data()
            invoices = shift_data.get('invoices', [])
            
            # ترتيب الفواتير حسب وقت البداية (الأحدث أولاً)
            invoices.sort(key=lambda x: x.get('start_time', datetime.min), reverse=True)
            
            # إضافة البيانات إلى الجدول
            self.invoices_table.setRowCount(len(invoices))
            
            for row, invoice in enumerate(invoices):
                # تحويل البيانات إلى التنسيق المطلوب
                formatted_invoice = self.format_invoice_data(invoice)
                
                # إضافة البيانات إلى الجدول
                self.invoices_table.setItem(row, 0, QTableWidgetItem(formatted_invoice.get('device_name', 'غير محدد')))
                
                # تنسيق وقت البدء
                start_time = formatted_invoice.get('start_time')
                if start_time:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    start_time_str = 'غير محدد'
                self.invoices_table.setItem(row, 1, QTableWidgetItem(start_time_str))
                
                # تنسيق وقت الإغلاق
                end_time = formatted_invoice.get('end_time')
                if end_time:
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    end_time_str = 'غير محدد'
                self.invoices_table.setItem(row, 2, QTableWidgetItem(end_time_str))
                
                # كاشير البداية
                cashier_open_name = formatted_invoice.get('cashier_open_name', 'غير محدد')
                if not cashier_open_name or cashier_open_name == 'None':
                    cashier_open_name = 'غير محدد'
                self.invoices_table.setItem(row, 3, QTableWidgetItem(cashier_open_name))
                
                # كاشير الإغلاق
                cashier_close_name = formatted_invoice.get('cashier_close_name', 'غير محدد')
                if not cashier_close_name or cashier_close_name == 'None':
                    cashier_close_name = 'غير محدد'
                self.invoices_table.setItem(row, 4, QTableWidgetItem(cashier_close_name))
                
                # إجمالي الفاتورة
                total_amount = formatted_invoice.get('total_amount', 0)
                total_str = f"{float(total_amount):.2f} جنيه"
                self.invoices_table.setItem(row, 5, QTableWidgetItem(total_str))
                
                # طريقة الدفع
                payment_method = formatted_invoice.get('paid_by', 'نقداً')
                self.invoices_table.setItem(row, 6, QTableWidgetItem(payment_method))
                
                # حفظ بيانات الفاتورة الكاملة للوصول إليها عند النقر
                self.invoice_cards[invoice['id']] = formatted_invoice
            
            # تحديث الإحصائيات
            self.update_stats(invoices)
            
            # إضافة رسالة إذا لم توجد فواتير مغلقة
            if not invoices:
                self.invoices_table.setRowCount(1)
                self.invoices_table.setItem(0, 0, QTableWidgetItem("لا توجد فواتير مغلقة للعرض"))
                self.invoices_table.setItem(0, 1, QTableWidgetItem(""))
                self.invoices_table.setItem(0, 2, QTableWidgetItem(""))
                self.invoices_table.setItem(0, 3, QTableWidgetItem(""))
                self.invoices_table.setItem(0, 4, QTableWidgetItem(""))
                self.invoices_table.setItem(0, 5, QTableWidgetItem(""))
                self.invoices_table.setItem(0, 6, QTableWidgetItem(""))
                # جعل السطر غير قابل للتحديد
                self.invoices_table.setItem(0, 0).setFlags(Qt.NoItemFlags)
            
            # تحديث فوري للواجهة
            self.invoices_table.repaint()
            self.repaint()
            
        except Exception as e:
            print(f"خطأ في تحميل الفواتير: {e}")
            import traceback
            traceback.print_exc()
    
    def format_invoice_data(self, invoice):
        """تنسيق بيانات الفاتورة للعرض"""
        try:
            # تحويل التواريخ
            start_time = invoice.get('start_time')
            end_time = invoice.get('end_time')
            
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # تنسيق طريقة الدفع
            paid_by = invoice.get('paid_by', 'cash')
            payment_text = 'نقداً' if paid_by == 'cash' else 'من حساب العميل'
            
            # تنسيق نوع التسعيرة
            # ⭐ الحصول على نوع التسعيرة الأصلي والمحسّن من pricing_details
            pricing_details = invoice.get('pricing_details', {})
            pricing_type_original = pricing_details.get('pricing_type_original', invoice.get('pricing_type', 'single'))
            pricing_type = pricing_details.get('pricing_type', invoice.get('pricing_type', 'single'))
            
            # ⭐ دعم جميع أنواع التسعيرة بما في ذلك المختلط
            if pricing_type == 'admin':
                pricing_text = 'معاملة إدارية'
            elif pricing_type == 'single':
                pricing_text = 'فردي'
            elif pricing_type == 'multi':
                pricing_text = 'جماعي'
            elif pricing_type == 'mixed':
                pricing_text = 'فردي / جماعي'  # ⭐ استخدام "/" بدلاً من "و"
            else:
                pricing_text = 'فردي'  # افتراضي
            
            # تنظيف أسماء الكاشيرات
            cashier_open_name = invoice.get('cashier_open_name', 'غير محدد')
            if not cashier_open_name or cashier_open_name == 'None':
                cashier_open_name = 'غير محدد'
                
            cashier_close_name = invoice.get('cashier_close_name', 'غير محدد')
            if not cashier_close_name or cashier_close_name == 'None':
                cashier_close_name = 'غير محدد'
            
            # تحديد اسم الجهاز بناءً على نوع الفاتورة
            device_name = invoice.get('device_name', 'غير محدد')
            customer_phone = invoice.get('customer_phone')
            pricing_type = invoice.get('pricing_type', '')
            
            # إذا كانت فاتورة عميل (معاملة إدارية) وليس لها جهاز محدد
            if pricing_type == 'admin' and customer_phone and (not device_name or device_name == 'غير محدد' or device_name == 'None'):
                device_name = f"خدمة عملاء - {customer_phone}"
            
            formatted_invoice = {
                'id': invoice.get('id'),
                'device_id': invoice.get('device_id'),
                'device_name': device_name,
                'cashier_open': invoice.get('cashier_open'),
                'cashier_open_name': cashier_open_name,
                'cashier_close': invoice.get('cashier_close'),
                'cashier_close_name': cashier_close_name,
                'shift_id': invoice.get('shift_id'),
                'start_time': start_time,
                'end_time': end_time,
                'pricing_type': pricing_text,  # ⭐ النوع المنسق للعرض
                'pricing_type_original': pricing_type_original,  # ⭐ النوع الأصلي من قاعدة البيانات
                'pricing_details': pricing_details,  # ⭐ إضافة تفاصيل التسعيرة الكاملة
                'session_price': invoice.get('session_price', 0),
                'products_total': invoice.get('products_total', 0),
                'total_amount': invoice.get('total_amount', 0),
                'customer_phone': customer_phone,
                'paid_by': payment_text,
                'paid_by_original': paid_by  # حفظ القيمة الأصلية للاستخدام في التحليل
            }
            
            return formatted_invoice
            
        except Exception as e:
            print(f"خطأ في تنسيق بيانات الفاتورة: {e}")
            return invoice
    
    def update_stats(self, invoices):
        """تحديث الإحصائيات"""
        total = len(invoices)
        open_invoices = len([i for i in invoices if not i['end_time']])
        closed_invoices = total - open_invoices
        total_revenue = sum(float(i['total_amount']) for i in invoices if i['end_time'])
        
        self.total_invoices_label.setText(f"إجمالي الفواتير: {total}")
        self.open_invoices_label.setText(f"مفتوحة: {open_invoices}")
        self.closed_invoices_label.setText(f"مغلقة: {closed_invoices}")
        self.total_revenue_label.setText(f"إجمالي الإيرادات: {total_revenue} جنيه")
    
    def on_invoice_row_clicked(self, item):
        """معالج النقر على سطر في جدول الفواتير"""
        try:
            row = item.row()
            
            # التحقق من أن السطر يحتوي على بيانات صحيحة
            device_name = self.invoices_table.item(row, 0)
            if not device_name or device_name.text() == "لا توجد فواتير مغلقة للعرض":
                return
            
            # الحصول على معرف الفاتورة من البيانات المحفوظة
            invoice_id = None
            for inv_id, invoice_data in self.invoice_cards.items():
                if invoice_data.get('device_name') == device_name.text():
                    invoice_id = inv_id
                    break
            
            if invoice_id:
                invoice_data = self.invoice_cards[invoice_id]
                print(f"تم النقر على الفاتورة: {invoice_id}")
                self.invoice_selected.emit(invoice_data)
                
                # عرض نافذة تفاصيل الفاتورة
                self.show_invoice_details(invoice_data)
            else:
                print("لم يتم العثور على بيانات الفاتورة")
                
        except Exception as e:
            print(f"خطأ في معالجة النقر على الفاتورة: {e}")
    
    def on_invoice_clicked(self, invoice_data):
        """معالج النقر على الفاتورة (للتوافق مع الكود القديم)"""
        print(f"تم النقر على الفاتورة: {invoice_data['id']}")
        self.invoice_selected.emit(invoice_data)
        
        # عرض نافذة تفاصيل الفاتورة
        self.show_invoice_details(invoice_data)
    
    
    def show_invoice_details(self, invoice_data):
        """عرض نافذة تفاصيل الفاتورة"""
        dialog = InvoiceDetailsDialog(invoice_data, self.current_user)
        dialog.exec()
    
    def show_total_invoices(self):
        """عرض إجمالي الفواتير مع تفاصيل طرق الدفع"""
        from PySide6.QtWidgets import QMessageBox
        
        # حساب إجمالي الفواتير
        total_invoices = len(self.invoice_cards)
        closed_invoices = len([card for card in self.invoice_cards.values() 
                              if (hasattr(card, 'invoice_data') and card.invoice_data.get('end_time')) or
                                 (isinstance(card, dict) and card.get('end_time'))])
        
        # حساب إجمالي مبلغ الفواتير
        total_amount = 0
        for card in self.invoice_cards.values():
            if hasattr(card, 'invoice_data'):
                total_amount += float(card.invoice_data.get('total_amount', 0))
            elif isinstance(card, dict):
                total_amount += float(card.get('total_amount', 0))
        
        # حساب إجمالي مبلغ الفواتير المغلقة
        closed_amount = 0
        for card in self.invoice_cards.values():
            if hasattr(card, 'invoice_data') and card.invoice_data.get('end_time'):
                closed_amount += float(card.invoice_data.get('total_amount', 0))
            elif isinstance(card, dict) and card.get('end_time'):
                closed_amount += float(card.get('total_amount', 0))
        
        # حساب الفواتير المدفوعة نقداً
        cash_invoices = 0
        cash_amount = 0
        for card in self.invoice_cards.values():
            if hasattr(card, 'invoice_data'):
                invoice_data = card.invoice_data
            elif isinstance(card, dict):
                invoice_data = card
            else:
                continue
                
            # التحقق من أن الفاتورة مغلقة ومدفوعة نقداً
            # استخدام القيمة الأصلية أو الافتراضية
            paid_by_original = invoice_data.get('paid_by_original', 'cash')
            if invoice_data.get('end_time') and paid_by_original == 'cash':
                cash_invoices += 1
                cash_amount += float(invoice_data.get('total_amount', 0))
        
        # حساب الفواتير المدفوعة من حساب العميل
        customer_balance_invoices = 0
        customer_balance_amount = 0
        for card in self.invoice_cards.values():
            if hasattr(card, 'invoice_data'):
                invoice_data = card.invoice_data
            elif isinstance(card, dict):
                invoice_data = card
            else:
                continue
                
            # التحقق من أن الفاتورة مغلقة ومدفوعة من حساب العميل
            # استخدام القيمة الأصلية أو الافتراضية
            paid_by_original = invoice_data.get('paid_by_original', 'cash')
            if invoice_data.get('end_time') and paid_by_original == 'customer_balance':
                customer_balance_invoices += 1
                customer_balance_amount += float(invoice_data.get('total_amount', 0))
        
        # إنشاء الرسالة التفصيلية
        message = "📊 تقرير إجمالي الفواتير\n"
        message += "=" * 40 + "\n\n"
        
        # إجمالي الفواتير
        message += f"📋 إجمالي الفواتير المعروضة: {total_invoices}\n"
        message += f"✅ إجمالي الفواتير المغلقة: {closed_invoices}\n\n"
        
        # الفواتير المدفوعة نقداً
        message += f"💰 الفواتير المدفوعة نقداً:\n"
        message += f"   • العدد: {cash_invoices} فاتورة\n"
        message += f"   • المبلغ: {cash_amount:.2f} جنيه\n\n"
        
        # الفواتير المدفوعة من حساب العميل
        message += f"💳 الفواتير المدفوعة من حساب العميل:\n"
        message += f"   • العدد: {customer_balance_invoices} فاتورة\n"
        message += f"   • المبلغ: {customer_balance_amount:.2f} جنيه\n\n"
        
        # الإجماليات
        message += f"📈 الإجماليات:\n"
        message += f"   • إجمالي مبلغ الفواتير المغلقة: {closed_amount:.2f} جنيه\n"
        message += f"   • إجمالي مبلغ جميع الفواتير: {total_amount:.2f} جنيه\n\n"
        
        # التحقق من التطابق
        total_payment_methods = cash_amount + customer_balance_amount
        if abs(closed_amount - total_payment_methods) < 0.01:  # تحمل خطأ صغير للفاصلة العشرية
            message += "✅ تم التحقق من تطابق المبالغ"
        else:
            message += f"⚠️ ملاحظة: هناك فرق في المبالغ ({closed_amount:.2f} vs {total_payment_methods:.2f})"
        
        QMessageBox.information(self, "إجمالي الفواتير", message)
    
    
    # تم إزالة دالة apply_filters الثانية
    
    def start_timer(self):
        """بدء التايمر لتحديث الفواتير"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_invoices_status)
        self.timer.start(30000)  # كل 30 ثانية
    
    def update_invoices_status(self):
        """تحديث حالة الفواتير"""
        for card in self.invoice_cards.values():
            # التحقق من نوع الكائن قبل استدعاء update_display
            if hasattr(card, 'update_display'):
                card.update_display()
            # إذا كان dict، لا نحتاج لتحديثه

class InvoiceDetailsDialog(QDialog):
    """نافذة تفاصيل الفاتورة"""
    
    def __init__(self, invoice_data, current_user):
        super().__init__()
        self.invoice_data = invoice_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(f"تفاصيل الفاتورة رقم {self.invoice_data['id']}")
        self.setFixedSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل الفاتورة رقم {self.invoice_data['id']}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات التفاصيل
        tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_info_tab = QWidget()
        basic_layout = QFormLayout(basic_info_tab)
        
        # معلومات الفاتورة
        basic_layout.addRow("رقم الفاتورة:", QLabel(str(self.invoice_data['id'])))
        basic_layout.addRow("الجهاز:", QLabel(self.invoice_data.get('device_name', 'غير محدد')))
        basic_layout.addRow("كاشير البداية:", QLabel(self.invoice_data.get('cashier_open_name', 'غير محدد')))
        basic_layout.addRow("كاشير الإغلاق:", QLabel(self.invoice_data.get('cashier_close_name', 'غير محدد')))
        
        # ⭐ تحديد نوع الفاتورة مع تفاصيل التسعيرة المتقدمة - تم إصلاحه بالكامل
        pricing_type = self.invoice_data.get('pricing_type', 'غير محدد')  # المنسق للعرض
        pricing_type_original = self.invoice_data.get('pricing_type_original', 'single')  # ⭐ الأصلي من قاعدة البيانات
        pricing_details = self.invoice_data.get('pricing_details', {})
        
        if pricing_type_original == 'admin':
            basic_layout.addRow("نوع المعاملة:", QLabel("معاملة إدارية"))
        else:
            # عرض تفاصيل التسعيرة المتقدمة
            if pricing_details.get('has_advanced_pricing', False):
                # تسعيرة متقدمة
                single_cost = pricing_details.get('single_cost', 0)
                multi_cost = pricing_details.get('multi_cost', 0)
                
                if single_cost > 0 and multi_cost > 0:
                    # تسعيرة مختلطة
                    single_hours = pricing_details.get('single_hours', 0)
                    multi_hours = pricing_details.get('multi_hours', 0)
                    
                    # تحويل الساعات إلى تنسيق HH:MM:SS
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    
                    pricing_text = f"👤 فردي: {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه\n👥 جماعي: {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه"
                    pricing_label = QLabel(pricing_text)
                    pricing_label.setStyleSheet("""
                        font-size: 12px;
                        padding: 8px;
                        background-color: #e8f4fd;
                        border-radius: 5px;
                        border: 1px solid #bee5eb;
                    """)
                    basic_layout.addRow("تفاصيل التسعيرة:", pricing_label)
                elif single_cost > 0:
                    # فردي فقط
                    single_hours = pricing_details.get('single_hours', 0)
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    basic_layout.addRow("نوع التسعيرة:", QLabel(f"👤 فردي: {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه"))
                elif multi_cost > 0:
                    # جماعي فقط
                    multi_hours = pricing_details.get('multi_hours', 0)
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    basic_layout.addRow("نوع التسعيرة:", QLabel(f"👥 جماعي: {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه"))
                else:
                    basic_layout.addRow("نوع التسعيرة:", QLabel(pricing_type))
            else:
                # ⭐ تسعيرة تقليدية - تم إصلاح المشكلة هنا
                # استخدام pricing_type_original للتحقق من النوع الصحيح
                if pricing_type_original == 'single':
                    basic_layout.addRow("نوع التسعيرة:", QLabel("👤 فردي"))
                elif pricing_type_original == 'multi':
                    basic_layout.addRow("نوع التسعيرة:", QLabel("👥 جماعي"))
                elif pricing_type_original == 'mixed':
                    basic_layout.addRow("نوع التسعيرة:", QLabel("👤👥 فردي / جماعي"))
                else:
                    # عرض القيمة المنسقة إذا لم تتطابق مع أي من القيم المعروفة
                    basic_layout.addRow("نوع التسعيرة:", QLabel(pricing_type if pricing_type != 'غير محدد' else "👤 فردي"))
        
        start_time = self.invoice_data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        basic_layout.addRow("وقت البداية:", QLabel(start_time.strftime('%Y-%m-%d %H:%M')))
        
        end_time = self.invoice_data.get('end_time')
        if end_time:
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            basic_layout.addRow("وقت النهاية:", QLabel(end_time.strftime('%Y-%m-%d %H:%M')))
            
            # حساب المدة
            duration = end_time - start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            basic_layout.addRow("المدة:", QLabel(f"{hours}س {minutes}د"))
        else:
            basic_layout.addRow("وقت النهاية:", QLabel("لم تنته بعد"))
            
            # المدة الحالية
            duration = datetime.now() - start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            basic_layout.addRow("المدة الحالية:", QLabel(f"{hours}س {minutes}د"))
        
        basic_layout.addRow("سعر الجلسة:", QLabel(f"{self.invoice_data.get('session_price', 0)} جنيه"))
        basic_layout.addRow("إجمالي المنتجات:", QLabel(f"{self.invoice_data.get('products_total', 0)} جنيه"))
        basic_layout.addRow("المبلغ الإجمالي:", QLabel(f"{self.invoice_data.get('total_amount', 0)} جنيه"))
        basic_layout.addRow("طريقة الدفع:", QLabel(self.invoice_data.get('paid_by', 'نقدي')))
        
        customer_phone = self.invoice_data.get('customer_phone')
        if customer_phone:
            basic_layout.addRow("هاتف العميل:", QLabel(customer_phone))
        
        tab_widget.addTab(basic_info_tab, "المعلومات الأساسية")
        
        # تبويب المنتجات
        products_tab = QWidget()
        products_layout = QVBoxLayout(products_tab)
        
        # جدول المنتجات
        products_table = QTableWidget()
        products_table.setColumnCount(4)
        products_table.setHorizontalHeaderLabels(["المنتج", "الكمية", "السعر", "الإجمالي"])
        
        # تحميل المنتجات الحقيقية من قاعدة البيانات
        try:
            from models.invoice_model import InvoiceModel
            invoice_model = InvoiceModel()
            invoice_id = self.invoice_data.get('id')
            pricing_type = self.invoice_data.get('pricing_type', '')
            
            # التحقق من نوع الفاتورة
            if pricing_type == 'admin':
                # فاتورة معاملة عميل - تحميل من invoice_items
                from models.customer_transaction_invoice_model import CustomerTransactionInvoiceModel
                transaction_model = CustomerTransactionInvoiceModel()
                products = transaction_model.get_transaction_invoice_products(invoice_id)
            else:
                # فاتورة عادية - محاولة الحصول على منتجات الفاتورة
                products = invoice_model.get_invoice_products(invoice_id)
                
                if not products:
                    # إذا لم توجد منتجات في جدول invoice_products، جرب الحصول على منتجات الجلسة
                    products = invoice_model.get_invoice_session_products(invoice_id)
            
            if products:
                products_table.setRowCount(len(products))
                for row, product in enumerate(products):
                    # استخدام product_name إذا كان متوفراً، وإلا name
                    product_name = product.get('product_name') or product.get('name', 'غير محدد')
                    quantity = product.get('quantity', 0)
                    
                    # تحديد السعر والإجمالي بناءً على نوع البيانات
                    if 'unit_price' in product and 'total_price' in product:
                        # بيانات من session_products
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
                    products_table.setItem(row, 2, QTableWidgetItem(f"{unit_price} جنيه"))
                    products_table.setItem(row, 3, QTableWidgetItem(f"{total_price} جنيه"))
            else:
                # لا توجد منتجات
                products_table.setRowCount(1)
                if pricing_type == 'admin':
                    products_table.setItem(0, 0, QTableWidgetItem("معاملة إدارية - لا توجد منتجات"))
                else:
                    products_table.setItem(0, 0, QTableWidgetItem("لا توجد منتجات في هذه الفاتورة"))
                products_table.setItem(0, 1, QTableWidgetItem(""))
                products_table.setItem(0, 2, QTableWidgetItem(""))
                products_table.setItem(0, 3, QTableWidgetItem(""))
                
        except Exception as e:
            print(f"خطأ في تحميل منتجات الفاتورة: {e}")
            # عرض رسالة خطأ
            products_table.setRowCount(1)
            products_table.setItem(0, 0, QTableWidgetItem("خطأ في تحميل المنتجات"))
            products_table.setItem(0, 1, QTableWidgetItem(""))
            products_table.setItem(0, 2, QTableWidgetItem(""))
            products_table.setItem(0, 3, QTableWidgetItem(""))
        
        products_table.horizontalHeader().setStretchLastSection(True)
        products_layout.addWidget(products_table)
        
        tab_widget.addTab(products_tab, "المنتجات")
        
        layout.addWidget(tab_widget)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        if not self.invoice_data.get('end_time'):
            # فاتورة مفتوحة - يمكن إضافة منتجات أو إغلاقها
            add_product_btn = QPushButton("إضافة منتج")
            add_product_btn.setStyleSheet("background-color: #3498db;")
            button_layout.addWidget(add_product_btn)
            
            close_invoice_btn = QPushButton("إغلاق الفاتورة")
            close_invoice_btn.setStyleSheet("background-color: #e74c3c;")
            button_layout.addWidget(close_invoice_btn)
        
        if self.current_user.get('role') == 'admin':
            # المدير يمكنه حذف الفاتورة
            delete_btn = QPushButton("حذف الفاتورة")
            delete_btn.setStyleSheet("background-color: #e74c3c;")
            delete_btn.clicked.connect(self.delete_invoice)
            button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def delete_invoice(self):
        """حذف الفاتورة"""
        try:
            # التحقق من الصلاحية
            from utils.permission_checker import permission_checker
            
            # إذا كان المستخدم لديه صلاحية حذف فاتورة، لا نطلب كلمة مرور المدير
            if permission_checker.check_permission_or_admin(self.current_user, "delete_invoice"):
                # تأكيد الحذف مباشرة
                reply = QMessageBox.question(
                    self, 
                    "تأكيد الحذف", 
                    f"هل أنت متأكد من حذف الفاتورة رقم {self.invoice_data['id']}؟\n"
                    "هذا الإجراء لا يمكن التراجع عنه!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # حذف الفاتورة
                    from models.invoice_model import InvoiceModel
                    invoice_model = InvoiceModel()
                    
                    success = invoice_model.delete_invoice(
                        invoice_id=self.invoice_data['id'],
                        admin_password=None  # لا نحتاج كلمة مرور لأن لدينا الصلاحية
                    )
                    
                    if success:
                        QMessageBox.information(
                            self,
                            "تم الحذف بنجاح",
                            f"تم حذف الفاتورة رقم {self.invoice_data['id']} بنجاح!"
                        )
                        self.product_deleted.emit()  # إشارة لتحديث القائمة
                        self.accept()
                    else:
                        QMessageBox.warning(self, "خطأ", "فشل في حذف الفاتورة")
            else:
                # طلب كلمة مرور المدير
                from views.device_management import AdminPasswordDialog
                password_dialog = AdminPasswordDialog()
                
                if password_dialog.exec() == QDialog.Accepted:
                    # تأكيد الحذف
                    reply = QMessageBox.question(
                    self, 
                    "تأكيد الحذف", 
                    f"هل أنت متأكد من حذف الفاتورة رقم {self.invoice_data['id']}؟\n"
                    "هذا الإجراء لا يمكن التراجع عنه!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # حذف الفاتورة
                    from models.invoice_model import InvoiceModel
                    invoice_model = InvoiceModel()
                    
                    # الحصول على كلمة مرور المدير من النافذة
                    admin_password = password_dialog.get_password()
                    
                    success = invoice_model.delete_invoice(
                        invoice_id=self.invoice_data['id'],
                        admin_password=admin_password
                    )
                    
                    if success:
                        QMessageBox.information(
                            self, 
                            "تم الحذف", 
                            f"تم حذف الفاتورة رقم {self.invoice_data['id']} بنجاح"
                        )
                        
                        # إغلاق النافذة
                        self.accept()
                        
                        # تحديث نافذة إدارة الفواتير إذا كانت مفتوحة
                        self.update_invoice_management_window()
                    else:
                        QMessageBox.warning(
                            self, 
                            "خطأ في الحذف", 
                            "فشل في حذف الفاتورة. تحقق من كلمة مرور المدير أو تأكد من وجود الفاتورة."
                        )
                else:
                    # المستخدم ألغى إدخال كلمة المرور
                    print("تم إلغاء حذف الفاتورة")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "خطأ", 
                f"حدث خطأ أثناء حذف الفاتورة: {str(e)}"
            )
            print(f"خطأ في حذف الفاتورة: {e}")
    
    def update_invoice_management_window(self):
        """تحديث نافذة إدارة الفواتير إذا كانت مفتوحة"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم تحديث نافذة إدارة الفواتير بعد الحذف")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في تحديث نافذة إدارة الفواتير: {e}")

class NewInvoiceDialog(QDialog):
    """نافذة إنشاء فاتورة جديدة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("فاتورة جديدة")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("إنشاء فاتورة جديدة")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اختيار الجهاز
        self.device_combo = QComboBox()
        self.device_combo.addItems([
            "PS5 - 1", "PS5 - 2", "PS4 - 1", "PS4 - 2",
            "PC Gaming - 1", "PC Gaming - 2", "بينج بونج - 1", "بلياردو - 1"
        ])
        form_layout.addRow("الجهاز:", self.device_combo)
        
        # نوع التسعيرة
        self.pricing_combo = QComboBox()
        self.pricing_combo.addItems(["Single", "Multi", "Standard"])
        form_layout.addRow("نوع التسعيرة:", self.pricing_combo)
        
        # مدة الجلسة
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["نصف ساعة", "ساعة", "ساعتان", "وقت مفتوح"])
        form_layout.addRow("مدة الجلسة:", self.duration_combo)
        
        # طريقة الدفع
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["نقدي", "رصيد العميل"])
        form_layout.addRow("طريقة الدفع:", self.payment_combo)
        
        # هاتف العميل (إذا كان الدفع برصيد العميل)
        self.customer_phone_input = QLineEdit()
        self.customer_phone_input.setPlaceholderText("أدخل رقم هاتف العميل")
        form_layout.addRow("هاتف العميل:", self.customer_phone_input)
        
        layout.addLayout(form_layout)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
