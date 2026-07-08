"""
موديل المنتجات
Product Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class ProductModel:
    """موديل إدارة المنتجات"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_product(self, name: str, price: Decimal, stock_quantity: int, 
                      category: str) -> Optional[int]:
        """إنشاء منتج جديد"""
        try:
            product_data = {
                'name': name,
                'price': float(price),  # تحويل Decimal إلى float لـ SQLite
                'stock_quantity': stock_quantity,
                'category': category
            }
            
            product_id = self.db.execute_query(
                """INSERT INTO products (name, price, stock_quantity, category) 
                   VALUES (?, ?, ?, ?)""",
                tuple(product_data.values()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء منتج جديد: {name}")
            return product_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء المنتج: {e}")
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على منتج بالمعرف"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM products WHERE id = ?",
                (product_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المنتج: {e}")
            return None
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المنتجات"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM products ORDER BY category, name"
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المنتجات: {e}")
            return []
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """الحصول على المنتجات حسب الفئة"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM products WHERE category = ? ORDER BY name",
                (category,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات الفئة: {e}")
            return []
    
    def get_available_products(self) -> List[Dict[str, Any]]:
        """الحصول على المنتجات المتاحة (المخزون > 0)"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM products WHERE stock_quantity > 0 ORDER BY category, name"
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المنتجات المتاحة: {e}")
            return []
    
    def update_product(self, product_id: int, name: str = None, price: Decimal = None,
                      stock_quantity: int = None, category: str = None, 
                      admin_password: str = None) -> bool:
        """تحديث المنتج (يتطلب باسورد المدير)"""
        try:
            # التحقق من باسورد المدير
            if admin_password:
                from models.user_model import UserModel
                user_model = UserModel()
                if not user_model.verify_admin_password(admin_password):
                    logger.error("باسورد المدير غير صحيح")
                    return False
            
            # بناء استعلام التحديث
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("name = ?")
                params.append(name)
            
            if price is not None:
                update_fields.append("price = ?")
                params.append(float(price))  # تحويل Decimal إلى float
            
            if stock_quantity is not None:
                update_fields.append("stock_quantity = ?")
                params.append(stock_quantity)
            
            if category is not None:
                update_fields.append("category = ?")
                params.append(category)
            
            if not update_fields:
                return False
            
            params.append(product_id)
            
            query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?"
            
            result = self.db.execute_query(query, tuple(params), fetch=False)
            
            if result:
                logger.info(f"تم تحديث المنتج {product_id}")
                return True
            else:
                logger.error(f"فشل في تحديث المنتج {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث المنتج: {e}")
            return False
    
    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        """تحديث المخزون"""
        try:
            # الحصول على المخزون الحالي
            product = self.get_product_by_id(product_id)
            if not product:
                logger.error(f"المنتج {product_id} غير موجود")
                return False
            
            new_stock = product['stock_quantity'] + quantity_change
            
            if new_stock < 0:
                logger.error(f"المخزون الجديد سالب: {new_stock}")
                return False
            
            result = self.db.execute_query(
                "UPDATE products SET stock_quantity = ? WHERE id = ?",
                (new_stock, product_id),
                fetch=False
            )
            
            if result:
                logger.info(f"تم تحديث مخزون المنتج {product_id}: {new_stock}")
                return True
            else:
                logger.error(f"فشل في تحديث مخزون المنتج {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث المخزون: {e}")
            return False
    
    def update_stock_with_password(self, product_id: int, quantity_change: int, 
                                  operation: str = "إضافة", admin_password: str = None) -> bool:
        """تحديث المخزون مع التحقق من كلمة مرور المدير"""
        try:
            # التحقق من باسورد المدير
            if admin_password:
                from models.user_model import UserModel
                user_model = UserModel()
                if not user_model.verify_admin_password(admin_password):
                    logger.error("باسورد المدير غير صحيح")
                    return False
            
            # الحصول على المخزون الحالي
            product = self.get_product_by_id(product_id)
            if not product:
                logger.error(f"المنتج {product_id} غير موجود")
                return False
            
            current_stock = product['stock_quantity']
            
            # حساب المخزون الجديد حسب نوع العملية
            if operation == "إضافة":
                new_stock = current_stock + quantity_change
            elif operation == "خصم":
                new_stock = max(0, current_stock - quantity_change)
            elif operation == "تعيين":
                new_stock = quantity_change
            else:
                logger.error(f"نوع عملية غير صحيح: {operation}")
                return False
            
            if new_stock < 0:
                logger.error(f"المخزون الجديد سالب: {new_stock}")
                return False
            
            result = self.db.execute_query(
                "UPDATE products SET stock_quantity = ? WHERE id = ?",
                (new_stock, product_id),
                fetch=False
            )
            
            if result:
                logger.info(f"تم تحديث مخزون المنتج {product_id}: {current_stock} -> {new_stock} ({operation})")
                return True
            else:
                logger.error(f"فشل في تحديث مخزون المنتج {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في تحديث المخزون: {e}")
            return False
    
    def delete_product(self, product_id: int, admin_password: str) -> bool:
        """حذف المنتج (يتطلب باسورد المدير)"""
        try:
            # التحقق من باسورد المدير
            from models.user_model import UserModel
            user_model = UserModel()
            if not user_model.verify_admin_password(admin_password):
                logger.error("باسورد المدير غير صحيح")
                return False
            
            # حذف المنتج
            result = self.db.execute_query(
                "DELETE FROM products WHERE id = ?",
                (product_id,),
                fetch=False
            )
            
            if result:
                logger.info(f"تم حذف المنتج {product_id}")
                return True
            else:
                logger.error(f"فشل في حذف المنتج {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في حذف المنتج: {e}")
            return False
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """الحصول على المنتجات ذات المخزون المنخفض"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM products WHERE stock_quantity <= ? ORDER BY stock_quantity",
                (threshold,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على المنتجات ذات المخزون المنخفض: {e}")
            return []
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المنتجات"""
        try:
            # إجمالي المنتجات
            total_result = self.db.execute_query(
                "SELECT COUNT(*) as total_products FROM products"
            )
            
            # المنتجات حسب الفئة
            category_result = self.db.execute_query(
                """SELECT category, COUNT(*) as count, 
                          COALESCE(SUM(stock_quantity), 0) as total_stock
                   FROM products 
                   GROUP BY category"""
            )
            
            # المنتجات ذات المخزون المنخفض
            low_stock_result = self.db.execute_query(
                "SELECT COUNT(*) as low_stock_count FROM products WHERE stock_quantity <= 10"
            )
            
            # إجمالي قيمة المخزون
            stock_value_result = self.db.execute_query(
                """SELECT COALESCE(SUM(price * stock_quantity), 0) as total_stock_value
                   FROM products"""
            )
            
            return {
                'total_products': total_result[0]['total_products'] if total_result else 0,
                'by_category': category_result if category_result else [],
                'low_stock_count': low_stock_result[0]['low_stock_count'] if low_stock_result else 0,
                'total_stock_value': stock_value_result[0]['total_stock_value'] if stock_value_result else 0
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المنتجات: {e}")
            return {}
    
    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في المنتجات"""
        try:
            result = self.db.execute_query(
                """SELECT * FROM products 
                   WHERE name LIKE ? OR category LIKE ?
                   ORDER BY category, name""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في البحث في المنتجات: {e}")
            return []