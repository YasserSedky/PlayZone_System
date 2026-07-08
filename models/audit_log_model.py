"""
موديل سجل التدقيق
Audit Log Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import json
import logging

logger = logging.getLogger(__name__)

class AuditLogModel:
    """موديل إدارة سجل التدقيق"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_audit_log(self, entity_type: str, entity_id: int, action: str,
                        performed_by: int, reason: Optional[str] = None,
                        old_value: Optional[Dict] = None, new_value: Optional[Dict] = None) -> Optional[int]:
        """إنشاء سجل تدقيق جديد"""
        try:
            audit_data = {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'action': action,
                'performed_by': performed_by,
                'reason': reason,
                'old_value': json.dumps(old_value) if old_value else None,
                'new_value': json.dumps(new_value) if new_value else None
            }
            
            log_id = self.db.execute_query(
                """INSERT INTO audit_log 
                   (entity_type, entity_id, action, performed_by, reason, old_value, new_value) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                tuple(audit_data.values()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء سجل تدقيق: {entity_type} - {action}")
            return log_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء سجل التدقيق: {e}")
            return None
    
    def get_audit_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على سجل تدقيق بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT al.*, u.username as performed_by_name
                   FROM audit_log al
                   LEFT JOIN users u ON al.performed_by = u.id
                   WHERE al.id = ?""",
                (log_id,)
            )
            
            if result:
                log_entry = result[0]
                # تحويل JSON strings إلى objects
                if log_entry['old_value']:
                    try:
                        log_entry['old_value'] = json.loads(log_entry['old_value'])
                    except:
                        pass
                if log_entry['new_value']:
                    try:
                        log_entry['new_value'] = json.loads(log_entry['new_value'])
                    except:
                        pass
                return log_entry
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجل التدقيق: {e}")
            return None
    
    def get_audit_logs(self, entity_type: Optional[str] = None,
                      entity_id: Optional[int] = None,
                      action: Optional[str] = None,
                      performed_by: Optional[int] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """الحصول على سجلات التدقيق"""
        try:
            query = """
                SELECT al.*, u.username as performed_by_name
                FROM audit_log al
                LEFT JOIN users u ON al.performed_by = u.id
            """
            
            params = []
            conditions = []
            
            if entity_type:
                conditions.append("al.entity_type = ?")
                params.append(entity_type)
            
            if entity_id:
                conditions.append("al.entity_id = ?")
                params.append(entity_id)
            
            if action:
                conditions.append("al.action = ?")
                params.append(action)
            
            if performed_by:
                conditions.append("al.performed_by = ?")
                params.append(performed_by)
            
            if start_date:
                conditions.append("al.performed_at >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("al.performed_at <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY al.performed_at DESC LIMIT ?"
            params.append(limit)
            
            result = self.db.execute_query(query, tuple(params))
            
            # تحويل JSON strings إلى objects
            for log_entry in result:
                if log_entry['old_value']:
                    try:
                        log_entry['old_value'] = json.loads(log_entry['old_value'])
                    except:
                        pass
                if log_entry['new_value']:
                    try:
                        log_entry['new_value'] = json.loads(log_entry['new_value'])
                    except:
                        pass
            
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجلات التدقيق: {e}")
            return []
    
    def get_entity_audit_logs(self, entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
        """الحصول على سجلات تدقيق كيان معين"""
        return self.get_audit_logs(entity_type=entity_type, entity_id=entity_id)
    
    def get_user_audit_logs(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على سجلات تدقيق مستخدم معين"""
        start_date = datetime.now() - timedelta(days=days)
        return self.get_audit_logs(performed_by=user_id, start_date=start_date)
    
    def search_audit_logs(self, search_term: str, start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """البحث في سجلات التدقيق"""
        try:
            search_pattern = f"%{search_term}%"
            query = """
                SELECT al.*, u.username as performed_by_name
                FROM audit_log al
                LEFT JOIN users u ON al.performed_by = u.id
                WHERE (al.entity_type LIKE ? OR al.action LIKE ? OR al.reason LIKE ? OR u.username LIKE ?)
            """
            
            params = [search_pattern, search_pattern, search_pattern, search_pattern]
            
            if start_date:
                query += " AND al.performed_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND al.performed_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY al.performed_at DESC"
            
            result = self.db.execute_query(query, tuple(params))
            
            # تحويل JSON strings إلى objects
            for log_entry in result:
                if log_entry['old_value']:
                    try:
                        log_entry['old_value'] = json.loads(log_entry['old_value'])
                    except:
                        pass
                if log_entry['new_value']:
                    try:
                        log_entry['new_value'] = json.loads(log_entry['new_value'])
                    except:
                        pass
            
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في سجلات التدقيق: {e}")
            return []
    
    def get_audit_stats(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """الحصول على إحصائيات سجلات التدقيق"""
        try:
            stats = {}
            
            # بناء شروط التاريخ
            date_condition = ""
            params = []
            
            if start_date and end_date:
                date_condition = "WHERE performed_at BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif start_date:
                date_condition = "WHERE performed_at >= ?"
                params = [start_date]
            elif end_date:
                date_condition = "WHERE performed_at <= ?"
                params = [end_date]
            
            # إجمالي السجلات
            total_logs = self.db.execute_query(
                f"SELECT COUNT(*) as count FROM audit_log {date_condition}",
                tuple(params) if params else None
            )
            stats['total_logs'] = total_logs[0]['count'] if total_logs else 0
            
            # إحصائيات حسب نوع الكيان
            entity_stats = self.db.execute_query(
                f"""SELECT entity_type, COUNT(*) as count
                    FROM audit_log {date_condition}
                    GROUP BY entity_type
                    ORDER BY count DESC""",
                tuple(params) if params else None
            )
            stats['by_entity_type'] = entity_stats or []
            
            # إحصائيات حسب نوع العملية
            action_stats = self.db.execute_query(
                f"""SELECT action, COUNT(*) as count
                    FROM audit_log {date_condition}
                    GROUP BY action
                    ORDER BY count DESC""",
                tuple(params) if params else None
            )
            stats['by_action'] = action_stats or []
            
            # إحصائيات حسب المستخدم
            user_stats = self.db.execute_query(
                f"""SELECT u.username, COUNT(*) as count
                    FROM audit_log al
                    JOIN users u ON al.performed_by = u.id
                    {date_condition.replace('performed_at', 'al.performed_at') if date_condition else 'WHERE 1=1'}
                    GROUP BY u.id, u.username
                    ORDER BY count DESC
                    LIMIT 10""",
                tuple(params) if params else None
            )
            stats['by_user'] = user_stats or []
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات سجلات التدقيق: {e}")
            return {}
    
    def get_daily_audit_logs(self, days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على سجلات التدقيق اليومية"""
        try:
            result = self.db.execute_query(
                """SELECT DATE(performed_at) as date,
                          COUNT(*) as log_count,
                          COUNT(DISTINCT performed_by) as users_count,
                          COUNT(DISTINCT entity_type) as entity_types_count
                   FROM audit_log
                   WHERE performed_at >= DATE('now', '-{} days')
                   GROUP BY DATE(performed_at)
                   ORDER BY date DESC""".format(days)
            )
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجلات التدقيق اليومية: {e}")
            return []
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """الحصول على الأنشطة الأخيرة"""
        return self.get_audit_logs(limit=limit)
    
    def log_user_action(self, user_id: int, action: str, entity_type: str, 
                       entity_id: int, reason: Optional[str] = None,
                       old_value: Optional[Dict] = None, new_value: Optional[Dict] = None):
        """تسجيل عمل مستخدم"""
        return self.create_audit_log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_login(self, user_id: int, success: bool, reason: Optional[str] = None):
        """تسجيل تسجيل الدخول"""
        action = "login_success" if success else "login_failed"
        return self.create_audit_log(
            entity_type="user",
            entity_id=user_id,
            action=action,
            performed_by=user_id,
            reason=reason
        )
    
    def log_invoice_action(self, user_id: int, action: str, invoice_id: int,
                          reason: Optional[str] = None, old_value: Optional[Dict] = None,
                          new_value: Optional[Dict] = None):
        """تسجيل عمل على الفاتورة"""
        return self.create_audit_log(
            entity_type="invoice",
            entity_id=invoice_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_customer_action(self, user_id: int, action: str, customer_phone: str,
                           reason: Optional[str] = None, old_value: Optional[Dict] = None,
                           new_value: Optional[Dict] = None):
        """تسجيل عمل على العميل"""
        return self.create_audit_log(
            entity_type="customer",
            entity_id=customer_phone,  # استخدام رقم الهاتف كمعرف
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_expense_action(self, user_id: int, action: str, expense_id: int,
                          reason: Optional[str] = None, old_value: Optional[Dict] = None,
                          new_value: Optional[Dict] = None):
        """تسجيل عمل على المصروف"""
        return self.create_audit_log(
            entity_type="expense",
            entity_id=expense_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_device_action(self, user_id: int, action: str, device_id: int,
                         reason: Optional[str] = None, old_value: Optional[Dict] = None,
                         new_value: Optional[Dict] = None):
        """تسجيل عمل على الجهاز"""
        return self.create_audit_log(
            entity_type="device",
            entity_id=device_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_product_action(self, user_id: int, action: str, product_id: int,
                          reason: Optional[str] = None, old_value: Optional[Dict] = None,
                          new_value: Optional[Dict] = None):
        """تسجيل عمل على المنتج"""
        return self.create_audit_log(
            entity_type="product",
            entity_id=product_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_session_action(self, user_id: int, action: str, session_id: int,
                          reason: Optional[str] = None, old_value: Optional[Dict] = None,
                          new_value: Optional[Dict] = None):
        """تسجيل عمل على الجلسة"""
        return self.create_audit_log(
            entity_type="session",
            entity_id=session_id,
            action=action,
            performed_by=user_id,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """تنظيف السجلات القديمة"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            result = self.db.execute_query(
                "DELETE FROM audit_log WHERE performed_at < ?",
                (cutoff_date,),
                fetch=False
            )
            
            logger.info(f"تم حذف السجلات القديمة قبل {cutoff_date}")
            return result if isinstance(result, int) else 0
            
        except Exception as e:
            logger.error(f"خطأ في تنظيف السجلات القديمة: {e}")
            return 0
