"""
تحكم الورديات الاحترافي
Professional Shift Controller
"""

import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.shift_model import ShiftModel
from models.user_model import UserModel
from models.invoice_model import InvoiceModel
from models.expense_model import ExpenseModel
from utils.security import hash_password, verify_password
from utils.notifications import show_success, show_error
import logging

logger = logging.getLogger(__name__)

class ShiftController:
    """تحكم الورديات الاحترافي"""
    
    def __init__(self):
        self.shift_model = ShiftModel()
        self.user_model = UserModel()
        self.invoice_model = InvoiceModel()
        self.expense_model = ExpenseModel()
        self.current_shift = None
        self.shift_data_cache = {}  # تخزين مؤقت لبيانات الورديات
    
    def start_shift(self, cashier_id: int, shift_name: str = "", notes: str = "") -> Dict[str, Any]:
        """بدء وردية جديدة"""
        try:
            # التحقق من البيانات
            if not cashier_id:
                return {
                    'success': False,
                    'message': 'معرف الكاشير مطلوب'
                }
            
            # التحقق من وجود وردية نشطة للكاشير
            active_shift = self.shift_model.get_active_shift(cashier_id)
            if active_shift:
                return {
                    'success': False,
                    'message': 'لديك وردية نشطة بالفعل، يجب إنهاؤها أولاً'
                }
            
            # بدء الوردية
            shift_id = self.shift_model.create_shift(
                cashier_id=cashier_id,
                shift_name=shift_name,
                notes=notes
            )
            
            if shift_id:
                # حفظ الوردية الحالية
                self.current_shift = {
                    'id': shift_id,
                    'cashier_id': cashier_id,
                    'shift_name': shift_name,
                    'start_time': datetime.now()
                }
                
                return {
                    'success': True,
                    'message': f'تم بدء الوردية "{shift_name}" بنجاح',
                    'shift_id': shift_id,
                    'shift_data': self.current_shift
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في بدء الوردية'
                }
                
        except Exception as e:
            logger.error(f"خطأ في بدء الوردية: {e}")
            return {
                'success': False,
                'message': f'خطأ في بدء الوردية: {str(e)}'
            }
    
    def end_shift(self, shift_id: int, notes: str = "") -> Dict[str, Any]:
        """إنهاء الوردية"""
        try:
            # التحقق من وجود الوردية
            shift = self.shift_model.get_shift_by_id(shift_id)
            if not shift:
                return {
                    'success': False,
                    'message': 'الوردية غير موجودة'
                }
            
            if shift['status'] != 'active':
                return {
                    'success': False,
                    'message': 'الوردية غير نشطة'
                }
            
            # إنهاء الوردية
            success = self.shift_model.end_shift(shift_id, notes)
            
            if success:
                # مسح الوردية الحالية
                if self.current_shift and self.current_shift['id'] == shift_id:
                    self.current_shift = None
                
                return {
                    'success': True,
                    'message': 'تم إنهاء الوردية بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنهاء الوردية'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إنهاء الوردية: {e}")
            return {
                'success': False,
                'message': f'خطأ في إنهاء الوردية: {str(e)}'
            }
    
    def get_current_shift(self) -> Optional[Dict[str, Any]]:
        """الحصول على الوردية الحالية"""
        return self.current_shift
    
    def get_active_shift(self, cashier_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على الوردية النشطة للكاشير"""
        return self.shift_model.get_active_shift(cashier_id)
    
    def get_today_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على ورديات اليوم"""
        return self.shift_model.get_today_shifts()
    
    def get_shift_summary(self, shift_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على ملخص الوردية"""
        return self.shift_model.get_shift_summary(shift_id)
    
    def get_shift_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """الحصول على إحصائيات الورديات"""
        return self.shift_model.get_shift_statistics(start_date, end_date)
    
    def is_shift_active(self, cashier_id: int) -> bool:
        """التحقق من وجود وردية نشطة للكاشير"""
        active_shift = self.shift_model.get_active_shift(cashier_id)
        return active_shift is not None
    
    def get_shift_duration(self, shift_id: int) -> Optional[float]:
        """الحصول على مدة الوردية بالساعات"""
        try:
            shift = self.shift_model.get_shift_by_id(shift_id)
            if not shift:
                return None
            
            start_time = shift['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            end_time = shift['end_time']
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = end_time - start_time
            else:
                duration = datetime.now() - start_time
            
            return duration.total_seconds() / 3600  # تحويل إلى ساعات
            
        except Exception as e:
            logger.error(f"خطأ في حساب مدة الوردية: {e}")
            return None
    
    def get_cashiers(self) -> List[Dict[str, Any]]:
        """الحصول على قائمة الكاشير"""
        try:
            return self.user_model.get_users_by_role('cashier')
        except Exception as e:
            logger.error(f"خطأ في الحصول على الكاشير: {e}")
            return []
    
    def create_cashier(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء كاشير جديد"""
        try:
            # التحقق من البيانات
            if not user_data.get('username'):
                return {
                    'success': False,
                    'message': 'اسم المستخدم مطلوب'
                }
            
            if not user_data.get('password'):
                return {
                    'success': False,
                    'message': 'كلمة المرور مطلوبة'
                }
            
            # التحقق من عدم وجود مستخدم بنفس الاسم
            if not self.user_model.is_username_available(user_data['username']):
                return {
                    'success': False,
                    'message': 'اسم المستخدم موجود بالفعل'
                }
            
            # إنشاء الكاشير
            user_data['role'] = 'cashier'
            user_id = self.user_model.create_user(user_data)
            
            if user_id:
                return {
                    'success': True,
                    'message': f'تم إنشاء كاشير "{user_data["username"]}" بنجاح',
                    'user_id': user_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء الكاشير'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الكاشير: {e}")
            return {
                'success': False,
                'message': f'خطأ في إنشاء الكاشير: {str(e)}'
            }
    
    def start_shift_with_clear_data(self, cashier_id: int, shift_name: str = "", notes: str = "") -> Dict[str, Any]:
        """بدء وردية جديدة مشتركة مع إنهاء جميع الورديات النشطة وإخفاء البيانات"""
        try:
            # إنهاء جميع الورديات النشطة أولاً
            active_shifts = self.shift_model.get_all_active_shifts()
            for shift in active_shifts:
                self.shift_model.end_shift(shift['id'], "إنهاء تلقائي لبدء وردية جديدة")
                logger.info(f"تم إنهاء الوردية {shift['id']} تلقائياً")
            
            # مسح جميع التخزين المؤقت
            self.shift_data_cache.clear()
            
            # إخفاء البيانات بشكل فعال
            self.clear_all_shift_data()
            
            # بدء الوردية الجديدة
            result = self.start_shift(cashier_id, shift_name, notes)
            
            if result['success']:
                logger.info(f"تم بدء وردية جديدة مشتركة للكاشير {cashier_id}")
                
                # إعادة تشغيل البرنامج مع تسجيل دخول تلقائي للكاشير الجديد
                try:
                    from utils.auto_restart import schedule_restart_with_auto_login
                    from models.user_model import UserModel
                    
                    # الحصول على بيانات الكاشير الجديد
                    user_model = UserModel()
                    cashier_data = user_model.get_user_by_id(cashier_id)
                    
                    if cashier_data:
                        # جدولة إعادة التشغيل مع تأخير 2 ثانية
                        schedule_restart_with_auto_login(
                            cashier_id=cashier_id,
                            username=cashier_data['username'],
                            role=cashier_data['role'],
                            delay_ms=2000,
                            parent_widget=None
                        )
                        logger.info(f"تم جدولة إعادة تشغيل البرنامج للكاشير {cashier_data['username']}")
                    else:
                        logger.error(f"لم يتم العثور على بيانات الكاشير {cashier_id}")
                        
                except Exception as restart_error:
                    logger.error(f"خطأ في جدولة إعادة التشغيل: {restart_error}")
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في بدء وردية مشتركة: {e}")
            return {
                'success': False,
                'message': f'خطأ في بدء الوردية: {str(e)}'
            }
    
    def clear_all_shift_data(self):
        """إخفاء جميع بيانات الورديات السابقة بشكل فعال"""
        try:
            # مسح التخزين المؤقت في جميع المتحكمات
            self.shift_data_cache.clear()
            
            # إشعار واجهات المستخدم بتحديث البيانات
            # هذا سيؤدي إلى إعادة تحميل البيانات من قاعدة البيانات
            # وبما أن الورديات السابقة أصبحت غير نشطة، لن تظهر بياناتها
            
            logger.info("تم إخفاء جميع بيانات الورديات السابقة")
            
        except Exception as e:
            logger.error(f"خطأ في إخفاء بيانات الورديات: {e}")
    
    def get_cashier_shift_data(self, cashier_id: int = None, shift_id: int = None) -> Dict[str, Any]:
        """الحصول على بيانات الوردية المشتركة (فواتير ومصروفات)"""
        try:
            # استخدام التخزين المؤقت إذا كان متوفراً
            cache_key = f"shared_{shift_id or 'active'}"
            if cache_key in self.shift_data_cache:
                return self.shift_data_cache[cache_key]
            
            # الحصول على فواتير الوردية المشتركة
            invoices = self.shift_model.get_cashier_shift_invoices(cashier_id, shift_id)
            
            # الحصول على مصروفات الوردية المشتركة
            expenses = self.shift_model.get_cashier_shift_expenses(cashier_id, shift_id)
            
            # حساب الإحصائيات التفصيلية
            total_invoices = len(invoices)
            total_revenue = sum(invoice.get('total_amount', 0) for invoice in invoices)
            total_expenses = len(expenses)
            total_expense_amount = sum(expense.get('amount', 0) for expense in expenses)
            
            # فصل الفواتير النقدية عن فواتير العملاء
            cash_invoices = []
            customer_invoices = []
            cash_revenue = 0
            customer_revenue = 0
            
            for invoice in invoices:
                # فاتورة عميل: فقط إذا كان paid_by = 'customer_balance' (جلسة مدفوعة من رصيد العميل)
                if invoice.get('paid_by') == 'customer_balance':
                    # فاتورة عميل (جلسة مدفوعة من رصيد العميل)
                    customer_invoices.append(invoice)
                    customer_revenue += invoice.get('total_amount', 0)
                else:
                    # فاتورة نقدية (جلسة عادية مدفوعة نقداً أو معاملة إدارية مدفوعة نقداً)
                    cash_invoices.append(invoice)
                    cash_revenue += invoice.get('total_amount', 0)
            
            # حساب صافي الكاش (الفواتير النقدية - المصروفات)
            net_cash = cash_revenue - total_expense_amount
            
            shift_data = {
                'invoices': invoices,
                'expenses': expenses,
                'cash_invoices': cash_invoices,
                'customer_invoices': customer_invoices,
                'statistics': {
                    'total_invoices': total_invoices,
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'total_expense_amount': total_expense_amount,
                    'net_profit': total_revenue - total_expense_amount,
                    'cash_invoices_count': len(cash_invoices),
                    'cash_revenue': cash_revenue,
                    'customer_invoices_count': len(customer_invoices),
                    'customer_revenue': customer_revenue,
                    'net_cash': net_cash
                },
                'last_updated': datetime.now()
            }
            
            # حفظ في التخزين المؤقت
            self.shift_data_cache[cache_key] = shift_data
            
            return shift_data
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على بيانات وردية الكاشير: {e}")
            return {
                'invoices': [],
                'expenses': [],
                'statistics': {
                    'total_invoices': 0,
                    'total_revenue': 0,
                    'total_expenses': 0,
                    'total_expense_amount': 0,
                    'net_profit': 0
                },
                'last_updated': datetime.now()
            }
    
    def refresh_cashier_shift_data(self, cashier_id: int, shift_id: int = None) -> Dict[str, Any]:
        """تحديث بيانات الوردية للكاشير"""
        try:
            # مسح التخزين المؤقت
            cache_key = f"{cashier_id}_{shift_id or 'active'}"
            if cache_key in self.shift_data_cache:
                del self.shift_data_cache[cache_key]
            
            # الحصول على البيانات المحدثة
            return self.get_cashier_shift_data(cashier_id, shift_id)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث بيانات وردية الكاشير: {e}")
            return self.get_cashier_shift_data(cashier_id, shift_id)
    
    def get_shift_performance_report(self, shift_id: int) -> Dict[str, Any]:
        """الحصول على تقرير أداء الوردية"""
        try:
            # الحصول على مؤشرات الأداء
            metrics = self.shift_model.get_shift_performance_metrics(shift_id)
            
            if not metrics:
                return {
                    'success': False,
                    'message': 'الوردية غير موجودة'
                }
            
            # إضافة تفاصيل إضافية
            shift_info = metrics.get('shift_info', {})
            cashier_id = shift_info.get('cashier_id')
            
            if cashier_id:
                # الحصول على بيانات مفصلة
                shift_data = self.get_cashier_shift_data(cashier_id, shift_id)
                metrics['detailed_data'] = shift_data
            
            return {
                'success': True,
                'metrics': metrics,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على تقرير أداء الوردية: {e}")
            return {
                'success': False,
                'message': f'خطأ في الحصول على التقرير: {str(e)}'
            }
    
    def get_all_active_shifts(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الورديات النشطة"""
        try:
            result = self.shift_model.db.execute_query(
                """SELECT s.*, u.username as cashier_name 
                   FROM shifts s
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.status = 'active'
                   ORDER BY s.start_time DESC"""
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الورديات النشطة: {e}")
            return []
    
    def force_end_shift(self, shift_id: int, admin_password: str, reason: str = "") -> Dict[str, Any]:
        """إنهاء وردية قسري (للمدير فقط)"""
        try:
            # التحقق من باسورد المدير
            if not self.user_model.verify_admin_password(admin_password):
                return {
                    'success': False,
                    'message': 'باسورد المدير غير صحيح'
                }
            
            # إنهاء الوردية
            notes = f"إنهاء قسري - {reason}" if reason else "إنهاء قسري من قبل المدير"
            success = self.shift_model.end_shift(shift_id, notes)
            
            if success:
                # مسح التخزين المؤقت
                shift = self.shift_model.get_shift_by_id(shift_id)
                if shift:
                    cashier_id = shift.get('cashier_id')
                    if cashier_id:
                        cache_key = f"{cashier_id}_{shift_id}"
                        if cache_key in self.shift_data_cache:
                            del self.shift_data_cache[cache_key]
                
                return {
                    'success': True,
                    'message': 'تم إنهاء الوردية بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إنهاء الوردية'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إنهاء الوردية القسري: {e}")
            return {
                'success': False,
                'message': f'خطأ في إنهاء الوردية: {str(e)}'
            }
    
    def get_shift_templates(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """الحصول على قوالب الورديات المتاحة"""
        try:
            # قوالب الورديات الافتراضية
            templates = [
                {
                    'id': 1,
                    'name': 'وردية صباحية',
                    'start_time': '08:00',
                    'end_time': '16:00',
                    'description': 'وردية العمل الصباحية',
                    'is_active': True
                },
                {
                    'id': 2,
                    'name': 'وردية مسائية',
                    'start_time': '16:00',
                    'end_time': '00:00',
                    'description': 'وردية العمل المسائية',
                    'is_active': True
                },
                {
                    'id': 3,
                    'name': 'وردية ليلية',
                    'start_time': '00:00',
                    'end_time': '08:00',
                    'description': 'وردية العمل الليلية',
                    'is_active': True
                }
            ]
            
            if active_only:
                templates = [t for t in templates if t.get('is_active', True)]
            
            return templates
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على قوالب الورديات: {e}")
            return []
    
    def login_to_shift(self, shift_name: str, password: str, cashier_id: int, notes: str = "") -> Dict[str, Any]:
        """تسجيل دخول إلى وردية (محاكاة)"""
        try:
            # التحقق من صحة كلمة المرور (محاكاة)
            if password != "shift123":  # كلمة مرور افتراضية للورديات
                return {
                    'success': False,
                    'message': 'كلمة مرور الوردية غير صحيحة'
                }
            
            # بدء الوردية
            result = self.start_shift_with_clear_data(cashier_id, shift_name, notes)
            
            if result['success']:
                # إضافة بيانات إضافية
                result['shift_data'] = {
                    'shift_name': shift_name,
                    'cashier_id': cashier_id,
                    'login_time': datetime.now(),
                    'notes': notes
                }
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في تسجيل دخول الوردية: {e}")
            return {
                'success': False,
                'message': f'خطأ في تسجيل الدخول: {str(e)}'
            }
