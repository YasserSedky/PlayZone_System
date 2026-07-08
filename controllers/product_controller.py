"""
تحكم المنتجات
Product Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product_model import ProductModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency
from utils.notifications import show_success, show_error

class ProductController:
    """تحكم المنتجات"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.product_model = ProductModel()
        self.audit_model = AuditLogModel()
    
    def get_all_products(self, category: str = None) -> List[Dict[str, Any]]:
        """الحصول على جميع المنتجات"""
        try:
            return self.product_model.get_all_products(category)
        except Exception as e:
            show_error(f"خطأ في الحصول على المنتجات: {str(e)}")
            return []
    
    def create_product(self, name: str, price: Decimal, stock_quantity: int, category: str, min_stock_level: int = 5) -> Dict[str, Any]:
        """إنشاء منتج جديد"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإنشاء منتجات'
                }
            
            # التحقق من صحة البيانات
            if not name or price <= 0 or stock_quantity < 0 or not category:
                return {
                    'success': False,
                    'message': 'يرجى إدخال بيانات صحيحة'
                }
            
            # إنشاء المنتج
            product_id = self.product_model.create_product(
                name=name,
                price=price,
                stock_quantity=stock_quantity,
                category=category,
                min_stock_level=min_stock_level
            )
            
            if product_id:
                # تسجيل العملية
                self.audit_model.log_product_action(
                    user_id=self.current_user['id'],
                    action='create',
                    product_id=product_id,
                    reason=f'إنشاء منتج جديد: {name}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إنشاء المنتج بنجاح',
                    'product_id': product_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء المنتج'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء المنتج: {str(e)}'
            }
    
    def update_product(self, product_id: int, **kwargs) -> Dict[str, Any]:
        """تحديث المنتج"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتحديث المنتجات'
                }
            
            # التحقق من وجود المنتج
            product = self.product_model.get_product_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'المنتج غير موجود'
                }
            
            # تحديث المنتج
            success = self.product_model.update_product(product_id, **kwargs)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_product_action(
                    user_id=self.current_user['id'],
                    action='update',
                    product_id=product_id,
                    reason='تحديث بيانات المنتج'
                )
                
                return {
                    'success': True,
                    'message': 'تم تحديث المنتج بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث المنتج'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث المنتج: {str(e)}'
            }
    
    def update_stock(self, product_id: int, quantity: int, operation: str = 'add') -> Dict[str, Any]:
        """تحديث المخزون"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتحديث المخزون'
                }
            
            # التحقق من وجود المنتج
            product = self.product_model.get_product_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'المنتج غير موجود'
                }
            
            # تحديث المخزون
            success = self.product_model.update_stock(product_id, quantity, operation)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_product_action(
                    user_id=self.current_user['id'],
                    action='update_stock',
                    product_id=product_id,
                    reason=f'{operation} {quantity} من المخزون'
                )
                
                return {
                    'success': True,
                    'message': f'تم تحديث المخزون بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث المخزون'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث المخزون: {str(e)}'
            }
    
    def get_low_stock_products(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات ذات المخزون المنخفض"""
        try:
            return self.product_model.get_low_stock_products()
        except Exception as e:
            show_error(f"خطأ في الحصول على المنتجات ذات المخزون المنخفض: {str(e)}")
            return []
    
    def get_product_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المنتجات"""
        try:
            return self.product_model.get_product_stats()
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات المنتجات: {str(e)}")
            return {}
    
    def get_best_selling_products(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على المنتجات الأكثر مبيعاً"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            return self.product_model.get_best_selling_products(
                start_date=start_date,
                limit=limit
            )
        except Exception as e:
            show_error(f"خطأ في الحصول على المنتجات الأكثر مبيعاً: {str(e)}")
            return []
    
    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في المنتجات"""
        try:
            return self.product_model.search_products(search_term)
        except Exception as e:
            show_error(f"خطأ في البحث في المنتجات: {str(e)}")
            return []
    
    def delete_product(self, product_id: int, admin_password: str) -> Dict[str, Any]:
        """حذف المنتج (للمدير فقط)"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف المنتجات'
                }
            
            # التحقق من كلمة مرور المدير
            from utils.security import verify_password
            if not verify_password(admin_password, self.current_user['password_hash']):
                return {
                    'success': False,
                    'message': 'كلمة مرور المدير غير صحيحة'
                }
            
            # التحقق من وجود المنتج
            product = self.product_model.get_product_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'المنتج غير موجود'
                }
            
            # حذف المنتج
            success = self.product_model.delete_product(product_id)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_product_action(
                    user_id=self.current_user['id'],
                    action='delete',
                    product_id=product_id,
                    reason=f'حذف المنتج: {product["name"]}'
                )
                
                return {
                    'success': True,
                    'message': 'تم حذف المنتج بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حذف المنتج'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حذف المنتج: {str(e)}'
            }
