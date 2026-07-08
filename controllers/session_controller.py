"""
تحكم الجلسات المحسن
Enhanced Session Controller
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.session_model import SessionModel
from models.device_model import DeviceModel
from models.shift_model import ShiftModel
from models.audit_log_model import AuditLogModel
from utils.helpers import format_currency, calculate_session_duration
from utils.notifications import show_success, show_error

class SessionController:
    """تحكم الجلسات المحسن"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.session_model = SessionModel()
        self.device_model = DeviceModel()
        self.shift_model = ShiftModel()
        self.audit_model = AuditLogModel()
    
    def start_session(self, device_id: int, pricing_type: str, time_type: str, 
                     duration_minutes: Optional[int] = None, customer_phone: str = None) -> Dict[str, Any]:
        """بدء جلسة جديدة"""
        try:
            # التحقق من توفر الجهاز
            if not self.device_model.is_device_available(device_id):
                return {
                    'success': False,
                    'message': 'الجهاز غير متاح'
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
            
            # التحقق من صحة نوع الوقت
            if time_type not in ['fixed', 'open']:
                return {
                    'success': False,
                    'message': 'نوع الوقت غير صحيح'
                }
            
            # التحقق من المدة للوقت المحدد
            if time_type == 'fixed' and (not duration_minutes or duration_minutes <= 0):
                return {
                    'success': False,
                    'message': 'يجب تحديد مدة صحيحة للوقت المحدد'
                }
            
            # إنشاء وردية مؤقتة إذا لم توجد وردية نشطة
            shift_id = None
            active_shift = self.shift_model.get_active_shift(self.current_user['id'])
            if not active_shift:
                # إنشاء وردية مؤقتة
                shift_id = self.shift_model.create_shift(
                    cashier_id=self.current_user['id'],
                    shift_name="جلسة مؤقتة",
                    notes="وردية مؤقتة لبدء جلسة"
                )
            else:
                shift_id = active_shift['id']
            
            if not shift_id:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء وردية للجلسة'
                }
            
            # إنشاء الجلسة
            session_id = self.session_model.create_session(
                device_id=device_id,
                cashier_id=self.current_user['id'],
                shift_id=shift_id,
                pricing_type=pricing_type,
                session_price=session_price,
                time_type=time_type,
                duration_minutes=duration_minutes,
                customer_phone=customer_phone
            )
            
            if session_id:
                # تحديث حالة الجهاز
                self.device_model.set_device_busy(device_id, session_id)
                
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='create',
                    session_id=session_id,
                    reason=f'بدء جلسة جديدة على الجهاز {device["name"]}'
                )
                
                return {
                    'success': True,
                    'message': 'تم بدء الجلسة بنجاح',
                    'session_id': session_id,
                    'session_info': {
                        'device_name': device['name'],
                        'pricing_type': pricing_type,
                        'time_type': time_type,
                        'duration_minutes': duration_minutes,
                        'session_price': session_price
                    }
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
    
    def end_session(self, session_id: int, notes: str = "") -> Dict[str, Any]:
        """إنهاء الجلسة"""
        try:
            # الحصول على بيانات الجلسة
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'Session not found'
                }
            
            if session['status'] not in ['active', 'paused']:
                return {
                    'success': False,
                    'message': 'Session is not active or paused'
                }
            
            # إنهاء الجلسة
            success = self.session_model.end_session(
                session_id=session_id,
                cashier_id=self.current_user['id'],
                notes=notes
            )
            
            if success:
                # تحديث حالة الجهاز
                self.device_model.set_device_available(session['device_id'])
                
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='end',
                    session_id=session_id,
                    reason='إنهاء الجلسة'
                )
                
                return {
                    'success': True,
                    'message': 'Session ended successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to end session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error ending session: {str(e)}'
            }
    
    def get_session_time_info(self, session_id: int) -> Dict[str, Any]:
        """الحصول على معلومات الوقت للجلسة"""
        try:
            return self.session_model.get_session_time_info(session_id)
        except Exception as e:
            return {
                'error': f'خطأ في الحصول على معلومات الوقت: {str(e)}'
            }
    
    def get_session_cost_info(self, session_id: int) -> Dict[str, Any]:
        """الحصول على معلومات تكلفة الجلسة"""
        try:
            # التحقق من حالة الجلسة أولاً
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'error': 'الجلسة غير موجودة'
                }
            
            # إذا كانت الجلسة متوقفة، تأكد من أن التكلفة لا تزيد
            if session.get('status') == 'paused':
                print(f"الجلسة {session_id} متوقفة - حساب التكلفة الثابتة")
            
            return self.session_model.calculate_session_cost(session_id)
        except Exception as e:
            return {
                'error': f'خطأ في الحصول على معلومات التكلفة: {str(e)}'
            }
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """الحصول على الجلسات النشطة"""
        try:
            return self.session_model.get_all_active_sessions()
        except Exception as e:
            show_error(f"خطأ في الحصول على الجلسات النشطة: {str(e)}")
            return []
    
    def get_device_session(self, device_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على جلسة الجهاز الحالية"""
        try:
            return self.session_model.get_active_session(device_id)
        except Exception as e:
            show_error(f"خطأ في الحصول على جلسة الجهاز: {str(e)}")
            return None
    
    def extend_session(self, session_id: int, additional_minutes: int) -> Dict[str, Any]:
        """تمديد الجلسة (للساعات المحددة)"""
        try:
            if additional_minutes <= 0:
                return {
                    'success': False,
                    'message': 'يجب أن تكون المدة الإضافية أكبر من صفر'
                }
            
            success = self.session_model.extend_session(session_id, additional_minutes)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='extend',
                    session_id=session_id,
                    reason=f'تمديد الجلسة بـ {additional_minutes} دقيقة'
                )
                
                return {
                    'success': True,
                    'message': f'تم تمديد الجلسة بـ {additional_minutes} دقيقة'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تمديد الجلسة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تمديد الجلسة: {str(e)}'
            }
    
    def get_session_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """الحصول على إحصائيات الجلسات"""
        try:
            return self.session_model.get_session_statistics(start_date, end_date)
        except Exception as e:
            show_error(f"خطأ في الحصول على إحصائيات الجلسات: {str(e)}")
            return {}
    
    def get_sessions_by_shift(self, shift_id: int) -> List[Dict[str, Any]]:
        """الحصول على جلسات الوردية"""
        try:
            return self.session_model.get_sessions_by_shift(shift_id)
        except Exception as e:
            show_error(f"خطأ في الحصول على جلسات الوردية: {str(e)}")
            return []
    
    def pause_session(self, session_id: int) -> Dict[str, Any]:
        """إيقاف الجلسة مؤقتاً"""
        try:
            # التحقق من وجود الجلسة
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'Session not found'
                }
            
            if session['status'] != 'active':
                return {
                    'success': False,
                    'message': 'Session is not active'
                }
            
            # إيقاف الجلسة
            success = self.session_model.pause_session(session_id)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='pause',
                    session_id=session_id,
                    reason='Session paused'
                )
                
                return {
                    'success': True,
                    'message': 'Session paused successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to pause session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error pausing session: {str(e)}'
            }
    
    def resume_session(self, session_id: int) -> Dict[str, Any]:
        """استئناف الجلسة"""
        try:
            # التحقق من وجود الجلسة
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'Session not found'
                }
            
            if session['status'] != 'paused':
                return {
                    'success': False,
                    'message': 'Session is not paused'
                }
            
            # استئناف الجلسة
            success = self.session_model.resume_session(session_id)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='resume',
                    session_id=session_id,
                    reason='Session resumed'
                )
                
                return {
                    'success': True,
                    'message': 'Session resumed successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to resume session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error resuming session: {str(e)}'
            }
    
    def add_product_to_session(self, session_id: int, product_id: int, quantity: int) -> Dict[str, Any]:
        """إضافة منتج للجلسة"""
        try:
            # الحصول على بيانات المنتج
            from models.product_model import ProductModel
            product_model = ProductModel()
            product = product_model.get_product_by_id(product_id)
            
            if not product:
                return {
                    'success': False,
                    'message': 'Product not found'
                }
            
            # التحقق من توفر الكمية
            if product['stock_quantity'] < quantity:
                return {
                    'success': False,
                    'message': f'Not enough stock. Available: {product["stock_quantity"]}'
                }
            
            # إضافة المنتج للجلسة
            result = self.session_model.add_product_to_session(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product['price']
            )
            
            if result:
                # تحديث المخزون
                new_stock = product['stock_quantity'] - quantity
                product_model.update_product(
                    product_id=product_id,
                    stock_quantity=new_stock,
                    admin_password=None  # لا يتطلب باسورد المدير لتحديث المخزون من الجلسة
                )
                
                # تسجيل في سجل التدقيق
                self.audit_model.create_audit_log(
                    entity_type='session',
                    entity_id=session_id,
                    action='add_product',
                    performed_by=self.current_user['id'],
                    reason=f'Added {quantity} of {product["name"]} to session',
                    new_value={
                        'product_id': product_id,
                        'product_name': product['name'],
                        'quantity': quantity,
                        'unit_price': product['price']
                    }
                )
                
                return {
                    'success': True,
                    'message': f'Added {quantity} of {product["name"]} to session',
                    'product_name': product['name'],
                    'quantity': quantity,
                    'unit_price': product['price'],
                    'total_price': product['price'] * quantity
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to add product to session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error adding product to session: {str(e)}'
            }
    
    def remove_product_from_session(self, session_product_id: int) -> Dict[str, Any]:
        """حذف منتج من الجلسة"""
        try:
            # الحصول على بيانات منتج الجلسة
            session_product = self.session_model.get_session_product_by_id(session_product_id)
            
            if not session_product:
                return {
                    'success': False,
                    'message': 'Session product not found'
                }
            
            # حذف المنتج من الجلسة
            result = self.session_model.remove_product_from_session(session_product_id)
            
            if result:
                # إعادة الكمية للمخزون
                from models.product_model import ProductModel
                product_model = ProductModel()
                product = product_model.get_product_by_id(session_product['product_id'])
                
                if product:
                    new_stock = product['stock_quantity'] + session_product['quantity']
                    product_model.update_product(
                        product_id=session_product['product_id'],
                        stock_quantity=new_stock,
                        admin_password=None  # لا يتطلب باسورد المدير لتحديث المخزون من الجلسة
                    )
                
                # تسجيل في سجل التدقيق
                self.audit_model.create_audit_log(
                    entity_type='session',
                    entity_id=session_product['session_id'],
                    action='remove_product',
                    performed_by=self.current_user['id'],
                    reason=f'Removed {session_product["quantity"]} of {session_product.get("product_name", "product")} from session',
                    old_value={
                        'product_id': session_product['product_id'],
                        'quantity': session_product['quantity'],
                        'unit_price': session_product['unit_price']
                    }
                )
                
                return {
                    'success': True,
                    'message': f'Removed {session_product["quantity"]} of {session_product.get("product_name", "product")} from session'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to remove product from session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error removing product from session: {str(e)}'
            }
    
    def get_session_products(self, session_id: int) -> Dict[str, Any]:
        """الحصول على منتجات الجلسة"""
        try:
            products = self.session_model.get_session_products(session_id)
            
            return {
                'success': True,
                'products': products
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting session products: {str(e)}'
            }
    
    def transfer_session(self, session_id: int, target_device_id: int) -> Dict[str, Any]:
        """نقل الجلسة إلى جهاز آخر"""
        try:
            # الحصول على بيانات الجلسة الحالية
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'الجلسة غير موجودة'
                }
            
            # التحقق من أن الجلسة نشطة أو متوقفة
            if session['status'] not in ['active', 'paused']:
                return {
                    'success': False,
                    'message': 'الجلسة غير نشطة'
                }
            
            # التحقق من توفر الجهاز الهدف
            if not self.device_model.is_device_available(target_device_id):
                return {
                    'success': False,
                    'message': 'الجهاز الهدف غير متاح'
                }
            
            # الحصول على بيانات الجهاز الهدف
            target_device = self.device_model.get_device_by_id(target_device_id)
            if not target_device:
                return {
                    'success': False,
                    'message': 'الجهاز الهدف غير موجود'
                }
            
            # التحقق من توافق نوع التسعيرة
            pricing_type = session['pricing_type']
            if pricing_type == 'single':
                target_price = target_device['price_single']
            elif pricing_type == 'multi':
                target_price = target_device['price_multi']
            else:
                return {
                    'success': False,
                    'message': 'نوع التسعيرة غير صحيح'
                }
            
            if target_price == 0:
                return {
                    'success': False,
                    'message': f'الجهاز الهدف لا يدعم تسعيرة {pricing_type}'
                }
            
            # بدء عملية النقل
            success = self.session_model.transfer_session(
                session_id=session_id,
                target_device_id=target_device_id,
                new_session_price=target_price
            )
            
            if success:
                # تحديث حالة الأجهزة
                # تحرير الجهاز المصدر
                self.device_model.set_device_available(session['device_id'])
                # حجز الجهاز الهدف
                self.device_model.set_device_busy(target_device_id, session_id)
                
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='transfer',
                    session_id=session_id,
                    reason=f'نقل الجلسة من الجهاز {session["device_name"]} إلى الجهاز {target_device["name"]}'
                )
                
                return {
                    'success': True,
                    'message': f'تم نقل الجلسة بنجاح من {session["device_name"]} إلى {target_device["name"]}',
                    'session_info': {
                        'session_id': session_id,
                        'source_device': session['device_name'],
                        'target_device': target_device['name'],
                        'new_price': target_price
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في نقل الجلسة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في نقل الجلسة: {str(e)}'
            }
    
    def update_session_data(self, session_id: int, **kwargs) -> Dict[str, Any]:
        """تحديث بيانات الجلسة"""
        try:
            # التحقق من وجود الجلسة
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'الجلسة غير موجودة'
                }
            
            # التحقق من أن الجلسة نشطة أو متوقفة
            if session['status'] not in ['active', 'paused']:
                return {
                    'success': False,
                    'message': 'لا يمكن تعديل جلسة منتهية'
                }
            
            # تحديث بيانات الجلسة
            success = self.session_model.update_session(session_id, **kwargs)
            
            if success:
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='update',
                    session_id=session_id,
                    reason='تحديث بيانات الجلسة'
                )
                
                return {
                    'success': True,
                    'message': 'تم تحديث بيانات الجلسة بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث بيانات الجلسة'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تحديث بيانات الجلسة: {str(e)}'
            }
    
    def change_session_pricing_type(self, session_id: int, new_pricing_type: str) -> Dict[str, Any]:
        """تغيير نوع التسعيرة للجلسة النشطة"""
        try:
            # التحقق من وجود الجلسة
            session = self.session_model.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'الجلسة غير موجودة'
                }
            
            # التحقق من أن الجلسة نشطة أو متوقفة
            if session['status'] not in ['active', 'paused']:
                return {
                    'success': False,
                    'message': 'يمكن تغيير نوع التسعيرة للجلسات النشطة أو المتوقفة فقط'
                }
            
            # التحقق من أن النوع الجديد مختلف عن الحالي
            current_pricing_type = session['pricing_type']
            if current_pricing_type == new_pricing_type:
                return {
                    'success': False,
                    'message': 'نوع التسعيرة الجديد مطابق للنوع الحالي'
                }
            
            # الحصول على بيانات الجهاز
            device = self.device_model.get_device_by_id(session['device_id'])
            if not device:
                return {
                    'success': False,
                    'message': 'الجهاز غير موجود'
                }
            
            # التحقق من أن الجهاز يحتوي على نوعي التسعيرة
            if not device.get('price_single') or not device.get('price_multi'):
                return {
                    'success': False,
                    'message': 'هذا الجهاز لا يحتوي على نوعي التسعيرة (فردي وجماعي)'
                }
            
            # تغيير نوع التسعيرة باستخدام نموذج الجلسات
            result = self.session_model.change_session_pricing_type(session_id, new_pricing_type)
            
            if result['success']:
                # تسجيل العملية
                self.audit_model.log_session_action(
                    user_id=self.current_user['id'],
                    action='change_pricing',
                    session_id=session_id,
                    reason=f'تغيير نوع التسعيرة من {result["old_pricing_type"]} إلى {result["new_pricing_type"]}'
                )
                
                # إضافة معلومات إضافية للنتيجة
                result.update({
                    'device_name': device['name'],
                    'old_price': session['session_price'],
                    'new_price': result['new_session_price']
                })
                
                return result
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'message': f'خطأ في تغيير نوع التسعيرة: {str(e)}'
            }