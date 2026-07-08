"""
تحكم العملاء
Customer Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.customer_model import CustomerModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency, validate_phone, format_phone
from utils.security import hash_password
from utils.notifications import show_success, show_error

class CustomerController:
    """تحكم العملاء"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.customer_model = CustomerModel()
        self.audit_model = AuditLogModel()
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """الحصول على جميع العملاء"""
        try:
            return self.customer_model.get_all_customers()
        except Exception as e:
            show_error(f"خطأ في الحصول على العملاء: {str(e)}")
            return []
    
    def create_customer(self, phone: str, name: str, password: str, balance: Decimal = Decimal('0.00')) -> Dict[str, Any]:
        """إنشاء عميل جديد"""
        try:
            # التحقق من صحة البيانات
            if not phone or not name or not password:
                return {
                    'success': False,
                    'message': 'يرجى ملء جميع الحقول المطلوبة'
                }
            
            # التحقق من صحة رقم الهاتف
            if not validate_phone(phone):
                return {
                    'success': False,
                    'message': 'رقم الهاتف غير صحيح'
                }
            
            # التحقق من عدم وجود العميل
            if not self.customer_model.is_phone_available(phone):
                return {
                    'success': False,
                    'message': 'رقم الهاتف مسجل مسبقاً'
                }
            
            # تشفير كلمة المرور
            password_hash = hash_password(password)
            
            # إنشاء العميل
            success = self.customer_model.create_customer(
                phone=phone,
                name=name,
                password=password,
                initial_balance=balance,
                cashier_id=self.current_user['id']
            )
            
            if success:
                # تسجيل العملية
                self.audit_model.log_customer_action(
                    user_id=self.current_user['id'],
                    action='create',
                    customer_phone=phone,
                    reason=f'إنشاء عميل جديد: {name}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إنشاء العميل بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء العميل'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء العميل: {str(e)}'
            }
    
    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """الحصول على عميل برقم الهاتف"""
        try:
            return self.customer_model.get_customer_by_phone(phone)
        except Exception as e:
            show_error(f"خطأ في الحصول على العميل: {str(e)}")
            return None
    
    def charge_balance(self, phone: str, amount: Decimal) -> Dict[str, Any]:
        """شحن رصيد العميل"""
        try:
            # التحقق من صحة البيانات
            if not phone or amount <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال بيانات صحيحة'
                }
            
            # التحقق من وجود العميل
            customer = self.customer_model.get_customer_by_phone(phone)
            if not customer:
                return {
                    'success': False,
                    'message': 'العميل غير موجود'
                }
            
            # شحن الرصيد
            success = self.customer_model.add_balance(phone, amount)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_customer_action(
                    user_id=self.current_user['id'],
                    action='charge_balance',
                    customer_phone=phone,
                    reason=f'شحن رصيد: {format_currency(amount)}'
                )
                
                return {
                    'success': True,
                    'message': f'تم شحن {format_currency(amount)} للعميل {customer["name"]}'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في شحن الرصيد'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في شحن الرصيد: {str(e)}'
            }
    
    def update_customer_info(self, phone: str, name: str = None, new_password: str = None) -> Dict[str, Any]:
        """تحديث معلومات العميل"""
        try:
            # التحقق من وجود العميل
            customer = self.customer_model.get_customer_by_phone(phone)
            if not customer:
                return {
                    'success': False,
                    'message': 'العميل غير موجود'
                }
            
            # تحديث البيانات
            update_data = {}
            if name:
                update_data['name'] = name
            if new_password:
                update_data['password_hash'] = hash_password(new_password)
            
            if update_data:
                success = self.customer_model.update_customer(phone, **update_data)
                
                if success:
                    # تسجيل العملية
                    self.audit_model.log_customer_action(
                        user_id=self.current_user['id'],
                        action='update',
                        customer_phone=phone,
                        reason='تحديث معلومات العميل'
                    )
                    
                    return {
                        'success': True,
                        'message': 'تم تحديث معلومات العميل بنجاح'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'فشل في تحديث معلومات العميل'
                    }
            else:
                return {
                    'success': False,
                    'message': 'لا توجد بيانات للتحديث'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث معلومات العميل: {str(e)}'
            }
    
    def get_customer_transactions(self, phone: str, days: int = 30) -> List[Dict[str, Any]]:
        """الحصول على معاملات العميل"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            return self.customer_model.get_customer_transactions(
                phone=phone,
                start_date=start_date
            )
        except Exception as e:
            show_error(f"خطأ في الحصول على معاملات العميل: {str(e)}")
            return []
    
    def get_customer_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات العملاء"""
        try:
            return self.customer_model.get_customer_stats()
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات العملاء: {str(e)}")
            return {}
    
    def search_customers(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في العملاء"""
        try:
            return self.customer_model.search_customers(search_term)
        except Exception as e:
            show_error(f"خطأ في البحث في العملاء: {str(e)}")
            return []
    
    def delete_customer(self, phone: str, admin_password: str) -> Dict[str, Any]:
        """حذف العميل (للمدير فقط)"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف العملاء'
                }
            
            # التحقق من كلمة مرور المدير
            from utils.security import verify_password
            if not verify_password(admin_password, self.current_user['password_hash']):
                return {
                    'success': False,
                    'message': 'كلمة مرور المدير غير صحيحة'
                }
            
            # التحقق من وجود العميل
            customer = self.customer_model.get_customer_by_phone(phone)
            if not customer:
                return {
                    'success': False,
                    'message': 'العميل غير موجود'
                }
            
            # حذف العميل
            success = self.customer_model.delete_customer(phone)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_customer_action(
                    user_id=self.current_user['id'],
                    action='delete',
                    customer_phone=phone,
                    reason=f'حذف العميل: {customer["name"]}'
                )
                
                return {
                    'success': True,
                    'message': 'تم حذف العميل بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حذف العميل'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حذف العميل: {str(e)}'
            }
    
    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على العملاء الأكثر رصيداً"""
        try:
            return self.customer_model.get_top_customers(limit)
        except Exception as e:
            show_error(f"خطأ في الحصول على العملاء الأكثر رصيداً: {str(e)}")
            return []
