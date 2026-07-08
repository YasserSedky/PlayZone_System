"""
موديل العملاء
Customer Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class CustomerModel:
    """موديل إدارة العملاء"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_customer(self, phone: str, name: str, password: str, 
                       initial_balance: Decimal = Decimal('0.00'), cashier_id: int = None) -> bool:
        """إنشاء عميل جديد"""
        try:
            # التحقق من وجود وردية نشطة
            from utils.shift_validation import check_active_shift
            active_shift = check_active_shift()
            if not active_shift:
                logger.error("لا يمكن إنشاء عميل جديد بدون وردية نشطة")
                return False
            
            # التحقق من عدم وجود العميل
            existing_customer = self.get_customer_by_phone(phone)
            if existing_customer:
                logger.error(f"العميل برقم الهاتف {phone} موجود بالفعل")
                return False
            
            # تشفير كلمة المرور
            from utils.security import hash_password
            password_hash = hash_password(password)
            
            customer_data = {
                'phone': phone,
                'name': name,
                'password_hash': password_hash,
                'balance': float(initial_balance)  # تحويل Decimal إلى float
            }
            
            result = self.db.execute_query(
                """INSERT INTO customers (phone, name, password_hash, balance) 
                   VALUES (?, ?, ?, ?)""",
                tuple(customer_data.values()),
                fetch=False
            )
            
            if result:
                logger.info(f"تم إنشاء عميل جديد: {name} ({phone})")
                
                # إنشاء فاتورة للمعاملة إذا كان هناك رصيد ابتدائي
                if initial_balance > 0 and cashier_id:
                    self.create_customer_transaction_invoice(
                        transaction_type="new_customer",
                        customer_phone=phone,
                        amount=initial_balance,
                        cashier_id=cashier_id,
                        notes=f"رصيد ابتدائي للعميل الجديد {name}"
                    )
                
                return True
            else:
                logger.error(f"فشل في إنشاء العميل {phone}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء العميل: {e}")
            return False
    
    def update_customer(self, phone: str, new_name: str = None, new_password: str = None) -> bool:
        """تحديث معلومات العميل"""
        try:
            # التحقق من وجود العميل
            existing_customer = self.get_customer_by_phone(phone)
            if not existing_customer:
                logger.error(f"العميل برقم الهاتف {phone} غير موجود")
                return False
            
            # بناء استعلام التحديث
            update_fields = []
            update_values = []
            
            if new_name:
                update_fields.append("name = ?")
                update_values.append(new_name)
            
            if new_password:
                from utils.security import hash_password
                password_hash = hash_password(new_password)
                update_fields.append("password_hash = ?")
                update_values.append(password_hash)
            
            if not update_fields:
                logger.warning("لا توجد بيانات للتحديث")
                return True
            
            # إضافة timestamp
            update_fields.append("updated_at = ?")
            update_values.append(datetime.now())
            
            # إضافة phone للقيم
            update_values.append(phone)
            
            query = f"UPDATE customers SET {', '.join(update_fields)} WHERE phone = ?"
            
            result = self.db.execute_query(query, tuple(update_values), fetch=False)
            
            if result:
                logger.info(f"تم تحديث معلومات العميل {phone}")
                return True
            else:
                logger.error(f"فشل في تحديث معلومات العميل {phone}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث العميل: {e}")
            return False
    
    def delete_customer(self, phone: str) -> bool:
        """حذف العميل"""
        try:
            # التحقق من وجود العميل
            existing_customer = self.get_customer_by_phone(phone)
            if not existing_customer:
                logger.error(f"العميل برقم الهاتف {phone} غير موجود")
                return False
            
            # حذف المعاملات أولاً (بسبب foreign key constraint)
            self.db.execute_query(
                "DELETE FROM customer_transactions WHERE customer_phone = ?",
                (phone,),
                fetch=False
            )
            
            # حذف العميل
            result = self.db.execute_query(
                "DELETE FROM customers WHERE phone = ?",
                (phone,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف العميل {phone} وجميع معاملاته")
                return True
            else:
                logger.error(f"فشل في حذف العميل {phone}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في حذف العميل: {e}")
            return False
    
    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """الحصول على عميل برقم الهاتف"""
        try:
            logger.info(f"البحث عن العميل برقم الهاتف: {phone}")
            result = self.db.execute_query(
                "SELECT * FROM customers WHERE phone = ?",
                (phone,)
            )
            if result:
                customer = result[0]
                logger.info(f"تم العثور على العميل: {customer['name']} - الرصيد: {customer['balance']}")
                return customer
            else:
                logger.warning(f"لم يتم العثور على العميل برقم الهاتف: {phone}")
                return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على العميل: {e}")
            return None
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """الحصول على جميع العملاء"""
        try:
            logger.info("جاري تحميل جميع العملاء من قاعدة البيانات")
            result = self.db.execute_query(
                "SELECT * FROM customers ORDER BY name"
            )
            if result:
                logger.info(f"تم تحميل {len(result)} عميل من قاعدة البيانات")
                for customer in result:
                    logger.info(f"العميل: {customer['name']} - الرصيد: {customer['balance']}")
                return result
            else:
                logger.warning("لم يتم العثور على أي عملاء في قاعدة البيانات")
                return []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على العملاء: {e}")
            return []
    
    def authenticate_customer(self, phone: str, password: str) -> Optional[Dict[str, Any]]:
        """التحقق من هوية العميل"""
        try:
            customer = self.get_customer_by_phone(phone)
            if not customer:
                logger.error(f"العميل برقم الهاتف {phone} غير موجود")
                return None
            
            # التحقق من كلمة المرور
            from utils.security import verify_password
            if not verify_password(password, customer['password_hash']):
                logger.error(f"كلمة المرور غير صحيحة للعميل {phone}")
                return None
            
            logger.info(f"تم التحقق من هوية العميل {phone}")
            return customer
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من هوية العميل: {e}")
            return None
    
    def update_customer_balance(self, phone: str, amount: Decimal, 
                               operation: str, cashier_id: int, 
                               notes: str = "") -> bool:
        """تحديث رصيد العميل"""
        try:
            # التحقق من وجود وردية نشطة
            from utils.shift_validation import check_active_shift
            active_shift = check_active_shift()
            if not active_shift:
                logger.error("لا يمكن تحديث رصيد العميل بدون وردية نشطة")
                return False
            
            logger.info(f"بدء تحديث رصيد العميل {phone} - العملية: {operation} - المبلغ: {amount}")
            
            customer = self.get_customer_by_phone(phone)
            if not customer:
                logger.error(f"العميل برقم الهاتف {phone} غير موجود")
                return False
            
            current_balance = customer['balance']
            logger.info(f"الرصيد الحالي للعميل {phone}: {current_balance}")
            
            if operation == 'add':
                new_balance = current_balance + amount
            elif operation == 'subtract':
                new_balance = current_balance - amount
                if new_balance < 0:
                    logger.error(f"الرصيد الجديد سالب: {new_balance}")
                    return False
            else:
                logger.error(f"عملية غير صحيحة: {operation}")
                return False
            
            logger.info(f"الرصيد الجديد للعميل {phone}: {new_balance}")
            
            # تحديث الرصيد باستخدام DatabaseManager
            result = self.db.execute_query(
                "UPDATE customers SET balance = ? WHERE phone = ?",
                (float(new_balance), phone),  # تحويل Decimal إلى float
                fetch=False
            )
            
            logger.info(f"نتيجة تحديث الرصيد: {result}")
            
            # التحقق من نجاح التحديث
            if result:
                # تسجيل العملية في سجل المعاملات
                self.log_balance_transaction(phone, operation, amount, 
                                           current_balance, new_balance, 
                                           cashier_id, notes)
                
                # إنشاء فاتورة للمعاملة إذا كانت عملية إضافة رصيد
                if operation == 'add':
                    self.create_customer_transaction_invoice(
                        transaction_type="balance_charge",
                        customer_phone=phone,
                        amount=amount,
                        cashier_id=cashier_id,
                        notes=notes or f"شحن رصيد العميل"
                    )
                
                logger.info(f"تم تحديث رصيد العميل {phone}: {new_balance}")
                return True
            else:
                logger.error(f"فشل في تحديث رصيد العميل {phone}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث رصيد العميل: {e}")
            return False
    
    def log_balance_transaction(self, phone: str, operation: str, amount: Decimal,
                               old_balance: Decimal, new_balance: Decimal,
                               cashier_id: int, notes: str = ""):
        """تسجيل معاملة الرصيد"""
        try:
            transaction_data = {
                'customer_phone': phone,
                'operation': operation,
                'amount': amount,
                'old_balance': old_balance,
                'new_balance': new_balance,
                'cashier_id': cashier_id,
                'notes': notes,
                'timestamp': datetime.now()
            }
            
            # تحويل Decimal إلى float
            transaction_values = [
                transaction_data['customer_phone'],
                transaction_data['operation'],
                float(transaction_data['amount']),
                float(transaction_data['old_balance']),
                float(transaction_data['new_balance']),
                transaction_data['cashier_id'],
                transaction_data['notes'],
                transaction_data['timestamp']
            ]
            
            result = self.db.execute_query(
                """INSERT INTO customer_transactions 
                   (customer_phone, operation, amount, old_balance, new_balance, 
                    cashier_id, notes, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                tuple(transaction_values),
                fetch=False
            )
            
            if result:
                logger.info(f"تم تسجيل معاملة الرصيد للعميل {phone}")
            else:
                logger.error(f"فشل في تسجيل معاملة الرصيد للعميل {phone}")
                
        except Exception as e:
            logger.error(f"خطأ في تسجيل معاملة الرصيد: {e}")
    
    def create_customer_transaction_invoice(self, transaction_type: str, customer_phone: str, 
                                          amount: Decimal, cashier_id: int, 
                                          notes: str = "") -> Optional[int]:
        """إنشاء فاتورة لمعاملة العميل"""
        try:
            from models.customer_transaction_invoice_model import CustomerTransactionInvoiceModel
            transaction_invoice_model = CustomerTransactionInvoiceModel()
            
            return transaction_invoice_model.create_customer_transaction_invoice(
                transaction_type=transaction_type,
                customer_phone=customer_phone,
                amount=amount,
                cashier_id=cashier_id,
                notes=notes
            )
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء فاتورة معاملة العميل: {e}")
            return None
    
    def get_customer_transactions(self, phone: str, limit: int = 50) -> List[Dict[str, Any]]:
        """الحصول على معاملات العميل"""
        try:
            result = self.db.execute_query(
                """SELECT ct.*, u.username as cashier_name
                   FROM customer_transactions ct
                   LEFT JOIN users u ON ct.cashier_id = u.id
                   WHERE ct.customer_phone = ?
                   ORDER BY ct.timestamp DESC
                   LIMIT ?""",
                (phone, limit)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معاملات العميل: {e}")
            return []
    
    def update_customer_info(self, phone: str, name: str = None, 
                           new_password: str = None) -> bool:
        """تحديث معلومات العميل"""
        try:
            # بناء استعلام التحديث
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("name = ?")
                params.append(name)
            
            if new_password is not None:
                from utils.security import hash_password
                password_hash = hash_password(new_password)
                update_fields.append("password_hash = ?")
                params.append(password_hash)
            
            if not update_fields:
                return False
            
            params.append(phone)
            
            query = f"UPDATE customers SET {', '.join(update_fields)} WHERE phone = ?"
            
            result = self.db.execute_query(query, tuple(params), fetch=False)
            
            if result:
                logger.info(f"تم تحديث معلومات العميل {phone}")
                return True
            else:
                logger.error(f"فشل في تحديث معلومات العميل {phone}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث معلومات العميل: {e}")
            return False
    
    
    def get_customer_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات العملاء"""
        try:
            # إجمالي العملاء
            total_result = self.db.execute_query(
                "SELECT COUNT(*) as total_customers FROM customers"
            )
            
            # إجمالي الرصيد
            balance_result = self.db.execute_query(
                "SELECT COALESCE(SUM(balance), 0) as total_balance FROM customers"
            )
            
            # العملاء ذوو الرصيد العالي
            high_balance_result = self.db.execute_query(
                "SELECT COUNT(*) as high_balance_count FROM customers WHERE balance > 100"
            )
            
            # العملاء ذوو الرصيد المنخفض
            low_balance_result = self.db.execute_query(
                "SELECT COUNT(*) as low_balance_count FROM customers WHERE balance < 10"
            )
            
            return {
                'total_customers': total_result[0]['total_customers'] if total_result else 0,
                'total_balance': balance_result[0]['total_balance'] if balance_result else 0,
                'high_balance_count': high_balance_result[0]['high_balance_count'] if high_balance_result else 0,
                'low_balance_count': low_balance_result[0]['low_balance_count'] if low_balance_result else 0
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات العملاء: {e}")
            return {}
    
    def search_customers(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في العملاء"""
        try:
            result = self.db.execute_query(
                """SELECT * FROM customers 
                   WHERE name LIKE ? OR phone LIKE ?
                   ORDER BY name""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في العملاء: {e}")
            return []