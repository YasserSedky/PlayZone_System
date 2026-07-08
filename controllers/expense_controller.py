"""
تحكم المصروفات
Expense Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.expense_model import ExpenseModel
from models.shift_model import ShiftModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency
from utils.notifications import show_success, show_error

class ExpenseController:
    """تحكم المصروفات"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.expense_model = ExpenseModel()
        self.shift_model = ShiftModel()
        self.audit_model = AuditLogModel()
    
    def get_expenses(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على المصروفات"""
        try:
            if self.current_user['role'] == 'admin':
                # المدير يمكنه رؤية جميع المصروفات
                return self.expense_model.get_all_expenses(start_date, end_date)
            else:
                # الكاشير يمكنه رؤية مصروفاته فقط
                return self.expense_model.get_expenses_by_cashier(
                    cashier_id=self.current_user['id'],
                    start_date=start_date,
                    end_date=end_date
                )
        except Exception as e:
            show_error(f"خطأ في الحصول على المصروفات: {str(e)}")
            return []
    
    def create_expense(self, amount: Decimal, reason: str, date_time: datetime = None) -> Dict[str, Any]:
        """إنشاء مصروف جديد"""
        try:
            # التحقق من صحة البيانات
            if amount <= 0 or not reason:
                return {
                    'success': False,
                    'message': 'يرجى إدخال بيانات صحيحة'
                }
            
            # الحصول على الوردية النشطة
            active_shift = self.shift_model.get_active_shift(self.current_user['id'])
            if not active_shift:
                return {
                    'success': False,
                    'message': 'لا توجد وردية نشطة. يرجى بدء وردية جديدة'
                }
            
            # إنشاء المصروف
            expense_id = self.expense_model.create_expense(
                amount=amount,
                reason=reason,
                cashier_id=self.current_user['id'],
                shift_id=active_shift['id'],
                date_time=date_time or datetime.now()
            )
            
            if expense_id:
                # تسجيل العملية
                self.audit_model.log_expense_action(
                    user_id=self.current_user['id'],
                    action='create',
                    expense_id=expense_id,
                    reason=f'إضافة مصروف: {reason} - {format_currency(amount)}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إضافة المصروف بنجاح',
                    'expense_id': expense_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة المصروف'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إضافة المصروف: {str(e)}'
            }
    
    def update_expense(self, expense_id: int, **kwargs) -> Dict[str, Any]:
        """تحديث المصروف"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتحديث المصروفات'
                }
            
            # التحقق من وجود المصروف
            expense = self.expense_model.get_expense_by_id(expense_id)
            if not expense:
                return {
                    'success': False,
                    'message': 'المصروف غير موجود'
                }
            
            # تحديث المصروف
            success = self.expense_model.update_expense(expense_id, **kwargs)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_expense_action(
                    user_id=self.current_user['id'],
                    action='update',
                    expense_id=expense_id,
                    reason='تحديث بيانات المصروف'
                )
                
                return {
                    'success': True,
                    'message': 'تم تحديث المصروف بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث المصروف'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث المصروف: {str(e)}'
            }
    
    def delete_expense(self, expense_id: int, admin_password: str) -> Dict[str, Any]:
        """حذف المصروف (للمدير فقط)"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف المصروفات'
                }
            
            # التحقق من كلمة مرور المدير
            from utils.security import verify_password
            if not verify_password(admin_password, self.current_user['password_hash']):
                return {
                    'success': False,
                    'message': 'كلمة مرور المدير غير صحيحة'
                }
            
            # التحقق من وجود المصروف
            expense = self.expense_model.get_expense_by_id(expense_id)
            if not expense:
                return {
                    'success': False,
                    'message': 'المصروف غير موجود'
                }
            
            # حذف المصروف
            success = self.expense_model.delete_expense(expense_id)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_expense_action(
                    user_id=self.current_user['id'],
                    action='delete',
                    expense_id=expense_id,
                    reason=f'حذف مصروف: {expense["reason"]} - {format_currency(expense["amount"])}'
                )
                
                return {
                    'success': True,
                    'message': 'تم حذف المصروف بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حذف المصروف'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حذف المصروف: {str(e)}'
            }
    
    def get_expense_stats(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """الحصول على إحصائيات المصروفات"""
        try:
            return self.expense_model.get_expense_stats(start_date, end_date)
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات المصروفات: {str(e)}")
            return {}
    
    def get_high_expenses(self, threshold: Decimal = Decimal('100.00'), days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على المصروفات الكبيرة"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            return self.expense_model.get_high_expenses(
                threshold=threshold,
                start_date=start_date
            )
        except Exception as e:
            show_error(f"خطأ في الحصول على المصروفات الكبيرة: {str(e)}")
            return []
    
    def search_expenses(self, search_term: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """البحث في المصروفات"""
        try:
            return self.expense_model.search_expenses(
                search_term=search_term,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            show_error(f"خطأ في البحث في المصروفات: {str(e)}")
            return []
    
    def get_expense_categories(self) -> List[Dict[str, Any]]:
        """الحصول على فئات المصروفات الأكثر شيوعاً"""
        try:
            return self.expense_model.get_expense_categories()
        except Exception as e:
            show_error(f"خطأ في الحصول على فئات المصروفات: {str(e)}")
            return []
    
    def get_daily_expenses(self, days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على المصروفات اليومية"""
        try:
            return self.expense_model.get_daily_expenses(days)
        except Exception as e:
            show_error(f"خطأ في الحصول على المصروفات اليومية: {str(e)}")
            return []
