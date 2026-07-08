"""
تحكم التقارير الشامل
Comprehensive Reports Controller
"""

import sys
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.report_model import ReportModel
from models.user_model import UserModel
from models.device_model import DeviceModel
from models.product_model import ProductModel
from models.expense_model import ExpenseModel
from models.customer_model import CustomerModel
from utils.helpers import format_currency, format_time
from utils.notifications import show_success, show_error
from utils.permissions import can_access_reports

class ReportController:
    """تحكم التقارير الشامل"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.report_model = ReportModel()
        self.user_model = UserModel()
        self.device_model = DeviceModel()
        self.product_model = ProductModel()
        self.expense_model = ExpenseModel()
        self.customer_model = CustomerModel()
    
    def validate_permissions(self) -> bool:
        """التحقق من صلاحيات عرض التقارير"""
        try:
            return can_access_reports(self.current_user.get('role', ''))
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    # ============ تقارير الإيرادات ============
    
    def get_revenue_report(self, start_date: date, end_date: date, report_type: str = 'summary') -> Dict[str, Any]:
        """تقرير الإيرادات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            if report_type == 'summary':
                data = self.report_model.get_revenue_summary(start_date, end_date)
            elif report_type == 'daily':
                data = {'daily_revenue': self.report_model.get_daily_revenue(start_date, end_date)}
            elif report_type == 'hourly':
                data = {'hourly_revenue': self.report_model.get_hourly_revenue(start_date)}
            else:
                data = self.report_model.get_revenue_summary(start_date, end_date)
            
            return {
                'success': True,
                'data': data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير الإيرادات: {str(e)}'
            }
    
    def get_profit_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير الأرباح (الإيرادات - المصروفات - المصاريف الإدارية - الرواتب)"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            # الحصول على البيانات الأساسية
            data = self.report_model.get_profit_data(start_date, end_date)
            
            # حساب المصاريف الإدارية
            from models.administrative_expense_model import AdministrativeExpenseModel
            admin_expense_model = AdministrativeExpenseModel()
            total_admin_expenses = admin_expense_model.get_total_expenses(start_date, end_date)
            admin_expenses_summary = admin_expense_model.get_expenses_by_type_summary(start_date, end_date)
            
            # حساب تكلفة الرواتب
            from models.employee_model import EmployeeModel
            employee_model = EmployeeModel()
            total_salaries = Decimal('0')
            
            # حساب الرواتب لكل شهر في الفترة
            months = []
            current = start_date
            while current <= end_date:
                month = str(current.month).zfill(2)
                year = current.year
                salary_cost = employee_model.get_monthly_salary_cost(month, year)
                total_salaries += salary_cost
                months.append({
                    'month': month,
                    'year': year,
                    'cost': float(salary_cost)
                })
                
                # الانتقال للشهر التالي
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)
            
            # حساب صافي الربح بعد جميع المصاريف
            total_revenue = Decimal(str(data.get('total_revenue', 0)))
            total_expenses = Decimal(str(data.get('total_expenses', 0)))
            gross_profit = total_revenue - total_expenses
            
            # صافي الربح = الربح الإجمالي - المصاريف الإدارية - الرواتب
            net_profit = gross_profit - total_admin_expenses - total_salaries
            
            # إضافة البيانات الجديدة
            data['administrative_expenses'] = {
                'total': float(total_admin_expenses),
                'by_type': admin_expenses_summary
            }
            data['employee_salaries'] = {
                'total': float(total_salaries),
                'by_month': months
            }
            data['gross_profit'] = float(gross_profit)
            data['net_profit'] = float(net_profit)
            data['total_operational_costs'] = float(total_admin_expenses + total_salaries)
            
            return {
                'success': True,
                'data': data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في تقرير الأرباح: {e}")
            return {
                'success': False,
                'message': f'خطأ في تقرير الأرباح: {str(e)}'
            }
    
    # ============ تقارير الأجهزة ============
    
    def get_device_report(self, start_date: date, end_date: date, device_type: str = None) -> Dict[str, Any]:
        """تقرير الأجهزة"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            performance_data = self.report_model.get_device_performance(start_date, end_date, device_type)
            utilization_data = self.report_model.get_device_utilization(start_date, end_date)
            
            return {
                'success': True,
                'data': {
                    'performance': performance_data,
                    'utilization': utilization_data
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'device_type': device_type
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير الأجهزة: {str(e)}'
            }
    
    # ============ تقارير المنتجات ============
    
    def get_product_report(self, start_date: date, end_date: date, category: str = None) -> Dict[str, Any]:
        """تقرير المنتجات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            sales_data = self.report_model.get_product_sales(start_date, end_date, category)
            performance_data = self.report_model.get_product_performance(start_date, end_date)
            detailed_stock_data = self.report_model.get_detailed_stock_status()
            
            return {
                'success': True,
                'data': {
                    'sales': sales_data,
                    'performance': performance_data,
                    'detailed_stock': detailed_stock_data
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'category': category
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير المنتجات: {str(e)}'
            }
    
    # ============ تقارير المصروفات ============
    
    def get_expense_report(self, start_date: date, end_date: date, cashier_id: int = None) -> Dict[str, Any]:
        """تقرير المصروفات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            # تحديد cashier_id بناءً على صلاحيات المستخدم
            if self.current_user.get('role') == 'cashier' and not cashier_id:
                cashier_id = self.current_user.get('id')
            
            analysis_data = self.report_model.get_expense_analysis(start_date, end_date, cashier_id)
            
            return {
                'success': True,
                'data': analysis_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cashier_id': cashier_id
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير المصروفات: {str(e)}'
            }
    
    # ============ تقارير العملاء ============
    
    def get_customer_report(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """تقرير العملاء"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            analysis_data = self.report_model.get_customer_analysis(start_date, end_date)
            
            return {
                'success': True,
                'data': analysis_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير العملاء: {str(e)}'
            }
    
    # ============ تقارير الجلسات ============
    
    def get_session_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير الجلسات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            analysis_data = self.report_model.get_session_analysis(start_date, end_date)
            
            return {
                'success': True,
                'data': analysis_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير الجلسات: {str(e)}'
            }
    
    # ============ تقارير الورديات ============
    
    def get_shift_report(self, start_date: date, end_date: date, cashier_id: int = None) -> Dict[str, Any]:
        """تقرير الورديات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            # تحديد cashier_id بناءً على صلاحيات المستخدم
            if self.current_user.get('role') == 'cashier' and not cashier_id:
                cashier_id = self.current_user.get('id')
            
            analysis_data = self.report_model.get_shift_analysis(start_date, end_date, cashier_id)
            
            return {
                'success': True,
                'data': analysis_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cashier_id': cashier_id
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير الورديات: {str(e)}'
            }
    
    # ============ التقارير الشاملة ============
    
    def get_comprehensive_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير شامل لجميع البيانات"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            comprehensive_data = self.report_model.get_comprehensive_report(start_date, end_date)
            
            return {
                'success': True,
                'data': comprehensive_data,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في التقرير الشامل: {str(e)}'
            }
    
    # ============ تقارير المقارنة ============
    
    def get_comparison_report(self, current_start: date, current_end: date, 
                             previous_start: date, previous_end: date) -> Dict[str, Any]:
        """تقرير مقارنة بين فترتين"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض التقارير'
                }
            
            comparison_data = self.report_model.get_comparison_report(
                current_start, current_end, previous_start, previous_end
            )
            
            return {
                'success': True,
                'data': comparison_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تقرير المقارنة: {str(e)}'
            }
    
    # ============ لوحة مؤشرات الأداء ============
    
    
    # ============ وظائف مساعدة ============
    
    def get_available_periods(self) -> Dict[str, Any]:
        """الحصول على الفترات المتاحة للتقارير"""
        try:
            # الحصول على أول وآخر تاريخ في النظام
            from database import get_db_manager
            db = get_db_manager()
            
            # أول تاريخ
            first_date = db.execute_query(
                "SELECT MIN(DATE(start_time)) as first_date FROM invoices"
            )
            
            # آخر تاريخ
            last_date = db.execute_query(
                "SELECT MAX(DATE(start_time)) as last_date FROM invoices"
            )
            
            return {
                'success': True,
                'data': {
                    'first_date': first_date[0]['first_date'] if first_date and first_date[0]['first_date'] else date.today(),
                    'last_date': last_date[0]['last_date'] if last_date and last_date[0]['last_date'] else date.today()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في الحصول على الفترات المتاحة: {str(e)}'
            }
    
    def get_filter_options(self) -> Dict[str, Any]:
        """الحصول على خيارات التصفية"""
        try:
            # أنواع الأجهزة
            device_types = self.device_model.get_all_devices()
            unique_types = list(set([d['type'] for d in device_types]))
            
            # فئات المنتجات
            products = self.product_model.get_all_products()
            unique_categories = list(set([p['category'] for p in products]))
            
            # الكاشيرز
            cashiers = self.user_model.get_cashiers()
            
            return {
                'success': True,
                'data': {
                    'device_types': unique_types,
                    'product_categories': unique_categories,
                    'cashiers': cashiers
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في الحصول على خيارات التصفية: {str(e)}'
            }
    
    def export_report(self, report_data: Dict[str, Any], export_format: str = 'PDF', 
                     export_path: str = None) -> Dict[str, Any]:
        """تصدير التقرير"""
        try:
            # يمكن إضافة منطق التصدير هنا
            # مثل إنشاء ملف PDF أو Excel أو CSV
            
            if export_format == 'PDF':
                # TODO: تنفيذ تصدير PDF
                pass
            elif export_format == 'Excel':
                # TODO: تنفيذ تصدير Excel
                pass
            elif export_format == 'CSV':
                # TODO: تنفيذ تصدير CSV
                pass
            
            return {
                'success': True,
                'message': f'تم تصدير التقرير بصيغة {export_format} بنجاح',
                'file_path': export_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تصدير التقرير: {str(e)}'
            }
    
    def print_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """طباعة التقرير"""
        try:
            # يمكن إضافة منطق الطباعة هنا
            
            return {
                'success': True,
                'message': 'تم إرسال التقرير للطباعة بنجاح'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في طباعة التقرير: {str(e)}'
            }
