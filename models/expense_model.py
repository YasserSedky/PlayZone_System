"""
موديل المصروفات
Expense Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class ExpenseModel:
    """موديل إدارة المصروفات"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_expense(self, amount: Decimal, reason: str, cashier_id: int, 
                      shift_id: int, notes: str = "") -> Optional[int]:
        """إنشاء مصروف جديد"""
        try:
            # التحقق من وجود وردية نشطة
            from utils.shift_validation import check_active_shift
            active_shift = check_active_shift()
            if not active_shift:
                logger.error("لا يمكن إنشاء مصروف بدون وردية نشطة")
                return None
            
            expense_data = {
                'amount': float(amount),  # تحويل Decimal إلى float لـ SQLite
                'reason': reason,
                'cashier_id': cashier_id,
                'shift_id': shift_id,
                'date_time': datetime.now(),
                'notes': notes
            }
            
            expense_id = self.db.execute_query(
                """INSERT INTO expenses (amount, reason, cashier_id, shift_id, date_time, notes) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                tuple(expense_data.values()),
                fetch=False
            )
            
            # ⭐ إضافة تأخير صغير في exe للتأكد من commit
            import time
            time.sleep(0.1)  # 100 ميلي ثانية
            
            # ⭐ التحقق الفوري من نجاح الإضافة
            if expense_id:
                verification = self.get_expense_by_id(expense_id)
                if verification:
                    logger.info(f"✅ تم التحقق من إضافة المصروف {expense_id}: {reason} - {amount} جنيه")
                else:
                    logger.warning(f"⚠️ المصروف {expense_id} غير موجود بعد الإضافة! محاولة التحقق مرة أخرى...")
                    time.sleep(0.1)
                    verification = self.get_expense_by_id(expense_id)
                    if verification:
                        logger.info(f"✅ تم العثور على المصروف في المحاولة الثانية")
                    else:
                        logger.error(f"❌ فشل في العثور على المصروف بعد الإضافة")
            
            logger.info(f"تم إنشاء مصروف جديد: {reason} - {amount} جنيه")
            return expense_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المصروف: {e}")
            return None
    
    def get_expense_by_id(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على مصروف بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.id = ?""",
                (expense_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصروف: {e}")
            return None
    
    def get_all_expenses(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المصروفات"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   ORDER BY e.date_time DESC"""
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جميع المصروفات: {e}")
            return []
    
    def delete_expense(self, expense_id: int) -> bool:
        """حذف مصروف"""
        try:
            # التحقق من وجود المصروف
            existing_expense = self.get_expense_by_id(expense_id)
            if not existing_expense:
                logger.error(f"المصروف برقم {expense_id} غير موجود")
                return False
            
            # حذف المصروف
            result = self.db.execute_query(
                "DELETE FROM expenses WHERE id = ?",
                (expense_id,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف المصروف {expense_id}")
                return True
            else:
                logger.error(f"فشل في حذف المصروف {expense_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في حذف المصروف: {e}")
            return False
    
    def get_expenses_by_shift(self, shift_id: int) -> List[Dict[str, Any]]:
        """الحصول على مصروفات الوردية"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.shift_id = ?
                   ORDER BY e.date_time DESC""",
                (shift_id,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مصروفات الوردية: {e}")
            return []
    
    def get_expenses_by_cashier(self, cashier_id: int, date_from: datetime = None, 
                               date_to: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على مصروفات الكاشير"""
        try:
            query = """SELECT e.*, u.username as cashier_name
                      FROM expenses e
                      LEFT JOIN users u ON e.cashier_id = u.id
                      WHERE e.cashier_id = ?"""
            
            params = [cashier_id]
            
            if date_from:
                query += " AND e.date_time >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND e.date_time <= ?"
                params.append(date_to)
            
            query += " ORDER BY e.date_time DESC"
            
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مصروفات الكاشير: {e}")
            return []
    
    def get_expenses_by_date_range(self, date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]:
        """الحصول على المصروفات في فترة زمنية"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.date_time >= ? AND e.date_time <= ?
                   ORDER BY e.date_time DESC""",
                (date_from, date_to)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصروفات: {e}")
            return []
    
    def update_expense(self, expense_id: int, amount: Decimal = None, 
                      reason: str = None, notes: str = None, 
                      admin_password: str = None) -> bool:
        """تحديث المصروف (يتطلب باسورد المدير)"""
        try:
            # التحقق من باسورد المدير
            if admin_password:
                from models.user_model import UserModel
                user_model = UserModel()
                if not user_model.verify_admin_password(admin_password):
                    logger.error("باسورد المدير غير صحيح")
                    return False
            
            # بناء استعلام التحديث
            update_fields = []
            params = []
            
            if amount is not None:
                update_fields.append("amount = ?")
                params.append(amount)
            
            if reason is not None:
                update_fields.append("reason = ?")
                params.append(reason)
            
            if notes is not None:
                update_fields.append("notes = ?")
                params.append(notes)
            
            if not update_fields:
                return False
            
            params.append(expense_id)
            
            query = f"UPDATE expenses SET {', '.join(update_fields)} WHERE id = ?"
            
            result = self.db.execute_query(query, tuple(params), fetch=False)
            
            if result:
                logger.info(f"تم تحديث المصروف {expense_id}")
                return True
            else:
                logger.error(f"فشل في تحديث المصروف {expense_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث المصروف: {e}")
            return False
    
    def get_expense_statistics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """الحصول على إحصائيات المصروفات"""
        try:
            # إجمالي المصروفات
            total_result = self.db.execute_query(
                """SELECT COUNT(*) as total_expenses, 
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM expenses 
                   WHERE date_time >= ? AND date_time <= ?""",
                (date_from, date_to)
            )
            
            # مصروفات حسب السبب
            reason_result = self.db.execute_query(
                """SELECT reason, COUNT(*) as count, 
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM expenses 
                   WHERE date_time >= ? AND date_time <= ?
                   GROUP BY reason
                   ORDER BY total_amount DESC""",
                (date_from, date_to)
            )
            
            # مصروفات حسب الكاشير
            cashier_result = self.db.execute_query(
                """SELECT u.username as cashier_name, COUNT(*) as count,
                          COALESCE(SUM(e.amount), 0) as total_amount
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.date_time >= ? AND e.date_time <= ?
                   GROUP BY u.username
                   ORDER BY total_amount DESC""",
                (date_from, date_to)
            )
            
            # مصروفات حسب اليوم
            daily_result = self.db.execute_query(
                """SELECT DATE(date_time) as expense_date, 
                          COUNT(*) as count,
                          COALESCE(SUM(amount), 0) as total_amount
                   FROM expenses 
                   WHERE date_time >= ? AND date_time <= ?
                   GROUP BY DATE(date_time)
                   ORDER BY expense_date DESC""",
                (date_from, date_to)
            )
            
            return {
                'total': total_result[0] if total_result else {'total_expenses': 0, 'total_amount': 0},
                'by_reason': reason_result if reason_result else [],
                'by_cashier': cashier_result if cashier_result else [],
                'by_date': daily_result if daily_result else []
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المصروفات: {e}")
            return {}
    
    def get_today_expenses(self) -> List[Dict[str, Any]]:
        """الحصول على مصروفات اليوم"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            return self.get_expenses_by_date_range(start_of_day, end_of_day)
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مصروفات اليوم: {e}")
            return []
    
    def get_high_expenses(self, threshold: Decimal = Decimal('100.00')) -> List[Dict[str, Any]]:
        """الحصول على المصروفات الكبيرة"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.amount >= ?
                   ORDER BY e.amount DESC, e.date_time DESC""",
                (threshold,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المصروفات الكبيرة: {e}")
            return []
    
    def search_expenses(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في المصروفات"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as cashier_name
                   FROM expenses e
                   LEFT JOIN users u ON e.cashier_id = u.id
                   WHERE e.reason LIKE ? OR e.notes LIKE ?
                   ORDER BY e.date_time DESC""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في المصروفات: {e}")
            return []