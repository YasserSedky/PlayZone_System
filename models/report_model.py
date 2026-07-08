"""
موديل التقارير الشامل
Comprehensive Reports Model
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class ReportModel:
    """موديل إدارة التقارير الشامل"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    # ============ تقارير الإيرادات ============
    
    def get_revenue_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير ملخص الإيرادات"""
        try:
            # إجمالي الإيرادات
            revenue_result = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_invoice_value,
                    COALESCE(SUM(session_price), 0) as session_revenue,
                    COALESCE(SUM(products_total), 0) as products_revenue
                FROM invoices 
                WHERE DATE(start_time) BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            
            revenue_data = revenue_result[0] if revenue_result else {}
            
            # إيرادات حسب نوع السعر
            pricing_result = self.db.execute_query(
                """SELECT 
                    pricing_type,
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0) as revenue
                FROM invoices 
                WHERE DATE(start_time) BETWEEN ? AND ?
                GROUP BY pricing_type""",
                (start_date, end_date)
            )
            
            # إيرادات يومية
            daily_revenue = self.get_daily_revenue(start_date, end_date)
            
            # إيرادات حسب طريقة الدفع
            payment_methods = self.db.execute_query(
                """SELECT 
                    paid_by,
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0) as revenue
                FROM invoices 
                WHERE DATE(start_time) BETWEEN ? AND ?
                GROUP BY paid_by""",
                (start_date, end_date)
            )
            
            return {
                'summary': revenue_data,
                'pricing_breakdown': pricing_result or [],
                'daily_revenue': daily_revenue,
                'payment_methods': payment_methods or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في تقرير ملخص الإيرادات: {e}")
            return {}
    
    def get_daily_revenue(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الإيرادات اليومية"""
        try:
            result = self.db.execute_query(
                """SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_invoice_value
                FROM invoices 
                WHERE DATE(start_time) BETWEEN ? AND ?
                GROUP BY DATE(start_time)
                ORDER BY date""",
                (start_date, end_date)
            )
            return result or []
        except Exception as e:
            logger.error(f"خطأ في الإيرادات اليومية: {e}")
            return []
    
    def get_profit_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """بيانات الأرباح (الإيرادات - المصروفات)"""
        try:
            # الحصول على الإيرادات
            revenue_result = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_invoice_value
                FROM invoices 
                WHERE DATE(start_time) BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            
            revenue_data = revenue_result[0] if revenue_result else {
                'total_invoices': 0,
                'total_revenue': 0,
                'avg_invoice_value': 0
            }
            
            # الحصول على المصروفات
            expense_result = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_expenses,
                    COALESCE(SUM(amount), 0) as total_expense_amount,
                    COALESCE(AVG(amount), 0) as avg_expense_amount
                FROM expenses 
                WHERE DATE(date_time) BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            
            expense_data = expense_result[0] if expense_result else {
                'total_expenses': 0,
                'total_expense_amount': 0,
                'avg_expense_amount': 0
            }
            
            # حساب صافي الربح
            total_revenue = revenue_data.get('total_revenue', 0)
            total_expenses = expense_data.get('total_expense_amount', 0)
            net_profit = total_revenue - total_expenses
            
            # الحصول على تفاصيل الإيرادات اليومية
            daily_revenue = self.get_daily_revenue(start_date, end_date)
            
            # الحصول على تفاصيل المصروفات اليومية
            daily_expenses = self.get_daily_expenses(start_date, end_date)
            
            return {
                'summary': {
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'net_profit': net_profit,
                    'total_invoices': revenue_data.get('total_invoices', 0),
                    'total_expense_count': expense_data.get('total_expenses', 0),
                    'avg_invoice_value': revenue_data.get('avg_invoice_value', 0),
                    'avg_expense_amount': expense_data.get('avg_expense_amount', 0)
                },
                'daily_revenue': daily_revenue,
                'daily_expenses': daily_expenses
            }
            
        except Exception as e:
            logger.error(f"خطأ في بيانات الأرباح: {e}")
            return {}
    
    def get_daily_expenses(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """المصروفات اليومية"""
        try:
            result = self.db.execute_query(
                """SELECT 
                    DATE(date_time) as date,
                    COUNT(*) as expense_count,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(AVG(amount), 0) as avg_amount
                FROM expenses 
                WHERE DATE(date_time) BETWEEN ? AND ?
                GROUP BY DATE(date_time)
                ORDER BY date""",
                (start_date, end_date)
            )
            return result or []
        except Exception as e:
            logger.error(f"خطأ في المصروفات اليومية: {e}")
            return []
    
    def get_hourly_revenue(self, target_date: date) -> List[Dict[str, Any]]:
        """الإيرادات الساعية ليوم محدد"""
        try:
            result = self.db.execute_query(
                """SELECT 
                    strftime('%H', start_time) as hour,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue
                FROM invoices 
                WHERE DATE(start_time) = ?
                GROUP BY strftime('%H', start_time)
                ORDER BY hour""",
                (target_date,)
            )
            return result or []
        except Exception as e:
            logger.error(f"خطأ في الإيرادات الساعية: {e}")
            return []
    
    # ============ تقارير الأجهزة ============
    
    def get_device_performance(self, start_date: date, end_date: date, device_type: str = None) -> List[Dict[str, Any]]:
        """أداء الأجهزة"""
        try:
            query = """SELECT 
                d.id,
                d.name,
                d.type,
                COUNT(i.id) as session_count,
                COALESCE(SUM(i.total_amount), 0) as total_revenue,
                COALESCE(AVG(i.total_amount), 0) as avg_revenue_per_session,
                COALESCE(SUM(i.session_price), 0) as session_revenue,
                COALESCE(SUM(i.products_total), 0) as products_revenue,
                COALESCE(AVG(julianday(i.end_time) - julianday(i.start_time)) * 24 * 60, 0) as avg_session_minutes
            FROM devices d
            LEFT JOIN invoices i ON d.id = i.device_id 
                AND DATE(i.start_time) BETWEEN ? AND ?
            WHERE 1=1"""
            
            params = [start_date, end_date]
            
            if device_type:
                query += " AND d.type = ?"
                params.append(device_type)
            
            query += " GROUP BY d.id, d.name, d.type ORDER BY total_revenue DESC"
            
            result = self.db.execute_query(query, tuple(params))
            return result or []
            
        except Exception as e:
            logger.error(f"خطأ في أداء الأجهزة: {e}")
            return []
    
    def get_device_utilization(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """استخدام الأجهزة"""
        try:
            # إحصائيات الاستخدام
            usage_stats = self.db.execute_query(
                """SELECT 
                    d.type,
                    COUNT(DISTINCT d.id) as total_devices,
                    COUNT(DISTINCT CASE WHEN i.id IS NOT NULL THEN d.id END) as used_devices,
                    COUNT(i.id) as total_sessions,
                    COALESCE(SUM(i.total_amount), 0) as total_revenue
                FROM devices d
                LEFT JOIN invoices i ON d.id = i.device_id 
                    AND DATE(i.start_time) BETWEEN ? AND ?
                GROUP BY d.type""",
                (start_date, end_date)
            )
            
            # أكثر الأجهزة استخداماً
            most_used = self.db.execute_query(
                """SELECT 
                    d.name,
                    d.type,
                    COUNT(i.id) as session_count,
                    COALESCE(SUM(i.total_amount), 0) as revenue
                FROM devices d
                LEFT JOIN invoices i ON d.id = i.device_id 
                    AND DATE(i.start_time) BETWEEN ? AND ?
                GROUP BY d.id, d.name, d.type
                ORDER BY session_count DESC
                LIMIT 10""",
                (start_date, end_date)
            )
            
            return {
                'usage_by_type': usage_stats or [],
                'most_used_devices': most_used or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في استخدام الأجهزة: {e}")
            return {}
    
    # ============ تقارير المنتجات ============
    
    def get_product_sales(self, start_date: date, end_date: date, category: str = None) -> List[Dict[str, Any]]:
        """مبيعات المنتجات - يجمع البيانات من session_products و invoice_items"""
        try:
            # استعلام يجمع البيانات من كلا المصدرين
            query = """SELECT 
                p.id,
                p.name,
                p.category,
                p.price,
                COALESCE(
                    (SELECT SUM(sp.quantity) FROM session_products sp 
                     LEFT JOIN sessions s ON sp.session_id = s.id 
                     WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                ) + COALESCE(
                    (SELECT SUM(ii.quantity) FROM invoice_items ii 
                     LEFT JOIN invoices i ON ii.invoice_id = i.id 
                     WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                ) as total_sold,
                COALESCE(
                    (SELECT SUM(sp.total_price) FROM session_products sp 
                     LEFT JOIN sessions s ON sp.session_id = s.id 
                     WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                ) + COALESCE(
                    (SELECT SUM(ii.total_price) FROM invoice_items ii 
                     LEFT JOIN invoices i ON ii.invoice_id = i.id 
                     WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                ) as total_revenue,
                COALESCE(
                    (SELECT AVG(sp.unit_price) FROM session_products sp 
                     LEFT JOIN sessions s ON sp.session_id = s.id 
                     WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                ) as avg_selling_price
            FROM products p
            WHERE 1=1"""
            
            params = [start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date]
            
            if category:
                query += " AND p.category = ?"
                params.append(category)
            
            query += " ORDER BY total_revenue DESC"
            
            result = self.db.execute_query(query, tuple(params))
            
            # تحويل النتائج إلى التنسيق المطلوب
            formatted_result = []
            for item in result or []:
                formatted_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'category': item['category'],
                    'price': item['price'],
                    'quantity_sold': item['total_sold'],
                    'revenue': item['total_revenue'],
                    'avg_selling_price': item['avg_selling_price']
                }
                formatted_result.append(formatted_item)
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"خطأ في مبيعات المنتجات: {e}")
            return []
    
    def get_product_performance(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """أداء المنتجات - يجمع البيانات من session_products و invoice_items"""
        try:
            # أفضل المنتجات مبيعاً - يجمع البيانات من كلا المصدرين
            best_selling = self.db.execute_query(
                """SELECT 
                    p.name,
                    p.category,
                    COALESCE(
                        (SELECT SUM(sp.quantity) FROM session_products sp 
                         LEFT JOIN sessions s ON sp.session_id = s.id 
                         WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                    ) + COALESCE(
                        (SELECT SUM(ii.quantity) FROM invoice_items ii 
                         LEFT JOIN invoices i ON ii.invoice_id = i.id 
                         WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                    ) as total_sold,
                    COALESCE(
                        (SELECT SUM(sp.total_price) FROM session_products sp 
                         LEFT JOIN sessions s ON sp.session_id = s.id 
                         WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                    ) + COALESCE(
                        (SELECT SUM(ii.total_price) FROM invoice_items ii 
                         LEFT JOIN invoices i ON ii.invoice_id = i.id 
                         WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                    ) as total_revenue
                FROM products p
                ORDER BY total_sold DESC
                LIMIT 10""",
                (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date)
            )
            
            # إحصائيات حسب الفئة - يجمع البيانات من كلا المصدرين
            category_stats = self.db.execute_query(
                """SELECT 
                    p.category,
                    COUNT(DISTINCT p.id) as product_count,
                    COALESCE(
                        (SELECT SUM(sp.quantity) FROM session_products sp 
                         LEFT JOIN sessions s ON sp.session_id = s.id 
                         WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                    ) + COALESCE(
                        (SELECT SUM(ii.quantity) FROM invoice_items ii 
                         LEFT JOIN invoices i ON ii.invoice_id = i.id 
                         WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                    ) as total_sold,
                    COALESCE(
                        (SELECT SUM(sp.total_price) FROM session_products sp 
                         LEFT JOIN sessions s ON sp.session_id = s.id 
                         WHERE sp.product_id = p.id AND DATE(s.start_time) BETWEEN ? AND ?), 0
                    ) + COALESCE(
                        (SELECT SUM(ii.total_price) FROM invoice_items ii 
                         LEFT JOIN invoices i ON ii.invoice_id = i.id 
                         WHERE ii.product_id = p.id AND DATE(i.start_time) BETWEEN ? AND ?), 0
                    ) as total_revenue
                FROM products p
                GROUP BY p.category
                ORDER BY total_revenue DESC""",
                (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date)
            )
            
            # حالة المخزون
            stock_status = self.db.execute_query(
                """SELECT 
                    category,
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN stock_quantity > 0 THEN 1 END) as in_stock,
                    COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) as out_of_stock,
                    COUNT(CASE WHEN stock_quantity <= min_stock_level THEN 1 END) as low_stock
                FROM products
                GROUP BY category"""
            )
            
            return {
                'best_selling': best_selling or [],
                'category_stats': category_stats or [],
                'stock_status': stock_status or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في أداء المنتجات: {e}")
            return {}
    
    def get_detailed_stock_status(self) -> List[Dict[str, Any]]:
        """الحصول على تفاصيل حالة المخزون لكل منتج"""
        try:
            result = self.db.execute_query(
                """SELECT 
                    id,
                    name,
                    category,
                    stock_quantity,
                    min_stock_level,
                    price
                FROM products
                ORDER BY name"""
            )
            
            # إضافة حالة المخزون لكل منتج
            stock_data = []
            for product in result:
                stock_quantity = product.get('stock_quantity', 0)
                min_level = product.get('min_stock_level', 0)
                
                # تحديد حالة المخزون
                if stock_quantity == 0:
                    status = "نفد"
                elif stock_quantity <= min_level:
                    status = "منخفض"
                else:
                    status = "متوفر"
                
                product['status'] = status
                stock_data.append(product)
            
            return stock_data
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على تفاصيل حالة المخزون: {e}")
            return []
    
    # ============ تقارير المصروفات ============
    
    def get_expense_analysis(self, start_date: date, end_date: date, cashier_id: int = None) -> Dict[str, Any]:
        """تحليل المصروفات"""
        try:
            query = """SELECT 
                e.id,
                e.amount,
                e.reason,
                e.date_time,
                u.username as cashier_name,
                s.shift_name
            FROM expenses e
            LEFT JOIN users u ON e.cashier_id = u.id
            LEFT JOIN shifts s ON e.shift_id = s.id
            WHERE DATE(e.date_time) BETWEEN ? AND ?"""
            
            params = [start_date, end_date]
            
            if cashier_id:
                query += " AND e.cashier_id = ?"
                params.append(cashier_id)
            
            query += " ORDER BY e.date_time DESC"
            
            expenses = self.db.execute_query(query, tuple(params))
            
            # إحصائيات المصروفات
            stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_expenses,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(AVG(amount), 0) as avg_amount,
                    COALESCE(MIN(amount), 0) as min_amount,
                    COALESCE(MAX(amount), 0) as max_amount
                FROM expenses 
                WHERE DATE(date_time) BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            
            # مصروفات حسب الكاشير
            by_cashier = self.db.execute_query(
                """SELECT 
                    u.username as cashier_name,
                    COUNT(*) as expense_count,
                    COALESCE(SUM(e.amount), 0) as total_amount
                FROM expenses e
                LEFT JOIN users u ON e.cashier_id = u.id
                WHERE DATE(e.date_time) BETWEEN ? AND ?
                GROUP BY e.cashier_id, u.username
                ORDER BY total_amount DESC""",
                (start_date, end_date)
            )
            
            return {
                'expenses': expenses or [],
                'statistics': stats[0] if stats else {},
                'by_cashier': by_cashier or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في تحليل المصروفات: {e}")
            return {}
    
    # ============ تقارير العملاء ============
    
    def get_customer_analysis(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """تحليل العملاء"""
        try:
            # إحصائيات العملاء العامة
            customer_stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_customers,
                    COALESCE(SUM(balance), 0) as total_balance,
                    COALESCE(AVG(balance), 0) as avg_balance,
                    COALESCE(MAX(balance), 0) as max_balance,
                    COALESCE(MIN(balance), 0) as min_balance
                FROM customers"""
            )
            
            # العملاء الأكثر رصيداً
            top_customers = self.db.execute_query(
                """SELECT 
                    phone,
                    name,
                    balance,
                    created_at
                FROM customers
                ORDER BY balance DESC
                LIMIT 10"""
            )
            
            # عملاء نشطين (لديهم فواتير)
            if start_date and end_date:
                active_customers = self.db.execute_query(
                    """SELECT 
                        c.phone,
                        c.name,
                        c.balance,
                        COUNT(i.id) as invoice_count,
                        COALESCE(SUM(i.total_amount), 0) as total_spent
                    FROM customers c
                    LEFT JOIN invoices i ON c.phone = i.customer_phone
                        AND DATE(i.start_time) BETWEEN ? AND ?
                    GROUP BY c.phone, c.name, c.balance
                    HAVING invoice_count > 0
                    ORDER BY total_spent DESC
                    LIMIT 10""",
                    (start_date, end_date)
                )
            else:
                active_customers = []
            
            # معاملات العملاء
            customer_transactions = self.db.execute_query(
                """SELECT 
                    customer_phone,
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(CASE WHEN operation = 'add' THEN amount ELSE 0 END), 0) as total_added,
                    COALESCE(SUM(CASE WHEN operation = 'subtract' THEN amount ELSE 0 END), 0) as total_subtracted
                FROM customer_transactions
                GROUP BY customer_phone
                ORDER BY transaction_count DESC
                LIMIT 10"""
            )
            
            return {
                'statistics': customer_stats[0] if customer_stats else {},
                'top_customers': top_customers or [],
                'active_customers': active_customers or [],
                'customer_transactions': customer_transactions or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في تحليل العملاء: {e}")
            return {}
    
    # ============ تقارير الجلسات ============
    
    def get_session_analysis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تحليل الجلسات"""
        try:
            # إحصائيات الجلسات
            session_stats = self.db.execute_query(
                """SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_sessions,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
                    COALESCE(AVG(julianday(end_time) - julianday(start_time)) * 24 * 60, 0) as avg_duration_minutes,
                    COALESCE(SUM(session_price), 0) as total_session_revenue
                FROM sessions
                WHERE DATE(start_time) BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            
            # جلسات حسب نوع الوقت
            by_time_type = self.db.execute_query(
                """SELECT 
                    time_type,
                    COUNT(*) as session_count,
                    COALESCE(AVG(julianday(end_time) - julianday(start_time)) * 24 * 60, 0) as avg_duration_minutes,
                    COALESCE(SUM(session_price), 0) as total_revenue
                FROM sessions
                WHERE DATE(start_time) BETWEEN ? AND ?
                GROUP BY time_type""",
                (start_date, end_date)
            )
            
            # جلسات حسب نوع السعر
            by_pricing_type = self.db.execute_query(
                """SELECT 
                    pricing_type,
                    COUNT(*) as session_count,
                    COALESCE(SUM(session_price), 0) as total_revenue,
                    COALESCE(AVG(session_price), 0) as avg_price
                FROM sessions
                WHERE DATE(start_time) BETWEEN ? AND ?
                GROUP BY pricing_type""",
                (start_date, end_date)
            )
            
            return {
                'statistics': session_stats[0] if session_stats else {},
                'by_time_type': by_time_type or [],
                'by_pricing_type': by_pricing_type or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في تحليل الجلسات: {e}")
            return {}
    
    # ============ تقارير الورديات ============
    
    def get_shift_analysis(self, start_date: date, end_date: date, cashier_id: int = None) -> Dict[str, Any]:
        """تحليل الورديات"""
        try:
            # ⭐ الحل: فصل حساب المصروفات عن الفواتير لتجنب التكرار
            query = """SELECT 
                s.id,
                s.shift_name,
                s.start_time,
                s.end_time,
                s.status,
                u.username as cashier_name,
                COUNT(DISTINCT i.id) as invoice_count,
                COALESCE(SUM(i.total_amount), 0) as total_revenue,
                COALESCE((
                    SELECT SUM(e.amount) 
                    FROM expenses e 
                    WHERE e.shift_id = s.id
                ), 0) as total_expenses
            FROM shifts s
            LEFT JOIN users u ON s.cashier_id = u.id
            LEFT JOIN invoices i ON s.id = i.shift_id
            WHERE DATE(s.start_time) BETWEEN ? AND ?"""
            
            params = [start_date, end_date]
            
            if cashier_id:
                query += " AND s.cashier_id = ?"
                params.append(cashier_id)
            
            query += """ GROUP BY s.id, s.shift_name, s.start_time, s.end_time, s.status, u.username
                        ORDER BY s.start_time DESC"""
            
            shifts = self.db.execute_query(query, tuple(params))
            
            # إحصائيات الورديات - ⭐ إصلاح: فصل حساب المصروفات
            shift_stats = self.db.execute_query(
                """SELECT 
                    COUNT(DISTINCT s.id) as total_shifts,
                    COUNT(DISTINCT CASE WHEN s.status = 'completed' THEN s.id END) as completed_shifts,
                    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.id END) as active_shifts,
                    COALESCE(AVG(julianday(s.end_time) - julianday(s.start_time)) * 24, 0) as avg_shift_hours,
                    COALESCE(SUM(DISTINCT i.total_amount), 0) as total_revenue,
                    COALESCE((
                        SELECT SUM(e.amount) 
                        FROM expenses e 
                        INNER JOIN shifts s2 ON e.shift_id = s2.id
                        WHERE DATE(s2.start_time) BETWEEN ? AND ?
                    ), 0) as total_expenses
                FROM shifts s
                LEFT JOIN invoices i ON s.id = i.shift_id
                WHERE DATE(s.start_time) BETWEEN ? AND ?""",
                (start_date, end_date, start_date, end_date)
            )
            
            # أداء الكاشيرز - ⭐ إصلاح: فصل حساب المصروفات
            cashier_performance = self.db.execute_query(
                """SELECT 
                    u.username as cashier_name,
                    COUNT(DISTINCT s.id) as shift_count,
                    COUNT(DISTINCT i.id) as invoice_count,
                    COALESCE(SUM(i.total_amount), 0) as total_revenue,
                    COALESCE((
                        SELECT SUM(e.amount) 
                        FROM expenses e 
                        INNER JOIN shifts s2 ON e.shift_id = s2.id
                        WHERE s2.cashier_id = s.cashier_id 
                        AND DATE(s2.start_time) BETWEEN ? AND ?
                    ), 0) as total_expenses,
                    COALESCE(AVG(julianday(s.end_time) - julianday(s.start_time)) * 24, 0) as avg_shift_hours
                FROM shifts s
                LEFT JOIN users u ON s.cashier_id = u.id
                LEFT JOIN invoices i ON s.id = i.shift_id
                WHERE DATE(s.start_time) BETWEEN ? AND ?
                GROUP BY s.cashier_id, u.username
                ORDER BY total_revenue DESC""",
                (start_date, end_date, start_date, end_date)
            )
            
            return {
                'shifts': shifts or [],
                'statistics': shift_stats[0] if shift_stats else {},
                'cashier_performance': cashier_performance or []
            }
            
        except Exception as e:
            logger.error(f"خطأ في تحليل الورديات: {e}")
            return {}
    
    # ============ تقارير شاملة ============
    
    def get_comprehensive_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير شامل لجميع البيانات"""
        try:
            return {
                'revenue': self.get_revenue_summary(start_date, end_date),
                'devices': self.get_device_performance(start_date, end_date),
                'products': self.get_product_performance(start_date, end_date),
                'expenses': self.get_expense_analysis(start_date, end_date),
                'customers': self.get_customer_analysis(start_date, end_date),
                'sessions': self.get_session_analysis(start_date, end_date),
                'shifts': self.get_shift_analysis(start_date, end_date),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': (end_date - start_date).days + 1
                }
            }
        except Exception as e:
            logger.error(f"خطأ في التقرير الشامل: {e}")
            return {}
    
    # ============ تقارير مقارنة ============
    
    def get_comparison_report(self, current_start: date, current_end: date, 
                             previous_start: date, previous_end: date) -> Dict[str, Any]:
        """تقرير مقارنة بين فترتين"""
        try:
            # الحصول على بيانات الفترة الحالية والسابقة
            current_data = self.get_comprehensive_report(current_start, current_end)
            previous_data = self.get_comprehensive_report(previous_start, previous_end)
            
            # حساب التغييرات
            def calculate_change(current, previous):
                if previous == 0:
                    return 100.0 if current > 0 else 0.0
                return ((current - previous) / previous) * 100
            
            # مقارنة الإيرادات
            current_revenue = current_data.get('revenue', {}).get('summary', {}).get('total_revenue', 0)
            previous_revenue = previous_data.get('revenue', {}).get('summary', {}).get('total_revenue', 0)
            
            # مقارنة عدد الفواتير
            current_invoices = current_data.get('revenue', {}).get('summary', {}).get('total_invoices', 0)
            previous_invoices = previous_data.get('revenue', {}).get('summary', {}).get('total_invoices', 0)
            
            return {
                'current_period': {
                    'start': current_start,
                    'end': current_end,
                    'data': current_data
                },
                'previous_period': {
                    'start': previous_start,
                    'end': previous_end,
                    'data': previous_data
                },
                'comparison': {
                    'revenue_change': calculate_change(current_revenue, previous_revenue),
                    'invoices_change': calculate_change(current_invoices, previous_invoices),
                    'current_revenue': current_revenue,
                    'previous_revenue': previous_revenue,
                    'current_invoices': current_invoices,
                    'previous_invoices': previous_invoices
                }
            }
            
        except Exception as e:
            logger.error(f"خطأ في تقرير المقارنة: {e}")
            return {}
    
    # ============ تقارير إضافية ============

