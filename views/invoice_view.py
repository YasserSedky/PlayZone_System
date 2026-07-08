"""
عرض وإدارة الفواتير
Invoice View and Management
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QMessageBox,
    QGroupBox, QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.invoice_model import InvoiceModel
from models.device_model import DeviceModel
from utils.helpers import format_currency, format_time
from utils.notifications import show_success, show_error

class InvoiceViewWindow(QMainWindow):
    """نافذة عرض وإدارة الفواتير"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.invoice_model = InvoiceModel()
        self.device_model = DeviceModel()
        self.setup_ui()
        self.load_invoices()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الفواتير - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1200, 800)
        
        # الـ widget المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # عنوان النافذة
        title_label = QLabel("إدارة الفواتير")
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
        
        # أدوات البحث والتصفية
        self.create_search_panel(main_layout)
        
        # جدول الفواتير
        self.create_invoices_table(main_layout)
        
        # أزرار التحكم
        self.create_control_buttons(main_layout)
    
    def create_search_panel(self, parent_layout):
        """إنشاء لوحة البحث والتصفية"""
        search_group = QGroupBox("البحث والتصفية")
        search_layout = QGridLayout(search_group)
        
        # البحث بالرقم
        search_layout.addWidget(QLabel("رقم الفاتورة:"), 0, 0)
        self.invoice_id_input = QLineEdit()
        self.invoice_id_input.setPlaceholderText("أدخل رقم الفاتورة")
        search_layout.addWidget(self.invoice_id_input, 0, 1)
        
        # البحث بالجهاز
        search_layout.addWidget(QLabel("الجهاز:"), 0, 2)
        self.device_combo = QComboBox()
        self.device_combo.addItem("جميع الأجهزة", "")
        search_layout.addWidget(self.device_combo, 0, 3)
        
        # البحث بالكاشير
        search_layout.addWidget(QLabel("الكاشير:"), 1, 0)
        self.cashier_combo = QComboBox()
        self.cashier_combo.addItem("جميع الكاشيرز", "")
        search_layout.addWidget(self.cashier_combo, 1, 1)
        
        # البحث بالتاريخ
        search_layout.addWidget(QLabel("من تاريخ:"), 1, 2)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        search_layout.addWidget(self.start_date_input, 1, 3)
        
        search_layout.addWidget(QLabel("إلى تاريخ:"), 2, 0)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        search_layout.addWidget(self.end_date_input, 2, 1)
        
        # زر البحث
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.search_invoices)
        search_layout.addWidget(search_btn, 2, 2)
        
        # زر إعادة تعيين
        reset_btn = QPushButton("إعادة تعيين")
        reset_btn.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_btn, 2, 3)
        
        parent_layout.addWidget(search_group)
    
    def create_invoices_table(self, parent_layout):
        """إنشاء جدول الفواتير"""
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(9)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "الجهاز", "الكاشير", "وقت البداية", 
            "وقت النهاية", "المدة", "المبلغ", "تفاصيل التسعيرة", "الحالة"
        ])
        
        # إعداد الجدول
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        parent_layout.addWidget(self.invoices_table)
    
    def create_control_buttons(self, parent_layout):
        """إنشاء أزرار التحكم"""
        controls_layout = QHBoxLayout()
        
        # زر تحديث
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_invoices)
        controls_layout.addWidget(refresh_btn)
        
        # زر طباعة
        print_btn = QPushButton("طباعة")
        print_btn.clicked.connect(self.print_invoice)
        controls_layout.addWidget(print_btn)
        
        # زر تصدير
        export_btn = QPushButton("تصدير")
        export_btn.clicked.connect(self.export_invoices)
        controls_layout.addWidget(export_btn)
        
        controls_layout.addStretch()
        
        parent_layout.addLayout(controls_layout)
    
    def load_invoices(self):
        """تحميل الفواتير"""
        try:
            # تحميل قوائم المراجع
            self.load_device_list()
            self.load_cashier_list()
            
            # تحميل الفواتير
            invoices = self.invoice_model.get_invoices_by_cashier(
                cashier_id=self.current_user['id']
            )
            
            self.display_invoices(invoices)
            
        except Exception as e:
            show_error(f"خطأ في تحميل الفواتير: {str(e)}")
    
    def load_device_list(self):
        """تحميل قائمة الأجهزة"""
        try:
            devices = self.device_model.get_all_devices()
            
            self.device_combo.clear()
            self.device_combo.addItem("جميع الأجهزة", "")
            
            for device in devices:
                self.device_combo.addItem(device['name'], device['id'])
                
        except Exception as e:
            pass
    
    def load_cashier_list(self):
        """تحميل قائمة الكاشيرز"""
        try:
            from models.user_model import UserModel
            user_model = UserModel()
            cashiers = user_model.get_cashiers()
            
            self.cashier_combo.clear()
            self.cashier_combo.addItem("جميع الكاشيرز", "")
            
            for cashier in cashiers:
                self.cashier_combo.addItem(cashier['username'], cashier['id'])
                
        except Exception as e:
            pass
    
    def display_invoices(self, invoices):
        """عرض الفواتير في الجدول"""
        try:
            self.invoices_table.setRowCount(len(invoices))
            
            for row, invoice in enumerate(invoices):
                self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice['id'])))
                self.invoices_table.setItem(row, 1, QTableWidgetItem(invoice.get('device_name', '')))
                self.invoices_table.setItem(row, 2, QTableWidgetItem(invoice.get('cashier_open_name', '')))
                self.invoices_table.setItem(row, 3, QTableWidgetItem(format_time(invoice['start_time'], 'short')))
                
                # وقت النهاية
                end_time = invoice.get('end_time')
                if end_time:
                    self.invoices_table.setItem(row, 4, QTableWidgetItem(format_time(end_time, 'short')))
                else:
                    self.invoices_table.setItem(row, 4, QTableWidgetItem("نشطة"))
                
                # المدة
                if end_time:
                    from datetime import datetime
                    duration = end_time - invoice['start_time']
                    duration_str = f"{int(duration.total_seconds() / 60)} دقيقة"
                else:
                    duration_str = "جارية"
                
                self.invoices_table.setItem(row, 5, QTableWidgetItem(duration_str))
                self.invoices_table.setItem(row, 6, QTableWidgetItem(format_currency(invoice['total_amount'])))
                
                # تفاصيل التسعيرة
                pricing_details = invoice.get('pricing_details', {})
                pricing_text = self.format_pricing_details(pricing_details)
                self.invoices_table.setItem(row, 7, QTableWidgetItem(pricing_text))
                
                # الحالة
                status = "مكتملة" if end_time else "نشطة"
                self.invoices_table.setItem(row, 8, QTableWidgetItem(status))
            
        except Exception as e:
            show_error(f"خطأ في عرض الفواتير: {str(e)}")
    
    def format_pricing_details(self, pricing_details):
        """تنسيق تفاصيل التسعيرة للعرض"""
        try:
            if not pricing_details:
                return "غير متوفر"
            
            if pricing_details.get('has_advanced_pricing', False):
                # تسعيرة متقدمة - عرض التفاصيل
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
                    
                    return f"👤 {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه\n👥 {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه"
                    
                elif single_cost > 0:
                    # فردي فقط
                    single_hours = pricing_details.get('single_hours', 0)
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    return f"👤 {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه"
                    
                elif multi_cost > 0:
                    # جماعي فقط
                    multi_hours = pricing_details.get('multi_hours', 0)
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    return f"👥 {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه"
                else:
                    return "لا توجد تكلفة"
            else:
                # ⭐ تسعيرة تقليدية - استخدام pricing_type_original للعرض الصحيح
                pricing_type_original = pricing_details.get('pricing_type_original', pricing_details.get('pricing_type', 'single'))
                
                # ⭐ دعم جميع أنواع التسعيرة
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
    
    def search_invoices(self):
        """البحث في الفواتير"""
        try:
            # جمع معايير البحث
            search_criteria = {}
            
            # رقم الفاتورة
            invoice_id = self.invoice_id_input.text().strip()
            if invoice_id:
                search_criteria['invoice_id'] = invoice_id
            
            # الجهاز
            device_id = self.device_combo.currentData()
            if device_id:
                search_criteria['device_id'] = device_id
            
            # الكاشير
            cashier_id = self.cashier_combo.currentData()
            if cashier_id:
                search_criteria['cashier_id'] = cashier_id
            
            # التاريخ
            start_date = self.start_date_input.date().toPython()
            end_date = self.end_date_input.date().toPython()
            
            # البحث
            invoices = self.invoice_model.search_invoices(
                search_term=invoice_id or "",
                start_date=start_date,
                end_date=end_date
            )
            
            # تصفية النتائج حسب المعايير الإضافية
            if device_id:
                invoices = [inv for inv in invoices if inv.get('device_id') == device_id]
            
            if cashier_id:
                invoices = [inv for inv in invoices if inv.get('cashier_open') == cashier_id or inv.get('cashier_close') == cashier_id]
            
            self.display_invoices(invoices)
            
        except Exception as e:
            show_error(f"خطأ في البحث: {str(e)}")
    
    def reset_search(self):
        """إعادة تعيين البحث"""
        self.invoice_id_input.clear()
        self.device_combo.setCurrentIndex(0)
        self.cashier_combo.setCurrentIndex(0)
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDate(QDate.currentDate())
        
        self.load_invoices()
    
    def print_invoice(self):
        """طباعة الفاتورة"""
        try:
            current_row = self.invoices_table.currentRow()
            if current_row < 0:
                show_error("يرجى اختيار فاتورة للطباعة")
                return
            
            invoice_id = self.invoices_table.item(current_row, 0).text()
            show_success(f"سيتم طباعة الفاتورة رقم {invoice_id}")
            
        except Exception as e:
            show_error(f"خطأ في الطباعة: {str(e)}")
    
    def export_invoices(self):
        """تصدير الفواتير"""
        try:
            show_success("سيتم تصدير الفواتير")
            
        except Exception as e:
            show_error(f"خطأ في التصدير: {str(e)}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = InvoiceViewWindow(test_user)
    window.show()
    sys.exit(app.exec())
