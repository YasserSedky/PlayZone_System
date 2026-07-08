"""
موديل الأجهزة
Device Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class DeviceModel:
    """موديل إدارة الأجهزة"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_device(self, name: str, device_type: str, price_single: Decimal, 
                     price_multi: Decimal) -> Optional[int]:
        """إنشاء جهاز جديد"""
        try:
            device_data = {
                'name': name,
                'type': device_type,
                'price_single': price_single,
                'price_multi': price_multi,
                'status': 'available'
            }
            
            device_id = self.db.execute_query(
                """INSERT INTO devices (name, type, price_single, price_multi, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                tuple(device_data.values()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء جهاز جديد: {name}")
            return device_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الجهاز: {e}")
            return None
    
    def get_device_by_id(self, device_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على جهاز بالمعرف"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM devices WHERE id = ?",
                (device_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجهاز: {e}")
            return None
    
    def get_all_devices(self, device_type: Optional[str] = None, 
                       status: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على جميع الأجهزة"""
        try:
            query = "SELECT * FROM devices"
            params = []
            conditions = []
            
            if device_type:
                conditions.append("type = ?")
                params.append(device_type)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY type, id"
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الأجهزة: {e}")
            return []
    
    def get_available_devices(self, device_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على الأجهزة المتاحة"""
        return self.get_all_devices(device_type, 'available')
    
    def get_busy_devices(self) -> List[Dict[str, Any]]:
        """الحصول على الأجهزة المشغولة"""
        return self.get_all_devices(status='busy')
    
    def update_device(self, device_id: int, **kwargs) -> bool:
        """تحديث بيانات الجهاز"""
        try:
            # إزالة القيم الفارغة
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            
            if not update_data:
                return False
            
            # بناء استعلام التحديث
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [device_id]
            
            result = self.db.execute_query(
                f"UPDATE devices SET {set_clause} WHERE id = ?",
                tuple(values),
                fetch=False
            )
            
            logger.info(f"تم تحديث الجهاز: {device_id}")
            # التحقق من أن التحديث تم بنجاح
            # لاستعلامات UPDATE، إذا لم يحدث خطأ، فالتحديث نجح
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الجهاز: {e}")
            return False
    
    def update_device_status(self, device_id: int, status: str, 
                           current_session_id: Optional[int] = None,
                           current_invoice_id: Optional[int] = None) -> bool:
        """تحديث حالة الجهاز"""
        try:
            if current_session_id is not None:
                self.db.execute_query(
                    "UPDATE devices SET status = ?, current_session_id = ?, current_invoice_id = ? WHERE id = ?",
                    (status, current_session_id, current_invoice_id, device_id),
                    fetch=False
                )
            else:
                self.db.execute_query(
                    "UPDATE devices SET status = ?, current_session_id = NULL, current_invoice_id = NULL WHERE id = ?",
                    (status, device_id),
                    fetch=False
                )
            
            logger.info(f"تم تحديث حالة الجهاز {device_id} إلى {status}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة الجهاز: {e}")
            return False
    
    def set_device_busy(self, device_id: int, session_id: int, invoice_id: int = None) -> bool:
        """تعيين الجهاز كمشغول"""
        return self.update_device_status(device_id, 'busy', session_id, invoice_id)
    
    def set_device_available(self, device_id: int) -> bool:
        """تعيين الجهاز كمتاح"""
        return self.update_device_status(device_id, 'available')
    
    def set_device_maintenance(self, device_id: int) -> bool:
        """تعيين الجهاز في الصيانة"""
        return self.update_device_status(device_id, 'maintenance')
    
    def set_device_disabled(self, device_id: int) -> bool:
        """تعطيل الجهاز"""
        return self.update_device_status(device_id, 'disabled')
    
    def delete_device(self, device_id: int) -> bool:
        """حذف الجهاز"""
        try:
            self.db.execute_query(
                "DELETE FROM devices WHERE id = ?",
                (device_id,),
                fetch=False
            )
            
            logger.info(f"تم حذف الجهاز: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف الجهاز: {e}")
            return False
    
    def get_device_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأجهزة"""
        try:
            stats = {}
            
            # إجمالي الأجهزة
            total_devices = self.db.execute_query("SELECT COUNT(*) as count FROM devices")
            stats['total_devices'] = total_devices[0]['count'] if total_devices else 0
            
            # الأجهزة المتاحة
            available_devices = self.db.execute_query(
                "SELECT COUNT(*) as count FROM devices WHERE status = 'available'"
            )
            stats['available_devices'] = available_devices[0]['count'] if available_devices else 0
            
            # الأجهزة المشغولة
            busy_devices = self.db.execute_query(
                "SELECT COUNT(*) as count FROM devices WHERE status = 'busy'"
            )
            stats['busy_devices'] = busy_devices[0]['count'] if busy_devices else 0
            
            # الأجهزة في الصيانة
            maintenance_devices = self.db.execute_query(
                "SELECT COUNT(*) as count FROM devices WHERE status = 'maintenance'"
            )
            stats['maintenance_devices'] = maintenance_devices[0]['count'] if maintenance_devices else 0
            
            # الأجهزة المعطلة
            disabled_devices = self.db.execute_query(
                "SELECT COUNT(*) as count FROM devices WHERE status = 'disabled'"
            )
            stats['disabled_devices'] = disabled_devices[0]['count'] if disabled_devices else 0
            
            # إحصائيات حسب النوع
            type_stats = self.db.execute_query(
                """SELECT type, COUNT(*) as count, 
                   SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
                   SUM(CASE WHEN status = 'busy' THEN 1 ELSE 0 END) as busy
                   FROM devices 
                   GROUP BY type"""
            )
            stats['by_type'] = type_stats or []
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الأجهزة: {e}")
            return {}
    
    def get_device_usage_stats(self, start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """الحصول على إحصائيات استخدام الأجهزة"""
        try:
            query = """
                SELECT d.id, d.name, d.type,
                       COUNT(i.id) as total_sessions,
                       SUM(CASE WHEN i.end_time IS NOT NULL THEN 
                           TIMESTAMPDIFF(MINUTE, i.start_time, i.end_time) ELSE 0 END) as total_minutes,
                       SUM(i.total_amount) as total_revenue,
                       AVG(CASE WHEN i.end_time IS NOT NULL THEN 
                           TIMESTAMPDIFF(MINUTE, i.start_time, i.end_time) ELSE 0 END) as avg_session_minutes
                FROM devices d
                LEFT JOIN invoices i ON d.id = i.device_id
            """
            
            params = []
            conditions = []
            
            if start_date:
                conditions.append("i.start_time >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("i.start_time <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += """
                GROUP BY d.id, d.name, d.type
                ORDER BY total_revenue DESC
            """
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات استخدام الأجهزة: {e}")
            return []
    
    def search_devices(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في الأجهزة"""
        try:
            search_pattern = f"%{search_term}%"
            result = self.db.execute_query(
                """SELECT * FROM devices 
                   WHERE name LIKE ? OR type LIKE ?
                   ORDER BY type, id""",
                (search_pattern, search_pattern)
            )
            
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في الأجهزة: {e}")
            return []
    
    def get_device_types(self) -> List[str]:
        """الحصول على أنواع الأجهزة المتاحة"""
        try:
            result = self.db.execute_query(
                "SELECT DISTINCT type FROM devices ORDER BY type"
            )
            return [row['type'] for row in result] if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على أنواع الأجهزة: {e}")
            return []
    
    def is_device_available(self, device_id: int) -> bool:
        """التحقق من توفر الجهاز"""
        try:
            result = self.db.execute_query(
                "SELECT status FROM devices WHERE id = ?",
                (device_id,)
            )
            
            if result:
                return result[0]['status'] == 'available'
            return False
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من توفر الجهاز: {e}")
            return False
    
    def get_device_current_session(self, device_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على الجلسة الحالية للجهاز"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   WHERE s.device_id = ? AND s.status IN ('active', 'paused')
                   ORDER BY s.start_time DESC
                   LIMIT 1""",
                (device_id,)
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسة الحالية: {e}")
            return None
    
    def recover_device_sessions(self) -> bool:
        """استرداد حالة الأجهزة عند بدء البرنامج"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            
            # الحصول على جميع الجلسات النشطة والمتوقفة
            active_sessions = session_model.get_all_active_sessions()
            
            # تحديث current_session_id في جدول الأجهزة
            for session in active_sessions:
                device_id = session['device_id']
                session_id = session['id']
                session_status = session['status']
                
                # تحديث الجهاز ليشير إلى الجلسة النشطة أو المتوقفة
                self.update_device_status(
                    device_id=device_id,
                    status='busy',
                    current_session_id=session_id
                )
                
                # تسجيل حالة الجلسة
                if session_status == 'paused':
                    logger.info(f"تم استرداد جلسة متوقفة: {session_id} للجهاز {device_id}")
                else:
                    logger.info(f"تم استرداد جلسة نشطة: {session_id} للجهاز {device_id}")
            
            # تنظيف الأجهزة التي لا تحتوي على جلسات نشطة أو متوقفة
            all_devices = self.get_all_devices()
            busy_devices = [d for d in all_devices if d['status'] == 'busy']
            
            for device in busy_devices:
                # التحقق من وجود جلسة نشطة أو متوقفة لهذا الجهاز
                active_session = session_model.get_active_session(device['id'])
                if not active_session:
                    # تنظيف الجهاز
                    self.set_device_available(device['id'])
                    logger.info(f"تم تنظيف الجهاز {device['id']} - لا توجد جلسة نشطة")
            
            logger.info(f"تم استرداد حالة الأجهزة: {len(active_sessions)} جلسة (نشطة ومتوقفة)")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في استرداد حالة الأجهزة: {e}")
            return False
