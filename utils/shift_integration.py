"""
تكامل نظام الورديات مع النظام الموجود
Shift System Integration
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.shift_controller import ShiftController
from models.shift_model import ShiftModel

logger = logging.getLogger(__name__)

class ShiftIntegration:
    """تكامل نظام الورديات مع النظام الموجود"""
    
    def __init__(self):
        self.shift_controller = ShiftController()
        self.shift_model = ShiftModel()
        self.current_shift_cache = {}
    
    def get_current_shift_for_cashier(self, cashier_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على الوردية الحالية للكاشير"""
        try:
            # استخدام التخزين المؤقت إذا كان متوفراً
            if cashier_id in self.current_shift_cache:
                cached_shift = self.current_shift_cache[cashier_id]
                # التحقق من أن الوردية لا تزال نشطة
                if cached_shift.get('status') == 'active':
                    return cached_shift
            
            # الحصول على الوردية النشطة من قاعدة البيانات
            active_shift = self.shift_model.get_active_shift(cashier_id)
            
            if active_shift:
                # حفظ في التخزين المؤقت
                self.current_shift_cache[cashier_id] = active_shift
                return active_shift
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الوردية الحالية: {e}")
            return None
    
    def clear_shift_cache(self, cashier_id: int = None):
        """مسح التخزين المؤقت للورديات"""
        try:
            if cashier_id:
                if cashier_id in self.current_shift_cache:
                    del self.current_shift_cache[cashier_id]
            else:
                self.current_shift_cache.clear()
                
        except Exception as e:
            logger.error(f"خطأ في مسح التخزين المؤقت: {e}")
    
    def start_shift_with_integration(self, cashier_id: int, shift_name: str = "", notes: str = "") -> Dict[str, Any]:
        """بدء وردية مع التكامل الكامل"""
        try:
            # التحقق من إمكانية بدء وردية جديدة
            validation = self.shift_model.validate_shift_transition(cashier_id, shift_name)
            if not validation['can_start']:
                return {
                    'success': False,
                    'message': validation['message'],
                    'reason': validation.get('reason', 'unknown')
                }
            
            # بدء الوردية مع تفريغ البيانات
            result = self.shift_controller.start_shift_with_clear_data(
                cashier_id=cashier_id,
                shift_name=shift_name,
                notes=notes
            )
            
            if result['success']:
                # مسح التخزين المؤقت
                self.clear_shift_cache(cashier_id)
                
                # إضافة معلومات إضافية للنتيجة
                result['integration_data'] = {
                    'cache_cleared': True,
                    'timestamp': datetime.now(),
                    'cashier_id': cashier_id
                }
                
                logger.info(f"تم بدء وردية جديدة للكاشير {cashier_id} مع التكامل الكامل")
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في بدء الوردية مع التكامل: {e}")
            return {
                'success': False,
                'message': f'خطأ في بدء الوردية: {str(e)}'
            }
    
    def end_shift_with_integration(self, shift_id: int, notes: str = "") -> Dict[str, Any]:
        """إنهاء وردية مع التكامل الكامل"""
        try:
            # الحصول على معلومات الوردية
            shift = self.shift_model.get_shift_by_id(shift_id)
            if not shift:
                return {
                    'success': False,
                    'message': 'الوردية غير موجودة'
                }
            
            cashier_id = shift.get('cashier_id')
            
            # إنهاء الوردية
            result = self.shift_controller.end_shift(shift_id, notes)
            
            if result['success']:
                # مسح التخزين المؤقت
                if cashier_id:
                    self.clear_shift_cache(cashier_id)
                
                # إضافة معلومات إضافية للنتيجة
                result['integration_data'] = {
                    'cache_cleared': True,
                    'timestamp': datetime.now(),
                    'cashier_id': cashier_id,
                    'shift_id': shift_id
                }
                
                logger.info(f"تم إنهاء الوردية {shift_id} للكاشير {cashier_id} مع التكامل الكامل")
            
            return result
            
        except Exception as e:
            logger.error(f"خطأ في إنهاء الوردية مع التكامل: {e}")
            return {
                'success': False,
                'message': f'خطأ في إنهاء الوردية: {str(e)}'
            }
    
    def get_shift_filtered_data(self, cashier_id: int, data_type: str = 'all') -> Dict[str, Any]:
        """الحصول على بيانات مصفاة حسب الوردية الحالية"""
        try:
            # الحصول على الوردية الحالية
            current_shift = self.get_current_shift_for_cashier(cashier_id)
            
            if not current_shift:
                return {
                    'has_active_shift': False,
                    'message': 'لا توجد وردية نشطة',
                    'data': {}
                }
            
            shift_id = current_shift['id']
            
            # الحصول على البيانات حسب النوع المطلوب
            if data_type in ['all', 'invoices']:
                invoices = self.shift_model.get_cashier_shift_invoices(cashier_id, shift_id)
            else:
                invoices = []
            
            if data_type in ['all', 'expenses']:
                expenses = self.shift_model.get_cashier_shift_expenses(cashier_id, shift_id)
            else:
                expenses = []
            
            # حساب الإحصائيات
            total_invoices = len(invoices)
            total_revenue = sum(invoice.get('total_amount', 0) for invoice in invoices)
            total_expenses = len(expenses)
            total_expense_amount = sum(expense.get('amount', 0) for expense in expenses)
            net_profit = total_revenue - total_expense_amount
            
            return {
                'has_active_shift': True,
                'shift_info': current_shift,
                'data': {
                    'invoices': invoices,
                    'expenses': expenses,
                    'statistics': {
                        'total_invoices': total_invoices,
                        'total_revenue': total_revenue,
                        'total_expenses': total_expenses,
                        'total_expense_amount': total_expense_amount,
                        'net_profit': net_profit
                    }
                },
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على البيانات المصفاة: {e}")
            return {
                'has_active_shift': False,
                'message': f'خطأ في الحصول على البيانات: {str(e)}',
                'data': {}
            }
    
    def refresh_shift_data(self, cashier_id: int) -> Dict[str, Any]:
        """تحديث بيانات الوردية"""
        try:
            # مسح التخزين المؤقت
            self.clear_shift_cache(cashier_id)
            
            # الحصول على البيانات المحدثة
            return self.get_shift_filtered_data(cashier_id)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث بيانات الوردية: {e}")
            return {
                'has_active_shift': False,
                'message': f'خطأ في التحديث: {str(e)}',
                'data': {}
            }
    
    def get_shift_status_summary(self, cashier_id: int) -> Dict[str, Any]:
        """الحصول على ملخص حالة الوردية"""
        try:
            current_shift = self.get_current_shift_for_cashier(cashier_id)
            
            if not current_shift:
                return {
                    'has_active_shift': False,
                    'status': 'no_shift',
                    'message': 'لا توجد وردية نشطة'
                }
            
            # حساب مدة الوردية
            start_time = current_shift.get('start_time')
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            duration = datetime.now() - start_time
            duration_hours = duration.total_seconds() / 3600
            
            # الحصول على إحصائيات سريعة
            shift_data = self.get_shift_filtered_data(cashier_id)
            stats = shift_data.get('data', {}).get('statistics', {})
            
            return {
                'has_active_shift': True,
                'status': 'active',
                'shift_info': current_shift,
                'duration_hours': duration_hours,
                'statistics': stats,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملخص حالة الوردية: {e}")
            return {
                'has_active_shift': False,
                'status': 'error',
                'message': f'خطأ في الحصول على الحالة: {str(e)}'
            }
    
    def validate_shift_operation(self, cashier_id: int, operation: str) -> Dict[str, Any]:
        """التحقق من إمكانية تنفيذ عملية على الوردية"""
        try:
            current_shift = self.get_current_shift_for_cashier(cashier_id)
            
            if operation == 'start_shift':
                if current_shift:
                    return {
                        'can_proceed': False,
                        'message': 'لديك وردية نشطة بالفعل',
                        'current_shift': current_shift
                    }
                else:
                    return {
                        'can_proceed': True,
                        'message': 'يمكن بدء وردية جديدة'
                    }
            
            elif operation == 'end_shift':
                if current_shift:
                    return {
                        'can_proceed': True,
                        'message': 'يمكن إنهاء الوردية',
                        'current_shift': current_shift
                    }
                else:
                    return {
                        'can_proceed': False,
                        'message': 'لا توجد وردية نشطة لإنهائها'
                    }
            
            elif operation in ['add_invoice', 'add_expense']:
                if current_shift:
                    return {
                        'can_proceed': True,
                        'message': 'يمكن إضافة البيانات للوردية',
                        'current_shift': current_shift
                    }
                else:
                    return {
                        'can_proceed': False,
                        'message': 'يجب بدء وردية أولاً'
                    }
            
            else:
                return {
                    'can_proceed': False,
                    'message': 'عملية غير معروفة'
                }
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من عملية الوردية: {e}")
            return {
                'can_proceed': False,
                'message': f'خطأ في التحقق: {str(e)}'
            }

# إنشاء مثيل عام للتكامل
shift_integration = ShiftIntegration()

def get_shift_integration() -> ShiftIntegration:
    """الحصول على مثيل تكامل الورديات"""
    return shift_integration
