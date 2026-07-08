"""
واجهة إدارة المصروفات
Expense Management Interface
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
    QSplitter, QTabWidget, QProgressBar, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.expense_model import ExpenseModel
from models.shift_model import ShiftModel

class ExpenseCard(QFrame):
    """كارت المصروف"""
    
    # إشارات
    expense_clicked = Signal(dict)  # بيانات المصروف
    
    def __init__(self, expense_data):
        super().__init__()
        self.expense_data = expense_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(260, 190)  # حجم أصغر قليلاً
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # عنوان المصروف
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # السبب
        self.reason_label = QLabel("")
        self.reason_label.setAlignment(Qt.AlignCenter)
        self.reason_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.reason_label)
        
        # المبلغ
        self.amount_label = QLabel("")
        self.amount_label.setAlignment(Qt.AlignCenter)
        self.amount_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.amount_label)
        
        # الكاشير
        self.cashier_label = QLabel("")
        self.cashier_label.setAlignment(Qt.AlignCenter)
        self.cashier_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.cashier_label)
        
        # حالة المصروف
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
    
    def update_display(self):
        """تحديث عرض الكارت"""
        # تحديث السبب
        reason = self.expense_data.get('reason', 'غير محدد')
        self.title_label.setText(f"💰 {reason}")
        
        # تحديث التفاصيل
        self.reason_label.setText(f"السبب: {reason}")
        
        # تحديث المبلغ
        amount = float(self.expense_data.get('amount', 0))
        self.amount_label.setText(f"💸 {amount} جنيه")
        
        # تحديث الكاشير
        cashier_name = self.expense_data.get('cashier_name', 'غير محدد')
        self.cashier_label.setText(f"👤 {cashier_name}")
        
        # تحديث حالة المصروف واللون
        if amount >= 200:
            self.status_label.setText("مصروف كبير!")
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
        elif amount >= 100:
            self.status_label.setText("مصروف متوسط!")
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
        elif amount >= 50:
            self.status_label.setText("مصروف متوسط")
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #3498db;
                    color: white;
                    border: 2px solid #2980b9;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setText("مصروف صغير")
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
            self.expense_clicked.emit(self.expense_data)

class ExpenseManagementWindow(QMainWindow):
    """نافذة إدارة المصروفات"""
    
    # إشارات
    expense_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.expense_cards = {}
        self.expense_model = ExpenseModel()
        self.shift_model = ShiftModel()
        self.setup_ui()
        self.setup_connections()
        self.load_expenses()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة المصروفات - نظام إدارة محل بلايستيشن")
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
        
        # منطقة المصروفات (في الأعلى مثل قسم المخزون)
        self.create_expenses_area(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("💰 إدارة المصروفات")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # أزرار التحكم
        self.add_expense_btn = QPushButton("إضافة مصروف")
        self.add_expense_btn.setStyleSheet("background-color: #e74c3c;")
        self.add_expense_btn.clicked.connect(self.add_expense)
        toolbar_layout.addWidget(self.add_expense_btn)
        
        
        parent_layout.addLayout(toolbar_layout)
    
    
    def create_expenses_area(self, parent_layout):
        """إنشاء منطقة المصروفات"""
        # مجموعة المصروفات
        expenses_group = QGroupBox("المصروفات")
        expenses_layout = QVBoxLayout(expenses_group)
        
        # منطقة التمرير للمصروفات
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # الـ widget المحتوي للمصروفات
        self.expenses_widget = QWidget()
        self.expenses_widget.setMinimumSize(800, 600)  # حد أدنى للحجم
        self.expenses_layout = QGridLayout(self.expenses_widget)
        self.expenses_layout.setSpacing(15)
        self.expenses_layout.setContentsMargins(15, 15, 15, 15)  # هوامش مناسبة
        self.expenses_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # بدء من أعلى الصفحة
        
        # إضافة رسالة ترحيب
        self.welcome_label = QLabel("مرحباً بك في قسم المصروفات\nاضغط على 'إضافة مصروف' لبدء إضافة المصروفات")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("""
            font-size: 18px;
            color: #7f8c8d;
            font-weight: bold;
            padding: 50px;
            background-color: #ecf0f1;
            border-radius: 10px;
            border: 2px dashed #bdc3c7;
        """)
        self.expenses_layout.addWidget(self.welcome_label, 0, 0, 1, 5)
        
        scroll_area.setWidget(self.expenses_widget)
        expenses_layout.addWidget(scroll_area)
        
        parent_layout.addWidget(expenses_group)
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات المصروفات")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات المصروفات
        self.total_expenses_label = QLabel("إجمالي المصروفات: 0")
        self.total_expenses_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_expenses_label)
        
        self.small_expenses_label = QLabel("صغيرة: 0")
        self.small_expenses_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.small_expenses_label)
        
        self.medium_expenses_label = QLabel("متوسطة: 0")
        self.medium_expenses_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(self.medium_expenses_label)
        
        self.large_expenses_label = QLabel("كبيرة: 0")
        self.large_expenses_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.large_expenses_label)
        
        self.total_amount_label = QLabel("إجمالي المبلغ: 0 جنيه")
        self.total_amount_label.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold; background-color: #fdf2f2; padding: 8px; border-radius: 5px; border: 2px solid #e74c3c;")
        stats_layout.addWidget(self.total_amount_label)
        
        # إجمالي مصروفات الوردية الحالية
        self.shift_expenses_label = QLabel("مصروفات الوردية: 0 جنيه")
        self.shift_expenses_label.setStyleSheet("font-size: 16px; color: #27ae60; font-weight: bold; background-color: #f0f8f0; padding: 8px; border-radius: 5px; border: 2px solid #27ae60;")
        stats_layout.addWidget(self.shift_expenses_label)
        
        parent_layout.addWidget(stats_group)
    
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
    
    def load_expenses(self):
        """تحميل مصروفات الوردية الحالية فقط"""
        try:
            # مسح المصروفات الموجودة
            for i in reversed(range(self.expenses_layout.count())):
                self.expenses_layout.itemAt(i).widget().setParent(None)
            
            self.expense_cards.clear()
            
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
            
            # الحصول على مصروفات الوردية المشتركة
            from controllers.shift_controller import ShiftController
            shift_controller = ShiftController()
            
            # الحصول على بيانات الوردية المشتركة
            shift_data = shift_controller.get_cashier_shift_data()
            expenses = shift_data.get('expenses', [])
            
            # إخفاء رسالة الترحيب إذا كان هناك مصروفات
            if hasattr(self, 'welcome_label'):
                self.welcome_label.setVisible(len(expenses) == 0)
            
            # إنشاء كروت المصروفات
            row = 1 if len(expenses) > 0 else 0  # البدء من الصف الثاني إذا كان هناك مصروفات
            col = 0
            max_cols = 5  # نفس عدد أعمدة كروت المخزون
            
            for expense in expenses:
                card = ExpenseCard(expense)
                card.expense_clicked.connect(self.on_expense_clicked)
                self.expense_cards[expense['id']] = card
                
                self.expenses_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # إعادة إضافة رسالة الترحيب إذا لم تكن موجودة
            if len(expenses) == 0 and hasattr(self, 'welcome_label'):
                self.expenses_layout.addWidget(self.welcome_label, 0, 0, 1, 5)
            
            # تحديث الإحصائيات
            self.update_stats(expenses)
            
            # إجبار التخطيط على التحديث
            self.expenses_layout.update()
            self.expenses_widget.update()
            
        except Exception as e:
            print(f"Error loading expenses: {e}")
    
    def update_stats(self, expenses):
        """تحديث الإحصائيات"""
        try:
            total = len(expenses)
            small_expenses = len([e for e in expenses if float(e['amount']) < 50])
            medium_expenses = len([e for e in expenses if 50 <= float(e['amount']) < 100])
            large_expenses = len([e for e in expenses if float(e['amount']) >= 100])
            total_amount = sum(float(e['amount']) for e in expenses)
            
            # التحقق من وجود العناصر قبل التحديث
            if hasattr(self, 'total_expenses_label') and self.total_expenses_label:
                self.total_expenses_label.setText(f"إجمالي المصروفات: {total}")
            if hasattr(self, 'small_expenses_label') and self.small_expenses_label:
                self.small_expenses_label.setText(f"صغيرة: {small_expenses}")
            if hasattr(self, 'medium_expenses_label') and self.medium_expenses_label:
                self.medium_expenses_label.setText(f"متوسطة: {medium_expenses}")
            if hasattr(self, 'large_expenses_label') and self.large_expenses_label:
                self.large_expenses_label.setText(f"كبيرة: {large_expenses}")
            if hasattr(self, 'total_amount_label') and self.total_amount_label:
                self.total_amount_label.setText(f"إجمالي المبلغ: {total_amount} جنيه")
            
            # تحديث مصروفات الوردية الحالية
            self.update_shift_expenses()
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def update_shift_expenses(self):
        """تحديث مصروفات الوردية الحالية"""
        try:
            # الحصول على الوردية النشطة للكاشير الحالي
            active_shift = self.shift_model.get_active_shift(self.current_user['id'])
            
            if active_shift:
                # الحصول على مصروفات الوردية
                shift_expenses = self.expense_model.get_expenses_by_shift(active_shift['id'])
                
                # حساب إجمالي مصروفات الوردية
                shift_total = sum(float(expense['amount']) for expense in shift_expenses)
                
                self.shift_expenses_label.setText(f"مصروفات الوردية: {shift_total} جنيه")
            else:
                self.shift_expenses_label.setText("مصروفات الوردية: لا توجد وردية نشطة")
                
        except Exception as e:
            print(f"خطأ في تحديث مصروفات الوردية: {e}")
            self.shift_expenses_label.setText("مصروفات الوردية: خطأ في التحميل")
    
    def on_expense_clicked(self, expense_data):
        """معالج النقر على المصروف"""
        print(f"تم النقر على المصروف: {expense_data['reason']}")
        self.expense_selected.emit(expense_data)
        
        # عرض نافذة تفاصيل المصروف
        self.show_expense_details(expense_data)
    
    def show_expense_details(self, expense_data):
        """عرض نافذة تفاصيل المصروف"""
        dialog = ExpenseDetailsDialog(expense_data, self.current_user)
        dialog.expense_deleted.connect(self.load_expenses)  # ربط إشارة الحذف بتحديث الواجهة
        dialog.exec()
    
    def add_expense(self):
        """إضافة مصروف جديد"""
        dialog = AddExpenseDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            expense_data = dialog.get_expense_data()
            
            # التحقق من صحة البيانات
            if not self.validate_expense_data(expense_data):
                return
            
            try:
                # الحصول على الوردية النشطة
                active_shift = self.shift_model.get_active_shift(self.current_user['id'])
                if not active_shift:
                    from utils.notifications import show_error
                    show_error("لا توجد وردية نشطة. يرجى بدء وردية أولاً.")
                    return
                
                # إضافة المصروف إلى قاعدة البيانات
                from decimal import Decimal
                expense_id = self.expense_model.create_expense(
                    amount=Decimal(str(expense_data['amount'])),
                    reason=expense_data['reason'],
                    cashier_id=self.current_user['id'],
                    shift_id=active_shift['id'],
                    notes=expense_data['notes']
                )
                
                if expense_id:
                    # ⭐ إضافة تأخير إضافي في exe للتأكد من commit كامل
                    import time
                    time.sleep(0.15)  # 150 ميلي ثانية إضافية
                    
                    from utils.notifications import show_success
                    show_success(f"تم إضافة المصروف بنجاح: {expense_data['reason']} - {expense_data['amount']} جنيه")
                    
                    # ⭐ مسح التخزين المؤقت للوردية قبل إعادة التحميل
                    try:
                        from controllers.shift_controller import ShiftController
                        shift_controller = ShiftController()
                        # مسح التخزين المؤقت للوردية المشتركة
                        keys_to_remove = [key for key in shift_controller.shift_data_cache.keys() if key.startswith("shared_")]
                        for key in keys_to_remove:
                            del shift_controller.shift_data_cache[key]
                        print(f"✅ تم مسح التخزين المؤقت للوردية")
                    except Exception as e:
                        print(f"⚠️ خطأ في مسح التخزين المؤقت: {e}")
                    
                    # تحديث الواجهة فوراً
                    self.load_expenses()
                    
                    # إجبار النافذة على التحديث
                    self.update()
                    self.expenses_widget.update()
                    
                    # معالجة الأحداث لضمان التحديث الفوري
                    from PySide6.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                    # ⭐ محاولة تحديث قسم إدارة الوردية إذا كان مفتوحاً
                    self.notify_shift_management_update()
                    
                    print(f"✅ تم إضافة المصروف وتحديث الواجهة: {expense_id}")
                    
                else:
                    from utils.notifications import show_error
                    show_error("فشل في إضافة المصروف. تحقق من البيانات أو جرب مرة أخرى.")
                    
            except Exception as e:
                from utils.notifications import show_error
                show_error(f"خطأ في إضافة المصروف: {str(e)}")
    
    def validate_expense_data(self, expense_data):
        """التحقق من صحة بيانات المصروف"""
        from utils.notifications import show_error
        
        if not expense_data['reason'].strip():
            show_error("سبب المصروف مطلوب")
            return False
        
        if expense_data['amount'] <= 0:
            show_error("المبلغ يجب أن يكون أكبر من صفر")
            return False
        
        if expense_data['amount'] > 10000:
            show_error("المبلغ كبير جداً. الحد الأقصى 10,000 جنيه")
            return False
        
        return True
    
    def notify_shift_management_update(self):
        """⭐ إرسال إشعار لقسم إدارة الوردية لتحديث المصروفات"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث عن نافذة إدارة الوردية المفتوحة
                for widget in app.allWidgets():
                    widget_class_name = str(widget.__class__.__name__)
                    if 'ProfessionalShiftManagement' in widget_class_name or 'SimpleShiftManagement' in widget_class_name:
                        # وجدنا نافذة إدارة الوردية
                        if hasattr(widget, 'load_shift_data'):
                            print(f"🔄 تحديث قسم إدارة الوردية بعد إضافة المصروف")
                            widget.load_shift_data()
                        elif hasattr(widget, 'refresh_data'):
                            print(f"🔄 تحديث قسم إدارة الوردية بعد إضافة المصروف")
                            widget.refresh_data()
                        break
                        
        except Exception as e:
            print(f"⚠️ خطأ في إرسال إشعار لقسم إدارة الوردية: {e}")
    
    def start_timer(self):
        """بدء التايمر لتحديث المصروفات"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_expenses_status)
        self.timer.start(60000)  # كل دقيقة
    
    def update_expenses_status(self):
        """تحديث حالة المصروفات"""
        for card in self.expense_cards.values():
            card.update_display()

class ExpenseDetailsDialog(QDialog):
    """نافذة تفاصيل المصروف"""
    
    # إشارات
    expense_deleted = Signal()
    
    def __init__(self, expense_data, current_user):
        super().__init__()
        self.expense_data = expense_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(f"تفاصيل المصروف - {self.expense_data['reason']}")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل المصروف - {self.expense_data['reason']}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات المصروف
        form_layout = QFormLayout()
        
        form_layout.addRow("رقم المصروف:", QLabel(str(self.expense_data['id'])))
        form_layout.addRow("السبب:", QLabel(self.expense_data.get('reason', 'غير محدد')))
        form_layout.addRow("المبلغ:", QLabel(f"{self.expense_data.get('amount', 0)} جنيه"))
        form_layout.addRow("الكاشير:", QLabel(self.expense_data.get('cashier_name', 'غير محدد')))
        
        date_time = self.expense_data.get('date_time')
        if date_time:
            if isinstance(date_time, str):
                date_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
            form_layout.addRow("التاريخ والوقت:", QLabel(date_time.strftime('%Y-%m-%d %H:%M')))
        
        notes = self.expense_data.get('notes', '')
        if notes:
            form_layout.addRow("الملاحظات:", QLabel(notes))
        
        layout.addLayout(form_layout)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        # زر حذف المصروف (للمدير فقط)
        delete_btn = QPushButton("حذف المصروف")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(self.delete_expense)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def delete_expense(self):
        """حذف المصروف"""
        try:
            from PySide6.QtWidgets import QMessageBox, QInputDialog
            from utils.notifications import show_success, show_error
            
            # التحقق من الصلاحية
            from utils.permission_checker import permission_checker
            
            # إذا كان المستخدم لديه صلاحية حذف مصروف، لا نطلب كلمة مرور المدير
            if permission_checker.check_permission_or_admin(self.current_user, "delete_expense"):
                # تأكيد الحذف مباشرة
                reply = QMessageBox.question(
                    self,
                    "تأكيد الحذف",
                    f"هل أنت متأكد من حذف المصروف '{self.expense_data.get('description', 'غير محدد')}'؟\n\n"
                    "⚠️ تحذير: هذا الإجراء لا يمكن التراجع عنه!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # حذف المصروف
                    from models.expense_model import ExpenseModel
                    expense_model = ExpenseModel()
                    
                    success = expense_model.delete_expense(self.expense_data['id'])
                    
                    if success:
                        show_success("تم حذف المصروف بنجاح")
                        self.expense_deleted.emit()  # إشارة لتحديث القائمة
                        self.accept()
                    else:
                        show_error("فشل في حذف المصروف")
            else:
                # طلب كلمة مرور المدير
                from PySide6.QtWidgets import QLineEdit
                password, ok = QInputDialog.getText(
                    self,
                    "تأكيد الحذف",
                    "هذه عملية حساسة تتطلب كلمة مرور المدير:\n\nأدخل كلمة مرور المدير:",
                    QLineEdit.Password
                )
                
                if not ok:
                    return  # المستخدم ألغى العملية
                
                if not password:
                    show_error("كلمة المرور مطلوبة")
                    return
                
                # التحقق من كلمة مرور المدير
                from models.user_model import UserModel
                user_model = UserModel()
                
                # البحث عن مدير في النظام
                admin_user = user_model.get_admin_user()
                if not admin_user:
                    show_error("لا يوجد مدير في النظام")
                    return
                
                # التحقق من كلمة المرور
                from utils.security import verify_password
                if not verify_password(password, admin_user['password_hash']):
                    show_error("كلمة المرور غير صحيحة")
                    return
                
                # تأكيد الحذف
                reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف المصروف التالي؟\n\n"
                f"رقم المصروف: {self.expense_data['id']}\n"
                f"السبب: {self.expense_data.get('reason', 'غير محدد')}\n"
                f"المبلغ: {self.expense_data.get('amount', 0)} جنيه\n\n"
                f"⚠️ تحذير: لا يمكن التراجع عن هذه العملية!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # حذف المصروف
                from models.expense_model import ExpenseModel
                expense_model = ExpenseModel()
                
                success = expense_model.delete_expense(self.expense_data['id'])
                if success:
                    show_success("تم حذف المصروف بنجاح")
                    
                    # إرسال إشارة لتحديث الواجهة الرئيسية
                    if hasattr(self, 'expense_deleted'):
                        self.expense_deleted.emit()
                    
                    self.accept()  # إغلاق نافذة التفاصيل
                else:
                    show_error("فشل في حذف المصروف")
            else:
                show_error("تم إلغاء عملية الحذف")
                
        except Exception as e:
            from utils.notifications import show_error
            show_error(f"خطأ في حذف المصروف: {str(e)}")

class AddExpenseDialog(QDialog):
    """نافذة إضافة مصروف جديد"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("إضافة مصروف جديد")
        self.setFixedSize(500, 650)
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
            QTextEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
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
        title_label = QLabel("إضافة مصروف جديد")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # السبب
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("سبب المصروف")
        self.reason_input.setMinimumHeight(45)
        layout.addWidget(self.reason_input)
        
        # المبلغ
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("المبلغ (جنيه)")
        self.amount_input.setText("10")
        self.amount_input.setMinimumHeight(45)
        layout.addWidget(self.amount_input)
        
        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        self.notes_input.setMaximumHeight(120)
        self.notes_input.setMinimumHeight(120)
        layout.addWidget(self.notes_input)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("إضافة المصروف")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # تعيين التركيز على حقل السبب
        self.reason_input.setFocus()
    
    def validate_and_accept(self):
        """التحقق من صحة البيانات وقبول النافذة"""
        try:
            # التحقق من السبب
            reason = self.reason_input.text().strip()
            if not reason:
                self.show_error("يرجى إدخال سبب المصروف")
                return
            
            # التحقق من المبلغ
            try:
                amount_text = self.amount_input.text().strip()
                if not amount_text:
                    self.show_error("يرجى إدخال مبلغ المصروف")
                    return
                
                amount = float(amount_text)
                if amount <= 0:
                    self.show_error("المبلغ يجب أن يكون أكبر من صفر")
                    return
                    
                if amount > 10000:
                    self.show_error("المبلغ لا يمكن أن يكون أكبر من 10000 جنيه")
                    return
                    
            except ValueError:
                self.show_error("يرجى إدخال مبلغ صحيح")
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
    
    def get_expense_data(self):
        """الحصول على بيانات المصروف"""
        try:
            amount = float(self.amount_input.text().strip()) if self.amount_input.text().strip() else 0.0
        except ValueError:
            amount = 0.0
            
        return {
            'reason': self.reason_input.text().strip(),
            'amount': amount,
            'notes': self.notes_input.toPlainText().strip()
        }
