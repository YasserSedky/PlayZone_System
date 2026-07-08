"""
موديل الفواتير
Invoice Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class InvoiceModel:
    """موديل إدارة الفواتير"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_invoice(self, device_id: int, cashier_id: int, shift_id: int, 
                      pricing_type: str, session_price: Decimal, 
                      customer_phone: str = None, paid_by: str = 'cash', 
                      session_id: int = None) -> Optional[int]:
        """إنشاء فاتورة جديدة"""
        try:
            invoice_data = {
                'device_id': device_id,
                'session_id': session_id,
                'cashier_open': cashier_id,
                'cashier_close': cashier_id,
                'shift_id': shift_id,
                'start_time': datetime.now(),
                'end_time': None,
                'pricing_type': pricing_type,
                'session_price': float(session_price),  # تحويل Decimal إلى float
                'products_total': 0.00,  # تحويل Decimal إلى float
                'total_amount': float(session_price),  # تحويل Decimal إلى float
                'customer_phone': customer_phone,
                'paid_by': paid_by,
                'created_by': cashier_id,
                'created_at': datetime.now()
            }
            
            invoice_id = self.db.execute_query(
                """INSERT INTO invoices 
                   (device_id, session_id, cashier_open, cashier_close, shift_id, start_time, 
                    pricing_type, session_price, products_total, total_amount, 
                    customer_phone, paid_by, created_by, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice_data['device_id'], invoice_data['session_id'], invoice_data['cashier_open'], 
                 invoice_data['cashier_close'], invoice_data['shift_id'], invoice_data['start_time'], 
                 invoice_data['pricing_type'], invoice_data['session_price'], invoice_data['products_total'], 
                 invoice_data['total_amount'], invoice_data['customer_phone'], invoice_data['paid_by'], 
                 invoice_data['created_by'], invoice_data['created_at']),
                fetch=False
            )
            
            logger.info(f"تم إنشاء فاتورة جديدة: {invoice_id}")
            return invoice_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الفاتورة: {e}")
            return None
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على فاتورة بالمعرف"""
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
    
    def get_invoice_session_products(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات الجلسة المرتبطة بالفاتورة"""
        try:
            # الحصول على session_id من الفاتورة
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice or not invoice.get('session_id'):
                return []
            
            # الحصول على منتجات الجلسة
            from models.session_model import SessionModel
            session_model = SessionModel()
            return session_model.get_session_products(invoice['session_id'])
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات جلسة الفاتورة: {e}")
            return []
    
    def get_invoice_pricing_details(self, invoice_id: int) -> Dict[str, Any]:
        """الحصول على تفاصيل التسعيرة المتقدمة للفاتورة"""
        try:
            # الحصول على الفاتورة
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice or not invoice.get('session_id'):
                # إرجاع نوع التسعيرة من الفاتورة مباشرة إذا لم توجد جلسة
                pricing_type_original = invoice.get('pricing_type', 'single') if invoice else 'single'
                return {
                    'has_advanced_pricing': False,
                    'pricing_type': pricing_type_original,
                    'pricing_type_original': pricing_type_original,  # ⭐ إضافة القيمة الأصلية
                    'session_price': invoice.get('session_price', 0) if invoice else 0
                }
            
            # الحصول على نوع التسعيرة الأصلي من الفاتورة
            pricing_type_original = invoice.get('pricing_type', 'single')
            
            # الحصول على تفاصيل التسعيرة المتقدمة من الجلسة
            from models.pricing_segment_model import PricingSegmentModel
            pricing_model = PricingSegmentModel()
            pricing_summary = pricing_model.get_session_pricing_summary(invoice['session_id'])
            
            if pricing_summary and (pricing_summary.get('total_single_cost', 0) > 0 or pricing_summary.get('total_multi_cost', 0) > 0):
                # يوجد تسعيرة متقدمة
                # ⭐ تحديد نوع التسعيرة بناءً على الأجزاء المستخدمة
                single_cost = pricing_summary.get('total_single_cost', 0)
                multi_cost = pricing_summary.get('total_multi_cost', 0)
                
                if single_cost > 0 and multi_cost > 0:
                    # تسعيرة مختلطة (تم استخدام كلا النوعين)
                    detected_pricing_type = 'mixed'
                elif single_cost > 0:
                    # فردي فقط
                    detected_pricing_type = 'single'
                elif multi_cost > 0:
                    # جماعي فقط
                    detected_pricing_type = 'multi'
                else:
                    detected_pricing_type = pricing_type_original
                
                return {
                    'has_advanced_pricing': True,
                    'pricing_type': detected_pricing_type,  # ⭐ النوع المكتشف من الأجزاء
                    'pricing_type_original': pricing_type_original,  # ⭐ القيمة الأصلية من الفاتورة
                    'pricing_summary': pricing_summary,
                    'single_cost': single_cost,
                    'multi_cost': multi_cost,
                    'single_hours': pricing_summary.get('total_single_hours', 0),
                    'multi_hours': pricing_summary.get('total_multi_hours', 0),
                    'total_cost': pricing_summary.get('total_cost', 0),
                    'total_hours': pricing_summary.get('total_hours', 0),
                    'single_segments': pricing_summary.get('single_segments', []),
                    'multi_segments': pricing_summary.get('multi_segments', [])
                }
            else:
                # لا يوجد تسعيرة متقدمة - استخدام البيانات التقليدية
                return {
                    'has_advanced_pricing': False,
                    'pricing_type': pricing_type_original,  # ⭐ النوع من الفاتورة
                    'pricing_type_original': pricing_type_original,  # ⭐ القيمة الأصلية
                    'session_price': invoice.get('session_price', 0),
                    'total_cost': invoice.get('session_price', 0)
                }
                
        except Exception as e:
            logger.error(f"خطأ في الحصول على تفاصيل التسعيرة للفاتورة: {e}")
            return {
                'has_advanced_pricing': False,
                'pricing_type': 'single',
                'session_price': 0,
                'total_cost': 0
            }
    
    def get_invoices_by_shift(self, shift_id: int) -> List[Dict[str, Any]]:
        """الحصول على فواتير الوردية مع تفاصيل التسعيرة المتقدمة"""
        try:
            result = self.db.execute_query(
                """SELECT i.*, d.name as device_name, 
                          u1.username as cashier_open_name,
                          u2.username as cashier_close_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN users u1 ON i.cashier_open = u1.id
                   LEFT JOIN users u2 ON i.cashier_close = u2.id
                   WHERE i.shift_id = ?
                   ORDER BY i.start_time DESC""",
                (shift_id,)
            )
            
            if not result:
                return []
            
            # إضافة تفاصيل التسعيرة المتقدمة لكل فاتورة
            enhanced_invoices = []
            for invoice in result:
                # الحصول على تفاصيل التسعيرة المتقدمة
                pricing_details = self.get_invoice_pricing_details(invoice['id'])
                invoice['pricing_details'] = pricing_details
                enhanced_invoices.append(invoice)
            
            return enhanced_invoices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على فواتير الوردية: {e}")
            return []
    
    def get_invoices_by_cashier(self, cashier_id: int, date_from: datetime = None, 
                               date_to: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على فواتير الكاشير"""
        try:
            query = """SELECT i.*, d.name as device_name, 
                             u1.username as cashier_open_name,
                             u2.username as cashier_close_name
                      FROM invoices i
                      LEFT JOIN devices d ON i.device_id = d.id
                      LEFT JOIN users u1 ON i.cashier_open = u1.id
                      LEFT JOIN users u2 ON i.cashier_close = u2.id
                      WHERE i.cashier_open = ?"""
            
            params = [cashier_id]
            
            if date_from:
                query += " AND i.start_time >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND i.start_time <= ?"
                params.append(date_to)
            
            query += " ORDER BY i.start_time DESC"
            
            result = self.db.execute_query(query, tuple(params))
            
            if not result:
                return []
            
            # إضافة تفاصيل التسعيرة المتقدمة لكل فاتورة
            enhanced_invoices = []
            for invoice in result:
                # الحصول على تفاصيل التسعيرة المتقدمة
                pricing_details = self.get_invoice_pricing_details(invoice['id'])
                invoice['pricing_details'] = pricing_details
                enhanced_invoices.append(invoice)
            
            return enhanced_invoices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على فواتير الكاشير: {e}")
            return []
    
    def get_invoices_by_date_range(self, date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]:
        """الحصول على الفواتير في فترة زمنية (تشمل معاملات العملاء)"""
        try:
            result = self.db.execute_query(
                """SELECT i.*, 
                          CASE 
                              WHEN i.device_id = 0 THEN 'إدارة العملاء - ' || COALESCE(i.customer_phone, 'غير محدد')
                              ELSE d.name 
                          END as device_name,
                          u1.username as cashier_open_name,
                          u2.username as cashier_close_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN users u1 ON i.cashier_open = u1.id
                   LEFT JOIN users u2 ON i.cashier_close = u2.id
                   WHERE DATE(i.start_time) >= DATE(?) AND DATE(i.start_time) <= DATE(?)
                   ORDER BY i.start_time DESC""",
                (date_from, date_to)
            )
            
            if not result:
                return []
            
            # إضافة تفاصيل التسعيرة المتقدمة لكل فاتورة
            enhanced_invoices = []
            for invoice in result:
                # الحصول على تفاصيل التسعيرة المتقدمة
                pricing_details = self.get_invoice_pricing_details(invoice['id'])
                invoice['pricing_details'] = pricing_details
                enhanced_invoices.append(invoice)
            
            return enhanced_invoices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الفواتير: {e}")
            return []
    
    def get_all_closed_invoices(self, date_from: datetime = None, date_to: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على جميع الفواتير المغلقة"""
        try:
            # بناء الاستعلام
            base_query = """SELECT i.*, 
                          CASE 
                              WHEN i.device_id = 0 THEN 'إدارة العملاء - ' || COALESCE(i.customer_phone, 'غير محدد')
                              ELSE d.name 
                          END as device_name,
                          u1.username as cashier_open_name,
                          u2.username as cashier_close_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN users u1 ON i.cashier_open = u1.id
                   LEFT JOIN users u2 ON i.cashier_close = u2.id
                   WHERE i.end_time IS NOT NULL"""
            
            params = []
            
            # إضافة فلاتر التاريخ إذا تم تحديدها
            if date_from:
                base_query += " AND DATE(i.start_time) >= DATE(?)"
                params.append(date_from)
            
            if date_to:
                base_query += " AND DATE(i.start_time) <= DATE(?)"
                params.append(date_to)
            
            base_query += " ORDER BY i.start_time DESC"
            
            result = self.db.execute_query(base_query, tuple(params))
            
            if not result:
                return []
            
            # إضافة تفاصيل التسعيرة المتقدمة لكل فاتورة
            enhanced_invoices = []
            for invoice in result:
                # الحصول على تفاصيل التسعيرة المتقدمة
                pricing_details = self.get_invoice_pricing_details(invoice['id'])
                invoice['pricing_details'] = pricing_details
                enhanced_invoices.append(invoice)
            
            return enhanced_invoices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الفواتير المغلقة: {e}")
            return []
    
    def close_invoice(self, invoice_id: int, cashier_close_id: int, 
                     products_total: Decimal = None) -> bool:
        """إغلاق الفاتورة"""
        try:
            # الحصول على الفاتورة
            invoice = self.get_invoice_by_id(invoice_id)
            if not invoice:
                logger.error(f"الفاتورة {invoice_id} غير موجودة")
                return False
            
            if invoice['end_time']:
                logger.warning(f"الفاتورة {invoice_id} مغلقة بالفعل")
                return False
            
            # ⭐ تحديد نوع التسعيرة الصحيح بناءً على الأجزاء المستخدمة
            final_pricing_type = invoice.get('pricing_type', 'single')  # القيمة الافتراضية
            
            if invoice.get('session_id'):
                try:
                    from models.pricing_segment_model import PricingSegmentModel
                    pricing_model = PricingSegmentModel()
                    pricing_summary = pricing_model.get_session_pricing_summary(invoice['session_id'])
                    
                    if pricing_summary:
                        has_single = pricing_summary.get('total_single_cost', 0) > 0
                        has_multi = pricing_summary.get('total_multi_cost', 0) > 0
                        
                        # تحديد نوع التسعيرة بناءً على ما تم استخدامه فعلياً
                        if has_single and has_multi:
                            final_pricing_type = 'mixed'  # استخدام "mixed" للتسعيرة المختلطة
                            logger.info(f"الفاتورة {invoice_id} استخدمت تسعيرة مختلطة (فردي + جماعي)")
                        elif has_single:
                            final_pricing_type = 'single'
                            logger.info(f"الفاتورة {invoice_id} استخدمت تسعيرة فردي فقط")
                        elif has_multi:
                            final_pricing_type = 'multi'
                            logger.info(f"الفاتورة {invoice_id} استخدمت تسعيرة جماعي فقط")
                except Exception as e:
                    logger.warning(f"خطأ في تحديد نوع التسعيرة النهائي: {e}")
            
            # حساب المبلغ الإجمالي
            total_amount = invoice['session_price']
            if products_total:
                total_amount += products_total
            
            # الحصول على الوردية النشطة الحالية (وردية الإغلاق)
            current_shift_id = invoice['shift_id']  # الاحتفاظ بالوردية الأصلية افتراضياً
            try:
                from models.shift_model import ShiftModel
                shift_model = ShiftModel()
                active_shift = shift_model.get_active_shared_shift()
                if active_shift:
                    current_shift_id = active_shift['id']
                    logger.info(f"حفظ الفاتورة {invoice_id} في وردية الإغلاق {current_shift_id} (كانت في وردية {invoice['shift_id']})")
                else:
                    logger.warning(f"لا توجد وردية نشطة، سيتم الاحتفاظ بالوردية الأصلية {invoice['shift_id']}")
            except Exception as e:
                logger.warning(f"لم يتم تحديث وردية الفاتورة: {e}")
            
            # إغلاق الفاتورة مع تحديث الوردية ونوع التسعيرة الصحيح
            result = self.db.execute_query(
                """UPDATE invoices 
                   SET end_time = ?, cashier_close = ?, products_total = ?, 
                       total_amount = ?, shift_id = ?, pricing_type = ?, modified_at = ?
                   WHERE id = ?""",
                (datetime.now(), cashier_close_id, float(products_total or Decimal('0.00')), 
                 float(total_amount), current_shift_id, final_pricing_type, datetime.now(), invoice_id),
                fetch=False
            )
            
            if result:
                logger.info(f"تم إغلاق الفاتورة {invoice_id} بنوع تسعيرة '{final_pricing_type}' وحفظها في وردية {current_shift_id}")
                return True
            else:
                logger.error(f"فشل في إغلاق الفاتورة {invoice_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إغلاق الفاتورة: {e}")
            return False
    
    def add_product_to_invoice(self, invoice_id: int, product_id: int, 
                              quantity: int, price: Decimal) -> bool:
        """إضافة منتج للفاتورة"""
        try:
            # إضافة المنتج للفاتورة
            result = self.db.execute_query(
                """INSERT INTO invoice_products (invoice_id, product_id, quantity, price)
                   VALUES (?, ?, ?, ?)""",
                (invoice_id, product_id, quantity, float(price)),  # تحويل Decimal إلى float
                fetch=False
            )
            
            if result:
                # تحديث إجمالي المنتجات في الفاتورة
                self.update_invoice_products_total(invoice_id)
                logger.info(f"تم إضافة منتج للفاتورة {invoice_id}")
                return True
            else:
                logger.error(f"فشل في إضافة منتج للفاتورة {invoice_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إضافة منتج للفاتورة: {e}")
            return False
    
    def update_invoice_products_total(self, invoice_id: int) -> bool:
        """تحديث إجمالي منتجات الفاتورة"""
        try:
            # حساب إجمالي المنتجات
            result = self.db.execute_query(
                """SELECT COALESCE(SUM(quantity * price), 0) as total
                   FROM invoice_products 
                   WHERE invoice_id = ?""",
                (invoice_id,)
            )
            
            products_total = result[0]['total'] if result else Decimal('0.00')
            
            # الحصول على سعر الجلسة
            invoice = self.get_invoice_by_id(invoice_id)
            session_price = invoice['session_price'] if invoice else Decimal('0.00')
            
            # تحديث المبلغ الإجمالي
            total_amount = session_price + products_total
            
            update_result = self.db.execute_query(
                """UPDATE invoices 
                   SET products_total = ?, total_amount = ?, modified_at = ?
                   WHERE id = ?""",
                (products_total, total_amount, datetime.now(), invoice_id),
                fetch=False
            )
            
            return update_result is not None
            
        except Exception as e:
            logger.error(f"خطأ في تحديث إجمالي منتجات الفاتورة: {e}")
            return False
    
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
    
    def delete_invoice(self, invoice_id: int, admin_password: str) -> bool:
        """حذف الفاتورة (يتطلب باسورد المدير)"""
        try:
            # التحقق من باسورد المدير
            from models.user_model import UserModel
            user_model = UserModel()
            if not user_model.verify_admin_password(admin_password):
                logger.error("باسورد المدير غير صحيح")
                return False
            
            # حذف منتجات الفاتورة
            self.db.execute_query(
                "DELETE FROM invoice_products WHERE invoice_id = ?",
                (invoice_id,),
                fetch=False
            )
            
            # حذف الفاتورة
            result = self.db.execute_query(
                "DELETE FROM invoices WHERE id = ?",
                (invoice_id,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف الفاتورة {invoice_id}")
                return True
            else:
                logger.error(f"فشل في حذف الفاتورة {invoice_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في حذف الفاتورة: {e}")
            return False
    
    def get_invoice_statistics(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """الحصول على إحصائيات الفواتير"""
        try:
            # إجمالي الفواتير والإيرادات
            total_result = self.db.execute_query(
                """SELECT COUNT(*) as total_invoices, 
                          COALESCE(SUM(total_amount), 0) as total_revenue
                   FROM invoices 
                   WHERE start_time >= ? AND start_time <= ?""",
                (date_from, date_to)
            )
            
            # فواتير حسب نوع التسعيرة
            pricing_result = self.db.execute_query(
                """SELECT pricing_type, COUNT(*) as count, 
                          COALESCE(SUM(total_amount), 0) as revenue
                   FROM invoices 
                   WHERE start_time >= ? AND start_time <= ?
                   GROUP BY pricing_type""",
                (date_from, date_to)
            )
            
            # فواتير حسب الكاشير
            cashier_result = self.db.execute_query(
                """SELECT u.username as cashier_name, COUNT(*) as count,
                          COALESCE(SUM(i.total_amount), 0) as revenue
                   FROM invoices i
                   LEFT JOIN users u ON i.cashier_open = u.id
                   WHERE i.start_time >= ? AND i.start_time <= ?
                   GROUP BY u.username""",
                (date_from, date_to)
            )
            
            # فواتير حسب الجهاز
            device_result = self.db.execute_query(
                """SELECT d.name as device_name, COUNT(*) as count,
                          COALESCE(SUM(i.total_amount), 0) as revenue
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   WHERE i.start_time >= ? AND i.start_time <= ?
                   GROUP BY d.name""",
                (date_from, date_to)
            )
            
            return {
                'total': total_result[0] if total_result else {'total_invoices': 0, 'total_revenue': 0},
                'by_pricing': pricing_result if pricing_result else [],
                'by_cashier': cashier_result if cashier_result else [],
                'by_device': device_result if device_result else []
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الفواتير: {e}")
            return {}
    
    def get_active_invoices(self) -> List[Dict[str, Any]]:
        """الحصول على الفواتير النشطة (غير المغلقة)"""
        try:
            result = self.db.execute_query(
                """SELECT i.*, d.name as device_name, c.name as customer_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN customers c ON i.customer_phone = c.phone
                   WHERE i.end_time IS NULL
                   ORDER BY i.start_time DESC""",
                ()
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الفواتير النشطة: {e}")
            return []
    
    def get_open_sessions_from_previous_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على الجلسات المفتوحة من الورديات السابقة"""
        try:
            # الحصول على الوردية النشطة الحالية
            from models.shift_model import ShiftModel
            shift_model = ShiftModel()
            active_shift = shift_model.get_active_shared_shift()
            
            if not active_shift:
                return []
            
            # البحث عن الجلسات المفتوحة من ورديات أخرى
            result = self.db.execute_query(
                """SELECT i.*, d.name as device_name, c.name as customer_name,
                          s.id as shift_id, s.shift_name, u.username as cashier_open_name
                   FROM invoices i
                   LEFT JOIN devices d ON i.device_id = d.id
                   LEFT JOIN customers c ON i.customer_phone = c.phone
                   LEFT JOIN shifts s ON i.shift_id = s.id
                   LEFT JOIN users u ON i.cashier_open = u.id
                   WHERE i.end_time IS NULL AND i.shift_id != ?
                   ORDER BY i.start_time DESC""",
                (active_shift['id'],)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسات المفتوحة من الورديات السابقة: {e}")
            return []