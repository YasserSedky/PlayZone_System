"""
أداة التحقق من الصلاحيات
Permission Checker Utility
"""

from typing import Optional
from models.user_permissions_model import UserPermissionsModel
import logging

logger = logging.getLogger(__name__)

class PermissionChecker:
    """أداة التحقق من صلاحيات المستخدمين"""
    
    def __init__(self):
        self.permissions_model = UserPermissionsModel()
    
    def has_permission(self, user_id: int, permission_key: str) -> bool:
        """التحقق من وجود صلاحية للمستخدم"""
        try:
            # التحقق من الصلاحية المخصصة
            return self.permissions_model.has_permission(user_id, permission_key)
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحية: {e}")
            return False
    
    def check_permission_or_admin(self, current_user: dict, permission_key: str) -> bool:
        """التحقق من الصلاحية أو إذا كان المستخدم مدير"""
        try:
            # إذا كان المستخدم مدير، فله جميع الصلاحيات
            if current_user.get('role') == 'admin':
                return True
            
            # التحقق من الصلاحية المخصصة
            user_id = current_user.get('id')
            if user_id:
                return self.has_permission(user_id, permission_key)
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحية أو المدير: {e}")
            return False
    
    def get_user_permissions(self, user_id: int) -> list:
        """الحصول على جميع صلاحيات المستخدم"""
        try:
            return self.permissions_model.get_user_permissions(user_id)
        except Exception as e:
            logger.error(f"خطأ في الحصول على صلاحيات المستخدم: {e}")
            return []

# إنشاء مثيل عام للاستخدام
permission_checker = PermissionChecker()
