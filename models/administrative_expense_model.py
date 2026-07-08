"""
موديل المصاريف الإدارية
Administrative Expense Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class AdministrativeExpenseModel:
    """موديل إدارة المصاريف الإدارية"""
    
    # أنواع المصاريف
    EXPENSE_TYPES = {
        'rent': 'إيجار',
        'electricity': 'كهرباء',
        'water': 'مياه',
        'gas': 'غاز',
        'internet': 'إنترنت',
        'phone': 'هاتف',
        'maintenance': 'صيانة',
        'taxes': 'ضرائب',
        'fees': 'رسوم',
        'insurance': 'تأمين',
        'other': 'أخرى'
    }
    
    RECURRENCE_PERIODS = {
        'monthly': 'شهري',
        'quarterly': 'ربع سنوي',
        'yearly': 'سنوي'
    }
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_expense(self, expense_type: str, amount: Decimal, date: date,
                      description: str = None, is_recurring: bool = False,
                      recurrence_period: str = None, notes: str = None,
                      created_by: int = None) -> Optional[int]:
        """إنشاء مصروف إداري جديد"""
        try:
            expense_id = self.db.execute_query(
                """INSERT INTO administrative_expenses 
                   (expense_type, amount, date, description, is_recurring, 
                    recurrence_period, notes, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (expense_type, float(amount), date.isoformat(), description,
                 1 if is_recurring else 0, recurrence_period, notes, created_by),
                fetch=False
            )
            
            if expense_id:
                logger.info(f"تم إنشاء مصروف إداري: {self.EXPENSE_TYPES.get(expense_type, expense_type)} - {amount} جنيه")
            return expense_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المصروف الإداري: {e}")
            return None
    
    def get_expense_by_id(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على مصروف إداري بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT ae.*, u.username as created_by_name
                   FROM administrative_expenses ae
                   LEFT JOIN users u ON ae.created_by = u.id
                   WHERE ae.id = ?""",
                (expense_id,)
            )
            
            if result:
                expense = result[0]
                expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                if expense['recurrence_period']:
                    expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
                return expense
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصروف الإداري: {e}")
            return None
    
    def get_all_expenses(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المصاريف الإدارية"""
        try:
            result = self.db.execute_query(
                """SELECT ae.*, u.username as created_by_name
                   FROM administrative_expenses ae
                   LEFT JOIN users u ON ae.created_by = u.id
                   ORDER BY ae.date DESC"""
            )
            
            if result:
                for expense in result:
                    expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                    if expense['recurrence_period']:
                        expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جميع المصاريف الإدارية: {e}")
            return []
    
    def get_expenses_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على المصاريف الإدارية في فترة زمنية"""
        try:
            result = self.db.execute_query(
                """SELECT ae.*, u.username as created_by_name
                   FROM administrative_expenses ae
                   LEFT JOIN users u ON ae.created_by = u.id
                   WHERE ae.date >= ? AND ae.date <= ?
                   ORDER BY ae.date DESC""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            if result:
                for expense in result:
                    expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                    if expense['recurrence_period']:
                        expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف الإدارية: {e}")
            return []
    
    def get_expenses_by_type(self, expense_type: str, start_date: date = None,
                            end_date: date = None) -> List[Dict[str, Any]]:
        """الحصول على المصاريف الإدارية حسب النوع"""
        try:
            query = """SELECT ae.*, u.username as created_by_name
                      FROM administrative_expenses ae
                      LEFT JOIN users u ON ae.created_by = u.id
                      WHERE ae.expense_type = ?"""
            
            params = [expense_type]
            
            if start_date:
                query += " AND ae.date >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND ae.date <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY ae.date DESC"
            
            result = self.db.execute_query(query, tuple(params))
            
            if result:
                for expense in result:
                    expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                    if expense['recurrence_period']:
                        expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف حسب النوع: {e}")
            return []
    
    def get_recurring_expenses(self) -> List[Dict[str, Any]]:
        """الحصول على المصاريف المتكررة"""
        try:
            result = self.db.execute_query(
                """SELECT ae.*, u.username as created_by_name
                   FROM administrative_expenses ae
                   LEFT JOIN users u ON ae.created_by = u.id
                   WHERE ae.is_recurring = 1
                   ORDER BY ae.expense_type ASC, ae.date DESC"""
            )
            
            if result:
                for expense in result:
                    expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                    if expense['recurrence_period']:
                        expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصاريف المتكررة: {e}")
            return []
    
    def update_expense(self, expense_id: int, **kwargs) -> bool:
        """تحديث مصروف إداري"""
        try:
            allowed_fields = ['expense_type', 'amount', 'date', 'description',
                            'is_recurring', 'recurrence_period', 'notes']
            
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    if isinstance(value, Decimal):
                        params.append(float(value))
                    elif isinstance(value, date):
                        params.append(value.isoformat())
                    elif isinstance(value, bool):
                        params.append(1 if value else 0)
                    else:
                        params.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(expense_id)
            
            query = f"UPDATE administrative_expenses SET {', '.join(update_fields)} WHERE id = ?"
            
            result = self.db.execute_query(query, tuple(params), fetch=False)
            
            if result:
                logger.info(f"تم تحديث المصروف الإداري {expense_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"خطأ في تحديث المصروف الإداري: {e}")
            return False
    
    def delete_expense(self, expense_id: int) -> bool:
        """حذف مصروف إداري"""
        try:
            result = self.db.execute_query(
                "DELETE FROM administrative_expenses WHERE id = ?",
                (expense_id,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف المصروف الإداري {expense_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"خطأ في حذف المصروف الإداري: {e}")
            return False
    
    def search_expenses(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في المصاريف الإدارية"""
        try:
            result = self.db.execute_query(
                """SELECT ae.*, u.username as created_by_name
                   FROM administrative_expenses ae
                   LEFT JOIN users u ON ae.created_by = u.id
                   WHERE ae.description LIKE ? OR ae.notes LIKE ?
                   ORDER BY ae.date DESC""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            
            if result:
                for expense in result:
                    expense['expense_type_ar'] = self.EXPENSE_TYPES.get(expense['expense_type'], expense['expense_type'])
                    if expense['recurrence_period']:
                        expense['recurrence_period_ar'] = self.RECURRENCE_PERIODS.get(expense['recurrence_period'], expense['recurrence_period'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في المصاريف الإدارية: {e}")
            return []
    
    # ============ إحصائيات ============
    
    def get_monthly_total(self, month: str, year: int) -> Decimal:
        """الحصول على إجمالي المصاريف الإدارية لشهر معين"""
        try:
            result = self.db.execute_query(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM administrative_expenses
                   WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?""",
                (month.zfill(2), str(year))
            )
            
            return Decimal(str(result[0]['total'])) if result else Decimal('0')
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إجمالي المصاريف الشهرية: {e}")
            return Decimal('0')
    
    def get_expenses_by_type_summary(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على ملخص المصاريف حسب النوع"""
        try:
            result = self.db.execute_query(
                """SELECT expense_type, COUNT(*) as count, 
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM administrative_expenses
                   WHERE date >= ? AND date <= ?
                   GROUP BY expense_type
                   ORDER BY total_amount DESC""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            if result:
                for item in result:
                    item['expense_type_ar'] = self.EXPENSE_TYPES.get(item['expense_type'], item['expense_type'])
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملخص المصاريف: {e}")
            return []
    
    def get_total_expenses(self, start_date: date, end_date: date) -> Decimal:
        """الحصول على إجمالي المصاريف الإدارية في فترة"""
        try:
            result = self.db.execute_query(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM administrative_expenses
                   WHERE date >= ? AND date <= ?""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            return Decimal(str(result[0]['total'])) if result else Decimal('0')
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إجمالي المصاريف: {e}")
            return Decimal('0')
    
    def get_statistics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على إحصائيات المصاريف الإدارية"""
        try:
            # إجمالي المصاريف
            total_result = self.db.execute_query(
                """SELECT COUNT(*) as total_expenses, 
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM administrative_expenses 
                   WHERE date >= ? AND date <= ?""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            # مصاريف حسب النوع
            type_summary = self.get_expenses_by_type_summary(start_date, end_date)
            
            # مصاريف حسب الشهر
            monthly_result = self.db.execute_query(
                """SELECT strftime('%Y-%m', date) as month,
                          COUNT(*) as count,
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM administrative_expenses 
                   WHERE date >= ? AND date <= ?
                   GROUP BY strftime('%Y-%m', date)
                   ORDER BY month DESC""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            # المصاريف المتكررة
            recurring_result = self.db.execute_query(
                """SELECT COUNT(*) as count,
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM administrative_expenses 
                   WHERE is_recurring = 1 AND date >= ? AND date <= ?""",
                (start_date.isoformat(), end_date.isoformat())
            )
            
            return {
                'total': total_result[0] if total_result else {'total_expenses': 0, 'total_amount': 0},
                'by_type': type_summary,
                'by_month': monthly_result if monthly_result else [],
                'recurring': recurring_result[0] if recurring_result else {'count': 0, 'total_amount': 0}
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المصاريف الإدارية: {e}")
            return {}
    
    def get_average_monthly_expenses(self, months: int = 6) -> Decimal:
        """الحصول على متوسط المصاريف الإدارية الشهرية"""
        try:
            result = self.db.execute_query(
                """SELECT COALESCE(AVG(monthly_total), 0) as average
                   FROM (
                       SELECT strftime('%Y-%m', date) as month,
                              SUM(amount) as monthly_total
                       FROM administrative_expenses
                       WHERE date >= date('now', '-' || ? || ' months')
                       GROUP BY strftime('%Y-%m', date)
                   )""",
                (months,)
            )
            
            return Decimal(str(result[0]['average'])) if result else Decimal('0')
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على متوسط المصاريف الشهرية: {e}")
            return Decimal('0')

