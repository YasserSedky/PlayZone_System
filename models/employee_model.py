"""
موديل الموظفين
Employee Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class EmployeeModel:
    """موديل إدارة الموظفين"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    # ============ إدارة الموظفين ============
    
    def create_employee(self, name: str, position: str, monthly_salary: Decimal,
                       hire_date: date, phone: str = None, national_id: str = None,
                       address: str = None, notes: str = None, created_by: int = None) -> Optional[int]:
        """إنشاء موظف جديد"""
        try:
            employee_id = self.db.execute_query(
                """INSERT INTO employees (name, phone, national_id, address, position, 
                   hire_date, monthly_salary, notes, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, phone, national_id, address, position, hire_date.isoformat(),
                 float(monthly_salary), notes, created_by),
                fetch=False
            )
            
            if employee_id:
                logger.info(f"تم إنشاء موظف جديد: {name} - {position}")
            return employee_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الموظف: {e}")
            return None
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على موظف بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as created_by_name
                   FROM employees e
                   LEFT JOIN users u ON e.created_by = u.id
                   WHERE e.id = ?""",
                (employee_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الموظف: {e}")
            return None
    
    def get_all_employees(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """الحصول على جميع الموظفين"""
        try:
            query = """SELECT e.*, u.username as created_by_name
                      FROM employees e
                      LEFT JOIN users u ON e.created_by = u.id"""
            
            if not include_inactive:
                query += " WHERE e.is_active = 1"
            
            query += " ORDER BY e.name ASC"
            
            result = self.db.execute_query(query)
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جميع الموظفين: {e}")
            return []
    
    def update_employee(self, employee_id: int, **kwargs) -> bool:
        """تحديث بيانات موظف"""
        try:
            allowed_fields = ['name', 'phone', 'national_id', 'address', 'position',
                            'monthly_salary', 'is_active', 'notes']
            
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    if isinstance(value, Decimal):
                        params.append(float(value))
                    elif isinstance(value, date):
                        params.append(value.isoformat())
                    else:
                        params.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(employee_id)
            
            query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = ?"
            
            result = self.db.execute_query(query, tuple(params), fetch=False)
            
            if result:
                logger.info(f"تم تحديث الموظف {employee_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الموظف: {e}")
            return False
    
    def delete_employee(self, employee_id: int) -> bool:
        """حذف موظف"""
        try:
            result = self.db.execute_query(
                "DELETE FROM employees WHERE id = ?",
                (employee_id,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف الموظف {employee_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"خطأ في حذف الموظف: {e}")
            return False
    
    def search_employees(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث عن موظفين"""
        try:
            result = self.db.execute_query(
                """SELECT e.*, u.username as created_by_name
                   FROM employees e
                   LEFT JOIN users u ON e.created_by = u.id
                   WHERE e.name LIKE ? OR e.phone LIKE ? OR e.national_id LIKE ? OR e.position LIKE ?
                   ORDER BY e.name ASC""",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في البحث عن موظفين: {e}")
            return []
    
    # ============ إدارة السلف ============
    
    def add_advance(self, employee_id: int, amount: Decimal, date: date,
                   reason: str = None, created_by: int = None) -> Optional[int]:
        """إضافة سلفة لموظف"""
        try:
            advance_id = self.db.execute_query(
                """INSERT INTO employee_advances (employee_id, amount, date, reason, created_by) 
                   VALUES (?, ?, ?, ?, ?)""",
                (employee_id, float(amount), date.isoformat(), reason, created_by),
                fetch=False
            )
            
            if advance_id:
                logger.info(f"تم إضافة سلفة {amount} للموظف {employee_id}")
            return advance_id
            
        except Exception as e:
            logger.error(f"خطأ في إضافة السلفة: {e}")
            return None
    
    def get_employee_advances(self, employee_id: int, month: str = None, year: int = None) -> List[Dict[str, Any]]:
        """الحصول على سلف الموظف"""
        try:
            query = """SELECT ea.*, e.name as employee_name, u.username as created_by_name
                      FROM employee_advances ea
                      LEFT JOIN employees e ON ea.employee_id = e.id
                      LEFT JOIN users u ON ea.created_by = u.id
                      WHERE ea.employee_id = ?"""
            
            params = [employee_id]
            
            if month and year:
                query += " AND strftime('%m', ea.date) = ? AND strftime('%Y', ea.date) = ?"
                params.extend([month.zfill(2), str(year)])
            
            query += " ORDER BY ea.date DESC"
            
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سلف الموظف: {e}")
            return []
    
    def mark_advance_paid(self, advance_id: int) -> bool:
        """تحديد السلفة كمدفوعة"""
        try:
            result = self.db.execute_query(
                "UPDATE employee_advances SET paid_back = 1 WHERE id = ?",
                (advance_id,),
                fetch=False
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة السلفة: {e}")
            return False
    
    def delete_advance(self, advance_id: int) -> bool:
        """حذف سلفة"""
        try:
            result = self.db.execute_query(
                "DELETE FROM employee_advances WHERE id = ?",
                (advance_id,),
                fetch=False
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في حذف السلفة: {e}")
            return False
    
    # ============ إدارة الخصومات ============
    
    def add_deduction(self, employee_id: int, amount: Decimal, date: date,
                     reason: str, deduction_type: str = 'other',
                     created_by: int = None) -> Optional[int]:
        """إضافة خصم على موظف"""
        try:
            deduction_id = self.db.execute_query(
                """INSERT INTO employee_deductions 
                   (employee_id, amount, date, reason, deduction_type, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (employee_id, float(amount), date.isoformat(), reason, deduction_type, created_by),
                fetch=False
            )
            
            if deduction_id:
                logger.info(f"تم إضافة خصم {amount} على الموظف {employee_id}")
            return deduction_id
            
        except Exception as e:
            logger.error(f"خطأ في إضافة الخصم: {e}")
            return None
    
    def get_employee_deductions(self, employee_id: int, month: str = None, year: int = None) -> List[Dict[str, Any]]:
        """الحصول على خصومات الموظف"""
        try:
            query = """SELECT ed.*, e.name as employee_name, u.username as created_by_name
                      FROM employee_deductions ed
                      LEFT JOIN employees e ON ed.employee_id = e.id
                      LEFT JOIN users u ON ed.created_by = u.id
                      WHERE ed.employee_id = ?"""
            
            params = [employee_id]
            
            if month and year:
                query += " AND strftime('%m', ed.date) = ? AND strftime('%Y', ed.date) = ?"
                params.extend([month.zfill(2), str(year)])
            
            query += " ORDER BY ed.date DESC"
            
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على خصومات الموظف: {e}")
            return []
    
    def delete_deduction(self, deduction_id: int) -> bool:
        """حذف خصم"""
        try:
            result = self.db.execute_query(
                "DELETE FROM employee_deductions WHERE id = ?",
                (deduction_id,),
                fetch=False
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في حذف الخصم: {e}")
            return False
    
    # ============ إدارة ساعات العمل الإضافية ============
    
    def add_overtime(self, employee_id: int, date: date, hours: Decimal,
                    hourly_rate: Decimal, notes: str = None,
                    created_by: int = None) -> Optional[int]:
        """إضافة ساعات عمل إضافية"""
        try:
            total_amount = hours * hourly_rate
            
            overtime_id = self.db.execute_query(
                """INSERT INTO employee_overtime 
                   (employee_id, date, hours, hourly_rate, total_amount, notes, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (employee_id, date.isoformat(), float(hours), float(hourly_rate),
                 float(total_amount), notes, created_by),
                fetch=False
            )
            
            if overtime_id:
                logger.info(f"تم إضافة {hours} ساعة عمل إضافية للموظف {employee_id}")
            return overtime_id
            
        except Exception as e:
            logger.error(f"خطأ في إضافة ساعات العمل الإضافية: {e}")
            return None
    
    def get_employee_overtime(self, employee_id: int, month: str = None, year: int = None) -> List[Dict[str, Any]]:
        """الحصول على ساعات العمل الإضافية للموظف"""
        try:
            query = """SELECT eo.*, e.name as employee_name, u.username as created_by_name
                      FROM employee_overtime eo
                      LEFT JOIN employees e ON eo.employee_id = e.id
                      LEFT JOIN users u ON eo.created_by = u.id
                      WHERE eo.employee_id = ?"""
            
            params = [employee_id]
            
            if month and year:
                query += " AND strftime('%m', eo.date) = ? AND strftime('%Y', eo.date) = ?"
                params.extend([month.zfill(2), str(year)])
            
            query += " ORDER BY eo.date DESC"
            
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ساعات العمل الإضافية: {e}")
            return []
    
    def delete_overtime(self, overtime_id: int) -> bool:
        """حذف ساعات عمل إضافية"""
        try:
            result = self.db.execute_query(
                "DELETE FROM employee_overtime WHERE id = ?",
                (overtime_id,),
                fetch=False
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في حذف ساعات العمل الإضافية: {e}")
            return False
    
    # ============ حساب الراتب ============
    
    def calculate_monthly_salary(self, employee_id: int, month: str, year: int) -> Dict[str, Decimal]:
        """حساب راتب الموظف الشهري"""
        try:
            # الحصول على الراتب الأساسي
            employee = self.get_employee_by_id(employee_id)
            if not employee:
                return {}
            
            base_salary = Decimal(str(employee['monthly_salary']))
            
            # حساب السلف غير المدفوعة
            advances = self.get_employee_advances(employee_id, month, year)
            advances_total = sum(Decimal(str(a['amount'])) for a in advances if not a['paid_back'])
            
            # حساب الخصومات
            deductions = self.get_employee_deductions(employee_id, month, year)
            deductions_total = sum(Decimal(str(d['amount'])) for d in deductions)
            
            # حساب ساعات العمل الإضافية
            overtime = self.get_employee_overtime(employee_id, month, year)
            overtime_total = sum(Decimal(str(o['total_amount'])) for o in overtime)
            
            # حساب الراتب الصافي
            net_salary = base_salary + overtime_total - advances_total - deductions_total
            
            return {
                'base_salary': base_salary,
                'overtime_amount': overtime_total,
                'advances_amount': advances_total,
                'deductions_amount': deductions_total,
                'net_salary': net_salary
            }
            
        except Exception as e:
            logger.error(f"خطأ في حساب الراتب الشهري: {e}")
            return {}
    
    def save_salary_record(self, employee_id: int, month: str, year: int,
                          base_salary: Decimal, overtime_amount: Decimal,
                          advances_amount: Decimal, deductions_amount: Decimal,
                          net_salary: Decimal, payment_date: date = None,
                          paid: bool = False, notes: str = None,
                          created_by: int = None) -> Optional[int]:
        """حفظ سجل راتب شهري"""
        try:
            record_id = self.db.execute_query(
                """INSERT OR REPLACE INTO employee_salary_records 
                   (employee_id, month, year, base_salary, overtime_amount, 
                    advances_amount, deductions_amount, net_salary, payment_date, paid, notes, created_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (employee_id, month, year, float(base_salary), float(overtime_amount),
                 float(advances_amount), float(deductions_amount), float(net_salary),
                 payment_date.isoformat() if payment_date else None,
                 1 if paid else 0, notes, created_by),
                fetch=False
            )
            
            if record_id:
                logger.info(f"تم حفظ سجل راتب الموظف {employee_id} لشهر {month}/{year}")
            return record_id
            
        except Exception as e:
            logger.error(f"خطأ في حفظ سجل الراتب: {e}")
            return None
    
    def get_salary_record(self, employee_id: int, month: str, year: int) -> Optional[Dict[str, Any]]:
        """الحصول على سجل راتب"""
        try:
            result = self.db.execute_query(
                """SELECT esr.*, e.name as employee_name, u.username as created_by_name
                   FROM employee_salary_records esr
                   LEFT JOIN employees e ON esr.employee_id = e.id
                   LEFT JOIN users u ON esr.created_by = u.id
                   WHERE esr.employee_id = ? AND esr.month = ? AND esr.year = ?""",
                (employee_id, month, year)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجل الراتب: {e}")
            return None
    
    def get_all_salary_records(self, month: str = None, year: int = None,
                              paid_only: bool = False) -> List[Dict[str, Any]]:
        """الحصول على جميع سجلات الرواتب"""
        try:
            query = """SELECT esr.*, e.name as employee_name, e.position, u.username as created_by_name
                      FROM employee_salary_records esr
                      LEFT JOIN employees e ON esr.employee_id = e.id
                      LEFT JOIN users u ON esr.created_by = u.id
                      WHERE 1=1"""
            
            params = []
            
            if month:
                query += " AND esr.month = ?"
                params.append(month)
            
            if year:
                query += " AND esr.year = ?"
                params.append(year)
            
            if paid_only:
                query += " AND esr.paid = 1"
            
            query += " ORDER BY esr.year DESC, esr.month DESC, e.name ASC"
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجلات الرواتب: {e}")
            return []
    
    def mark_salary_paid(self, record_id: int, payment_date: date = None) -> bool:
        """تحديد الراتب كمدفوع"""
        try:
            if not payment_date:
                payment_date = date.today()
            
            result = self.db.execute_query(
                "UPDATE employee_salary_records SET paid = 1, payment_date = ? WHERE id = ?",
                (payment_date.isoformat(), record_id),
                fetch=False
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة الراتب: {e}")
            return False
    
    # ============ إحصائيات ============
    
    def get_employee_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الموظفين"""
        try:
            # عدد الموظفين
            total = self.db.execute_query(
                "SELECT COUNT(*) as count FROM employees WHERE is_active = 1"
            )
            
            # إجمالي الرواتب الشهرية
            salaries = self.db.execute_query(
                "SELECT COALESCE(SUM(monthly_salary), 0) as total FROM employees WHERE is_active = 1"
            )
            
            return {
                'total_employees': total[0]['count'] if total else 0,
                'total_monthly_salaries': Decimal(str(salaries[0]['total'])) if salaries else Decimal('0')
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الموظفين: {e}")
            return {}
    
    def get_monthly_salary_cost(self, month: str, year: int) -> Decimal:
        """الحصول على إجمالي تكلفة الرواتب لشهر معين"""
        try:
            result = self.db.execute_query(
                """SELECT COALESCE(SUM(net_salary), 0) as total
                   FROM employee_salary_records
                   WHERE month = ? AND year = ?""",
                (month, year)
            )
            
            return Decimal(str(result[0]['total'])) if result else Decimal('0')
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على تكلفة الرواتب: {e}")
            return Decimal('0')

