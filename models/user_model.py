"""
موديل المستخدمين
User Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class UserModel:
    """موديل إدارة المستخدمين"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """إنشاء مستخدم جديد"""
        try:
            from utils.security import hash_password
            
            # تشفير كلمة المرور
            password_hash = hash_password(user_data['password'])
            
            # إدراج المستخدم
            user_id = self.db.execute_query(
                """INSERT INTO users (username, full_name, phone, email, password_hash, 
                   role, enabled, notes, created_by, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_data['username'], user_data.get('full_name', ''),
                 user_data.get('phone', ''), user_data.get('email', ''),
                 password_hash, user_data['role'], user_data.get('enabled', True),
                 user_data.get('notes', ''), user_data.get('created_by', 1),
                 datetime.now()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء مستخدم جديد: {user_data['username']}")
            return user_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المستخدم: {e}")
            return None
    
    def create_user_legacy(self, role: str, username: str, phone: str, password_hash: str, 
                   enabled: bool = True) -> Optional[int]:
        """إنشاء مستخدم جديد (للتوافق مع النظام القديم)"""
        try:
            user_data = {
                'role': role,
                'username': username,
                'phone': phone,
                'password_hash': password_hash,
                'enabled': enabled
            }
            
            user_id = self.db.execute_query(
                """INSERT INTO users (role, username, phone, password_hash, enabled) 
                   VALUES (?, ?, ?, ?, ?)""",
                tuple(user_data.values()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء مستخدم جديد: {username}")
            return user_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المستخدم: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على مستخدم بالمعرف"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدم: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """الحصول على مستخدم باسم المستخدم"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدم: {e}")
            return None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """الحصول على مستخدم برقم الهاتف"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE phone = ?",
                (phone,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدم: {e}")
            return None
    
    def get_admin_user(self) -> Optional[Dict[str, Any]]:
        """الحصول على مدير النظام"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE role = 'admin' AND enabled = 1 LIMIT 1"
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المدير: {e}")
            return None
    
    def verify_admin_password(self, password: str) -> bool:
        """التحقق من كلمة مرور المدير"""
        try:
            from utils.security import verify_password
            
            # الحصول على المدير
            admin_user = self.get_admin_user()
            if not admin_user:
                logger.error("لا يوجد مدير في النظام")
                return False
            
            # التحقق من كلمة المرور
            if verify_password(password, admin_user['password_hash']):
                logger.info("تم التحقق من كلمة مرور المدير بنجاح")
                return True
            else:
                logger.error("كلمة مرور المدير غير صحيحة")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من كلمة مرور المدير: {e}")
            return False
    
    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """مصادقة المستخدم"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM users WHERE username = ? AND password_hash = ? AND enabled = 1",
                (username, password_hash)
            )
            
            if result:
                user = result[0]
                # تحديث آخر تسجيل دخول
                self.update_last_login(user['id'])
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في مصادقة المستخدم: {e}")
            return None
    
    def authenticate_user_with_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """مصادقة المستخدم بكلمة المرور العادية"""
        try:
            from utils.security import verify_password
            
            # الحصول على المستخدم
            result = self.db.execute_query(
                "SELECT * FROM users WHERE username = ? AND enabled = 1",
                (username,)
            )
            
            if result:
                user = result[0]
                # التحقق من كلمة المرور
                if verify_password(password, user['password_hash']):
                    # تحديث آخر تسجيل دخول
                    self.update_last_login(user['id'])
                    return user
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في مصادقة المستخدم: {e}")
            return None
    
    def authenticate_user_by_id(self, user_id: int, password: str) -> Optional[Dict[str, Any]]:
        """مصادقة المستخدم بالمعرف وكلمة المرور"""
        try:
            from utils.security import verify_password
            
            # الحصول على المستخدم
            result = self.db.execute_query(
                "SELECT * FROM users WHERE id = ? AND enabled = 1",
                (user_id,)
            )
            
            if result:
                user = result[0]
                # التحقق من كلمة المرور
                if verify_password(password, user['password_hash']):
                    # تحديث آخر تسجيل دخول
                    self.update_last_login(user['id'])
                    return user
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في مصادقة المستخدم بالمعرف: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """تحديث بيانات المستخدم"""
        try:
            # إزالة القيم الفارغة
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            
            if not update_data:
                return False
            
            # بناء استعلام التحديث
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [user_id]
            
            self.db.execute_query(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                tuple(values),
                fetch=False
            )
            
            logger.info(f"تم تحديث المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديث المستخدم: {e}")
            return False
    
    def update_last_login(self, user_id: int) -> bool:
        """تحديث آخر تسجيل دخول"""
        try:
            from datetime import datetime
            self.db.execute_query(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user_id),
                fetch=False
            )
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديث آخر تسجيل دخول: {e}")
            return False
    
    def verify_password(self, username: str, password: str) -> bool:
        """التحقق من كلمة مرور المستخدم"""
        try:
            from utils.security import verify_password
            
            # الحصول على المستخدم
            result = self.db.execute_query(
                "SELECT password_hash FROM users WHERE username = ? AND enabled = 1",
                (username,)
            )
            
            if result:
                user = result[0]
                # التحقق من كلمة المرور
                return verify_password(password, user['password_hash'])
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من كلمة المرور: {e}")
            return False
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """تغيير كلمة المرور"""
        try:
            # تشفير كلمة المرور الجديدة باستخدام النظام الآمن
            from utils.security import hash_password
            new_password_hash = hash_password(new_password)
            
            self.db.execute_query(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user_id),
                fetch=False
            )
            
            logger.info(f"تم تغيير كلمة مرور المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تغيير كلمة المرور: {e}")
            return False
    
    def update_admin_password_to_new_system(self, current_password: str = 'admin123') -> bool:
        """تحديث كلمة مرور المدير لتستخدم النظام الجديد"""
        try:
            import hashlib
            from utils.security import hash_password, verify_password
            
            # الحصول على المدير
            admin_user = self.db.execute_query(
                "SELECT id, username, password_hash FROM users WHERE username = 'admin' AND role = 'admin'"
            )
            
            if not admin_user:
                logger.error("المدير غير موجود في قاعدة البيانات")
                return False
            
            admin = admin_user[0]
            current_hash = admin['password_hash']
            
            # التحقق من نوع التشفير الحالي
            if ':' in current_hash:
                logger.info("كلمة المرور تستخدم النظام الجديد بالفعل")
                return True
            
            # التحقق من كلمة المرور الحالية
            old_hash = hashlib.sha256(current_password.encode()).hexdigest()
            if current_hash != old_hash:
                logger.error("كلمة المرور الحالية غير صحيحة")
                return False
            
            # إنشاء كلمة مرور جديدة باستخدام النظام الآمن
            new_password_hash = hash_password(current_password)
            
            # تحديث كلمة المرور في قاعدة البيانات
            result = self.db.execute_query(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, admin['id']),
                fetch=False
            )
            
            if result:
                logger.info("تم تحديث كلمة مرور المدير للنظام الجديد")
                return True
            else:
                logger.error("فشل في تحديث كلمة مرور المدير")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث كلمة مرور المدير: {e}")
            return False
    
    def enable_user(self, user_id: int) -> bool:
        """تفعيل المستخدم"""
        try:
            self.db.execute_query(
                "UPDATE users SET enabled = 1 WHERE id = ?",
                (user_id,),
                fetch=False
            )
            
            logger.info(f"تم تفعيل المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تفعيل المستخدم: {e}")
            return False
    
    def disable_user(self, user_id: int) -> bool:
        """إلغاء تفعيل المستخدم"""
        try:
            self.db.execute_query(
                "UPDATE users SET enabled = 0 WHERE id = ?",
                (user_id,),
                fetch=False
            )
            
            logger.info(f"تم إلغاء تفعيل المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إلغاء تفعيل المستخدم: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """حذف المستخدم"""
        try:
            self.db.execute_query(
                "DELETE FROM users WHERE id = ?",
                (user_id,),
                fetch=False
            )
            
            logger.info(f"تم حذف المستخدم: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف المستخدم: {e}")
            return False
    
    def get_all_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على جميع المستخدمين"""
        try:
            if role:
                result = self.db.execute_query(
                    "SELECT * FROM users WHERE role = ? ORDER BY created_at DESC",
                    (role,)
                )
            else:
                result = self.db.execute_query(
                    "SELECT * FROM users ORDER BY created_at DESC"
                )
            
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدمين: {e}")
            return []
    
    def get_cashiers(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الكاشيرز"""
        return self.get_all_users('cashier')
    
    def get_admins(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المديرين"""
        return self.get_all_users('admin')
    
    def search_users(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في المستخدمين"""
        try:
            search_pattern = f"%{search_term}%"
            result = self.db.execute_query(
                """SELECT * FROM users 
                   WHERE username LIKE ? OR phone LIKE ? OR name LIKE ?
                   ORDER BY created_at DESC""",
                (search_pattern, search_pattern, search_pattern)
            )
            
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في المستخدمين: {e}")
            return []
    
    def get_user_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المستخدمين"""
        try:
            stats = {}
            
            # إجمالي المستخدمين
            total_users = self.db.execute_query("SELECT COUNT(*) as count FROM users")
            stats['total_users'] = total_users[0]['count'] if total_users else 0
            
            # المديرين
            admins = self.db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
            stats['admins'] = admins[0]['count'] if admins else 0
            
            # الكاشيرز
            cashiers = self.db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'cashier'")
            stats['cashiers'] = cashiers[0]['count'] if cashiers else 0
            
            # المستخدمين المفعلين
            enabled_users = self.db.execute_query("SELECT COUNT(*) as count FROM users WHERE enabled = 1")
            stats['enabled_users'] = enabled_users[0]['count'] if enabled_users else 0
            
            # آخر تسجيل دخول
            last_login = self.db.execute_query(
                "SELECT MAX(last_login) as last_login FROM users WHERE last_login IS NOT NULL"
            )
            stats['last_login'] = last_login[0]['last_login'] if last_login and last_login[0]['last_login'] else None
            
            return stats
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المستخدمين: {e}")
            return {}
    
    def is_username_available(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """التحقق من توفر اسم المستخدم"""
        try:
            if exclude_user_id:
                result = self.db.execute_query(
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (username, exclude_user_id)
                )
            else:
                result = self.db.execute_query(
                    "SELECT id FROM users WHERE username = ?",
                    (username,)
                )
            
            return len(result) == 0
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من توفر اسم المستخدم: {e}")
            return False
    
    def is_phone_available(self, phone: str, exclude_user_id: Optional[int] = None) -> bool:
        """التحقق من توفر رقم الهاتف"""
        try:
            if exclude_user_id:
                result = self.db.execute_query(
                    "SELECT id FROM users WHERE phone = ? AND id != ?",
                    (phone, exclude_user_id)
                )
            else:
                result = self.db.execute_query(
                    "SELECT id FROM users WHERE phone = ?",
                    (phone,)
                )
            
            return len(result) == 0
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من توفر رقم الهاتف: {e}")
            return False
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """الحصول على المستخدمين حسب الدور"""
        try:
            result = self.db.execute_query(
                """SELECT * FROM users WHERE role = ? ORDER BY created_at DESC""",
                (role,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المستخدمين حسب الدور: {e}")
            return []
