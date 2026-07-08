"""
تحكم المصاريف الإدارية
Administrative Expense Controller
"""

import sys
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.administrative_expense_model import AdministrativeExpenseModel
from utils.helpers import format_currency, format_time
from utils.permissions import can_manage_system

class AdministrativeExpenseController:
    """تحكم المصاريف الإدارية"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.expense_model = AdministrativeExpenseModel()
    
    def validate_permissions(self) -> bool:
        """التحقق من صلاحيات إدارة المصاريف الإدارية"""
        try:
            return can_manage_system(self.current_user.get('role', ''))
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    def create_expense(self, expense_type: str, amount: Decimal, date: date,
                      description: str = None, is_recurring: bool = False,
                      recurrence_period: str = None, notes: str = None) -> Dict[str, Any]:
        """إنشاء مصروف إداري جديد"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإضافة مصاريف إدارية'
                }
            
            # التحقق من البيانات
            if not expense_type or amount <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال جميع البيانات المطلوبة'
                }
            
            # التحقق من الفترة التكرارية
            if is_recurring and not recurrence_period:
                return {
                    'success': False,
                    'message': 'يرجى تحديد فترة التكرار للمصروف المتكرر'
                }
            
            expense_id = self.expense_model.create_expense(
                expense_type=expense_type,
                amount=amount,
                date=date,
                description=description,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period,
                notes=notes,
                created_by=self.current_user.get('id')
            )
            
            if expense_id:
                return {
                    'success': True,
                    'message': f'تم إضافة المصروف بقيمة {format_currency(amount)} بنجاح',
                    'expense_id': expense_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة المصروف'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء المصروف الإداري: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_all_expenses(self) -> Dict[str, Any]:
        """الحصول على جميع المصاريف الإدارية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض المصاريف الإدارية'
                }
            
            expenses = self.expense_model.get_all_expenses()
            
            return {
                'success': True,
                'expenses': expenses
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف الإدارية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_expenses_by_date_range(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على المصاريف الإدارية في فترة زمنية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض المصاريف الإدارية'
                }
            
            expenses = self.expense_model.get_expenses_by_date_range(start_date, end_date)
            
            return {
                'success': True,
                'expenses': expenses,
                'total': sum(Decimal(str(e['amount'])) for e in expenses)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف الإدارية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_expenses_by_type(self, expense_type: str, start_date: date = None,
                            end_date: date = None) -> Dict[str, Any]:
        """الحصول على المصاريف الإدارية حسب النوع"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض المصاريف الإدارية'
                }
            
            expenses = self.expense_model.get_expenses_by_type(expense_type, start_date, end_date)
            
            return {
                'success': True,
                'expenses': expenses,
                'total': sum(Decimal(str(e['amount'])) for e in expenses)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف حسب النوع: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_recurring_expenses(self) -> Dict[str, Any]:
        """الحصول على المصاريف المتكررة"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض المصاريف الإدارية'
                }
            
            expenses = self.expense_model.get_recurring_expenses()
            
            return {
                'success': True,
                'expenses': expenses
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف المتكررة: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def update_expense(self, expense_id: int, **kwargs) -> Dict[str, Any]:
        """تحديث مصروف إداري"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتعديل المصاريف الإدارية'
                }
            
            success = self.expense_model.update_expense(expense_id, **kwargs)
            
            if success:
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
            logger.error(f"خطأ في تحديث المصروف الإداري: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def delete_expense(self, expense_id: int) -> Dict[str, Any]:
        """حذف مصروف إداري"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف المصاريف الإدارية'
                }
            
            success = self.expense_model.delete_expense(expense_id)
            
            if success:
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
            logger.error(f"خطأ في حذف المصروف الإداري: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def search_expenses(self, search_term: str) -> Dict[str, Any]:
        """البحث في المصاريف الإدارية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية للبحث في المصاريف الإدارية'
                }
            
            expenses = self.expense_model.search_expenses(search_term)
            
            return {
                'success': True,
                'expenses': expenses
            }
            
        except Exception as e:
            logger.error(f"خطأ في البحث في المصاريف الإدارية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ إحصائيات وتقارير ============
    
    def get_monthly_total(self, month: str, year: int) -> Dict[str, Any]:
        """الحصول على إجمالي المصاريف الإدارية لشهر معين"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض إحصائيات المصاريف الإدارية'
                }
            
            total = self.expense_model.get_monthly_total(month, year)
            
            return {
                'success': True,
                'total': total,
                'formatted_total': format_currency(total)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إجمالي المصاريف الشهرية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_expenses_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على ملخص المصاريف الإدارية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض ملخص المصاريف الإدارية'
                }
            
            summary = self.expense_model.get_expenses_by_type_summary(start_date, end_date)
            total = self.expense_model.get_total_expenses(start_date, end_date)
            
            return {
                'success': True,
                'summary': summary,
                'total': total,
                'formatted_total': format_currency(total)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملخص المصاريف: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_statistics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على إحصائيات المصاريف الإدارية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض إحصائيات المصاريف الإدارية'
                }
            
            stats = self.expense_model.get_statistics(start_date, end_date)
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المصاريف الإدارية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_average_monthly_expenses(self, months: int = 6) -> Dict[str, Any]:
        """الحصول على متوسط المصاريف الإدارية الشهرية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض متوسط المصاريف الإدارية'
                }
            
            average = self.expense_model.get_average_monthly_expenses(months)
            
            return {
                'success': True,
                'average': average,
                'formatted_average': format_currency(average)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على متوسط المصاريف الشهرية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_expense_types(self) -> Dict[str, Any]:
        """الحصول على أنواع المصاريف المتاحة"""
        return {
            'success': True,
            'expense_types': self.expense_model.EXPENSE_TYPES
        }
    
    def get_recurrence_periods(self) -> Dict[str, Any]:
        """الحصول على فترات التكرار المتاحة"""
        return {
            'success': True,
            'recurrence_periods': self.expense_model.RECURRENCE_PERIODS
        }

