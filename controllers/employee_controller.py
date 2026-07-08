"""
تحكم الموظفين
Employee Controller
"""

import sys
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.employee_model import EmployeeModel
from utils.helpers import format_currency, format_time
from utils.permissions import can_manage_system

class EmployeeController:
    """تحكم الموظفين"""
    
    def __init__(self, current_user):
        self.current_user = current_user
        self.employee_model = EmployeeModel()
    
    def validate_permissions(self) -> bool:
        """التحقق من صلاحيات إدارة الموظفين"""
        try:
            return can_manage_system(self.current_user.get('role', ''))
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    # ============ إدارة الموظفين ============
    
    def create_employee(self, name: str, position: str, monthly_salary: Decimal,
                       hire_date: date, phone: str = None, national_id: str = None,
                       address: str = None, notes: str = None) -> Dict[str, Any]:
        """إنشاء موظف جديد"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإدارة الموظفين'
                }
            
            # التحقق من البيانات
            if not name or not position or monthly_salary <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال جميع البيانات المطلوبة'
                }
            
            employee_id = self.employee_model.create_employee(
                name=name,
                position=position,
                monthly_salary=monthly_salary,
                hire_date=hire_date,
                phone=phone,
                national_id=national_id,
                address=address,
                notes=notes,
                created_by=self.current_user.get('id')
            )
            
            if employee_id:
                return {
                    'success': True,
                    'message': f'تم إضافة الموظف {name} بنجاح',
                    'employee_id': employee_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة الموظف'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء الموظف: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_all_employees(self, include_inactive: bool = False) -> Dict[str, Any]:
        """الحصول على جميع الموظفين"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض الموظفين'
                }
            
            employees = self.employee_model.get_all_employees(include_inactive)
            
            return {
                'success': True,
                'employees': employees
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الموظفين: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def update_employee(self, employee_id: int, **kwargs) -> Dict[str, Any]:
        """تحديث بيانات موظف"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتعديل بيانات الموظفين'
                }
            
            success = self.employee_model.update_employee(employee_id, **kwargs)
            
            if success:
                return {
                    'success': True,
                    'message': 'تم تحديث بيانات الموظف بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث بيانات الموظف'
                }
                
        except Exception as e:
            logger.error(f"خطأ في تحديث الموظف: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def delete_employee(self, employee_id: int) -> Dict[str, Any]:
        """حذف موظف"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحذف الموظفين'
                }
            
            success = self.employee_model.delete_employee(employee_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'تم حذف الموظف بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حذف الموظف'
                }
                
        except Exception as e:
            logger.error(f"خطأ في حذف الموظف: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ إدارة السلف ============
    
    def add_advance(self, employee_id: int, amount: Decimal, date: date,
                   reason: str = None) -> Dict[str, Any]:
        """إضافة سلفة لموظف"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإضافة سلف'
                }
            
            if amount <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال مبلغ صحيح'
                }
            
            advance_id = self.employee_model.add_advance(
                employee_id=employee_id,
                amount=amount,
                date=date,
                reason=reason,
                created_by=self.current_user.get('id')
            )
            
            if advance_id:
                return {
                    'success': True,
                    'message': f'تم إضافة سلفة بقيمة {format_currency(amount)} بنجاح',
                    'advance_id': advance_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة السلفة'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إضافة السلفة: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_employee_advances(self, employee_id: int, month: str = None,
                             year: int = None) -> Dict[str, Any]:
        """الحصول على سلف الموظف"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض السلف'
                }
            
            advances = self.employee_model.get_employee_advances(employee_id, month, year)
            
            return {
                'success': True,
                'advances': advances
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على السلف: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ إدارة الخصومات ============
    
    def add_deduction(self, employee_id: int, amount: Decimal, date: date,
                     reason: str, deduction_type: str = 'other') -> Dict[str, Any]:
        """إضافة خصم على موظف"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإضافة خصومات'
                }
            
            if amount <= 0 or not reason:
                return {
                    'success': False,
                    'message': 'يرجى إدخال جميع البيانات المطلوبة'
                }
            
            deduction_id = self.employee_model.add_deduction(
                employee_id=employee_id,
                amount=amount,
                date=date,
                reason=reason,
                deduction_type=deduction_type,
                created_by=self.current_user.get('id')
            )
            
            if deduction_id:
                return {
                    'success': True,
                    'message': f'تم إضافة خصم بقيمة {format_currency(amount)} بنجاح',
                    'deduction_id': deduction_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة الخصم'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إضافة الخصم: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ إدارة ساعات العمل الإضافية ============
    
    def add_overtime(self, employee_id: int, date: date, hours: Decimal,
                    hourly_rate: Decimal, notes: str = None) -> Dict[str, Any]:
        """إضافة ساعات عمل إضافية"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لإضافة ساعات عمل إضافية'
                }
            
            if hours <= 0 or hourly_rate <= 0:
                return {
                    'success': False,
                    'message': 'يرجى إدخال بيانات صحيحة'
                }
            
            overtime_id = self.employee_model.add_overtime(
                employee_id=employee_id,
                date=date,
                hours=hours,
                hourly_rate=hourly_rate,
                notes=notes,
                created_by=self.current_user.get('id')
            )
            
            if overtime_id:
                total = hours * hourly_rate
                return {
                    'success': True,
                    'message': f'تم إضافة {hours} ساعة عمل إضافية بإجمالي {format_currency(total)}',
                    'overtime_id': overtime_id
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في إضافة ساعات العمل الإضافية'
                }
                
        except Exception as e:
            logger.error(f"خطأ في إضافة ساعات العمل الإضافية: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ حساب ومعالجة الرواتب ============
    
    def calculate_salary(self, employee_id: int, month: str, year: int) -> Dict[str, Any]:
        """حساب راتب الموظف الشهري"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لحساب الرواتب'
                }
            
            salary_breakdown = self.employee_model.calculate_monthly_salary(employee_id, month, year)
            
            if salary_breakdown:
                return {
                    'success': True,
                    'salary': salary_breakdown
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في حساب الراتب'
                }
                
        except Exception as e:
            logger.error(f"خطأ في حساب الراتب: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def process_monthly_salaries(self, month: str, year: int) -> Dict[str, Any]:
        """معالجة رواتب جميع الموظفين لشهر معين"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لمعالجة الرواتب'
                }
            
            employees = self.employee_model.get_all_employees(include_inactive=False)
            processed_count = 0
            failed_count = 0
            
            for employee in employees:
                try:
                    # حساب الراتب
                    salary_breakdown = self.employee_model.calculate_monthly_salary(
                        employee['id'], month, year
                    )
                    
                    if salary_breakdown:
                        # حفظ سجل الراتب
                        record_id = self.employee_model.save_salary_record(
                            employee_id=employee['id'],
                            month=month,
                            year=year,
                            base_salary=salary_breakdown['base_salary'],
                            overtime_amount=salary_breakdown['overtime_amount'],
                            advances_amount=salary_breakdown['advances_amount'],
                            deductions_amount=salary_breakdown['deductions_amount'],
                            net_salary=salary_breakdown['net_salary'],
                            created_by=self.current_user.get('id')
                        )
                        
                        if record_id:
                            processed_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"خطأ في معالجة راتب الموظف {employee['id']}: {e}")
                    failed_count += 1
            
            return {
                'success': True,
                'message': f'تم معالجة {processed_count} راتب بنجاح',
                'processed_count': processed_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الرواتب: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def get_salary_records(self, month: str = None, year: int = None) -> Dict[str, Any]:
        """الحصول على سجلات الرواتب"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض سجلات الرواتب'
                }
            
            records = self.employee_model.get_all_salary_records(month, year)
            
            return {
                'success': True,
                'records': records
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على سجلات الرواتب: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    def mark_salary_paid(self, record_id: int, payment_date: date = None) -> Dict[str, Any]:
        """تحديد الراتب كمدفوع"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لتحديث حالة الرواتب'
                }
            
            success = self.employee_model.mark_salary_paid(record_id, payment_date)
            
            if success:
                return {
                    'success': True,
                    'message': 'تم تحديث حالة الراتب بنجاح'
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث حالة الراتب'
                }
                
        except Exception as e:
            logger.error(f"خطأ في تحديث حالة الراتب: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }
    
    # ============ إحصائيات ============
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الموظفين"""
        try:
            if not self.validate_permissions():
                return {
                    'success': False,
                    'message': 'ليس لديك صلاحية لعرض الإحصائيات'
                }
            
            stats = self.employee_model.get_employee_statistics()
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الإحصائيات: {e}")
            return {
                'success': False,
                'message': f'خطأ: {str(e)}'
            }

