"""
نظام الصلاحيات والأدوار
Permissions and Roles System
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Permission(Enum):
    """تعداد الصلاحيات"""
    # إدارة الأجهزة
    DEVICE_VIEW = "device_view"
    DEVICE_ADD = "device_add"
    DEVICE_EDIT = "device_edit"
    DEVICE_DELETE = "device_delete"
    
    # إدارة الفواتير
    INVOICE_VIEW = "invoice_view"
    INVOICE_ADD = "invoice_add"
    INVOICE_EDIT = "invoice_edit"
    INVOICE_DELETE = "invoice_delete"
    INVOICE_EXPORT = "invoice_export"
    INVOICE_PRINT = "invoice_print"
    
    # إدارة العملاء
    CUSTOMER_VIEW = "customer_view"
    CUSTOMER_ADD = "customer_add"
    CUSTOMER_EDIT = "customer_edit"
    CUSTOMER_DELETE = "customer_delete"
    
    # إدارة المصروفات
    EXPENSE_VIEW = "expense_view"
    EXPENSE_ADD = "expense_add"
    EXPENSE_EDIT = "expense_edit"
    EXPENSE_DELETE = "expense_delete"
    
    # إدارة الكاشيرات
    CASHIER_VIEW = "cashier_view"
    CASHIER_ADD = "cashier_add"
    CASHIER_EDIT = "cashier_edit"
    CASHIER_DELETE = "cashier_delete"
    
    # إدارة المنتجات
    PRODUCT_VIEW = "product_view"
    PRODUCT_ADD = "product_add"
    PRODUCT_EDIT = "product_edit"
    PRODUCT_DELETE = "product_delete"
    
    # إدارة المخزون
    INVENTORY_VIEW = "inventory_view"
    INVENTORY_EDIT = "inventory_edit"
    
    # إدارة الورديات
    SHIFT_VIEW = "shift_view"
    SHIFT_ADD = "shift_add"
    SHIFT_EDIT = "shift_edit"
    SHIFT_DELETE = "shift_delete"
    
    # إدارة المستخدمين
    USER_VIEW = "user_view"
    USER_ADD = "user_add"
    USER_EDIT = "user_edit"
    USER_DELETE = "user_delete"
    USER_CHANGE_PASSWORD = "user_change_password"
    
    # التقارير
    REPORT_VIEW = "report_view"
    REPORT_EXPORT = "report_export"
    REPORT_PRINT = "report_print"
    
    # إعدادات النظام
    SYSTEM_SETTINGS = "system_settings"
    
    # صلاحيات خاصة
    ADMIN_OVERRIDE = "admin_override"  # لتعديل/حذف الفواتير والمصروفات
    PASSWORD_CHANGE_ALL = "password_change_all"  # تغيير جميع كلمات المرور

class Role(Enum):
    """تعداد الأدوار"""
    ADMIN = "admin"
    CASHIER = "cashier"
    DEVELOPER = "developer"

class PermissionManager:
    """مدير الصلاحيات"""
    
    def __init__(self):
        self.role_permissions = self._define_role_permissions()
    
    def _define_role_permissions(self) -> Dict[Role, List[Permission]]:
        """تحديد صلاحيات كل دور"""
        return {
            Role.DEVELOPER: [
                # جميع الصلاحيات - المطور له صلاحيات كاملة
                Permission.DEVICE_VIEW,
                Permission.DEVICE_ADD,
                Permission.DEVICE_EDIT,
                Permission.DEVICE_DELETE,
                
                Permission.INVOICE_VIEW,
                Permission.INVOICE_ADD,
                Permission.INVOICE_EDIT,
                Permission.INVOICE_DELETE,
                Permission.INVOICE_EXPORT,
                Permission.INVOICE_PRINT,
                
                Permission.CUSTOMER_VIEW,
                Permission.CUSTOMER_ADD,
                Permission.CUSTOMER_EDIT,
                Permission.CUSTOMER_DELETE,
                
                Permission.EXPENSE_VIEW,
                Permission.EXPENSE_ADD,
                Permission.EXPENSE_EDIT,
                Permission.EXPENSE_DELETE,
                
                Permission.CASHIER_VIEW,
                Permission.CASHIER_ADD,
                Permission.CASHIER_EDIT,
                Permission.CASHIER_DELETE,
                
                Permission.PRODUCT_VIEW,
                Permission.PRODUCT_ADD,
                Permission.PRODUCT_EDIT,
                Permission.PRODUCT_DELETE,
                
                Permission.INVENTORY_VIEW,
                Permission.INVENTORY_EDIT,
                
                Permission.SHIFT_VIEW,
                Permission.SHIFT_ADD,
                Permission.SHIFT_EDIT,
                Permission.SHIFT_DELETE,
                
                Permission.USER_VIEW,
                Permission.USER_ADD,
                Permission.USER_EDIT,
                Permission.USER_DELETE,
                Permission.USER_CHANGE_PASSWORD,
                
                Permission.REPORT_VIEW,
                Permission.REPORT_EXPORT,
                Permission.REPORT_PRINT,
                
                Permission.SYSTEM_SETTINGS,
                Permission.ADMIN_OVERRIDE,
                Permission.PASSWORD_CHANGE_ALL,
            ],
            
            Role.ADMIN: [
                # كل الصلاحيات
                Permission.DEVICE_VIEW,
                Permission.DEVICE_ADD,
                Permission.DEVICE_EDIT,
                Permission.DEVICE_DELETE,
                
                Permission.INVOICE_VIEW,
                Permission.INVOICE_ADD,
                Permission.INVOICE_EDIT,
                Permission.INVOICE_DELETE,
                Permission.INVOICE_EXPORT,
                Permission.INVOICE_PRINT,
                
                Permission.CUSTOMER_VIEW,
                Permission.CUSTOMER_ADD,
                Permission.CUSTOMER_EDIT,
                Permission.CUSTOMER_DELETE,
                
                Permission.EXPENSE_VIEW,
                Permission.EXPENSE_ADD,
                Permission.EXPENSE_EDIT,
                Permission.EXPENSE_DELETE,
                
                Permission.CASHIER_VIEW,
                Permission.CASHIER_ADD,
                Permission.CASHIER_EDIT,
                Permission.CASHIER_DELETE,
                
                Permission.PRODUCT_VIEW,
                Permission.PRODUCT_ADD,
                Permission.PRODUCT_EDIT,
                Permission.PRODUCT_DELETE,
                
                Permission.INVENTORY_VIEW,
                Permission.INVENTORY_EDIT,
                
                Permission.SHIFT_VIEW,
                Permission.SHIFT_ADD,
                Permission.SHIFT_EDIT,
                Permission.SHIFT_DELETE,
                
                Permission.USER_VIEW,
                Permission.USER_ADD,
                Permission.USER_EDIT,
                Permission.USER_DELETE,
                Permission.USER_CHANGE_PASSWORD,
                
                Permission.REPORT_VIEW,
                Permission.REPORT_EXPORT,
                Permission.REPORT_PRINT,
                
                Permission.SYSTEM_SETTINGS,
                Permission.ADMIN_OVERRIDE,
                Permission.PASSWORD_CHANGE_ALL,
            ],
            
            Role.CASHIER: [
                # صلاحيات محدودة للكاشير
                Permission.DEVICE_VIEW,
                
                Permission.INVOICE_VIEW,
                Permission.INVOICE_ADD,
                
                Permission.CUSTOMER_VIEW,
                Permission.CUSTOMER_ADD,
                
                Permission.EXPENSE_VIEW,
                Permission.EXPENSE_ADD,
                
                Permission.PRODUCT_VIEW,
                
                Permission.INVENTORY_VIEW,
                
                Permission.SHIFT_VIEW,
                Permission.SHIFT_ADD,
            ]
        }
    
    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """التحقق من وجود صلاحية للمستخدم"""
        try:
            role = Role(user_role)
            return permission in self.role_permissions.get(role, [])
        except ValueError:
            logger.error(f"دور غير صحيح: {user_role}")
            return False
    
    def get_user_permissions(self, user_role: str) -> List[Permission]:
        """الحصول على جميع صلاحيات المستخدم"""
        try:
            role = Role(user_role)
            return self.role_permissions.get(role, [])
        except ValueError:
            logger.error(f"دور غير صحيح: {user_role}")
            return []
    
    def can_edit_invoice(self, user_role: str, invoice_creator_id: int, current_user_id: int) -> bool:
        """التحقق من إمكانية تعديل الفاتورة"""
        # المدير يمكنه تعديل أي فاتورة
        if self.has_permission(user_role, Permission.ADMIN_OVERRIDE):
            return True
        
        # الكاشير يمكنه تعديل الفواتير التي أنشأها فقط
        if self.has_permission(user_role, Permission.INVOICE_EDIT):
            return invoice_creator_id == current_user_id
        
        return False
    
    def can_delete_invoice(self, user_role: str, invoice_creator_id: int, current_user_id: int) -> bool:
        """التحقق من إمكانية حذف الفاتورة"""
        # المدير فقط يمكنه حذف الفواتير
        return self.has_permission(user_role, Permission.ADMIN_OVERRIDE)
    
    def can_edit_expense(self, user_role: str, expense_creator_id: int, current_user_id: int) -> bool:
        """التحقق من إمكانية تعديل المصروف"""
        # المدير يمكنه تعديل أي مصروف
        if self.has_permission(user_role, Permission.ADMIN_OVERRIDE):
            return True
        
        # الكاشير يمكنه تعديل المصروفات التي أنشأها فقط
        if self.has_permission(user_role, Permission.EXPENSE_EDIT):
            return expense_creator_id == current_user_id
        
        return False
    
    def can_delete_expense(self, user_role: str, expense_creator_id: int, current_user_id: int) -> bool:
        """التحقق من إمكانية حذف المصروف"""
        # المدير فقط يمكنه حذف المصروفات
        return self.has_permission(user_role, Permission.ADMIN_OVERRIDE)
    
    def can_manage_cashiers(self, user_role: str) -> bool:
        """التحقق من إمكانية إدارة الكاشيرات"""
        return self.has_permission(user_role, Permission.CASHIER_ADD)
    
    def can_change_passwords(self, user_role: str) -> bool:
        """التحقق من إمكانية تغيير كلمات المرور"""
        return self.has_permission(user_role, Permission.PASSWORD_CHANGE_ALL)
    
    def can_access_reports(self, user_role: str) -> bool:
        """التحقق من إمكانية الوصول للتقارير"""
        return self.has_permission(user_role, Permission.REPORT_VIEW)
    
    def can_export_data(self, user_role: str) -> bool:
        """التحقق من إمكانية تصدير البيانات"""
        return (self.has_permission(user_role, Permission.REPORT_EXPORT) or 
                self.has_permission(user_role, Permission.INVOICE_EXPORT))
    
    def can_print_data(self, user_role: str) -> bool:
        """التحقق من إمكانية طباعة البيانات"""
        return (self.has_permission(user_role, Permission.REPORT_PRINT) or 
                self.has_permission(user_role, Permission.INVOICE_PRINT))
    
    def can_manage_system(self, user_role: str) -> bool:
        """التحقق من إمكانية إدارة النظام"""
        return self.has_permission(user_role, Permission.SYSTEM_SETTINGS)
    
    def get_role_description(self, role: str) -> str:
        """الحصول على وصف الدور"""
        descriptions = {
            Role.DEVELOPER.value: "مطور النظام - صلاحيات كاملة ومطلقة",
            Role.ADMIN.value: "مدير النظام - جميع الصلاحيات",
            Role.CASHIER.value: "كاشير - صلاحيات محدودة للعمل اليومي"
        }
        return descriptions.get(role, "دور غير معروف")
    
    def get_permission_description(self, permission: Permission) -> str:
        """الحصول على وصف الصلاحية"""
        descriptions = {
            Permission.DEVICE_VIEW: "عرض الأجهزة",
            Permission.DEVICE_ADD: "إضافة أجهزة",
            Permission.DEVICE_EDIT: "تعديل الأجهزة",
            Permission.DEVICE_DELETE: "حذف الأجهزة",
            
            Permission.INVOICE_VIEW: "عرض الفواتير",
            Permission.INVOICE_ADD: "إضافة فواتير",
            Permission.INVOICE_EDIT: "تعديل الفواتير",
            Permission.INVOICE_DELETE: "حذف الفواتير",
            Permission.INVOICE_EXPORT: "تصدير الفواتير",
            Permission.INVOICE_PRINT: "طباعة الفواتير",
            
            Permission.CUSTOMER_VIEW: "عرض العملاء",
            Permission.CUSTOMER_ADD: "إضافة عملاء",
            Permission.CUSTOMER_EDIT: "تعديل العملاء",
            Permission.CUSTOMER_DELETE: "حذف العملاء",
            
            Permission.EXPENSE_VIEW: "عرض المصروفات",
            Permission.EXPENSE_ADD: "إضافة مصروفات",
            Permission.EXPENSE_EDIT: "تعديل المصروفات",
            Permission.EXPENSE_DELETE: "حذف المصروفات",
            
            Permission.CASHIER_VIEW: "عرض الكاشيرات",
            Permission.CASHIER_ADD: "إضافة كاشيرات",
            Permission.CASHIER_EDIT: "تعديل الكاشيرات",
            Permission.CASHIER_DELETE: "حذف الكاشيرات",
            
            Permission.PRODUCT_VIEW: "عرض المنتجات",
            Permission.PRODUCT_ADD: "إضافة منتجات",
            Permission.PRODUCT_EDIT: "تعديل المنتجات",
            Permission.PRODUCT_DELETE: "حذف المنتجات",
            
            Permission.INVENTORY_VIEW: "عرض المخزون",
            Permission.INVENTORY_EDIT: "تعديل المخزون",
            
            Permission.SHIFT_VIEW: "عرض الورديات",
            Permission.SHIFT_ADD: "إضافة ورديات",
            Permission.SHIFT_EDIT: "تعديل الورديات",
            Permission.SHIFT_DELETE: "حذف الورديات",
            
            Permission.USER_VIEW: "عرض المستخدمين",
            Permission.USER_ADD: "إضافة مستخدمين",
            Permission.USER_EDIT: "تعديل المستخدمين",
            Permission.USER_DELETE: "حذف المستخدمين",
            Permission.USER_CHANGE_PASSWORD: "تغيير كلمات المرور",
            
            Permission.REPORT_VIEW: "عرض التقارير",
            Permission.REPORT_EXPORT: "تصدير التقارير",
            Permission.REPORT_PRINT: "طباعة التقارير",
            
            Permission.SYSTEM_SETTINGS: "إعدادات النظام",
            Permission.ADMIN_OVERRIDE: "صلاحيات إدارية خاصة",
            Permission.PASSWORD_CHANGE_ALL: "تغيير جميع كلمات المرور",
        }
        return descriptions.get(permission, "صلاحية غير معروفة")

# إنشاء مثيل عام لمدير الصلاحيات
permission_manager = PermissionManager()

def check_permission(user_role: str, permission: Permission) -> bool:
    """دالة مساعدة للتحقق من الصلاحية"""
    return permission_manager.has_permission(user_role, permission)

def get_user_permissions(user_role: str) -> List[Permission]:
    """دالة مساعدة للحصول على صلاحيات المستخدم"""
    return permission_manager.get_user_permissions(user_role)

def can_edit_invoice(user_role: str, invoice_creator_id: int, current_user_id: int) -> bool:
    """دالة مساعدة للتحقق من إمكانية تعديل الفاتورة"""
    return permission_manager.can_edit_invoice(user_role, invoice_creator_id, current_user_id)

def can_delete_invoice(user_role: str, invoice_creator_id: int, current_user_id: int) -> bool:
    """دالة مساعدة للتحقق من إمكانية حذف الفاتورة"""
    return permission_manager.can_delete_invoice(user_role, invoice_creator_id, current_user_id)

def can_edit_expense(user_role: str, expense_creator_id: int, current_user_id: int) -> bool:
    """دالة مساعدة للتحقق من إمكانية تعديل المصروف"""
    return permission_manager.can_edit_expense(user_role, expense_creator_id, current_user_id)

def can_delete_expense(user_role: str, expense_creator_id: int, current_user_id: int) -> bool:
    """دالة مساعدة للتحقق من إمكانية حذف المصروف"""
    return permission_manager.can_delete_expense(user_role, expense_creator_id, current_user_id)

def can_manage_cashiers(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية إدارة الكاشيرات"""
    return permission_manager.can_manage_cashiers(user_role)

def can_change_passwords(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية تغيير كلمات المرور"""
    return permission_manager.can_change_passwords(user_role)

def can_access_reports(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية الوصول للتقارير"""
    return permission_manager.can_access_reports(user_role)

def can_export_data(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية تصدير البيانات"""
    return permission_manager.can_export_data(user_role)

def can_print_data(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية طباعة البيانات"""
    return permission_manager.can_print_data(user_role)

def can_manage_system(user_role: str) -> bool:
    """دالة مساعدة للتحقق من إمكانية إدارة النظام"""
    return permission_manager.can_manage_system(user_role)

def is_developer(user_role: str) -> bool:
    """دالة مساعدة للتحقق من دور المطور"""
    return user_role == Role.DEVELOPER.value

def has_developer_access(user_role: str) -> bool:
    """دالة مساعدة للتحقق من وصول المطور"""
    return user_role == Role.DEVELOPER.value
