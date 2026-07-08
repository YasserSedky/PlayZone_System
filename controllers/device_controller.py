"""
تحكم الأجهزة
Device Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.device_model import DeviceModel
from models.invoice_model import InvoiceModel
from models.shift_model import ShiftModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency, calculate_session_duration
from utils.notifications import show_success, show_error

class DeviceController:
    """تحكم الأجهزة"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.device_model = DeviceModel()
        self.invoice_model = InvoiceModel()
        self.shift_model = ShiftModel()
        self.audit_model = AuditLogModel()
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الأجهزة"""
        try:
            return self.device_model.get_all_devices()
        except Exception as e:
            show_error(f"خطأ في الحصول على الأجهزة: {str(e)}")
            return []
    
    def create_device(self, name: str, device_type: str, price_single: Decimal, price_multi: Decimal) -> Dict[str, Any]:
        """إنشاء جهاز جديد"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإنشاء أجهزة'
                }
            
            # التحقق من صحة البيانات
            if not name or not device_type or price_single <= 0 or price_multi <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال بيانات صحيحة'
                }
            
            # إنشاء الجهاز
            device_id = self.device_model.create_device(
                name=name,
                device_type=device_type,
                price_single=price_single,
                price_multi=price_multi
            )
            
            if device_id:
                # تسجيل العملية
                self.audit_model.log_device_action(
                    user_id=self.current_user['id'],
                    action='create',
                    device_id=device_id,
                    reason=f'إنشاء جهاز جديد: {name}'
                )
                
                return {
                    'success': True,
                    'message': 'تم إنشاء الجهاز بنجاح',
                    'device_id': device_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء الجهاز'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إنشاء الجهاز: {str(e)}'
            }
    
    def start_session(self, device_id: int, pricing_type: str, customer_phone: str = None) -> Dict[str, Any]:
        """بدء جلسة جديدة"""
        try:
            # التحقق من توفر الجهاز
            if not self.device_model.is_device_available(device_id):
                return {
                    'success': False,
                    'message': 'الجهاز غير متاح'
                }
            
            # الحصول على الوردية النشطة
            active_shift = self.shift_model.get_active_shift(self.current_user['id'])
            if not active_shift:
                return {
                    'success': False,
                    'message': 'لا توجد وردية نشطة. يرجى بدء وردية جديدة'
                }
            
            # الحصول على بيانات الجهاز
            device = self.device_model.get_device_by_id(device_id)
            if not device:
                return {
                    'success': False,
                    'message': 'الجهاز غير موجود'
                }
            
            # تحديد السعر
            if pricing_type == 'single':
                session_price = device['price_single']
            elif pricing_type == 'multi':
                session_price = device['price_multi']
            else:
                return {
                    'success': False,
                    'message': 'نوع التسعيرة غير صحيح'
                }
            
            # تحديد طريقة الدفع
            paid_by = 'customer_balance' if customer_phone else 'cash'
            
            # إنشاء الفاتورة
            invoice_id = self.invoice_model.create_invoice(
                device_id=device_id,
                cashier_open=self.current_user['id'],
                shift_id=active_shift['id'],
                pricing_type=pricing_type,
                session_price=session_price,
                customer_phone=customer_phone,
                paid_by=paid_by
            )
            
            if invoice_id:
                # تحديث حالة الجهاز
                self.device_model.set_device_occupied(device_id, invoice_id)
                
                # تسجيل العملية
                self.audit_model.log_invoice_action(
                    user_id=self.current_user['id'],
                    action='create',
                    invoice_id=invoice_id,
                    reason=f'بدء جلسة جديدة على الجهاز {device["name"]}'
                )
                
                return {
                    'success': True,
                    'message': 'تم بدء الجلسة بنجاح',
                    'invoice_id': invoice_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في بدء الجلسة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في بدء الجلسة: {str(e)}'
            }
    
    def close_session(self, invoice_id: int) -> Dict[str, Any]:
        """إغلاق الجلسة"""
        try:
            # الحصول على بيانات الفاتورة
            invoice = self.invoice_model.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    'success': False,
                    'message': 'الفاتورة غير موجودة'
                }
            
            # إغلاق الفاتورة
            success = self.invoice_model.close_invoice(
                invoice_id=invoice_id,
                cashier_close=self.current_user['id']
            )
            
            if success:
                # تحديث حالة الجهاز
                self.device_model.set_device_available(invoice['device_id'])
                
                # تسجيل العملية
                self.audit_model.log_invoice_action(
                    user_id=self.current_user['id'],
                    action='close',
                    invoice_id=invoice_id,
                    reason='إغلاق الجلسة'
                )
                
                # إشعار واجهات أخرى بتحديث البيانات
                self.notify_invoice_refresh()
                
                return {
                    'success': True,
                    'message': 'تم إغلاق الجلسة بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إغلاق الجلسة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في إغلاق الجلسة: {str(e)}'
            }
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """الحصول على الجلسات النشطة"""
        try:
            return self.invoice_model.get_active_invoices()
        except Exception as e:
            show_error(f"خطأ في الحصول على الجلسات النشطة: {str(e)}")
            return []
    
    def get_open_sessions_from_previous_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على الجلسات المفتوحة من الورديات السابقة"""
        try:
            return self.invoice_model.get_open_sessions_from_previous_shifts()
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسات المفتوحة من الورديات السابقة: {e}")
            return []
    
    def notify_invoice_refresh(self):
        """إشعار واجهات أخرى بتحديث البيانات"""
        try:
            # مسح التخزين المؤقت للورديات
            from controllers.shift_controller import ShiftController
            shift_controller = ShiftController()
            shift_controller.shift_data_cache.clear()
            
            # إشعار واجهة الفواتير بتحديث البيانات
            try:
                # البحث عن واجهة الفواتير في التطبيق
                import sys
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    # البحث عن نافذة لوحة التحكم
                    for widget in app.allWidgets():
                        if hasattr(widget, 'invoice_management'):
                            widget.invoice_management.load_invoices()
                            print("تم تحديث واجهة الفواتير من DeviceController")
                            break
            except Exception as e:
                print(f"خطأ في تحديث واجهة الفواتير من DeviceController: {e}")
            
            logger.info("تم إشعار واجهات أخرى بتحديث بيانات الفواتير")
            
        except Exception as e:
            logger.error(f"خطأ في إشعار تحديث البيانات: {e}")
    
    def get_device_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأجهزة"""
        try:
            return self.device_model.get_device_stats()
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات الأجهزة: {str(e)}")
            return {}
    
    def update_device_prices(self, device_id: int, price_single: Decimal, price_multi: Decimal) -> Dict[str, Any]:
        """تحديث أسعار الجهاز"""
        try:
            if not self.current_user or self.current_user['role'] != 'admin':
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتحديث الأسعار'
                }
            
            # التحقق من صحة الأسعار
            if price_single <= 0 or price_multi <= 0:
                return {
                    'success': False,
                    'message': 'الأسعار يجب أن تكون أكبر من صفر'
                }
            
            # تحديث الأسعار
            success = self.device_model.update_device(
                device_id=device_id,
                price_single=price_single,
                price_multi=price_multi
            )
            
            if success:
                # تسجيل العملية
                self.audit_model.log_device_action(
                    user_id=self.current_user['id'],
                    action='update_prices',
                    device_id=device_id,
                    reason=f'تحديث أسعار الجهاز: {price_single} / {price_multi}'
                )
                
                return {
                    'success': True,
                    'message': 'تم تحديث أسعار الجهاز بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث أسعار الجهاز'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث أسعار الجهاز: {str(e)}'
            }
