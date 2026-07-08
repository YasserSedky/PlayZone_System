"""
أدوات التحقق من الورديات
Shift Validation Utilities
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QMessageBox
from models.shift_model import ShiftModel


def check_active_shift() -> Optional[Dict[str, Any]]:
    """التحقق من وجود وردية نشطة"""
    try:
        shift_model = ShiftModel()
        active_shift = shift_model.get_active_shared_shift()
        return active_shift
    except Exception as e:
        print(f"خطأ في التحقق من الوردية النشطة: {e}")
        return None


def validate_shift_required(parent_widget=None) -> bool:
    """التحقق من وجود وردية نشطة وإظهار رسالة خطأ إذا لم تكن موجودة"""
    try:
        active_shift = check_active_shift()
        
        if not active_shift:
            if parent_widget:
                QMessageBox.warning(
                    parent_widget,
                    "وردية غير نشطة",
                    "يجب أن تبدأ وردية أولاً قبل القيام بهذه العملية.\n\n"
                    "يرجى الذهاب إلى قسم الورديات وبدء وردية جديدة."
                )
            else:
                print("تحذير: يجب أن تبدأ وردية أولاً قبل القيام بهذه العملية")
            return False
        
        return True
        
    except Exception as e:
        print(f"خطأ في التحقق من الوردية: {e}")
        if parent_widget:
            QMessageBox.critical(
                parent_widget,
                "خطأ",
                f"حدث خطأ في التحقق من الوردية: {str(e)}"
            )
        return False


def get_active_shift_info() -> Optional[Dict[str, Any]]:
    """الحصول على معلومات الوردية النشطة"""
    try:
        active_shift = check_active_shift()
        if active_shift:
            return {
                'id': active_shift.get('id'),
                'shift_name': active_shift.get('shift_name', 'وردية بدون اسم'),
                'cashier_name': active_shift.get('cashier_name', 'غير محدد'),
                'start_time': active_shift.get('start_time'),
                'status': active_shift.get('status')
            }
        return None
    except Exception as e:
        print(f"خطأ في الحصول على معلومات الوردية: {e}")
        return None
