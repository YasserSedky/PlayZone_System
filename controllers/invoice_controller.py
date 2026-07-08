"""
تحكم الفواتير
Invoice Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.invoice_model import InvoiceModel
from models.product_model import ProductModel
from models.customer_model import CustomerModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency, calculate_session_cost
from utils.notifications import show_success, show_error

class InvoiceController:
    """تحكم الفواتير"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.invoice_model = InvoiceModel()
        self.product_model = ProductModel()
        self.customer_model = CustomerModel()
        self.audit_model = AuditLogModel()
    
    def get_invoices(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على الفواتير"""
        try:
            if self.current_user['role'] == 'admin':
                # المدير يمكنه رؤية جميع الفواتير
                if start_date and end_date:
                    return self.invoice_model.search_invoices("", start_date, end_date)
                else:
                    return self.invoice_model.get_invoices_by_cashier(self.current_user['id'])
            else:
                # الكاشير يمكنه رؤية فواتيره فقط
                return self.invoice_model.get_invoices_by_cashier(
                    cashier_id=self.current_user['id'],
                    start_date=start_date,
                    end_date=end_date
                )
        except Exception as e:
            show_error(f"خطأ في الحصول على الفواتير: {str(e)}")
            return []
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على فاتورة بالمعرف"""
        try:
            invoice = self.invoice_model.get_invoice_by_id(invoice_id)
            
            # التحقق من الصلاحيات
            if invoice and self.current_user['role'] == 'cashier':
                if invoice['cashier_open'] != self.current_user['id'] and invoice['cashier_close'] != self.current_user['id']:
                    return None
            
            return invoice
        except Exception as e:
            show_error(f"خطأ في الحصول على الفاتورة: {str(e)}")
            return None
    
    def add_product_to_invoice(self, invoice_id: int, product_id: int, quantity: int) -> Dict[str, Any]:
        """إضافة منتج للفاتورة"""
        try:
            # التحقق من وجود الفاتورة
            invoice = self.invoice_model.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    'success': False,
                    'message': 'الفاتورة غير موجودة'
                }
            
            # التحقق من أن الفاتورة نشطة
            if invoice['end_time']:
                return {
                    'success': False,
                    'message': 'لا يمكن إضافة منتجات لفاتورة مغلقة'
                }
            
            # التحقق من الصلاحيات
            if self.current_user['role'] == 'cashier' and invoice['cashier_open'] != self.current_user['id']:
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتعديل هذه الفاتورة'
                }
            
            # الحصول على بيانات المنتج
            product = self.product_model.get_product_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'المنتج غير موجود'
                }
            
            # التحقق من توفر الكمية
            if not self.product_model.is_product_available(product_id, quantity):
                return {
                    'success': False,
                    'message': 'الكمية المطلوبة غير متوفرة في المخزون'
                }
            
            # إضافة المنتج للفاتورة
            success = self.invoice_model.add_product_to_invoice(
                invoice_id=invoice_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product['price']
            )
            
            if success:
                # خصم الكمية من المخزون
                self.product_model.subtract_stock(product_id, quantity)
                
                # تسجيل العملية
                self.audit_model.log_invoice_action(
                    user_id=self.current_user['id'],
                    action='add_product',
                    invoice_id=invoice_id,
                    reason=f'إضافة {quantity} من {product["name"]}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إضافة المنتج للفاتورة بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة المنتج للفاتورة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إضافة المنتج للفاتورة: {str(e)}'
            }
    
    def remove_product_from_invoice(self, item_id: int) -> Dict[str, Any]:
        """إزالة منتج من الفاتورة"""
        try:
            # الحصول على بيانات العنصر
            invoice_items = self.invoice_model.get_invoice_items(item_id)
            if not invoice_items:
                return {
                    'success': False,
                    'message': 'العنصر غير موجود'
                }
            
            # التحقق من الصلاحيات
            if self.current_user['role'] == 'cashier':
                # يمكن للكاشير إزالة المنتجات من فواتيره فقط
                pass
            
            # إزالة المنتج من الفاتورة
            success = self.invoice_model.remove_product_from_invoice(item_id)
            
            if success:
                # إرجاع الكمية للمخزون
                # يمكن إضافة منطق إرجاع المخزون هنا
                
                # تسجيل العملية
                self.audit_model.log_invoice_action(
                    user_id=self.current_user['id'],
                    action='remove_product',
                    invoice_id=invoice_items[0]['invoice_id'],
                    reason='إزالة منتج من الفاتورة'
                )
                
                return {
                    'success': True,
                    'message': 'تم إزالة المنتج من الفاتورة بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إزالة المنتج من الفاتورة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إزالة المنتج من الفاتورة: {str(e)}'
            }
    
    def pay_with_customer_balance(self, invoice_id: int, customer_phone: str, customer_password: str) -> Dict[str, Any]:
        """الدفع برصيد العميل"""
        try:
            # التحقق من بيانات العميل
            customer = self.customer_model.authenticate_customer(customer_phone, customer_password)
            if not customer:
                return {
                    'success': False,
                    'message': 'بيانات العميل غير صحيحة'
                }
            
            # الحصول على بيانات الفاتورة
            invoice = self.invoice_model.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    'success': False,
                    'message': 'الفاتورة غير موجودة'
                }
            
            # التحقق من كفاية الرصيد
            if not self.customer_model.has_sufficient_balance(customer_phone, invoice['total_amount']):
                return {
                    'success': False,
                    'message': 'رصيد العميل غير كافي'
                }
            
            # خصم المبلغ من رصيد العميل
            success = self.customer_model.subtract_balance(customer_phone, invoice['total_amount'])
            
            if success:
                # تحديث الفاتورة
                self.invoice_model.update_invoice_total(invoice_id)
                
                # تسجيل العملية
                self.audit_model.log_customer_action(
                    user_id=self.current_user['id'],
                    action='payment',
                    customer_phone=customer_phone,
                    reason=f'دفع فاتورة رقم {invoice_id}'
                )
                
                return {
                    'success': True,
                    'message': 'تم الدفع برصيد العميل بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في خصم المبلغ من رصيد العميل'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في الدفع برصيد العميل: {str(e)}'
            }
    
    def get_invoice_items(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات الفاتورة"""
        try:
            return self.invoice_model.get_invoice_items(invoice_id)
        except Exception as e:
            show_error(f"خطأ في الحصول على منتجات الفاتورة: {str(e)}")
            return []
    
    def get_invoice_stats(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """الحصول على إحصائيات الفواتير"""
        try:
            return self.invoice_model.get_invoice_stats(start_date, end_date)
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات الفواتير: {str(e)}")
            return {}
    
    def delete_invoice(self, invoice_id: int, admin_password: str) -> Dict[str, Any]:
        """حذف الفاتورة (للمدير فقط)"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف الفواتير'
                }
            
            # التحقق من كلمة مرور المدير
            from utils.security import hash_password, verify_password
            if not verify_password(admin_password, self.current_user['password_hash']):
                return {
                    'success': False,
                    'message': 'كلمة مرور المدير غير صحيحة'
                }
            
            # حذف الفاتورة
            success = self.invoice_model.delete_invoice(invoice_id)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_invoice_action(
                    user_id=self.current_user['id'],
                    action='delete',
                    invoice_id=invoice_id,
                    reason='حذف الفاتورة'
                )
                
                return {
                    'success': True,
                    'message': 'تم حذف الفاتورة بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حذف الفاتورة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في حذف الفاتورة: {str(e)}'
            }
