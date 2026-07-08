"""
تحكم المصادقة والأمان
Authentication and Security Controller
"""

import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_model import UserModel
from models.audit_log_model import AuditLogModel
from utils.security import hash_password, verify_password, validate_password_strength
from utils.notifications import show_success, show_error

class AuthController:
    """تحكم المصادقة والأمان"""
    
    def __init__(self):
        self.user_model = UserModel()
        self.audit_model = AuditLogModel()
        self.current_user = None
        self.session_start_time = None
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """تسجيل الدخول"""
        try:
            # التحقق من صحة البيانات
            if not username or not password:
                return {
                    'success': False,
                    'message': 'يرجى إدخال اسم المستخدم وكلمة المرور'
                }
            
            # التحقق من بيانات المستخدم
            user = self.user_model.authenticate_user_with_password(username, password)
            
            if user:
                # تسجيل عملية تسجيل الدخول
                self.audit_model.log_login(user['id'], True)
                
                # حفظ بيانات المستخدم الحالي
                self.current_user = user
                self.session_start_time = datetime.now()
                
                return {
                    'success': True,
                    'message': 'تم تسجيل الدخول بنجاح',
                    'user': user
                }
            else:
                # تسجيل محاولة تسجيل دخول فاشلة
                # البحث عن المستخدم أولاً
                user_by_username = self.user_model.get_user_by_username(username)
                if user_by_username:
                    self.audit_model.log_login(user_by_username['id'], False, "كلمة مرور خاطئة")
                
                return {
                    'success': False,
                    'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تسجيل الدخول: {str(e)}'
            }
    
    def logout(self) -> Dict[str, Any]:
        """تسجيل الخروج"""
        try:
            if self.current_user:
                # تسجيل عملية تسجيل الخروج
                self.audit_model.log_user_action(
                    user_id=self.current_user['id'],
                    action='logout',
                    entity_type='user',
                    entity_id=self.current_user['id']
                )
                
                # مسح بيانات المستخدم الحالي
                self.current_user = None
                self.session_start_time = None
                
                return {
                    'success': True,
                    'message': 'تم تسجيل الخروج بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'لا يوجد مستخدم مسجل دخول'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تسجيل الخروج: {str(e)}'
            }
    
    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """تغيير كلمة المرور"""
        try:
            if not self.current_user:
                return {
                    'success': False,
                    'message': 'يجب تسجيل الدخول أولاً'
                }
            
            # التحقق من كلمة المرور القديمة
            old_password_hash = hash_password(old_password)
            if not verify_password(old_password, self.current_user['password_hash']):
                return {
                    'success': False,
                    'message': 'كلمة المرور القديمة غير صحيحة'
                }
            
            # التحقق من قوة كلمة المرور الجديدة
            password_validation = validate_password_strength(new_password)
            if not password_validation['valid']:
                return {
                    'success': False,
                    'message': f"كلمة المرور ضعيفة: {', '.join(password_validation['issues'])}"
                }
            
            # تشفير كلمة المرور الجديدة
            new_password_hash = hash_password(new_password)
            
            # تحديث كلمة المرور
            success = self.user_model.change_password(self.current_user['id'], new_password_hash)
            
            if success:
                # تسجيل عملية تغيير كلمة المرور
                self.audit_model.log_user_action(
                    user_id=self.current_user['id'],
                    action='change_password',
                    entity_type='user',
                    entity_id=self.current_user['id'],
                    reason='تغيير كلمة المرور'
                )
                
                return {
                    'success': True,
                    'message': 'تم تغيير كلمة المرور بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تغيير كلمة المرور'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تغيير كلمة المرور: {str(e)}'
            }
    
    def create_user(self, username: str, password: str, role: str, phone: str = None) -> Dict[str, Any]:
        """إنشاء مستخدم جديد"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإنشاء مستخدمين'
                }
            
            # التحقق من صحة البيانات
            if not username or not password or not role:
                return {
                    'success': False,
                    'message': 'يرجى ملء جميع الحقول المطلوبة'
                }
            
            # التحقق من قوة كلمة المرور
            password_validation = validate_password_strength(password)
            if not password_validation['valid']:
                return {
                    'success': False,
                    'message': f"كلمة المرور ضعيفة: {', '.join(password_validation['issues'])}"
                }
            
            # التحقق من عدم وجود المستخدم
            if not self.user_model.is_username_available(username):
                return {
                    'success': False,
                    'message': 'اسم المستخدم مسجل مسبقاً'
                }
            
            # تشفير كلمة المرور
            password_hash = hash_password(password)
            
            # إنشاء المستخدم
            user_id = self.user_model.create_user(
                role=role,
                username=username,
                phone=phone,
                password_hash=password_hash
            )
            
            if user_id:
                # تسجيل عملية إنشاء المستخدم
                self.audit_model.log_user_action(
                    user_id=self.current_user['id'],
                    action='create_user',
                    entity_type='user',
                    entity_id=user_id,
                    reason=f'إنشاء مستخدم جديد: {username}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إنشاء المستخدم بنجاح',
                    'user_id': user_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء المستخدم'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء المستخدم: {str(e)}'
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """الحصول على المستخدم الحالي"""
        return self.current_user
    
    def is_authenticated(self) -> bool:
        """التحقق من تسجيل الدخول"""
        return self.current_user is not None
    
    def is_admin(self) -> bool:
        """التحقق من كون المستخدم مدير"""
        return self.current_user and self.current_user['role'] == 'admin'
    
    def is_cashier(self) -> bool:
        """التحقق من كون المستخدم كاشير"""
        return self.current_user and self.current_user['role'] == 'cashier'
    
    def has_permission(self, permission: str) -> bool:
        """التحقق من الصلاحية"""
        if not self.current_user:
            return False
        
        # صلاحيات المدير
        if self.current_user['role'] == 'admin':
            return True
        
        # صلاحيات الكاشير
        if self.current_user['role'] == 'cashier':
            cashier_permissions = [
                'create_invoice',
                'add_product_to_invoice',
                'close_invoice',
                'add_expense',
                'view_own_invoices',
                'view_own_expenses',
                'charge_customer_balance'
            ]
            return permission in cashier_permissions
        
        return False
    
    def get_session_duration(self) -> Optional[int]:
        """الحصول على مدة الجلسة بالدقائق"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            return int(duration.total_seconds() / 60)
        return None
    
    def validate_admin_password(self, password: str) -> bool:
        """التحقق من كلمة مرور المدير"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return False
            
            password_hash = hash_password(password)
            return verify_password(password, self.current_user['password_hash'])
            
        except Exception as e:
            return False
    
    def get_user_activity_log(self, user_id: int = None, days: int = 30) -> list:
        """الحصول على سجل نشاط المستخدم"""
        try:
            if user_id is None:
                user_id = self.current_user['id'] if self.current_user else None
            
            if not user_id:
                return []
            
            return self.audit_model.get_user_audit_logs(user_id, days)
            
        except Exception as e:
            return []
    
    def get_security_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأمان"""
        try:
            stats = {}
            
            # عدد محاولات تسجيل الدخول الفاشلة اليوم
            today = datetime.now().date()
            failed_logins = self.audit_model.get_audit_logs(
                action='login_failed',
                start_date=datetime.combine(today, datetime.min.time()),
                end_date=datetime.combine(today, datetime.max.time())
            )
            stats['failed_logins_today'] = len(failed_logins)
            
            # آخر تسجيل دخول
            if self.current_user:
                stats['last_login'] = self.current_user.get('last_login')
            
            # مدة الجلسة الحالية
            stats['session_duration'] = self.get_session_duration()
            
            return stats
            
        except Exception as e:
            return {}
