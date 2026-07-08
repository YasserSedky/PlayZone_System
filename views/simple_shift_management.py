"""
واجهة إدارة الورديات المبسطة
Simple Shift Management Interface
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
    QSplitter, QTabWidget, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SimpleShiftManagementWindow(QMainWindow):
    """نافذة إدارة الورديات المبسطة"""
    
    # إشارات
    shift_started = Signal(dict)
    shift_ended = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        self.load_current_shift()
    
    def setup_timer(self):
        """إعداد التايمر لتحديث البيانات"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_shift_data)
        self.timer.start(5000)  # كل 5 ثواني للتحديث الفوري
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الورديات - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1000, 700)
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
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
    
    def create_header(self, parent_layout):
        """إنشاء شريط العنوان"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #3498db;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # عنوان الصفحة
        title_label = QLabel("إدارة الورديات")
        title_label.setStyleSheet("""
            font-size: 24px;
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
        start_shift_btn = QPushButton("بدء وردية جديدة")
        start_shift_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 20px 40px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #229954;
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
        self.create_data_area(layout)
        
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
        end_shift_btn = QPushButton("إنهاء الوردية")
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
    
    def create_data_area(self, parent_layout):
        """إنشاء منطقة البيانات"""
        data_frame = QFrame()
        data_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        data_layout = QVBoxLayout(data_frame)
        
        # عنوان البيانات
        data_title = QLabel("بيانات الوردية الحالية")
        data_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        """)
        data_layout.addWidget(data_title)
        
        # إحصائيات سريعة - الصف الأول
        stats_layout1 = QHBoxLayout()
        
        # إجمالي الفواتير
        self.invoices_count_label = QLabel("0")
        self.invoices_count_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #27ae60;
            background-color: #d5f4e6;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        invoices_label = QLabel("إجمالي الفواتير")
        invoices_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        invoices_layout = QVBoxLayout()
        invoices_layout.addWidget(self.invoices_count_label)
        invoices_layout.addWidget(invoices_label)
        stats_layout1.addLayout(invoices_layout)
        
        # الفواتير النقدية
        self.cash_invoices_label = QLabel("0")
        self.cash_invoices_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #f39c12;
            background-color: #fef9e7;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        cash_invoices_text_label = QLabel("فواتير نقدية")
        cash_invoices_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        cash_invoices_layout = QVBoxLayout()
        cash_invoices_layout.addWidget(self.cash_invoices_label)
        cash_invoices_layout.addWidget(cash_invoices_text_label)
        stats_layout1.addLayout(cash_invoices_layout)
        
        # فواتير العملاء
        self.customer_invoices_label = QLabel("0")
        self.customer_invoices_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #9b59b6;
            background-color: #f4ecf7;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        customer_invoices_text_label = QLabel("فواتير عملاء")
        customer_invoices_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        customer_invoices_layout = QVBoxLayout()
        customer_invoices_layout.addWidget(self.customer_invoices_label)
        customer_invoices_layout.addWidget(customer_invoices_text_label)
        stats_layout1.addLayout(customer_invoices_layout)
        
        data_layout.addLayout(stats_layout1)
        
        # إحصائيات سريعة - الصف الثاني
        stats_layout2 = QHBoxLayout()
        
        # إجمالي الإيرادات
        self.revenue_label = QLabel("0.00")
        self.revenue_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #3498db;
            background-color: #d6eaf8;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        revenue_text_label = QLabel("إجمالي الإيرادات")
        revenue_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        revenue_layout = QVBoxLayout()
        revenue_layout.addWidget(self.revenue_label)
        revenue_layout.addWidget(revenue_text_label)
        stats_layout2.addLayout(revenue_layout)
        
        # إيرادات نقدية
        self.cash_revenue_label = QLabel("0.00")
        self.cash_revenue_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #e67e22;
            background-color: #fdf2e9;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        cash_revenue_text_label = QLabel("إيرادات نقدية")
        cash_revenue_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        cash_revenue_layout = QVBoxLayout()
        cash_revenue_layout.addWidget(self.cash_revenue_label)
        cash_revenue_layout.addWidget(cash_revenue_text_label)
        stats_layout2.addLayout(cash_revenue_layout)
        
        # إيرادات عملاء
        self.customer_revenue_label = QLabel("0.00")
        self.customer_revenue_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #8e44ad;
            background-color: #e8daef;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        customer_revenue_text_label = QLabel("إيرادات عملاء")
        customer_revenue_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        customer_revenue_layout = QVBoxLayout()
        customer_revenue_layout.addWidget(self.customer_revenue_label)
        customer_revenue_layout.addWidget(customer_revenue_text_label)
        stats_layout2.addLayout(customer_revenue_layout)
        
        data_layout.addLayout(stats_layout2)
        
        # إحصائيات سريعة - الصف الثالث
        stats_layout3 = QHBoxLayout()
        
        # إجمالي المصروفات
        self.expenses_label = QLabel("0.00")
        self.expenses_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #e74c3c;
            background-color: #fadbd8;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        expenses_text_label = QLabel("إجمالي المصروفات")
        expenses_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        expenses_layout = QVBoxLayout()
        expenses_layout.addWidget(self.expenses_label)
        expenses_layout.addWidget(expenses_text_label)
        stats_layout3.addLayout(expenses_layout)
        
        # صافي الكاش
        self.net_cash_label = QLabel("0.00")
        self.net_cash_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #27ae60;
            background-color: #d5f4e6;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        net_cash_text_label = QLabel("صافي الكاش")
        net_cash_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        net_cash_layout = QVBoxLayout()
        net_cash_layout.addWidget(self.net_cash_label)
        net_cash_layout.addWidget(net_cash_text_label)
        stats_layout3.addLayout(net_cash_layout)
        
        # صافي الربح
        self.profit_label = QLabel("0.00")
        self.profit_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #8e44ad;
            background-color: #e8daef;
            padding: 10px;
            border-radius: 5px;
            min-width: 60px;
            text-align: center;
        """)
        profit_text_label = QLabel("صافي الربح")
        profit_text_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        profit_layout = QVBoxLayout()
        profit_layout.addWidget(self.profit_label)
        profit_layout.addWidget(profit_text_label)
        stats_layout3.addLayout(profit_layout)
        
        data_layout.addLayout(stats_layout3)
        
        parent_layout.addWidget(data_frame)
    
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
        refresh_btn = QPushButton("تحديث البيانات")
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
            
            # محاولة الحصول على الوردية النشطة
            try:
                from controllers.shift_controller import ShiftController
                shift_controller = ShiftController()
                active_shift = shift_controller.get_active_shift(cashier_id)
                
                if active_shift:
                    self.current_shift_data = active_shift
                    self.show_active_shift()
                else:
                    self.current_shift_data = None
                    self.show_no_shift()
            except Exception as e:
                print(f"خطأ في تحميل الوردية: {e}")
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
            
            # التبديل إلى صفحة الوردية النشطة
            self.content_stack.setCurrentWidget(self.active_shift_page)
            
            # تحديث البيانات
            self.refresh_shift_data()
    
    def show_no_shift(self):
        """عرض صفحة عدم وجود وردية"""
        # التبديل إلى صفحة عدم وجود وردية
        self.content_stack.setCurrentWidget(self.no_shift_page)
    
    def start_new_shift(self):
        """بدء وردية جديدة"""
        # رسالة تأكيد
        reply = QMessageBox.question(
            self, 
            "تأكيد بدء وردية جديدة", 
            "هل أنت متأكد من بدء وردية جديدة؟\n\nسيتم:\n• إنهاء جميع الورديات النشطة\n• إخفاء جميع الفواتير والمصروفات السابقة\n• بدء وردية جديدة نظيفة",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        dialog = StartShiftDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            try:
                cashier_id = dialog.get_cashier_id()
                shift_name = dialog.get_shift_name()
                notes = dialog.get_notes()
                
                # بدء الوردية
                try:
                    from controllers.shift_controller import ShiftController
                    shift_controller = ShiftController()
                    
                    result = shift_controller.start_shift_with_clear_data(
                        cashier_id=cashier_id,
                        shift_name=shift_name,
                        notes=notes
                    )
                    
                    if result['success']:
                        QMessageBox.information(self, "نجح", f"تم بدء وردية جديدة بنجاح!\n\nكاشير البداية: {dialog.get_cashier_name()}\nاسم الوردية: {shift_name}")
                        self.load_current_shift()
                        self.shift_started.emit(result.get('shift_data', {}))
                        
                        # إشعار واجهات أخرى بتحديث البيانات
                        self.notify_data_refresh()
                        
                        # تحديث البيانات فوراً
                        self.refresh_shift_data()
                        
                        # التبديل التلقائي للكاشير
                        self.switch_to_cashier(cashier_id)
                        
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
                        QMessageBox.warning(self, "خطأ", result['message'])
                        
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"خطأ في بدء الوردية: {str(e)}")
                    
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في بدء الوردية: {str(e)}")
    
    def end_current_shift(self):
        """إنهاء الوردية الحالية"""
        if not self.current_shift_data:
            return
        
        dialog = EndShiftDialog(self.current_shift_data, self.current_user)
        if dialog.exec() == QDialog.Accepted:
            try:
                shift_id = self.current_shift_data['id']
                notes = dialog.get_notes()
                
                try:
                    from controllers.shift_controller import ShiftController
                    shift_controller = ShiftController()
                    
                    result = shift_controller.end_shift(shift_id, notes)
                    
                    if result['success']:
                        QMessageBox.information(self, "نجح", result['message'])
                        self.load_current_shift()
                        self.shift_ended.emit(self.current_shift_data)
                    else:
                        QMessageBox.warning(self, "خطأ", result['message'])
                        
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"خطأ في إنهاء الوردية: {str(e)}")
                    
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في إنهاء الوردية: {str(e)}")
    
    def refresh_shift_data(self):
        """تحديث بيانات الوردية"""
        try:
            cashier_id = self.current_user.get('id')
            if not cashier_id:
                return
            
            try:
                from controllers.shift_controller import ShiftController
                shift_controller = ShiftController()
                
                # الحصول على بيانات الوردية
                shift_data = shift_controller.get_cashier_shift_data(cashier_id)
                
                # تحديث الإحصائيات
                stats = shift_data.get('statistics', {})
                
                # الصف الأول - عدد الفواتير
                self.invoices_count_label.setText(str(stats.get('total_invoices', 0)))
                self.cash_invoices_label.setText(str(stats.get('cash_invoices_count', 0)))
                self.customer_invoices_label.setText(str(stats.get('customer_invoices_count', 0)))
                
                # الصف الثاني - الإيرادات
                self.revenue_label.setText(f"{stats.get('total_revenue', 0):.2f}")
                self.cash_revenue_label.setText(f"{stats.get('cash_revenue', 0):.2f}")
                self.customer_revenue_label.setText(f"{stats.get('customer_revenue', 0):.2f}")
                
                # الصف الثالث - المصروفات وصافي الكاش والربح
                self.expenses_label.setText(f"{stats.get('total_expense_amount', 0):.2f}")
                self.net_cash_label.setText(f"{stats.get('net_cash', 0):.2f}")
                self.profit_label.setText(f"{stats.get('net_profit', 0):.2f}")
                
                self.last_update_label.setText(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
                
            except Exception as e:
                print(f"خطأ في تحديث البيانات: {e}")
                
        except Exception as e:
            print(f"خطأ في تحديث بيانات الوردية: {e}")
    
    def notify_data_refresh(self):
        """إشعار واجهات أخرى بتحديث البيانات"""
        try:
            # إرسال إشارة لتحديث البيانات في واجهات أخرى
            self.shift_started.emit({'action': 'data_refresh'})
            
            # تحديث واجهة الفواتير مباشرة
            try:
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'invoice_management'):
                        parent.invoice_management.load_invoices()
                        print("تم تحديث واجهة الفواتير من إدارة الورديات")
                        break
                    parent = parent.parent()
            except Exception as e:
                print(f"خطأ في تحديث واجهة الفواتير من إدارة الورديات: {e}")
                
        except Exception as e:
            print(f"خطأ في إشعار تحديث البيانات: {e}")
    
    def switch_to_cashier(self, cashier_id):
        """التبديل التلقائي للكاشير"""
        try:
            # الحصول على بيانات الكاشير
            from models.user_model import UserModel
            user_model = UserModel()
            cashier = user_model.get_user_by_id(cashier_id)
            
            if cashier:
                # تحديث المستخدم الحالي
                self.current_user = cashier
                
                # إشعار لوحة التحكم بالتبديل
                if hasattr(self, 'parent') and hasattr(self.parent(), 'switch_cashier'):
                    self.parent().switch_cashier(cashier)
                
                print(f"تم التبديل التلقائي للكاشير: {cashier.get('username')}")
            else:
                print(f"لم يتم العثور على الكاشير: {cashier_id}")
                
        except Exception as e:
            print(f"خطأ في التبديل التلقائي للكاشير: {e}")

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
        title_label = QLabel("بدء وردية جديدة")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اختيار الكاشير (لجميع المستخدمين)
        self.cashier_combo = QComboBox()
        self.cashier_combo.setStyleSheet("font-size: 14px; padding: 5px;")
        self.load_cashiers()
        form_layout.addRow("كاشير البداية:", self.cashier_combo)
        
        # كلمة مرور الكاشير
        self.cashier_password_input = QLineEdit()
        self.cashier_password_input.setEchoMode(QLineEdit.Password)
        self.cashier_password_input.setPlaceholderText("أدخل كلمة مرور الكاشير")
        self.cashier_password_input.setStyleSheet("font-size: 14px; padding: 5px;")
        form_layout.addRow("كلمة مرور الكاشير:", self.cashier_password_input)
        
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
        return self.cashier_combo.currentData()
    
    def get_cashier_name(self):
        """الحصول على اسم الكاشير المختار"""
        return self.cashier_combo.currentText()
    
    def get_cashier_password(self):
        """الحصول على كلمة مرور الكاشير"""
        return self.cashier_password_input.text().strip()
    
    def get_shift_name(self):
        """الحصول على اسم الوردية"""
        return self.shift_name_input.text().strip()
    
    def get_notes(self):
        """الحصول على الملاحظات"""
        return self.notes_input.toPlainText().strip()
    
    def validate_cashier_password(self):
        """التحقق من كلمة مرور الكاشير"""
        try:
            cashier_id = self.get_cashier_id()
            password = self.get_cashier_password()
            
            if not password:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة مرور الكاشير")
                return False
            
            # التحقق من كلمة المرور
            from models.user_model import UserModel
            user_model = UserModel()
            user = user_model.authenticate_user_by_id(cashier_id, password)
            
            if user:
                return True
            else:
                QMessageBox.warning(self, "خطأ", "كلمة مرور الكاشير غير صحيحة")
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في التحقق من كلمة المرور: {str(e)}")
            return False
    
    def accept(self):
        """تأكيد البيانات"""
        if not self.get_shift_name():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم الوردية")
            return
        
        # التحقق من كلمة مرور الكاشير
        if not self.validate_cashier_password():
            return
        
        super().accept()

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
        title_label = QLabel("إنهاء وردية")
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
    
    window = SimpleShiftManagementWindow(test_user)
    window.show()
    sys.exit(app.exec())
