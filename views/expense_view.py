"""
عرض وإدارة المصروفات
Expense View and Management
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QMessageBox, QGroupBox,
    QTabWidget, QDoubleSpinBox, QTextEdit, QDateEdit
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.expense_model import ExpenseModel
from models.shift_model import ShiftModel
from utils.helpers import format_currency, format_time
from utils.notifications import show_success, show_error

class ExpenseViewWindow(QMainWindow):
    """نافذة عرض وإدارة المصروفات"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.expense_model = ExpenseModel()
        self.shift_model = ShiftModel()
        self.setup_ui()
        self.load_expenses()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة المصروفات - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1000, 700)
        
        # الـ widget المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # عنوان النافذة
        title_label = QLabel("إدارة المصروفات")
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
        
        # تبويب عرض المصروفات
        self.create_expenses_tab()
        
        # تبويب إضافة مصروف جديد
        self.create_add_expense_tab()
        
        # تبويب الإحصائيات
        self.create_stats_tab()
    
    def create_expenses_tab(self):
        """إنشاء تبويب عرض المصروفات"""
        expenses_widget = QWidget()
        expenses_layout = QVBoxLayout(expenses_widget)
        
        # أدوات البحث والتصفية
        search_group = QGroupBox("البحث والتصفية")
        search_layout = QGridLayout(search_group)
        
        # البحث بالسبب
        search_layout.addWidget(QLabel("السبب:"), 0, 0)
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("البحث بالسبب")
        search_layout.addWidget(self.reason_input, 0, 1)
        
        # البحث بالكاشير
        search_layout.addWidget(QLabel("الكاشير:"), 0, 2)
        self.cashier_combo = QComboBox()
        self.cashier_combo.addItem("جميع الكاشيرز", "")
        search_layout.addWidget(self.cashier_combo, 0, 3)
        
        # البحث بالتاريخ
        search_layout.addWidget(QLabel("من تاريخ:"), 1, 0)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        search_layout.addWidget(self.start_date_input, 1, 1)
        
        search_layout.addWidget(QLabel("إلى تاريخ:"), 1, 2)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        search_layout.addWidget(self.end_date_input, 1, 3)
        
        # أزرار البحث
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.search_expenses)
        search_layout.addWidget(search_btn, 2, 0)
        
        reset_btn = QPushButton("إعادة تعيين")
        reset_btn.clicked.connect(self.reset_search)
        search_layout.addWidget(reset_btn, 2, 1)
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_expenses)
        search_layout.addWidget(refresh_btn, 2, 2)
        
        expenses_layout.addWidget(search_group)
        
        # جدول المصروفات
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(6)
        self.expenses_table.setHorizontalHeaderLabels([
            "المعرف", "المبلغ", "السبب", "الكاشير", "التاريخ", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.expenses_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        expenses_layout.addWidget(self.expenses_table)
        
        self.tab_widget.addTab(expenses_widget, "المصروفات")
    
    def create_add_expense_tab(self):
        """إنشاء تبويب إضافة مصروف جديد"""
        add_widget = QWidget()
        add_layout = QVBoxLayout(add_widget)
        
        # نموذج إضافة المصروف
        form_group = QGroupBox("إضافة مصروف جديد")
        form_layout = QGridLayout(form_group)
        
        # المبلغ
        form_layout.addWidget(QLabel("المبلغ:"), 0, 0)
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 100000)
        self.amount_input.setDecimals(2)
        form_layout.addWidget(self.amount_input, 0, 1)
        
        # السبب
        form_layout.addWidget(QLabel("السبب:"), 1, 0)
        self.reason_input_add = QLineEdit()
        self.reason_input_add.setPlaceholderText("أدخل سبب المصروف")
        form_layout.addWidget(self.reason_input_add, 1, 1)
        
        # التاريخ
        form_layout.addWidget(QLabel("التاريخ:"), 2, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.date_input, 2, 1)
        
        add_layout.addWidget(form_group)
        
        # زر الإضافة
        add_btn = QPushButton("إضافة المصروف")
        add_btn.clicked.connect(self.add_expense)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        add_layout.addWidget(add_btn)
        
        add_layout.addStretch()
        
        self.tab_widget.addTab(add_widget, "إضافة مصروف")
    
    def create_stats_tab(self):
        """إنشاء تبويب الإحصائيات"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # إحصائيات المصروفات
        stats_group = QGroupBox("إحصائيات المصروفات")
        stats_form_layout = QGridLayout(stats_group)
        
        # إجمالي المصروفات
        self.total_expenses_label = QLabel("0.00 ج.م")
        self.total_expenses_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #e74c3c;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
        """)
        stats_form_layout.addWidget(QLabel("إجمالي المصروفات:"), 0, 0)
        stats_form_layout.addWidget(self.total_expenses_label, 0, 1)
        
        # عدد المصروفات
        self.expenses_count_label = QLabel("0")
        self.expenses_count_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2E86AB;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
        """)
        stats_form_layout.addWidget(QLabel("عدد المصروفات:"), 1, 0)
        stats_form_layout.addWidget(self.expenses_count_label, 1, 1)
        
        # متوسط المصروف
        self.avg_expense_label = QLabel("0.00 ج.م")
        self.avg_expense_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
        """)
        stats_form_layout.addWidget(QLabel("متوسط المصروف:"), 2, 0)
        stats_form_layout.addWidget(self.avg_expense_label, 2, 1)
        
        stats_layout.addWidget(stats_group)
        
        # زر تحديث الإحصائيات
        refresh_stats_btn = QPushButton("تحديث الإحصائيات")
        refresh_stats_btn.clicked.connect(self.update_stats)
        stats_layout.addWidget(refresh_stats_btn)
        
        stats_layout.addStretch()
        
        self.tab_widget.addTab(stats_widget, "الإحصائيات")
    
    def load_expenses(self):
        """تحميل المصروفات"""
        try:
            # تحميل قائمة الكاشيرز
            self.load_cashier_list()
            
            # تحميل المصروفات
            expenses = self.expense_model.get_expenses_by_cashier(
                cashier_id=self.current_user['id']
            )
            
            self.display_expenses(expenses)
            self.update_stats()
            
        except Exception as e:
            show_error(f"خطأ في تحميل المصروفات: {str(e)}")
    
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
    
    def display_expenses(self, expenses):
        """عرض المصروفات في الجدول"""
        try:
            self.expenses_table.setRowCount(len(expenses))
            
            for row, expense in enumerate(expenses):
                self.expenses_table.setItem(row, 0, QTableWidgetItem(str(expense['id'])))
                self.expenses_table.setItem(row, 1, QTableWidgetItem(format_currency(expense['amount'])))
                self.expenses_table.setItem(row, 2, QTableWidgetItem(expense['reason']))
                self.expenses_table.setItem(row, 3, QTableWidgetItem(expense.get('cashier_name', '')))
                self.expenses_table.setItem(row, 4, QTableWidgetItem(format_time(expense['date_time'], 'short')))
                
                # زر الإجراءات
                actions_btn = QPushButton("حذف")
                actions_btn.clicked.connect(lambda checked, exp_id=expense['id']: self.delete_expense(exp_id))
                actions_btn.setStyleSheet("""
                    QPushButton {
                        background: #e74c3c;
                        color: white;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background: #c0392b;
                    }
                """)
                self.expenses_table.setCellWidget(row, 5, actions_btn)
            
        except Exception as e:
            show_error(f"خطأ في عرض المصروفات: {str(e)}")
    
    def search_expenses(self):
        """البحث في المصروفات"""
        try:
            # جمع معايير البحث
            reason = self.reason_input.text().strip()
            cashier_id = self.cashier_combo.currentData()
            start_date = self.start_date_input.date().toPython()
            end_date = self.end_date_input.date().toPython()
            
            # البحث
            if reason or cashier_id:
                expenses = self.expense_model.search_expenses(
                    search_term=reason,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # تصفية حسب الكاشير
                if cashier_id:
                    expenses = [exp for exp in expenses if exp.get('cashier_id') == cashier_id]
            else:
                expenses = self.expense_model.get_all_expenses(
                    start_date=start_date,
                    end_date=end_date
                )
            
            self.display_expenses(expenses)
            
        except Exception as e:
            show_error(f"خطأ في البحث: {str(e)}")
    
    def reset_search(self):
        """إعادة تعيين البحث"""
        self.reason_input.clear()
        self.cashier_combo.setCurrentIndex(0)
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDate(QDate.currentDate())
        
        self.load_expenses()
    
    def add_expense(self):
        """إضافة مصروف جديد"""
        try:
            amount = self.amount_input.value()
            reason = self.reason_input_add.text().strip()
            date_time = self.date_input.date().toPython()
            
            # التحقق من الحقول المطلوبة
            if amount <= 0:
                show_error("يرجى إدخال مبلغ صحيح")
                return
            
            if not reason:
                show_error("يرجى إدخال سبب المصروف")
                return
            
            # الحصول على الوردية النشطة
            active_shift = self.shift_model.get_active_shift(self.current_user['id'])
            if not active_shift:
                show_error("لا توجد وردية نشطة. يرجى بدء وردية جديدة")
                return
            
            # إضافة المصروف
            expense_id = self.expense_model.create_expense(
                amount=amount,
                reason=reason,
                cashier_id=self.current_user['id'],
                shift_id=active_shift['id'],
                date_time=date_time
            )
            
            if expense_id:
                show_success("تم إضافة المصروف بنجاح")
                self.clear_add_form()
                self.load_expenses()
            else:
                show_error("فشل في إضافة المصروف")
                
        except Exception as e:
            show_error(f"خطأ في إضافة المصروف: {str(e)}")
    
    def delete_expense(self, expense_id):
        """حذف المصروف"""
        try:
            # التحقق من الصلاحيات (فقط المدير يمكنه الحذف)
            if self.current_user.get('role') != 'admin':
                show_error("ليس لديك صلاحية لحذف المصروفات")
                return
            
            reply = QMessageBox.question(
                self,
                "حذف المصروف",
                "هل أنت متأكد من حذف هذا المصروف؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.expense_model.delete_expense(expense_id)
                
                if success:
                    show_success("تم حذف المصروف بنجاح")
                    self.load_expenses()
                else:
                    show_error("فشل في حذف المصروف")
                    
        except Exception as e:
            show_error(f"خطأ في حذف المصروف: {str(e)}")
    
    def update_stats(self):
        """تحديث الإحصائيات"""
        try:
            # الحصول على إحصائيات المصروفات
            stats = self.expense_model.get_expense_stats()
            
            self.total_expenses_label.setText(format_currency(stats.get('total_amount', 0)))
            self.expenses_count_label.setText(str(stats.get('total_expenses', 0)))
            self.avg_expense_label.setText(format_currency(stats.get('avg_expense', 0)))
            
        except Exception as e:
            show_error(f"خطأ في تحديث الإحصائيات: {str(e)}")
    
    def clear_add_form(self):
        """مسح نموذج الإضافة"""
        self.amount_input.setValue(0)
        self.reason_input_add.clear()
        self.date_input.setDate(QDate.currentDate())

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # بيانات مستخدم تجريبية
    test_user = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    
    window = ExpenseViewWindow(test_user)
    window.show()
    sys.exit(app.exec())
