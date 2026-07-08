"""
موديل إدارة المدفوعات وإنهاء الجلسات
Payment Model for Session Checkout
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class PaymentModel:
    """موديل إدارة المدفوعات وإنهاء الجلسات"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def process_session_checkout(self, session_id: int, cashier_id: int, 
                               payment_method: str, total_amount: Decimal,
                               cash_amount: Decimal = Decimal('0.00'),
                               customer_amount: Decimal = Decimal('0.00'),
                               customer_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """معالجة إنهاء الجلسة والدفع"""
        try:
            # بدء المعاملة
            self.db.connection.execute("BEGIN TRANSACTION")
            
            # الحصول على بيانات الجلسة
            session = self.get_session_data(session_id)
            if not session:
                self.db.connection.rollback()
                return {
                    'success': False,
                    'message': 'الجلسة غير موجودة'
                }
            
            # التحقق من حالة الجلسة
            if session['status'] not in ['active', 'paused']:
                self.db.connection.rollback()
                return {
                    'success': False,
                    'message': 'الجلسة غير نشطة'
                }
            
            # إنشاء الفاتورة
            invoice_id = self.create_invoice_from_session(
                session=session,
                cashier_id=cashier_id,
                payment_method=payment_method,
                total_amount=total_amount,
                customer_data=customer_data
            )
            
            if not invoice_id:
                self.db.connection.rollback()
                return {
                    'success': False,
                    'message': 'فشل في إنشاء الفاتورة'
                }
            
            # نسخ منتجات الجلسة إلى الفاتورة
            self.copy_session_products_to_invoice(session_id, invoice_id)
            
            # إنهاء الجلسة
            success = self.end_session(session_id, cashier_id)
            if not success:
                self.db.connection.rollback()
                return {
                    'success': False,
                    'message': 'فشل في إنهاء الجلسة'
                }
            
            # معالجة الدفع من حساب العميل
            if payment_method == 'customer_balance' and customer_data and customer_amount > 0:
                logger.info(f"بدء معالجة الدفع من حساب العميل: {customer_data.get('phone', 'غير محدد')} - المبلغ: {customer_amount}")
                success = self.process_customer_payment(
                    customer_data=customer_data,
                    amount=customer_amount,
                    cashier_id=cashier_id,
                    invoice_id=invoice_id
                )
                if not success:
                    logger.error(f"فشل في معالجة الدفع من حساب العميل: {customer_data.get('phone', 'غير محدد')}")
                    self.db.connection.rollback()
                    return {
                        'success': False,
                        'message': f'فشل في معالجة الدفع من حساب العميل {customer_data.get("phone", "غير محدد")}'
                    }
                else:
                    logger.info(f"تم معالجة الدفع من حساب العميل بنجاح: {customer_data.get('phone', 'غير محدد')}")
            
            # تحديث حالة الجهاز
            self.set_device_available(session['device_id'])
            
            # تأكيد المعاملة
            self.db.connection.commit()
            
            logger.info(f"تم إنهاء الجلسة {session_id} بنجاح - الفاتورة {invoice_id}")
            
            return {
                'success': True,
                'message': 'تم إنهاء الجلسة والدفع بنجاح',
                'invoice_id': invoice_id,
                'total_amount': total_amount,
                'payment_method': payment_method
            }
            
        except Exception as e:
            try:
                self.db.connection.rollback()
            except Exception as rollback_error:
                logger.error(f"خطأ في إلغاء المعاملة: {rollback_error}")
            
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"خطأ في معالجة إنهاء الجلسة: {error_details}")
            
            # إرجاع رسالة خطأ آمنة
            error_message = str(e) if str(e) else "خطأ غير معروف"
            return {
                'success': False,
                'message': f'حدث خطأ في معالجة الدفع: {error_message}'
            }
    
    def get_session_data(self, session_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات الجلسة"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.id = ?""",
                (session_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على بيانات الجلسة: {e}")
            return None
    
    def create_invoice_from_session(self, session: Dict[str, Any], cashier_id: int,
                                  payment_method: str, total_amount: Decimal,
                                  customer_data: Dict[str, Any] = None) -> Optional[int]:
        """إنشاء فاتورة من الجلسة"""
        try:
            # حساب تكلفة الجلسة
            session_cost = self.calculate_session_cost(session['id'])
            products_total = self.get_session_products_total(session['id'])
            
            # الحصول على الوردية النشطة الحالية (وردية الإغلاق)
            current_shift_id = session['shift_id']  # الاحتفاظ بالوردية الأصلية افتراضياً
            try:
                from models.shift_model import ShiftModel
                shift_model = ShiftModel()
                active_shift = shift_model.get_active_shared_shift()
                if active_shift:
                    current_shift_id = active_shift['id']
                    logger.info(f"حفظ الفاتورة في وردية الإغلاق {current_shift_id} (كانت في وردية {session['shift_id']})")
                else:
                    logger.warning(f"لا توجد وردية نشطة، سيتم الاحتفاظ بالوردية الأصلية {session['shift_id']}")
            except Exception as e:
                logger.warning(f"لم يتم تحديث وردية الفاتورة: {e}")
            
            # ⭐ تحديد نوع التسعيرة الصحيح بناءً على الأجزاء المستخدمة
            final_pricing_type = session.get('pricing_type', 'single')  # القيمة الافتراضية
            
            try:
                from models.pricing_segment_model import PricingSegmentModel
                pricing_model = PricingSegmentModel()
                pricing_summary = pricing_model.get_session_pricing_summary(session['id'])
                
                if pricing_summary:
                    has_single = pricing_summary.get('total_single_cost', 0) > 0
                    has_multi = pricing_summary.get('total_multi_cost', 0) > 0
                    
                    # تحديد نوع التسعيرة بناءً على ما تم استخدامه فعلياً
                    if has_single and has_multi:
                        final_pricing_type = 'mixed'  # استخدام "mixed" للتسعيرة المختلطة
                        logger.info(f"الجلسة {session['id']} استخدمت تسعيرة مختلطة (فردي + جماعي)")
                    elif has_single:
                        final_pricing_type = 'single'
                        logger.info(f"الجلسة {session['id']} استخدمت تسعيرة فردي فقط")
                    elif has_multi:
                        final_pricing_type = 'multi'
                        logger.info(f"الجلسة {session['id']} استخدمت تسعيرة جماعي فقط")
            except Exception as e:
                logger.warning(f"خطأ في تحديد نوع التسعيرة النهائي: {e}")
            
            # بيانات الفاتورة
            invoice_data = {
                'device_id': session['device_id'],
                'cashier_open': session['cashier_id'],
                'cashier_close': cashier_id,
                'shift_id': current_shift_id,  # استخدام الوردية النشطة الحالية
                'start_time': session['start_time'],
                'end_time': datetime.now(),
                'pricing_type': final_pricing_type,  # ⭐ استخدام النوع الصحيح (single/multi/mixed)
                'session_price': float(session_cost),  # تحويل Decimal إلى float
                'products_total': float(products_total),  # تحويل Decimal إلى float
                'total_amount': float(total_amount),  # تحويل Decimal إلى float
                'customer_phone': customer_data['phone'] if customer_data else session.get('customer_phone'),
                'paid_by': payment_method,
                'created_by': cashier_id,
                'created_at': datetime.now()
            }
            
            # إنشاء الفاتورة
            cursor = self.db.connection.cursor()
            cursor.execute(
                """INSERT INTO invoices 
                   (device_id, session_id, cashier_open, cashier_close, shift_id, start_time, end_time,
                    pricing_type, session_price, products_total, total_amount, 
                    customer_phone, paid_by, created_by, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice_data['device_id'], session['id'], invoice_data['cashier_open'], 
                 invoice_data['cashier_close'], invoice_data['shift_id'], invoice_data['start_time'], 
                 invoice_data['end_time'], invoice_data['pricing_type'], invoice_data['session_price'], 
                 invoice_data['products_total'], invoice_data['total_amount'], invoice_data['customer_phone'], 
                 invoice_data['paid_by'], invoice_data['created_by'], invoice_data['created_at'])
            )
            
            invoice_id = cursor.lastrowid
            
            if invoice_id:
                logger.info(f"تم إنشاء الفاتورة {invoice_id} من الجلسة {session['id']}")
                return invoice_id
            else:
                logger.error(f"فشل في إنشاء الفاتورة من الجلسة {session['id']}")
                return None
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الفاتورة: {e}")
            return None
    
    def copy_session_products_to_invoice(self, session_id: int, invoice_id: int) -> bool:
        """نسخ منتجات الجلسة إلى الفاتورة"""
        try:
            # الحصول على منتجات الجلسة
            session_products = self.get_session_products(session_id)
            
            cursor = self.db.connection.cursor()
            for product in session_products:
                # إضافة المنتج للفاتورة
                cursor.execute(
                    """INSERT INTO invoice_products (invoice_id, product_id, quantity, price)
                       VALUES (?, ?, ?, ?)""",
                    (invoice_id, product['product_id'], product['quantity'], float(product['unit_price']))
                )
                
                if cursor.rowcount == 0:
                    logger.error(f"فشل في إضافة منتج {product['product_id']} للفاتورة {invoice_id}")
                    return False
            
            # حفظ التغييرات في قاعدة البيانات
            self.db.connection.commit()
            
            logger.info(f"تم نسخ {len(session_products)} منتج من الجلسة {session_id} إلى الفاتورة {invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في نسخ منتجات الجلسة: {e}")
            return False
    
    def end_session(self, session_id: int, cashier_id: int) -> bool:
        """إنهاء الجلسة"""
        try:
            end_time = datetime.now()
            cursor = self.db.connection.cursor()
            cursor.execute(
                """UPDATE sessions SET end_time = ?, status = ?, notes = ? WHERE id = ?""",
                (end_time, 'completed', 'تم إنهاء الجلسة مع الدفع', session_id)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"تم إنهاء الجلسة {session_id}")
                return True
            else:
                logger.error(f"فشل في إنهاء الجلسة {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إنهاء الجلسة: {e}")
            return False
    
    def process_customer_payment(self, customer_data: Dict[str, Any], amount: Decimal,
                               cashier_id: int, invoice_id: int) -> bool:
        """معالجة الدفع من حساب العميل"""
        try:
            # استخدام نفس cursor المعاملة الرئيسية (بدون بدء معاملة جديدة)
            cursor = self.db.connection.cursor()
            
            # الحصول على الرصيد الحالي
            cursor.execute("SELECT balance FROM customers WHERE phone = ?", (customer_data['phone'],))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"العميل برقم الهاتف {customer_data['phone']} غير موجود")
                return False
            
            current_balance = result[0]
            new_balance = current_balance - float(amount)
            
            if new_balance < 0:
                logger.error(f"الرصيد غير كافي. الرصيد الحالي: {current_balance}, المبلغ المطلوب: {amount}")
                return False
            
            # تحديث الرصيد
            cursor.execute(
                "UPDATE customers SET balance = ? WHERE phone = ?",
                (new_balance, customer_data['phone'])
            )
            
            if cursor.rowcount > 0:
                # تسجيل المعاملة
                cursor.execute(
                    """INSERT INTO customer_transactions 
                       (customer_phone, operation, amount, old_balance, new_balance, 
                        cashier_id, notes, timestamp) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (customer_data['phone'], 'subtract', float(amount), 
                     current_balance, new_balance, cashier_id, 
                     f"دفع فاتورة رقم {invoice_id}", datetime.now())
                )
                
                logger.info(f"تم خصم {amount} جنيه من حساب العميل {customer_data['phone']}")
                logger.info(f"الرصيد الجديد: {new_balance} جنيه")
                return True
            else:
                logger.error(f"فشل في تحديث رصيد العميل {customer_data['phone']}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في معالجة الدفع من حساب العميل: {e}")
            import traceback
            logger.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
            return False
    
    def set_device_available(self, device_id: int) -> bool:
        """تحديث حالة الجهاز إلى متاح"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """UPDATE devices SET status = 'available', current_session_id = NULL 
                   WHERE id = ?""",
                (device_id,)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"تم تحديث حالة الجهاز {device_id} إلى متاح")
                return True
            else:
                logger.error(f"فشل في تحديث حالة الجهاز {device_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة الجهاز: {e}")
            return False
    
    def calculate_session_cost(self, session_id: int) -> Decimal:
        """حساب تكلفة الجلسة"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            cost_info = session_model.calculate_session_cost(session_id)
            
            if cost_info:
                return Decimal(str(cost_info['total_cost']))
            else:
                # استخدام السعر الافتراضي
                session = self.get_session_data(session_id)
                return Decimal(str(session.get('session_price', 0))) if session else Decimal('0.00')
                
        except Exception as e:
            logger.error(f"خطأ في حساب تكلفة الجلسة: {e}")
            return Decimal('0.00')
    
    def get_session_products_total(self, session_id: int) -> Decimal:
        """الحصول على إجمالي منتجات الجلسة"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            products_total = session_model.get_session_products_total(session_id)
            return Decimal(str(products_total))
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إجمالي منتجات الجلسة: {e}")
            return Decimal('0.00')
    
    def get_session_products(self, session_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات الجلسة"""
        try:
            from models.session_model import SessionModel
            session_model = SessionModel()
            return session_model.get_session_products(session_id)
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات الجلسة: {e}")
            return []
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على الفاتورة بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT i.*, d.name as device_name, 
                          u1.username as cashier_open_name,
                          u2.username as cashier_close_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN users u1 ON i.cashier_open = u1.id
                   LEFT JOIN users u2 ON i.cashier_close = u2.id
                   WHERE i.id = ?""",
                (invoice_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الفاتورة: {e}")
            return None
    
    def get_invoice_products(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات الفاتورة - ⭐ محدث للبحث في جميع الجداول"""
        try:
            # ⭐ أولاً: جلب معلومات الفاتورة للحصول على session_id
            invoice_info = self.db.execute_query(
                """SELECT session_id FROM invoices WHERE id = ?""",
                (invoice_id,)
            )
            
            session_id = None
            if invoice_info and invoice_info[0]:
                session_id = invoice_info[0].get('session_id')
            
            # ⭐ البحث في invoice_items أولاً (الأولوية للمنتجات المحفوظة مع الفاتورة)
            result = self.db.execute_query(
                """SELECT ii.*, p.name as product_name, p.category
                   FROM invoice_items ii
                   LEFT JOIN products p ON ii.product_id = p.id
                   WHERE ii.invoice_id = ?
                   ORDER BY ii.id""",
                (invoice_id,)
            )
            
            if result:
                return result
            
            # ⭐ إذا لم توجد منتجات في invoice_items وكانت الفاتورة مرتبطة بجلسة، ابحث في session_products
            if session_id:
                result = self.db.execute_query(
                    """SELECT sp.*, p.name as product_name, p.category
                       FROM session_products sp
                       LEFT JOIN products p ON sp.product_id = p.id
                       WHERE sp.session_id = ?
                       ORDER BY sp.id""",
                    (session_id,)
                )
                
                if result:
                    return result
            
            return []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات الفاتورة: {e}")
            return []
    
    def print_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """طباعة الفاتورة"""
        try:
            # الحصول على بيانات الفاتورة
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    'success': False,
                    'message': 'الفاتورة غير موجودة'
                }
            
            # الحصول على منتجات الفاتورة
            products = self.get_invoice_products(invoice_id)
            
            # إعداد بيانات الطباعة
            print_data = {
                'invoice': invoice,
                'products': products,
                'print_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"تم إعداد بيانات طباعة الفاتورة {invoice_id}")
            
            return {
                'success': True,
                'data': print_data
            }
            
        except Exception as e:
            logger.error(f"خطأ في طباعة الفاتورة: {e}")
            return {
                'success': False,
                'message': f'حدث خطأ في طباعة الفاتورة: {str(e)}'
            }
