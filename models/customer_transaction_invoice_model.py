"""
موديل فواتير معاملات العملاء
Customer Transaction Invoice Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class CustomerTransactionInvoiceModel:
    """موديل فواتير معاملات العملاء"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_customer_transaction_invoice(self, transaction_type: str, customer_phone: str, 
                                          amount: Decimal, cashier_id: int, 
                                          notes: str = "") -> Optional[int]:
        """إنشاء فاتورة لمعاملة العميل"""
        try:
            # الحصول على معلومات العميل
            from models.customer_model import CustomerModel
            customer_model = CustomerModel()
            customer = customer_model.get_customer_by_phone(customer_phone)
            
            if not customer:
                logger.error(f"العميل برقم الهاتف {customer_phone} غير موجود")
                return None
            
            # تحديد نوع المعاملة والنص
            if transaction_type == "new_customer":
                transaction_text = "إنشاء عميل جديد"
                device_name = f"خدمة عملاء - {customer_phone}"
                device_id = 0  # معرف خاص للعمليات الإدارية
            elif transaction_type == "balance_charge":
                transaction_text = "شحن رصيد العميل"
                device_name = f"خدمة عملاء - {customer_phone}"
                device_id = 0
            else:
                logger.error(f"نوع معاملة غير صحيح: {transaction_type}")
                return None
            
            # الحصول على الوردية النشطة المشتركة
            from models.shift_model import ShiftModel
            shift_model = ShiftModel()
            active_shift = shift_model.get_active_shared_shift()
            
            if not active_shift:
                logger.warning(f"لا توجد وردية نشطة مشتركة، سيتم إنشاء وردية مؤقتة")
                # إنشاء وردية مؤقتة
                shift_id = shift_model.create_shift(
                    cashier_id=cashier_id,
                    shift_name="وردية مؤقتة - إدارة العملاء",
                    notes="وردية مؤقتة لمعاملة العميل"
                )
                if not shift_id:
                    logger.error("فشل في إنشاء وردية مؤقتة")
                    return None
            else:
                shift_id = active_shift['id']
            
            # بيانات الفاتورة
            invoice_data = {
                'device_id': device_id,
                'cashier_open': cashier_id,
                'cashier_close': cashier_id,
                'shift_id': shift_id,
                'start_time': datetime.now(),
                'end_time': datetime.now(),
                'pricing_type': 'admin',
                'session_price': 0.00,  # تحويل Decimal إلى float
                'products_total': 0.00,  # تحويل Decimal إلى float
                'total_amount': float(amount),  # تحويل Decimal إلى float
                'customer_phone': customer_phone,
                'paid_by': 'cash',  # طريقة الدفع نقداً
                'created_by': cashier_id,
                'created_at': datetime.now()
            }
            
            # إنشاء الفاتورة باستخدام DatabaseManager
            invoice_id = self.db.execute_query(
                """INSERT INTO invoices 
                   (device_id, session_id, cashier_open, cashier_close, shift_id, start_time, end_time,
                    pricing_type, session_price, products_total, total_amount, 
                    customer_phone, paid_by, created_by, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice_data['device_id'], None, invoice_data['cashier_open'], 
                 invoice_data['cashier_close'], invoice_data['shift_id'], invoice_data['start_time'], 
                 invoice_data['end_time'], invoice_data['pricing_type'], invoice_data['session_price'], 
                 invoice_data['products_total'], invoice_data['total_amount'], invoice_data['customer_phone'], 
                 invoice_data['paid_by'], invoice_data['created_by'], invoice_data['created_at']),
                fetch=False
            )
            
            if invoice_id:
                logger.info(f"تم إنشاء فاتورة معاملة العميل {invoice_id}: {transaction_text}")
                
                # إضافة منتج افتراضي للمعاملة
                product_name = f"{transaction_text} - {customer['name']} ({customer_phone})"
                if notes:
                    product_name += f" - {notes}"
                self.add_transaction_product(invoice_id, product_name, amount)
                
                # إشعار واجهة الفواتير بتحديث البيانات
                self.notify_invoice_refresh()
                
                return invoice_id
            else:
                logger.error(f"فشل في إنشاء فاتورة معاملة العميل")
                return None
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء فاتورة معاملة العميل: {e}")
            return None
    
    def add_transaction_product(self, invoice_id: int, product_name: str, amount: Decimal):
        """إضافة منتج افتراضي للمعاملة"""
        try:
            # التحقق من وجود جدول invoice_items
            table_check = self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_items'")
            if not table_check:
                logger.warning("جدول invoice_items غير موجود، سيتم تخطي إضافة المنتج")
                return
            
            # محاولة إضافة المنتج
            try:
                result = self.db.execute_query(
                    """INSERT INTO invoice_items 
                       (invoice_id, product_id, product_name, quantity, unit_price, total_price) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (invoice_id, 0, product_name, 1, float(amount), float(amount)),
                    fetch=False
                )
                
                if result:
                    logger.info(f"تم إضافة منتج المعاملة للفاتورة {invoice_id}")
                else:
                    logger.error(f"فشل في إضافة منتج المعاملة للفاتورة {invoice_id}")
                    
            except Exception as e:
                # إذا فشل، جرب بدون product_name
                logger.warning(f"فشل في إضافة المنتج مع product_name، جاري المحاولة بدونها: {e}")
                result = self.db.execute_query(
                    """INSERT INTO invoice_items 
                       (invoice_id, product_id, quantity, unit_price, total_price) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (invoice_id, 0, 1, float(amount), float(amount)),
                    fetch=False
                )
                
                if result:
                    logger.info(f"تم إضافة منتج المعاملة للفاتورة {invoice_id} (بدون اسم المنتج)")
                else:
                    logger.error(f"فشل في إضافة منتج المعاملة للفاتورة {invoice_id}")
                
        except Exception as e:
            logger.error(f"خطأ في إضافة منتج المعاملة: {e}")
    
    def notify_invoice_refresh(self):
        """إشعار واجهة الفواتير بتحديث البيانات"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم العثور على نافذة إدارة الفواتير وتحديثها")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في تحديث واجهة الفواتير: {e}")
    
    def get_customer_transaction_invoices(self, date_from: datetime = None, 
                                        date_to: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على فواتير معاملات العملاء"""
        try:
            if not date_from:
                date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not date_to:
                date_to = datetime.now()
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                """SELECT 
                    i.id,
                    i.device_id,
                    i.session_price,
                    i.products_total,
                    i.total_amount,
                    i.paid_by,
                    i.start_time,
                    i.end_time,
                    i.pricing_type,
                    i.customer_phone,
                    u.username as cashier_name,
                    c.name as customer_name
                FROM invoices i
                LEFT JOIN users u ON i.cashier_open = u.id
                LEFT JOIN customers c ON i.customer_phone = c.phone
                WHERE i.pricing_type = 'admin' 
                AND i.start_time >= ? 
                AND i.start_time <= ?
                ORDER BY i.start_time DESC""",
                (date_from, date_to)
            )
            
            invoices = []
            for row in cursor.fetchall():
                invoice = {
                    'id': row[0],
                    'device_id': row[1],
                    'session_price': row[2],
                    'products_total': row[3],
                    'total_amount': row[4],
                    'paid_by': row[5],
                    'start_time': row[6],
                    'end_time': row[7],
                    'pricing_type': row[8],
                    'customer_phone': row[9],
                    'cashier_name': row[10],
                    'customer_name': row[11],
                    'device_name': f'إدارة العملاء - {row[9]}'  # إضافة رقم الهاتف
                }
                invoices.append(invoice)
            
            return invoices
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على فواتير معاملات العملاء: {e}")
            return []
    
    def get_transaction_invoice_products(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات فاتورة المعاملة"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """SELECT 
                    product_name,
                    quantity,
                    unit_price,
                    total_price
                FROM invoice_items 
                WHERE invoice_id = ?""",
                (invoice_id,)
            )
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'name': row[0],
                    'quantity': row[1],
                    'unit_price': row[2],
                    'total_price': row[3]
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات فاتورة المعاملة: {e}")
            return []
