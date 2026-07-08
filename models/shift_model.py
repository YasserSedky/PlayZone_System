"""
موديل الورديات الاحترافي
Professional Shift Management Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class ShiftModel:
    """موديل إدارة الورديات الاحترافي"""
    
    def __init__(self):
        self.db = get_db_manager()
        self.current_shift_cache = {}  # تخزين مؤقت للوردية الحالية
    
    def create_shift(self, cashier_id: int, shift_name: str = "", notes: str = "") -> Optional[int]:
        """إنشاء وردية جديدة"""
        try:
            # التحقق من وجود وردية نشطة للكاشير
            active_shift = self.get_active_shift(cashier_id)
            if active_shift:
                logger.warning(f"الكاشير {cashier_id} لديه وردية نشطة بالفعل")
                return None
            
            # إنشاء وردية جديدة
            shift_id = self.db.execute_query(
                """INSERT INTO shifts (cashier_id, shift_name, start_time, notes, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (cashier_id, shift_name, datetime.now(), notes, 'active'),
                fetch=False
            )
            
            logger.info(f"تم إنشاء وردية جديدة للكاشير {cashier_id}")
            return shift_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الوردية: {e}")
            return None
    
    def end_shift(self, shift_id: int, notes: str = "") -> bool:
        """إنهاء الوردية"""
        try:
            # التحقق من وجود الوردية
            shift = self.get_shift_by_id(shift_id)
            if not shift:
                logger.error(f"الوردية {shift_id} غير موجودة")
                return False
            
            if shift['status'] != 'active':
                logger.warning(f"الوردية {shift_id} غير نشطة")
                return False
            
            # إنهاء الوردية
            result = self.db.execute_query(
                """UPDATE shifts SET end_time = ?, notes = ?, status = ? WHERE id = ?""",
                (datetime.now(), notes, 'completed', shift_id),
                fetch=False
            )
            
            if result:
                logger.info(f"تم إنهاء الوردية {shift_id}")
                return True
            else:
                logger.error(f"فشل في إنهاء الوردية {shift_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إنهاء الوردية: {e}")
            return False
    
    def get_active_shift(self, cashier_id: int = None) -> Optional[Dict[str, Any]]:
        """الحصول على الوردية النشطة العامة (مشتركة لجميع الكاشيرات)"""
        try:
            if cashier_id:
                # للحفاظ على التوافق مع الكود القديم
                result = self.db.execute_query(
                    """SELECT s.*, u.username as cashier_name 
                       FROM shifts s
                       LEFT JOIN users u ON s.cashier_id = u.id
                       WHERE s.cashier_id = ? AND s.status = 'active' 
                       ORDER BY s.start_time DESC LIMIT 1""",
                    (cashier_id,)
                )
                return result[0] if result else None
            else:
                # الوردية النشطة العامة
                result = self.db.execute_query(
                    """SELECT s.*, u.username as cashier_name 
                       FROM shifts s
                       LEFT JOIN users u ON s.cashier_id = u.id
                       WHERE s.status = 'active' 
                       ORDER BY s.start_time DESC LIMIT 1""",
                    ()
                )
                return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الوردية النشطة: {e}")
            return None
    
    def get_active_shared_shift(self) -> Optional[Dict[str, Any]]:
        """الحصول على الوردية النشطة المشتركة لجميع الكاشيرات"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.status = 'active' 
                   ORDER BY s.start_time DESC LIMIT 1""",
                ()
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الوردية النشطة المشتركة: {e}")
            return None
    
    def get_all_active_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الورديات النشطة"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.status = 'active' 
                   ORDER BY s.start_time DESC""",
                ()
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الورديات النشطة: {e}")
            return []
    
    def get_shift_by_id(self, shift_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على وردية بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.id = ?""",
                (shift_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الوردية: {e}")
            return None
    
    def get_today_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على ورديات اليوم"""
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.start_time >= ? AND s.start_time <= ?
                   ORDER BY s.start_time DESC""",
                (start_of_day, end_of_day)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ورديات اليوم: {e}")
            return []
    
    def get_shifts_by_cashier(self, cashier_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """الحصول على ورديات الكاشير"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.cashier_id = ? 
                   ORDER BY s.start_time DESC 
                   LIMIT ?""",
                (cashier_id, limit)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ورديات الكاشير: {e}")
            return []
    
    def get_shift_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """الحصول على إحصائيات الورديات"""
        try:
            shifts = self.get_shifts_by_date_range(start_date, end_date)
            
            if not shifts:
                return {
                    'total_shifts': 0,
                    'active_shifts': 0,
                    'completed_shifts': 0,
                    'total_duration_hours': 0,
                    'average_duration_hours': 0
                }
            
            total_shifts = len(shifts)
            active_shifts = len([s for s in shifts if s['status'] == 'active'])
            completed_shifts = len([s for s in shifts if s['status'] == 'completed'])
            
            total_duration = 0
            for shift in shifts:
                if shift['end_time']:
                    duration = shift['end_time'] - shift['start_time']
                    total_duration += duration.total_seconds() / 3600
                elif shift['status'] == 'active':
                    duration = datetime.now() - shift['start_time']
                    total_duration += duration.total_seconds() / 3600
            
            average_duration = total_duration / total_shifts if total_shifts > 0 else 0
            
            return {
                'total_shifts': total_shifts,
                'active_shifts': active_shifts,
                'completed_shifts': completed_shifts,
                'total_duration_hours': total_duration,
                'average_duration_hours': average_duration
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الورديات: {e}")
            return {}
    
    def get_shifts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """الحصول على الورديات في فترة زمنية"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.start_time >= ? AND s.start_time <= ?
                   ORDER BY s.start_time DESC""",
                (start_date, end_date)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الورديات: {e}")
            return []
    
    def get_shift_summary(self, shift_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على ملخص الوردية"""
        try:
            # معلومات الوردية الأساسية
            shift = self.get_shift_by_id(shift_id)
            if not shift:
                return None
            
            # إحصائيات الفواتير
            invoices_result = self.db.execute_query(
                """SELECT COUNT(*) as total_invoices, 
                          COALESCE(SUM(total_amount), 0) as total_revenue
                   FROM invoices 
                   WHERE shift_id = ?""",
                (shift_id,)
            )
            
            # إحصائيات المصروفات
            expenses_result = self.db.execute_query(
                """SELECT COUNT(*) as total_expenses, 
                          COALESCE(SUM(amount), 0) as total_expense_amount
                   FROM expenses 
                   WHERE shift_id = ?""",
                (shift_id,)
            )
            
            summary = {
                'shift': shift,
                'invoices': invoices_result[0] if invoices_result else {'total_invoices': 0, 'total_revenue': 0},
                'expenses': expenses_result[0] if expenses_result else {'total_expenses': 0, 'total_expense_amount': 0}
            }
            
            # حساب مدة الوردية
            if shift['end_time']:
                duration = shift['end_time'] - shift['start_time']
                summary['duration_hours'] = duration.total_seconds() / 3600
            else:
                duration = datetime.now() - shift['start_time']
                summary['duration_hours'] = duration.total_seconds() / 3600
                summary['is_active'] = True
            
            return summary
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملخص الوردية: {e}")
            return None
    
    def clear_shift_data_for_cashier(self, cashier_id: int) -> bool:
        """تفريغ بيانات الفواتير والمصروفات للكاشير عند بدء وردية جديدة"""
        try:
            # هذا الوظيفة تهدف إلى "تفريغ" عرض البيانات للكاشير
            # وليس حذف البيانات الفعلية من قاعدة البيانات
            # البيانات الفعلية تبقى محفوظة للتقارير والتدقيق
            
            # مسح التخزين المؤقت للوردية الحالية
            if cashier_id in self.current_shift_cache:
                del self.current_shift_cache[cashier_id]
            
            logger.info(f"تم تفريغ بيانات العرض للكاشير {cashier_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تفريغ بيانات الكاشير: {e}")
            return False
    
    def get_cashier_shift_invoices(self, cashier_id: int = None, shift_id: int = None) -> List[Dict[str, Any]]:
        """الحصول على فواتير الوردية النشطة المشتركة"""
        try:
            if shift_id:
                # فواتير وردية محددة
                result = self.db.execute_query(
                    """SELECT i.*, 
                              CASE 
                                  WHEN i.device_id = 0 AND i.pricing_type = 'admin' AND i.customer_phone IS NOT NULL 
                                  THEN 'خدمة عملاء - ' || i.customer_phone
                                  ELSE COALESCE(d.name, 'غير محدد')
                              END as device_name,
                              u1.username as cashier_open_name,
                              u2.username as cashier_close_name
                       FROM invoices i
                       LEFT JOIN devices d ON i.device_id = d.id
                       LEFT JOIN users u1 ON i.cashier_open = u1.id
                       LEFT JOIN users u2 ON i.cashier_close = u2.id
                       WHERE i.shift_id = ? AND i.end_time IS NOT NULL
                       ORDER BY i.start_time DESC""",
                    (shift_id,)
                )
            else:
                # فواتير الوردية النشطة المشتركة
                active_shift = self.get_active_shared_shift()
                if not active_shift:
                    return []
                
                result = self.db.execute_query(
                    """SELECT i.*, 
                              CASE 
                                  WHEN i.device_id = 0 AND i.pricing_type = 'admin' AND i.customer_phone IS NOT NULL 
                                  THEN 'خدمة عملاء - ' || i.customer_phone
                                  ELSE COALESCE(d.name, 'غير محدد')
                              END as device_name,
                              u1.username as cashier_open_name,
                              u2.username as cashier_close_name
                       FROM invoices i
                       LEFT JOIN devices d ON i.device_id = d.id
                       LEFT JOIN users u1 ON i.cashier_open = u1.id
                       LEFT JOIN users u2 ON i.cashier_close = u2.id
                       WHERE i.shift_id = ? AND i.end_time IS NOT NULL
                       ORDER BY i.start_time DESC""",
                    (active_shift['id'],)
                )
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على فواتير الوردية: {e}")
            return []
    
    def get_cashier_shift_expenses(self, cashier_id: int = None, shift_id: int = None) -> List[Dict[str, Any]]:
        """الحصول على مصروفات الوردية النشطة المشتركة"""
        try:
            if shift_id:
                # مصروفات وردية محددة
                result = self.db.execute_query(
                    """SELECT e.*, u.username as cashier_name
                       FROM expenses e
                       LEFT JOIN users u ON e.cashier_id = u.id
                       WHERE e.shift_id = ?
                       ORDER BY e.date_time DESC""",
                    (shift_id,)
                )
            else:
                # مصروفات الوردية النشطة المشتركة
                active_shift = self.get_active_shared_shift()
                if not active_shift:
                    return []
                
                result = self.db.execute_query(
                    """SELECT e.*, u.username as cashier_name
                       FROM expenses e
                       LEFT JOIN users u ON e.cashier_id = u.id
                       WHERE e.shift_id = ?
                       ORDER BY e.date_time DESC""",
                    (active_shift['id'],)
                )
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مصروفات الوردية: {e}")
            return []
    
    def get_shift_performance_metrics(self, shift_id: int) -> Dict[str, Any]:
        """الحصول على مؤشرات أداء الوردية"""
        try:
            shift = self.get_shift_by_id(shift_id)
            if not shift:
                return {}
            
            # إحصائيات الفواتير
            invoices_stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_invoice_amount,
                    COALESCE(MAX(total_amount), 0) as max_invoice_amount,
                    COALESCE(MIN(total_amount), 0) as min_invoice_amount
                   FROM invoices 
                   WHERE shift_id = ?""",
                (shift_id,)
            )
            
            # إحصائيات المصروفات
            expenses_stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_expenses,
                    COALESCE(SUM(amount), 0) as total_expense_amount,
                    COALESCE(AVG(amount), 0) as avg_expense_amount
                   FROM expenses 
                   WHERE shift_id = ?""",
                (shift_id,)
            )
            
            # إحصائيات الجلسات
            sessions_stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed_sessions,
                    COALESCE(SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END), 0) as active_sessions
                   FROM sessions 
                   WHERE shift_id = ?""",
                (shift_id,)
            )
            
            # حساب مدة الوردية
            start_time = shift['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            end_time = shift['end_time']
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = end_time - start_time
                is_active = False
            else:
                duration = datetime.now() - start_time
                is_active = True
            
            duration_hours = duration.total_seconds() / 3600
            
            # حساب الإيراد في الساعة
            revenue_per_hour = 0
            if duration_hours > 0 and invoices_stats and invoices_stats[0]['total_revenue']:
                revenue_per_hour = invoices_stats[0]['total_revenue'] / duration_hours
            
            return {
                'shift_info': shift,
                'duration_hours': duration_hours,
                'is_active': is_active,
                'invoices': invoices_stats[0] if invoices_stats else {},
                'expenses': expenses_stats[0] if expenses_stats else {},
                'sessions': sessions_stats[0] if sessions_stats else {},
                'revenue_per_hour': revenue_per_hour,
                'net_profit': (invoices_stats[0]['total_revenue'] if invoices_stats else 0) - 
                             (expenses_stats[0]['total_expense_amount'] if expenses_stats else 0)
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على مؤشرات أداء الوردية: {e}")
            return {}
    
    def validate_shift_transition(self, cashier_id: int, new_shift_name: str = "") -> Dict[str, Any]:
        """التحقق من إمكانية بدء وردية جديدة"""
        try:
            # التحقق من وجود وردية نشطة
            active_shift = self.get_active_shift(cashier_id)
            
            if active_shift:
                return {
                    'can_start': False,
                    'reason': 'active_shift_exists',
                    'message': 'لديك وردية نشطة بالفعل، يجب إنهاؤها أولاً',
                    'active_shift': active_shift
                }
            
            # التحقق من وجود ورديات غير مكتملة اليوم
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            incomplete_shifts = self.db.execute_query(
                """SELECT COUNT(*) as count
                   FROM shifts 
                   WHERE cashier_id = ? 
                   AND start_time >= ? 
                   AND start_time <= ?
                   AND status = 'active'""",
                (cashier_id, start_of_day, end_of_day)
            )
            
            if incomplete_shifts and incomplete_shifts[0]['count'] > 0:
                return {
                    'can_start': False,
                    'reason': 'incomplete_shifts_today',
                    'message': 'يوجد ورديات غير مكتملة اليوم، يرجى مراجعة المدير'
                }
            
            return {
                'can_start': True,
                'message': 'يمكن بدء وردية جديدة'
            }
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من إمكانية بدء وردية: {e}")
            return {
                'can_start': False,
                'reason': 'error',
                'message': f'خطأ في التحقق: {str(e)}'
            }
