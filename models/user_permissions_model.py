"""
موديل صلاحيات المستخدمين
User Permissions Model
"""

from typing import List, Dict, Any, Optional
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class UserPermissionsModel:
    """موديل إدارة صلاحيات المستخدمين"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def grant_permission(self, user_id: int, permission_key: str, granted_by: int = None) -> bool:
        """منح صلاحية لمستخدم"""
        try:
            # التحقق من وجود الصلاحية مسبقاً
            existing = self.db.execute_query(
                "SELECT id FROM user_permissions WHERE user_id = ? AND permission_key = ?",
                (user_id, permission_key)
            )
            
            if existing:
                logger.info(f"الصلاحية {permission_key} موجودة بالفعل للمستخدم {user_id}")
                return True
            
            # منح الصلاحية
            result = self.db.execute_query(
                """INSERT INTO user_permissions (user_id, permission_key, granted_by) 
                   VALUES (?, ?, ?)""",
                (user_id, permission_key, granted_by),
                fetch=False
            )
            
            logger.info(f"تم منح الصلاحية {permission_key} للمستخدم {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في منح الصلاحية: {e}")
            return False
    
    def revoke_permission(self, user_id: int, permission_key: str) -> bool:
        """سحب صلاحية من مستخدم"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_permissions WHERE user_id = ? AND permission_key = ?",
                (user_id, permission_key),
                fetch=False
            )
            
            logger.info(f"تم سحب الصلاحية {permission_key} من المستخدم {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في سحب الصلاحية: {e}")
            return False
    
    def has_permission(self, user_id: int, permission_key: str) -> bool:
        """التحقق من وجود صلاحية للمستخدم"""
        try:
            result = self.db.execute_query(
                "SELECT id FROM user_permissions WHERE user_id = ? AND permission_key = ?",
                (user_id, permission_key)
            )
            
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحية: {e}")
            return False
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """الحصول على جميع صلاحيات المستخدم"""
        try:
            result = self.db.execute_query(
                "SELECT permission_key FROM user_permissions WHERE user_id = ?",
                (user_id,)
            )
            
            return [row['permission_key'] for row in result]
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على صلاحيات المستخدم: {e}")
            return []
    
    def set_user_permissions(self, user_id: int, permissions: List[str], granted_by: int = None) -> bool:
        """تعيين صلاحيات المستخدم (استبدال جميع الصلاحيات الموجودة)"""
        try:
            # حذف جميع الصلاحيات الموجودة
            self.db.execute_query(
                "DELETE FROM user_permissions WHERE user_id = ?",
                (user_id,),
                fetch=False
            )
            
            # إضافة الصلاحيات الجديدة
            for permission in permissions:
                self.grant_permission(user_id, permission, granted_by)
            
            logger.info(f"تم تعيين {len(permissions)} صلاحية للمستخدم {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تعيين صلاحيات المستخدم: {e}")
            return False
    
    def get_all_user_permissions(self) -> Dict[int, List[str]]:
        """الحصول على جميع صلاحيات جميع المستخدمين"""
        try:
            result = self.db.execute_query(
                "SELECT user_id, permission_key FROM user_permissions ORDER BY user_id"
            )
            
            permissions_dict = {}
            for row in result:
                user_id = row['user_id']
                permission_key = row['permission_key']
                
                if user_id not in permissions_dict:
                    permissions_dict[user_id] = []
                
                permissions_dict[user_id].append(permission_key)
            
            return permissions_dict
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جميع صلاحيات المستخدمين: {e}")
            return {}
    
    def revoke_all_permissions(self, user_id: int) -> bool:
        """سحب جميع الصلاحيات من مستخدم"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_permissions WHERE user_id = ?",
                (user_id,),
                fetch=False
            )
            
            logger.info(f"تم سحب جميع الصلاحيات من المستخدم {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في سحب جميع الصلاحيات: {e}")
            return False
