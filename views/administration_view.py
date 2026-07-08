"""
واجهة الإداريات الشاملة
Administration View - Employees & Administrative Expenses
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTabWidget,
    QSpinBox, QDoubleSpinBox, QCheckBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate, QPoint
from PySide6.QtGui import QFont, QIcon, QColor, QAction

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.employee_controller import EmployeeController
from controllers.administrative_expense_controller import AdministrativeExpenseController
from models.employee_model import EmployeeModel
from models.administrative_expense_model import AdministrativeExpenseModel

class AdministrationView(QWidget):
    """واجهة الإداريات الشاملة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.employee_controller = EmployeeController(current_user)
        self.admin_expense_controller = AdministrativeExpenseController(current_user)
        self.employees_data = []  # لحفظ بيانات الموظفين للوصول السريع
        self.expenses_data = []  # لحفظ بيانات المصاريف للوصول السريع
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # عنوان الصفحة
        title_label = QLabel("📊 الإداريات")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 8px;
        """)
        main_layout.addWidget(title_label)
        
        # إنشاء التبويبات
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 12px 25px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
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
        
        # تبويب الموظفين
        self.employees_tab = self.create_employees_tab()
        self.tab_widget.addTab(self.employees_tab, "👥 الموظفين")
        
        # تبويب المصاريف الإدارية
        self.expenses_tab = self.create_admin_expenses_tab()
        self.tab_widget.addTab(self.expenses_tab, "💰 المصاريف الإدارية")
        
        # تبويب تقارير الإداريات
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "📈 التقارير")
        
        main_layout.addWidget(self.tab_widget)
    
    # ================ تبويب الموظفين ================
    
    def create_employees_tab(self):
        """إنشاء تبويب الموظفين"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ إضافة موظف")
        add_btn.setStyleSheet(self.get_button_style("#27ae60"))
        add_btn.clicked.connect(self.show_add_employee_dialog)
        buttons_layout.addWidget(add_btn)
        
        advances_btn = QPushButton("💵 السلف")
        advances_btn.setStyleSheet(self.get_button_style("#3498db"))
        advances_btn.clicked.connect(self.show_advances_dialog)
        buttons_layout.addWidget(advances_btn)
        
        deductions_btn = QPushButton("➖ الخصومات")
        deductions_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        deductions_btn.clicked.connect(self.show_deductions_dialog)
        buttons_layout.addWidget(deductions_btn)
        
        overtime_btn = QPushButton("⏰ ساعات إضافية")
        overtime_btn.setStyleSheet(self.get_button_style("#9b59b6"))
        overtime_btn.clicked.connect(self.show_overtime_dialog)
        buttons_layout.addWidget(overtime_btn)
        
        salaries_btn = QPushButton("💰 معالجة الرواتب")
        salaries_btn.setStyleSheet(self.get_button_style("#e67e22"))
        salaries_btn.clicked.connect(self.show_process_salaries_dialog)
        buttons_layout.addWidget(salaries_btn)
        
        buttons_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        refresh_btn.clicked.connect(self.load_employees)
        buttons_layout.addWidget(refresh_btn)
        
        layout.addLayout(buttons_layout)
        
        # جدول الموظفين
        self.employees_table = QTableWidget()
        self.employees_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
                cursor: pointer;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        self.employees_table.setColumnCount(8)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "الاسم", "الوظيفة", "الراتب الشهري", "الهاتف",
            "الرقم القومي", "تاريخ التعيين", "الحالة"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.employees_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.employees_table.setAlternatingRowColors(True)
        
        # إضافة حدث الضغط على الصف
        self.employees_table.cellClicked.connect(self.show_employee_details)
        
        layout.addWidget(self.employees_table)
        
        return tab
    
    # ================ تبويب المصاريف الإدارية ================
    
    def create_admin_expenses_tab(self):
        """إنشاء تبويب المصاريف الإدارية"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ إضافة مصروف")
        add_btn.setStyleSheet(self.get_button_style("#27ae60"))
        add_btn.clicked.connect(self.show_add_expense_dialog)
        buttons_layout.addWidget(add_btn)
        
        recurring_btn = QPushButton("🔁 المصاريف المتكررة")
        recurring_btn.setStyleSheet(self.get_button_style("#3498db"))
        recurring_btn.clicked.connect(self.show_recurring_expenses)
        buttons_layout.addWidget(recurring_btn)
        
        buttons_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet(self.get_button_style("#95a5a6"))
        refresh_btn.clicked.connect(self.load_admin_expenses)
        buttons_layout.addWidget(refresh_btn)
        
        layout.addLayout(buttons_layout)
        
        # فلاتر
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        # فلتر النوع
        filter_layout.addWidget(QLabel("النوع:"))
        self.expense_type_filter = QComboBox()
        self.expense_type_filter.addItem("الكل", "")
        expense_model = AdministrativeExpenseModel()
        for key, value in expense_model.EXPENSE_TYPES.items():
            self.expense_type_filter.addItem(value, key)
        self.expense_type_filter.currentIndexChanged.connect(self.filter_admin_expenses)
        self.expense_type_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.expense_type_filter)
        
        filter_layout.addWidget(QLabel("│"))  # فاصل
        
        # فلتر التاريخ - من
        filter_layout.addWidget(QLabel("من:"))
        self.expense_date_from = QDateEdit()
        self.expense_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.expense_date_from.setCalendarPopup(True)
        self.expense_date_from.setDisplayFormat("yyyy-MM-dd")
        self.expense_date_from.setMinimumWidth(120)
        self.expense_date_from.dateChanged.connect(self.filter_admin_expenses)
        self.expense_date_from.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        """)
        filter_layout.addWidget(self.expense_date_from)
        
        # فلتر التاريخ - إلى
        filter_layout.addWidget(QLabel("إلى:"))
        self.expense_date_to = QDateEdit()
        self.expense_date_to.setDate(QDate.currentDate())
        self.expense_date_to.setCalendarPopup(True)
        self.expense_date_to.setDisplayFormat("yyyy-MM-dd")
        self.expense_date_to.setMinimumWidth(120)
        self.expense_date_to.dateChanged.connect(self.filter_admin_expenses)
        self.expense_date_to.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
        """)
        filter_layout.addWidget(self.expense_date_to)
        
        # زر إعادة تعيين الفلاتر
        reset_filter_btn = QPushButton("🔄 إعادة تعيين")
        reset_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 6px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        reset_filter_btn.clicked.connect(self.reset_expense_filters)
        filter_layout.addWidget(reset_filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # جدول المصاريف
        self.expenses_table = QTableWidget()
        self.expenses_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        self.expenses_table.setColumnCount(6)
        self.expenses_table.setHorizontalHeaderLabels([
            "ID", "النوع", "المبلغ", "التاريخ", "الوصف", "متكرر"
        ])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expenses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.expenses_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.expenses_table.customContextMenuRequested.connect(self.show_expense_context_menu)
        
        layout.addWidget(self.expenses_table)
        
        # ملخص النتائج
        self.expenses_summary_label = QLabel("📊 النتائج: 0 مصروف | الإجمالي: 0.00 جنيه")
        self.expenses_summary_label.setAlignment(Qt.AlignCenter)
        self.expenses_summary_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-top: 10px;
        """)
        layout.addWidget(self.expenses_summary_label)
        
        return tab
    
    # ================ تبويب التقارير ================
    
    def create_reports_tab(self):
        """إنشاء تبويب التقارير"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # فترة التقرير
        period_group = QGroupBox("فترة التقرير")
        period_group.setStyleSheet("""
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
                padding: 0 5px;
            }
        """)
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel("من:"))
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.report_start_date.setCalendarPopup(True)
        period_layout.addWidget(self.report_start_date)
        
        period_layout.addWidget(QLabel("إلى:"))
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        period_layout.addWidget(self.report_end_date)
        
        generate_btn = QPushButton("📊 إنشاء التقرير")
        generate_btn.setStyleSheet(self.get_button_style("#3498db"))
        generate_btn.clicked.connect(self.generate_admin_report)
        period_layout.addWidget(generate_btn)
        
        period_layout.addStretch()
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # نتائج التقرير
        results_group = QGroupBox("نتائج التقرير")
        results_group.setStyleSheet("""
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
                padding: 0 5px;
            }
        """)
        results_layout = QVBoxLayout()
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                font-family: 'Courier New';
                font-size: 13px;
            }
        """)
        results_layout.addWidget(self.report_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        return tab
    
    # ================ دوال مساعدة ================
    
    def get_button_style(self, color):
        """الحصول على نمط الزر"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """
    
    # ================ تحميل البيانات ================
    
    def load_data(self):
        """تحميل جميع البيانات"""
        self.load_employees()
        self.load_admin_expenses()
    
    def load_employees(self):
        """تحميل الموظفين"""
        try:
            result = self.employee_controller.get_all_employees(include_inactive=False)
            
            if result['success']:
                self.employees_data = result['employees']  # حفظ البيانات للاستخدام عند الضغط
                self.employees_table.setRowCount(len(self.employees_data))
                
                for row, emp in enumerate(self.employees_data):
                    self.employees_table.setItem(row, 0, QTableWidgetItem(str(emp['id'])))
                    self.employees_table.setItem(row, 1, QTableWidgetItem(emp['name']))
                    self.employees_table.setItem(row, 2, QTableWidgetItem(emp['position']))
                    self.employees_table.setItem(row, 3, QTableWidgetItem(f"{emp['monthly_salary']:.2f} جنيه"))
                    self.employees_table.setItem(row, 4, QTableWidgetItem(emp['phone'] or '-'))
                    self.employees_table.setItem(row, 5, QTableWidgetItem(emp['national_id'] or '-'))
                    self.employees_table.setItem(row, 6, QTableWidgetItem(emp['hire_date']))
                    
                    status_item = QTableWidgetItem("نشط" if emp['is_active'] else "غير نشط")
                    if emp['is_active']:
                        status_item.setForeground(Qt.darkGreen)
                    else:
                        status_item.setForeground(Qt.red)
                    self.employees_table.setItem(row, 7, status_item)
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل الموظفين: {str(e)}")
    
    def load_admin_expenses(self):
        """تحميل المصاريف الإدارية"""
        try:
            result = self.admin_expense_controller.get_all_expenses()
            
            if result['success']:
                self.expenses_data = result['expenses']  # حفظ البيانات للاستخدام في القائمة السياقية
                self.expenses_table.setRowCount(len(self.expenses_data))
                
                for row, exp in enumerate(self.expenses_data):
                    self.expenses_table.setItem(row, 0, QTableWidgetItem(str(exp['id'])))
                    self.expenses_table.setItem(row, 1, QTableWidgetItem(exp.get('expense_type_ar', exp['expense_type'])))
                    self.expenses_table.setItem(row, 2, QTableWidgetItem(f"{exp['amount']:.2f} جنيه"))
                    self.expenses_table.setItem(row, 3, QTableWidgetItem(exp['date']))
                    self.expenses_table.setItem(row, 4, QTableWidgetItem(exp['description'] or '-'))
                    
                    recurring_item = QTableWidgetItem("نعم ✓" if exp['is_recurring'] else "لا")
                    if exp['is_recurring']:
                        recurring_item.setForeground(QColor("#27ae60"))
                        recurring_item.setFont(QFont("Arial", 10, QFont.Bold))
                    else:
                        recurring_item.setForeground(QColor("#95a5a6"))
                    self.expenses_table.setItem(row, 5, recurring_item)
                
                # تحديث ملخص النتائج
                total = sum(Decimal(str(e['amount'])) for e in self.expenses_data)
                if hasattr(self, 'expenses_summary_label'):
                    self.expenses_summary_label.setText(
                        f"📊 النتائج: {len(self.expenses_data)} مصروف | الإجمالي: {total:.2f} جنيه"
                    )
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المصاريف الإدارية: {str(e)}")
    
    def filter_admin_expenses(self):
        """تصفية المصاريف الإدارية حسب النوع والتاريخ"""
        try:
            # الحصول على الفلاتر
            selected_type = self.expense_type_filter.currentData()
            date_from = self.expense_date_from.date().toPython()
            date_to = self.expense_date_to.date().toPython()
            
            # جلب المصاريف حسب الفلاتر
            if selected_type:
                # فلترة حسب النوع والتاريخ
                result = self.admin_expense_controller.get_expenses_by_type(
                    selected_type, date_from, date_to
                )
            else:
                # فلترة حسب التاريخ فقط
                result = self.admin_expense_controller.get_expenses_by_date_range(
                    date_from, date_to
                )
            
            if result['success']:
                self.expenses_data = result['expenses']
                self.expenses_table.setRowCount(len(self.expenses_data))
                
                for row, exp in enumerate(self.expenses_data):
                    self.expenses_table.setItem(row, 0, QTableWidgetItem(str(exp['id'])))
                    self.expenses_table.setItem(row, 1, QTableWidgetItem(exp.get('expense_type_ar', exp['expense_type'])))
                    self.expenses_table.setItem(row, 2, QTableWidgetItem(f"{exp['amount']:.2f} جنيه"))
                    self.expenses_table.setItem(row, 3, QTableWidgetItem(exp['date']))
                    self.expenses_table.setItem(row, 4, QTableWidgetItem(exp['description'] or '-'))
                    
                    recurring_item = QTableWidgetItem("نعم ✓" if exp['is_recurring'] else "لا")
                    if exp['is_recurring']:
                        recurring_item.setForeground(QColor("#27ae60"))
                        recurring_item.setFont(QFont("Arial", 10, QFont.Bold))
                    else:
                        recurring_item.setForeground(QColor("#95a5a6"))
                    self.expenses_table.setItem(row, 5, recurring_item)
                
                # عرض عدد النتائج
                total = result.get('total', sum(Decimal(str(e['amount'])) for e in self.expenses_data))
                if hasattr(self, 'expenses_summary_label'):
                    self.expenses_summary_label.setText(
                        f"📊 النتائج: {len(self.expenses_data)} مصروف | الإجمالي: {total:.2f} جنيه"
                    )
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصفية المصاريف: {str(e)}")
    
    def reset_expense_filters(self):
        """إعادة تعيين فلاتر المصاريف"""
        try:
            # إعادة تعيين النوع
            self.expense_type_filter.setCurrentIndex(0)
            
            # إعادة تعيين التواريخ
            self.expense_date_from.setDate(QDate.currentDate().addMonths(-1))
            self.expense_date_to.setDate(QDate.currentDate())
            
            # تحديث الجدول
            self.load_admin_expenses()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إعادة تعيين الفلاتر: {str(e)}")
    
    def show_expense_context_menu(self, position):
        """عرض القائمة السياقية للمصروف عند الضغط بالزر الأيمن"""
        try:
            # الحصول على الصف المحدد
            row = self.expenses_table.rowAt(position.y())
            
            if row < 0 or row >= len(self.expenses_data):
                return
            
            expense = self.expenses_data[row]
            
            # إنشاء القائمة السياقية
            context_menu = QMenu(self)
            context_menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            
            # إضافة خيار الحذف
            delete_action = context_menu.addAction("🗑️ حذف المصروف")
            delete_action.setFont(QFont("Arial", 10, QFont.Bold))
            
            # عرض القائمة
            action = context_menu.exec(self.expenses_table.viewport().mapToGlobal(position))
            
            # تنفيذ الإجراء
            if action == delete_action:
                self.delete_expense(expense['id'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في عرض القائمة: {str(e)}")
    
    # ================ نافذة تفاصيل الموظف ================
    
    def show_employee_details(self, row, column):
        """عرض نافذة تفاصيل الموظف عند الضغط على صف"""
        try:
            if row < 0 or row >= len(self.employees_data):
                return
            
            employee = self.employees_data[row]
            
            # إنشاء نافذة التفاصيل
            dialog = QDialog(self)
            dialog.setWindowTitle(f"تفاصيل الموظف - {employee['name']}")
            dialog.setMinimumWidth(750)
            dialog.setMinimumHeight(600)
            
            main_layout = QVBoxLayout(dialog)
            main_layout.setSpacing(20)
            
            # عنوان النافذة
            title_label = QLabel(f"👤 {employee['name']}")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("""
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
            """)
            main_layout.addWidget(title_label)
            
            # إنشاء تبويبات
            details_tabs = QTabWidget()
            details_tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                    background-color: white;
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
            """)
            
            # تبويب البيانات الأساسية
            basic_info_tab = QWidget()
            basic_info_layout = QVBoxLayout(basic_info_tab)
            
            # البيانات الأساسية
            info_group = QGroupBox("📋 البيانات الأساسية")
            info_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            info_layout = QGridLayout()
            info_layout.setHorizontalSpacing(15)
            info_layout.setVerticalSpacing(12)
            
            # إنشاء العناوين مع محاذاة يمين
            def create_label(text, is_value=False):
                label = QLabel(text)
                if is_value:
                    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    label.setStyleSheet("padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
                else:
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    label.setStyleSheet("font-weight: bold; padding: 5px;")
                return label
            
            # رقم الموظف
            info_layout.addWidget(create_label(str(employee['id']), True), 0, 0)
            info_layout.addWidget(create_label(" رقم الموظف:"), 0, 1)
            
            # الاسم
            name_label = QLabel(employee['name'])
            name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px; padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
            info_layout.addWidget(name_label, 1, 0)
            info_layout.addWidget(create_label("👤 الاسم:"), 1, 1)
            
            # الوظيفة
            info_layout.addWidget(create_label(employee['position'], True), 2, 0)
            info_layout.addWidget(create_label("💼 الوظيفة:"), 2, 1)
            
            # الراتب الشهري
            salary_label = QLabel(f"{employee['monthly_salary']:.2f} جنيه")
            salary_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            salary_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 17px; padding: 8px; background-color: #e8f8f5; border-radius: 4px; border: 2px solid #27ae60;")
            info_layout.addWidget(salary_label, 3, 0)
            info_layout.addWidget(create_label("💰 الراتب الشهري:"), 3, 1)
            
            # الهاتف
            info_layout.addWidget(create_label(employee['phone'] or '-', True), 4, 0)
            info_layout.addWidget(create_label("📱 الهاتف:"), 4, 1)
            
            # الرقم القومي
            info_layout.addWidget(create_label(employee['national_id'] or '-', True), 5, 0)
            info_layout.addWidget(create_label(" الرقم القومي:"), 5, 1)
            
            # تاريخ التعيين
            info_layout.addWidget(create_label(employee['hire_date'], True), 6, 0)
            info_layout.addWidget(create_label("📅 تاريخ التعيين:"), 6, 1)
            
            # العنوان
            address_label = QLabel(employee.get('address', '-') or '-')
            address_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            address_label.setWordWrap(True)
            address_label.setStyleSheet("padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
            info_layout.addWidget(address_label, 7, 0)
            info_layout.addWidget(create_label("📍 العنوان:"), 7, 1)
            
            # الحالة
            status_label = QLabel("نشط ✓" if employee['is_active'] else "غير نشط ✗")
            status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            status_label.setStyleSheet("font-weight: bold; padding: 8px; border-radius: 4px; " + 
                                      ("color: white; background-color: #27ae60;" if employee['is_active'] else "color: white; background-color: #e74c3c;"))
            info_layout.addWidget(status_label, 8, 0)
            info_layout.addWidget(create_label("✅ الحالة:"), 8, 1)
            
            # الملاحظات
            if employee.get('notes'):
                notes_label = QLabel(employee['notes'])
                notes_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                notes_label.setWordWrap(True)
                notes_label.setStyleSheet("padding: 5px; background-color: #fff3cd; border-radius: 4px; border: 1px solid #ffc107;")
                info_layout.addWidget(notes_label, 9, 0)
                info_layout.addWidget(create_label("📝 ملاحظات:"), 9, 1)
            
            info_group.setLayout(info_layout)
            basic_info_layout.addWidget(info_group)
            
            # أزرار الإجراءات
            actions_group = QGroupBox("⚙️ الإجراءات")
            actions_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            actions_layout = QHBoxLayout()
            
            # زر حساب الراتب
            calc_salary_btn = QPushButton("💰 حساب الراتب")
            calc_salary_btn.setStyleSheet(self.get_button_style("#3498db"))
            calc_salary_btn.setMinimumHeight(45)
            calc_salary_btn.clicked.connect(lambda: self.calculate_employee_salary_from_details(employee['id'], dialog))
            actions_layout.addWidget(calc_salary_btn)
            
            # زر إضافة سلفة
            add_advance_btn = QPushButton("💵 إضافة سلفة")
            add_advance_btn.setStyleSheet(self.get_button_style("#9b59b6"))
            add_advance_btn.setMinimumHeight(45)
            add_advance_btn.clicked.connect(lambda: self.add_advance_for_employee(employee['id'], dialog))
            actions_layout.addWidget(add_advance_btn)
            
            # زر إضافة خصم
            add_deduction_btn = QPushButton("➖ إضافة خصم")
            add_deduction_btn.setStyleSheet(self.get_button_style("#e67e22"))
            add_deduction_btn.setMinimumHeight(45)
            add_deduction_btn.clicked.connect(lambda: self.add_deduction_for_employee(employee['id'], dialog))
            actions_layout.addWidget(add_deduction_btn)
            
            # زر إضافة ساعات إضافية
            add_overtime_btn = QPushButton("⏰ ساعات إضافية")
            add_overtime_btn.setStyleSheet(self.get_button_style("#16a085"))
            add_overtime_btn.setMinimumHeight(45)
            add_overtime_btn.clicked.connect(lambda: self.add_overtime_for_employee(employee['id'], dialog))
            actions_layout.addWidget(add_overtime_btn)
            
            # زر حذف
            delete_btn = QPushButton("🗑️ حذف الموظف")
            delete_btn.setStyleSheet(self.get_button_style("#e74c3c"))
            delete_btn.setMinimumHeight(45)
            delete_btn.clicked.connect(lambda: self.delete_employee_from_details(employee['id'], dialog))
            actions_layout.addWidget(delete_btn)
            
            actions_group.setLayout(actions_layout)
            basic_info_layout.addWidget(actions_group)
            
            # إضافة تبويب البيانات الأساسية
            details_tabs.addTab(basic_info_tab, "📋 البيانات والإجراءات")
            
            # تبويب المعاملات
            transactions_tab = self.create_transactions_tab(employee['id'])
            details_tabs.addTab(transactions_tab, "📊 المعاملات")
            
            # إضافة التبويبات للنافذة
            main_layout.addWidget(details_tabs)
            
            # زر إغلاق
            close_layout = QHBoxLayout()
            close_layout.addStretch()
            close_btn = QPushButton("إغلاق")
            close_btn.setStyleSheet(self.get_button_style("#95a5a6"))
            close_btn.setMinimumWidth(150)
            close_btn.setMinimumHeight(40)
            close_btn.clicked.connect(dialog.accept)
            close_layout.addWidget(close_btn)
            close_layout.addStretch()
            main_layout.addLayout(close_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض تفاصيل الموظف: {str(e)}")
    
    def create_transactions_tab(self, employee_id):
        """إنشاء تبويب المعاملات للموظف"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # معلومات الشهر الحالي
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_str = str(current_month).zfill(2)
        
        info_label = QLabel(f"📅 معاملات شهر {current_month}/{current_year}")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #e8f4f8;
            border-radius: 5px;
        """)
        layout.addWidget(info_label)
        
        # جدول المعاملات
        transactions_table = QTableWidget()
        transactions_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        transactions_table.setColumnCount(5)
        transactions_table.setHorizontalHeaderLabels([
            "النوع", "المبلغ", "التاريخ", "التفاصيل", "حذف"
        ])
        transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        transactions_table.setSelectionBehavior(QTableWidget.SelectRows)
        transactions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        transactions_table.setAlternatingRowColors(True)
        
        # جلب المعاملات
        from models.employee_model import EmployeeModel
        emp_model = EmployeeModel()
        
        # السلف
        advances = emp_model.get_employee_advances(employee_id, month_str, current_year)
        # الخصومات
        deductions = emp_model.get_employee_deductions(employee_id, month_str, current_year)
        # الساعات الإضافية
        overtime = emp_model.get_employee_overtime(employee_id, month_str, current_year)
        
        # دمج جميع المعاملات
        all_transactions = []
        
        for adv in advances:
            all_transactions.append({
                'type': 'سلفة',
                'type_key': 'advance',
                'amount': adv['amount'],
                'date': adv['date'],
                'details': adv.get('reason', '-') or '-',
                'id': adv['id'],
                'color': '#9b59b6'
            })
        
        for ded in deductions:
            deduction_types = {
                'absence': 'غياب',
                'lateness': 'تأخير',
                'damage': 'أضرار',
                'other': 'أخرى'
            }
            all_transactions.append({
                'type': f"خصم ({deduction_types.get(ded['deduction_type'], 'أخرى')})",
                'type_key': 'deduction',
                'amount': ded['amount'],
                'date': ded['date'],
                'details': ded.get('reason', '-'),
                'id': ded['id'],
                'color': '#e74c3c'
            })
        
        for ovt in overtime:
            all_transactions.append({
                'type': 'ساعات إضافية',
                'type_key': 'overtime',
                'amount': ovt['total_amount'],
                'date': ovt['date'],
                'details': f"{ovt['hours']} ساعة × {ovt['hourly_rate']} جنيه" + (f" - {ovt['notes']}" if ovt.get('notes') else ""),
                'id': ovt['id'],
                'color': '#27ae60'
            })
        
        # ترتيب حسب التاريخ (الأحدث أولاً)
        all_transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # ملء الجدول
        transactions_table.setRowCount(len(all_transactions))
        
        for row, trans in enumerate(all_transactions):
            # النوع
            type_item = QTableWidgetItem(trans['type'])
            type_item.setForeground(QColor(trans['color']))
            type_item.setFont(QFont("Arial", 10, QFont.Bold))
            transactions_table.setItem(row, 0, type_item)
            
            # المبلغ
            amount_text = f"{trans['amount']:.2f} جنيه"
            if trans['type_key'] == 'overtime':
                amount_text = f"+{amount_text}"
            elif trans['type_key'] in ['advance', 'deduction']:
                amount_text = f"-{amount_text}"
            
            amount_item = QTableWidgetItem(amount_text)
            amount_item.setFont(QFont("Arial", 10, QFont.Bold))
            if trans['type_key'] == 'overtime':
                amount_item.setForeground(QColor("#27ae60"))
            else:
                amount_item.setForeground(QColor("#e74c3c"))
            transactions_table.setItem(row, 1, amount_item)
            
            # التاريخ
            transactions_table.setItem(row, 2, QTableWidgetItem(trans['date']))
            
            # التفاصيل
            transactions_table.setItem(row, 3, QTableWidgetItem(trans['details']))
            
            # زر حذف
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("حذف المعاملة")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_btn.clicked.connect(lambda checked, t=trans: self.delete_transaction(t, employee_id, transactions_table))
            transactions_table.setCellWidget(row, 4, delete_btn)
        
        layout.addWidget(transactions_table)
        
        # ملخص المعاملات
        summary_layout = QHBoxLayout()
        
        total_advances = sum(t['amount'] for t in all_transactions if t['type_key'] == 'advance')
        total_deductions = sum(t['amount'] for t in all_transactions if t['type_key'] == 'deduction')
        total_overtime = sum(t['amount'] for t in all_transactions if t['type_key'] == 'overtime')
        
        summary_label = QLabel(f"""
        <div style='padding: 10px; background-color: #ecf0f1; border-radius: 5px;'>
            <b>📊 ملخص المعاملات:</b><br/>
            <span style='color: #9b59b6;'>💵 إجمالي السلف: {total_advances:.2f} جنيه</span> | 
            <span style='color: #e74c3c;'>➖ إجمالي الخصومات: {total_deductions:.2f} جنيه</span> | 
            <span style='color: #27ae60;'>⏰ إجمالي الساعات الإضافية: {total_overtime:.2f} جنيه</span>
        </div>
        """)
        summary_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(summary_label)
        
        layout.addLayout(summary_layout)
        
        # زر حذف معاملات الشهر
        clear_btn_layout = QHBoxLayout()
        clear_btn_layout.addStretch()
        
        clear_month_btn = QPushButton("🗑️ حذف جميع معاملات هذا الشهر")
        clear_month_btn.setStyleSheet(self.get_button_style("#e74c3c"))
        clear_month_btn.clicked.connect(lambda: self.clear_current_month_transactions(employee_id, month_str, current_year))
        clear_btn_layout.addWidget(clear_month_btn)
        
        clear_btn_layout.addStretch()
        layout.addLayout(clear_btn_layout)
        
        note_label = QLabel("💡 ملاحظة: يُنصح بحذف المعاملات بعد معالجة الرواتب الشهرية")
        note_label.setAlignment(Qt.AlignCenter)
        note_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic; padding: 5px;")
        layout.addWidget(note_label)
        
        return tab
    
    def delete_transaction(self, transaction, employee_id, table):
        """حذف معاملة واحدة"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف هذه المعاملة؟\n\n{transaction['type']}: {transaction['amount']:.2f} جنيه",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from models.employee_model import EmployeeModel
            emp_model = EmployeeModel()
            success = False
            
            if transaction['type_key'] == 'advance':
                success = emp_model.delete_advance(transaction['id'])
            elif transaction['type_key'] == 'deduction':
                success = emp_model.delete_deduction(transaction['id'])
            elif transaction['type_key'] == 'overtime':
                success = emp_model.delete_overtime(transaction['id'])
            
            if success:
                QMessageBox.information(self, "نجاح", "تم حذف المعاملة بنجاح")
                # تحديث الجدول
                self.load_employees()
            else:
                QMessageBox.warning(self, "خطأ", "فشل في حذف المعاملة")
    
    def clear_current_month_transactions(self, employee_id, month, year):
        """حذف جميع معاملات الشهر الحالي"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف جميع معاملات شهر {month}/{year}؟\n\n"
            "سيتم حذف:\n"
            "• جميع السلف\n"
            "• جميع الخصومات\n"
            "• جميع الساعات الإضافية\n\n"
            "⚠️ هذا الإجراء لا يمكن التراجع عنه!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from models.employee_model import EmployeeModel
                emp_model = EmployeeModel()
                
                deleted_count = 0
                
                # حذف السلف
                advances = emp_model.get_employee_advances(employee_id, month, year)
                for adv in advances:
                    if emp_model.delete_advance(adv['id']):
                        deleted_count += 1
                
                # حذف الخصومات
                deductions = emp_model.get_employee_deductions(employee_id, month, year)
                for ded in deductions:
                    if emp_model.delete_deduction(ded['id']):
                        deleted_count += 1
                
                # حذف الساعات الإضافية
                overtime = emp_model.get_employee_overtime(employee_id, month, year)
                for ovt in overtime:
                    if emp_model.delete_overtime(ovt['id']):
                        deleted_count += 1
                
                if deleted_count > 0:
                    QMessageBox.information(
                        self, 
                        "نجاح", 
                        f"تم حذف {deleted_count} معاملة بنجاح!\n\nالموظف الآن جاهز لشهر جديد."
                    )
                    self.load_employees()
                else:
                    QMessageBox.information(self, "معلومات", "لا توجد معاملات لحذفها")
                    
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل في حذف المعاملات: {str(e)}")
    
    
    # ================ نوافذ الموظفين ================
    
    def show_add_employee_dialog(self):
        """عرض نافذة إضافة موظف"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة موظف جديد")
        dialog.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        name_input = QLineEdit()
        position_input = QLineEdit()
        salary_input = QDoubleSpinBox()
        salary_input.setMaximum(999999.99)
        salary_input.setSuffix(" جنيه")
        
        hire_date_input = QDateEdit()
        hire_date_input.setDate(QDate.currentDate())
        hire_date_input.setCalendarPopup(True)
        
        phone_input = QLineEdit()
        national_id_input = QLineEdit()
        address_input = QTextEdit()
        address_input.setMaximumHeight(80)
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        
        layout.addRow("الاسم:", name_input)
        layout.addRow("الوظيفة:", position_input)
        layout.addRow("الراتب الشهري:", salary_input)
        layout.addRow("تاريخ التعيين:", hire_date_input)
        layout.addRow("رقم الهاتف:", phone_input)
        layout.addRow("الرقم القومي:", national_id_input)
        layout.addRow("العنوان:", address_input)
        layout.addRow("ملاحظات:", notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            position = position_input.text().strip()
            salary = Decimal(str(salary_input.value()))
            hire_date = hire_date_input.date().toPython()
            phone = phone_input.text().strip() or None
            national_id = national_id_input.text().strip() or None
            address = address_input.toPlainText().strip() or None
            notes = notes_input.toPlainText().strip() or None
            
            if not name or not position:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم والوظيفة")
                return
            
            result = self.employee_controller.create_employee(
                name=name,
                position=position,
                monthly_salary=salary,
                hire_date=hire_date,
                phone=phone,
                national_id=national_id,
                address=address,
                notes=notes
            )
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
                self.load_employees()
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def show_advances_dialog(self):
        """عرض نافذة إضافة سلفة"""
        if self.employees_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا يوجد موظفين")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة سلفة")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # قائمة الموظفين
        employee_combo = QComboBox()
        result = self.employee_controller.get_all_employees()
        if result['success']:
            for emp in result['employees']:
                employee_combo.addItem(f"{emp['name']} - {emp['position']}", emp['id'])
        
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999.99)
        amount_input.setSuffix(" جنيه")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        reason_input = QLineEdit()
        
        layout.addRow("الموظف:", employee_combo)
        layout.addRow("المبلغ:", amount_input)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("السبب:", reason_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            employee_id = employee_combo.currentData()
            amount = Decimal(str(amount_input.value()))
            date_val = date_input.date().toPython()
            reason = reason_input.text().strip() or None
            
            if amount <= 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال مبلغ صحيح")
                return
            
            result = self.employee_controller.add_advance(
                employee_id=employee_id,
                amount=amount,
                date=date_val,
                reason=reason
            )
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def show_deductions_dialog(self):
        """عرض نافذة إضافة خصم"""
        if self.employees_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا يوجد موظفين")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة خصم")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # قائمة الموظفين
        employee_combo = QComboBox()
        result = self.employee_controller.get_all_employees()
        if result['success']:
            for emp in result['employees']:
                employee_combo.addItem(f"{emp['name']} - {emp['position']}", emp['id'])
        
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999.99)
        amount_input.setSuffix(" جنيه")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        type_combo = QComboBox()
        type_combo.addItem("غياب", "absence")
        type_combo.addItem("تأخير", "lateness")
        type_combo.addItem("أضرار", "damage")
        type_combo.addItem("أخرى", "other")
        
        reason_input = QLineEdit()
        
        layout.addRow("الموظف:", employee_combo)
        layout.addRow("المبلغ:", amount_input)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("النوع:", type_combo)
        layout.addRow("السبب:", reason_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            employee_id = employee_combo.currentData()
            amount = Decimal(str(amount_input.value()))
            date_val = date_input.date().toPython()
            deduction_type = type_combo.currentData()
            reason = reason_input.text().strip()
            
            if amount <= 0 or not reason:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال جميع البيانات")
                return
            
            result = self.employee_controller.add_deduction(
                employee_id=employee_id,
                amount=amount,
                date=date_val,
                reason=reason,
                deduction_type=deduction_type
            )
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def show_overtime_dialog(self):
        """عرض نافذة إضافة ساعات إضافية"""
        if self.employees_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا يوجد موظفين")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة ساعات عمل إضافية")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # قائمة الموظفين
        employee_combo = QComboBox()
        result = self.employee_controller.get_all_employees()
        if result['success']:
            for emp in result['employees']:
                employee_combo.addItem(f"{emp['name']} - {emp['position']}", emp['id'])
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        hours_input = QDoubleSpinBox()
        hours_input.setMaximum(24.0)
        hours_input.setSuffix(" ساعة")
        hours_input.setDecimals(2)
        
        rate_input = QDoubleSpinBox()
        rate_input.setMaximum(999999.99)
        rate_input.setSuffix(" جنيه/ساعة")
        rate_input.setValue(20.0)  # قيمة افتراضية
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        
        layout.addRow("الموظف:", employee_combo)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("عدد الساعات:", hours_input)
        layout.addRow("سعر الساعة:", rate_input)
        layout.addRow("ملاحظات:", notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            employee_id = employee_combo.currentData()
            date_val = date_input.date().toPython()
            hours = Decimal(str(hours_input.value()))
            rate = Decimal(str(rate_input.value()))
            notes = notes_input.toPlainText().strip() or None
            
            if hours <= 0 or rate <= 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال بيانات صحيحة")
                return
            
            result = self.employee_controller.add_overtime(
                employee_id=employee_id,
                date=date_val,
                hours=hours,
                hourly_rate=rate,
                notes=notes
            )
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def show_process_salaries_dialog(self):
        """عرض نافذة معالجة الرواتب"""
        dialog = QDialog(self)
        dialog.setWindowTitle("معالجة الرواتب الشهرية")
        dialog.setMinimumWidth(350)
        
        layout = QFormLayout()
        
        month_input = QSpinBox()
        month_input.setRange(1, 12)
        month_input.setValue(datetime.now().month)
        
        year_input = QSpinBox()
        year_input.setRange(2020, 2100)
        year_input.setValue(datetime.now().year)
        
        layout.addRow("الشهر:", month_input)
        layout.addRow("السنة:", year_input)
        
        info_label = QLabel("سيتم حساب رواتب جميع الموظفين النشطين لهذا الشهر")
        info_label.setStyleSheet("color: #3498db; padding: 10px;")
        layout.addRow(info_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            month = str(month_input.value()).zfill(2)
            year = year_input.value()
            
            reply = QMessageBox.question(
                self,
                "تأكيد",
                f"هل أنت متأكد من معالجة رواتب شهر {month}/{year} لجميع الموظفين؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                result = self.employee_controller.process_monthly_salaries(month, year)
                
                if result['success']:
                    QMessageBox.information(self, "نجاح", result['message'])
                else:
                    QMessageBox.warning(self, "خطأ", result['message'])
    
    def calculate_employee_salary(self, employee_id):
        """حساب راتب موظف"""
        dialog = QDialog(self)
        dialog.setWindowTitle("حساب الراتب")
        dialog.setMinimumWidth(350)
        
        layout = QFormLayout()
        
        month_input = QSpinBox()
        month_input.setRange(1, 12)
        month_input.setValue(datetime.now().month)
        
        year_input = QSpinBox()
        year_input.setRange(2020, 2100)
        year_input.setValue(datetime.now().year)
        
        layout.addRow("الشهر:", month_input)
        layout.addRow("السنة:", year_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            month = str(month_input.value()).zfill(2)
            year = year_input.value()
            
            result = self.employee_controller.calculate_salary(employee_id, month, year)
            
            if result['success']:
                salary = result['salary']
                msg = f"""
                الراتب الأساسي: {salary['base_salary']:.2f} جنيه
                ساعات إضافية: +{salary['overtime_amount']:.2f} جنيه
                السلف: -{salary['advances_amount']:.2f} جنيه
                الخصومات: -{salary['deductions_amount']:.2f} جنيه
                ═══════════════════════
                صافي الراتب: {salary['net_salary']:.2f} جنيه
                """
                QMessageBox.information(self, "الراتب الشهري", msg)
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def calculate_employee_salary_from_details(self, employee_id, parent_dialog):
        """حساب راتب موظف من نافذة التفاصيل"""
        self.calculate_employee_salary(employee_id)
    
    def add_advance_for_employee(self, employee_id, parent_dialog):
        """إضافة سلفة لموظف محدد من نافذة التفاصيل"""
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("إضافة سلفة")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999.99)
        amount_input.setSuffix(" جنيه")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        reason_input = QLineEdit()
        
        layout.addRow("المبلغ:", amount_input)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("السبب:", reason_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            amount = Decimal(str(amount_input.value()))
            date_val = date_input.date().toPython()
            reason = reason_input.text().strip() or None
            
            if amount <= 0:
                QMessageBox.warning(parent_dialog, "تحذير", "يرجى إدخال مبلغ صحيح")
                return
            
            result = self.employee_controller.add_advance(
                employee_id=employee_id,
                amount=amount,
                date=date_val,
                reason=reason
            )
            
            if result['success']:
                QMessageBox.information(parent_dialog, "نجاح", result['message'])
            else:
                QMessageBox.warning(parent_dialog, "خطأ", result['message'])
    
    def add_deduction_for_employee(self, employee_id, parent_dialog):
        """إضافة خصم لموظف محدد من نافذة التفاصيل"""
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("إضافة خصم")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999.99)
        amount_input.setSuffix(" جنيه")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        type_combo = QComboBox()
        type_combo.addItem("غياب", "absence")
        type_combo.addItem("تأخير", "lateness")
        type_combo.addItem("أضرار", "damage")
        type_combo.addItem("أخرى", "other")
        
        reason_input = QLineEdit()
        
        layout.addRow("المبلغ:", amount_input)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("النوع:", type_combo)
        layout.addRow("السبب:", reason_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            amount = Decimal(str(amount_input.value()))
            date_val = date_input.date().toPython()
            deduction_type = type_combo.currentData()
            reason = reason_input.text().strip()
            
            if amount <= 0 or not reason:
                QMessageBox.warning(parent_dialog, "تحذير", "يرجى إدخال جميع البيانات")
                return
            
            result = self.employee_controller.add_deduction(
                employee_id=employee_id,
                amount=amount,
                date=date_val,
                reason=reason,
                deduction_type=deduction_type
            )
            
            if result['success']:
                QMessageBox.information(parent_dialog, "نجاح", result['message'])
            else:
                QMessageBox.warning(parent_dialog, "خطأ", result['message'])
    
    def add_overtime_for_employee(self, employee_id, parent_dialog):
        """إضافة ساعات إضافية لموظف محدد من نافذة التفاصيل"""
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("إضافة ساعات عمل إضافية")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        hours_input = QDoubleSpinBox()
        hours_input.setMaximum(24.0)
        hours_input.setSuffix(" ساعة")
        hours_input.setDecimals(2)
        
        rate_input = QDoubleSpinBox()
        rate_input.setMaximum(999999.99)
        rate_input.setSuffix(" جنيه/ساعة")
        rate_input.setValue(20.0)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        
        layout.addRow("التاريخ:", date_input)
        layout.addRow("عدد الساعات:", hours_input)
        layout.addRow("سعر الساعة:", rate_input)
        layout.addRow("ملاحظات:", notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            date_val = date_input.date().toPython()
            hours = Decimal(str(hours_input.value()))
            rate = Decimal(str(rate_input.value()))
            notes = notes_input.toPlainText().strip() or None
            
            if hours <= 0 or rate <= 0:
                QMessageBox.warning(parent_dialog, "تحذير", "يرجى إدخال بيانات صحيحة")
                return
            
            result = self.employee_controller.add_overtime(
                employee_id=employee_id,
                date=date_val,
                hours=hours,
                hourly_rate=rate,
                notes=notes
            )
            
            if result['success']:
                QMessageBox.information(parent_dialog, "نجاح", result['message'])
            else:
                QMessageBox.warning(parent_dialog, "خطأ", result['message'])
    
    def delete_employee_from_details(self, employee_id, parent_dialog):
        """حذف موظف من نافذة التفاصيل"""
        reply = QMessageBox.question(
            parent_dialog,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الموظف؟\n\nسيتم حذف جميع البيانات المرتبطة به (السلف، الخصومات، الساعات الإضافية).",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.employee_controller.delete_employee(employee_id)
            
            if result['success']:
                QMessageBox.information(parent_dialog, "نجاح", result['message'])
                parent_dialog.accept()  # إغلاق نافذة التفاصيل
                self.load_employees()  # تحديث الجدول
            else:
                QMessageBox.warning(parent_dialog, "خطأ", result['message'])
    
    
    # ================ نوافذ المصاريف الإدارية ================
    
    def show_add_expense_dialog(self):
        """عرض نافذة إضافة مصروف إداري"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة مصروف إداري")
        dialog.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        type_combo = QComboBox()
        expense_model = AdministrativeExpenseModel()
        for key, value in expense_model.EXPENSE_TYPES.items():
            type_combo.addItem(value, key)
        
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(9999999.99)
        amount_input.setSuffix(" جنيه")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        description_input = QLineEdit()
        
        recurring_check = QCheckBox("مصروف متكرر")
        
        recurrence_combo = QComboBox()
        recurrence_combo.addItem("اختر الفترة...", "")
        for key, value in expense_model.RECURRENCE_PERIODS.items():
            recurrence_combo.addItem(value, key)
        recurrence_combo.setEnabled(False)
        recurring_check.toggled.connect(recurrence_combo.setEnabled)
        
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        
        layout.addRow("النوع:", type_combo)
        layout.addRow("المبلغ:", amount_input)
        layout.addRow("التاريخ:", date_input)
        layout.addRow("الوصف:", description_input)
        layout.addRow(recurring_check)
        layout.addRow("فترة التكرار:", recurrence_combo)
        layout.addRow("ملاحظات:", notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            expense_type = type_combo.currentData()
            amount = Decimal(str(amount_input.value()))
            date_val = date_input.date().toPython()
            description = description_input.text().strip() or None
            is_recurring = recurring_check.isChecked()
            recurrence_period = recurrence_combo.currentData() if is_recurring else None
            notes = notes_input.toPlainText().strip() or None
            
            if amount <= 0:
                QMessageBox.warning(self, "تحذير", "يرجى إدخال مبلغ صحيح")
                return
            
            if is_recurring and not recurrence_period:
                QMessageBox.warning(self, "تحذير", "يرجى تحديد فترة التكرار")
                return
            
            result = self.admin_expense_controller.create_expense(
                expense_type=expense_type,
                amount=amount,
                date=date_val,
                description=description,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period,
                notes=notes
            )
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
                self.load_admin_expenses()
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    def show_recurring_expenses(self):
        """عرض المصاريف المتكررة"""
        result = self.admin_expense_controller.get_recurring_expenses()
        
        if result['success']:
            if not result['expenses']:
                QMessageBox.information(self, "معلومات", "لا توجد مصاريف متكررة")
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle("المصاريف المتكررة")
            dialog.setMinimumSize(700, 400)
            
            layout = QVBoxLayout(dialog)
            
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "النوع", "المبلغ", "آخر تسجيل", "فترة التكرار", "الوصف", "ملاحظات"
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            expenses = result['expenses']
            table.setRowCount(len(expenses))
            
            for row, exp in enumerate(expenses):
                table.setItem(row, 0, QTableWidgetItem(exp.get('expense_type_ar', exp['expense_type'])))
                table.setItem(row, 1, QTableWidgetItem(f"{exp['amount']:.2f} جنيه"))
                table.setItem(row, 2, QTableWidgetItem(exp['date']))
                table.setItem(row, 3, QTableWidgetItem(exp.get('recurrence_period_ar', exp['recurrence_period']) if exp['recurrence_period'] else '-'))
                table.setItem(row, 4, QTableWidgetItem(exp['description'] or '-'))
                table.setItem(row, 5, QTableWidgetItem(exp['notes'] or '-'))
            
            layout.addWidget(table)
            
            close_btn = QPushButton("إغلاق")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
        else:
            QMessageBox.warning(self, "خطأ", result['message'])
    
    
    def delete_expense(self, expense_id):
        """حذف مصروف إداري"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا المصروف؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.admin_expense_controller.delete_expense(expense_id)
            
            if result['success']:
                QMessageBox.information(self, "نجاح", result['message'])
                self.load_admin_expenses()
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
    
    # ================ التقارير ================
    
    def generate_admin_report(self):
        """إنشاء تقرير الإداريات"""
        try:
            start_date = self.report_start_date.date().toPython()
            end_date = self.report_end_date.date().toPython()
            
            # حساب تكلفة الرواتب
            emp_model = EmployeeModel()
            total_salaries = Decimal('0')
            
            months = []
            current = start_date
            while current <= end_date:
                month = str(current.month).zfill(2)
                year = current.year
                salary_cost = emp_model.get_monthly_salary_cost(month, year)
                total_salaries += salary_cost
                months.append((month, year, salary_cost))
                
                # الانتقال للشهر التالي
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
            
            # حساب المصاريف الإدارية
            admin_expense_model = AdministrativeExpenseModel()
            total_admin_expenses = admin_expense_model.get_total_expenses(start_date, end_date)
            expenses_summary = admin_expense_model.get_expenses_by_type_summary(start_date, end_date)
            
            # إنشاء التقرير
            report = "=" * 60 + "\n"
            report += "تقرير الإداريات الشامل\n"
            report += f"من {start_date} إلى {end_date}\n"
            report += "=" * 60 + "\n\n"
            
            report += "📊 ملخص الرواتب:\n"
            report += "-" * 60 + "\n"
            for month, year, cost in months:
                report += f"  {month}/{year}: {cost:.2f} جنيه\n"
            report += f"\nإجمالي الرواتب: {total_salaries:.2f} جنيه\n\n"
            
            report += "💰 ملخص المصاريف الإدارية:\n"
            report += "-" * 60 + "\n"
            for exp_summary in expenses_summary:
                report += f"  {exp_summary['expense_type_ar']}: {exp_summary['total_amount']:.2f} جنيه\n"
            report += f"\nإجمالي المصاريف الإدارية: {total_admin_expenses:.2f} جنيه\n\n"
            
            total_costs = total_salaries + total_admin_expenses
            report += "=" * 60 + "\n"
            report += f"إجمالي التكاليف الإدارية: {total_costs:.2f} جنيه\n"
            report += "=" * 60 + "\n"
            
            self.report_text.setPlainText(report)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء التقرير: {str(e)}")

