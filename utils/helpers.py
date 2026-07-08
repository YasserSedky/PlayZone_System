"""
الدوال المساعدة
Helper Functions
"""

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, List, Dict, Any
import re
import locale
import logging

logger = logging.getLogger(__name__)

def get_currency_mapping():
    """الحصول على خريطة العملات"""
    return {
        "جنيه مصري (ج.م)": {"code": "EGP", "symbol": "ج.م"},
        "دينار أردني (د.أ)": {"code": "JOD", "symbol": "د.أ"},
        "دينار عراقي (د.ع)": {"code": "IQD", "symbol": "د.ع"},
        "ريال عماني (ر.ع)": {"code": "OMR", "symbol": "ر.ع"},
        "ريال سعودي (ر.س)": {"code": "SAR", "symbol": "ر.س"},
        "درهم إماراتي (د.إ)": {"code": "AED", "symbol": "د.إ"}
    }

def get_current_currency_settings():
    """الحصول على إعدادات العملة الحالية من الإعدادات"""
    try:
        from utils.settings_manager import settings_manager
        currency_display = settings_manager.get_currency()
        currency_mapping = get_currency_mapping()
        
        if currency_display in currency_mapping:
            return currency_mapping[currency_display]
        else:
            # افتراضي
            return {"code": "EGP", "symbol": "ج.م"}
    except Exception as e:
        logger.error(f"خطأ في الحصول على إعدادات العملة: {e}")
        return {"code": "EGP", "symbol": "ج.م"}

def get_current_date_format():
    """الحصول على تنسيق التاريخ الحالي من الإعدادات"""
    try:
        from utils.settings_manager import settings_manager
        date_format = settings_manager.get_setting("ui.date_format", "dd/mm/yyyy")
        
        # تحويل تنسيق التاريخ إلى Python format
        format_mapping = {
            "dd/mm/yyyy": "%d/%m/%Y",
            "mm/dd/yyyy": "%m/%d/%Y", 
            "yyyy-mm-dd": "%Y-%m-%d"
        }
        
        return format_mapping.get(date_format, "%d/%m/%Y")
    except Exception as e:
        logger.error(f"خطأ في الحصول على تنسيق التاريخ: {e}")
        return "%d/%m/%Y"

def format_currency(amount: Union[Decimal, float, int], currency: str = None) -> str:
    """تنسيق العملة"""
    try:
        if amount is None:
            amount = 0
        
        # تحويل إلى Decimal للتأكد من الدقة
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # تقريب إلى منزلتين عشريتين
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # الحصول على إعدادات العملة الحالية
        if currency is None:
            currency_settings = get_current_currency_settings()
            currency_code = currency_settings["code"]
            currency_symbol = currency_settings["symbol"]
        else:
            currency_code = currency
            currency_symbol = currency
        
        # تنسيق الرقم
        formatted_amount = f"{amount:,.2f}"
        
        return f"{formatted_amount} {currency_symbol}"
        
    except Exception as e:
        logger.error(f"خطأ في تنسيق العملة: {e}")
        return f"0.00 ج.م"

def refresh_application_views():
    """تحديث جميع نوافذ التطبيق عند تغيير الإعدادات"""
    try:
        from PySide6.QtWidgets import QApplication
        
        # البحث عن جميع النوافذ المفتوحة وتحديثها
        for widget in QApplication.allWidgets():
            if hasattr(widget, 'refresh_data'):
                try:
                    widget.refresh_data()
                except:
                    pass
            elif hasattr(widget, 'load_data'):
                try:
                    widget.load_data()
                except:
                    pass
            elif hasattr(widget, 'update_display'):
                try:
                    widget.update_display()
                except:
                    pass
        
        logger.info("تم تحديث جميع نوافذ التطبيق")
        
    except Exception as e:
        logger.error(f"خطأ في تحديث نوافذ التطبيق: {e}")

def format_time(dt, format_type: str = "full") -> str:
    """تنسيق الوقت"""
    try:
        if not dt:
            return ""
        
        # إذا كان النص عبارة عن string، نحوله إلى datetime
        if isinstance(dt, str):
            if 'T' in dt:
                # تنسيق ISO
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                # تنسيق SQLite
                try:
                    dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    try:
                        dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # إذا فشل التحويل، نعيد النص كما هو
                        return str(dt)
        
        # التحقق من أن dt هو datetime
        if not isinstance(dt, datetime):
            return str(dt)
        
        # الحصول على تنسيق التاريخ الحالي من الإعدادات
        current_date_format = get_current_date_format()
        
        if format_type == "full":
            return dt.strftime(f"{current_date_format} %H:%M:%S")
        elif format_type == "date":
            return dt.strftime(current_date_format)
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        elif format_type == "short":
            return dt.strftime(f"{current_date_format} %H:%M")
        elif format_type == "arabic":
            return dt.strftime(f"{current_date_format} %H:%M")
        else:
            return dt.strftime(format_type)
            
    except Exception as e:
        logger.error(f"خطأ في تنسيق الوقت: {e}")
        return str(dt) if dt else ""

def format_duration(seconds: Union[int, float]) -> str:
    """تنسيق المدة الزمنية"""
    try:
        if not seconds or seconds <= 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
    except Exception as e:
        logger.error(f"خطأ في تنسيق المدة: {e}")
        return "00:00:00"

def calculate_session_duration(start_time: datetime, end_time: Optional[datetime] = None) -> int:
    """حساب مدة الجلسة بالدقائق"""
    try:
        if not end_time:
            end_time = datetime.now()
        
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)
        
    except Exception as e:
        logger.error(f"خطأ في حساب مدة الجلسة: {e}")
        return 0

def calculate_session_cost(duration_minutes: int, price_per_hour: Decimal) -> Decimal:
    """حساب تكلفة الجلسة"""
    try:
        if duration_minutes <= 0 or price_per_hour <= 0:
            return Decimal('0.00')
        
        # تحويل السعر من ساعة إلى دقيقة
        price_per_minute = price_per_hour / Decimal('60')
        
        # حساب التكلفة
        cost = price_per_minute * Decimal(str(duration_minutes))
        
        # تقريب إلى منزلتين عشريتين
        return cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except Exception as e:
        logger.error(f"خطأ في حساب تكلفة الجلسة: {e}")
        return Decimal('0.00')

def validate_phone(phone: str) -> bool:
    """التحقق من صحة رقم الهاتف"""
    try:
        if not phone:
            return False
        
        # إزالة المسافات والرموز
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # التحقق من الطول
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            return False
        
        # التحقق من الأرقام المصرية
        if clean_phone.startswith('01') and len(clean_phone) == 11:
            return True
        elif clean_phone.startswith('1') and len(clean_phone) == 10:
            return True
        elif clean_phone.startswith('20') and len(clean_phone) == 12:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من رقم الهاتف: {e}")
        return False

def format_phone(phone: str) -> str:
    """تنسيق رقم الهاتف"""
    try:
        if not phone:
            return ""
        
        # إزالة المسافات والرموز
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # تنسيق رقم مصري
        if clean_phone.startswith('01') and len(clean_phone) == 11:
            return f"+20 {clean_phone[1:4]} {clean_phone[4:7]} {clean_phone[7:]}"
        elif clean_phone.startswith('1') and len(clean_phone) == 10:
            return f"+20 1{clean_phone[1:4]} {clean_phone[4:7]} {clean_phone[7:]}"
        elif clean_phone.startswith('20') and len(clean_phone) == 12:
            return f"+{clean_phone[:2]} {clean_phone[2:5]} {clean_phone[5:8]} {clean_phone[8:]}"
        
        return clean_phone
        
    except Exception as e:
        logger.error(f"خطأ في تنسيق رقم الهاتف: {e}")
        return phone

def parse_phone(phone: str) -> str:
    """تحليل رقم الهاتف إلى تنسيق موحد"""
    try:
        if not phone:
            return ""
        
        # إزالة المسافات والرموز
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # تحويل إلى تنسيق موحد
        if clean_phone.startswith('01') and len(clean_phone) == 11:
            return f"+20{clean_phone}"
        elif clean_phone.startswith('1') and len(clean_phone) == 10:
            return f"+201{clean_phone}"
        elif clean_phone.startswith('20') and len(clean_phone) == 12:
            return f"+{clean_phone}"
        
        return clean_phone
        
    except Exception as e:
        logger.error(f"خطأ في تحليل رقم الهاتف: {e}")
        return phone

def validate_email(email: str) -> bool:
    """التحقق من صحة البريد الإلكتروني"""
    try:
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من البريد الإلكتروني: {e}")
        return False

def sanitize_filename(filename: str) -> str:
    """تنظيف اسم الملف من الرموز الخطيرة"""
    try:
        if not filename:
            return "file"
        
        # إزالة الرموز الخطيرة
        dangerous_chars = r'[<>:"/\\|?*]'
        clean_filename = re.sub(dangerous_chars, '_', filename)
        
        # إزالة المسافات الزائدة
        clean_filename = re.sub(r'\s+', '_', clean_filename)
        
        # إزالة النقاط في البداية والنهاية
        clean_filename = clean_filename.strip('.')
        
        return clean_filename or "file"
        
    except Exception as e:
        logger.error(f"خطأ في تنظيف اسم الملف: {e}")
        return "file"

def generate_invoice_number(prefix: str = "INV") -> str:
    """إنشاء رقم فاتورة فريد"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}{timestamp}"
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء رقم الفاتورة: {e}")
        return f"{prefix}{int(datetime.now().timestamp())}"

def calculate_age(birth_date: datetime) -> int:
    """حساب العمر"""
    try:
        today = datetime.now()
        age = today.year - birth_date.year
        
        # التحقق من عيد الميلاد هذا العام
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
        
    except Exception as e:
        logger.error(f"خطأ في حساب العمر: {e}")
        return 0

def get_date_range(days: int) -> tuple:
    """الحصول على نطاق تاريخ"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على نطاق التاريخ: {e}")
        return datetime.now(), datetime.now()

def get_week_range() -> tuple:
    """الحصول على نطاق الأسبوع الحالي"""
    try:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return start_of_week, end_of_week
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على نطاق الأسبوع: {e}")
        return datetime.now(), datetime.now()

def get_month_range() -> tuple:
    """الحصول على نطاق الشهر الحالي"""
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # الحصول على آخر يوم في الشهر
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        
        end_of_month = next_month - timedelta(days=1)
        end_of_month = end_of_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return start_of_month, end_of_month
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على نطاق الشهر: {e}")
        return datetime.now(), datetime.now()

def round_to_nearest(value: Decimal, nearest: Decimal) -> Decimal:
    """تقريب القيمة إلى أقرب قيمة"""
    try:
        if nearest <= 0:
            return value
        
        return (value / nearest).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * nearest
        
    except Exception as e:
        logger.error(f"خطأ في التقريب: {e}")
        return value

def calculate_percentage(part: Decimal, total: Decimal) -> Decimal:
    """حساب النسبة المئوية"""
    try:
        if total <= 0:
            return Decimal('0.00')
        
        percentage = (part / total) * Decimal('100')
        return percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except Exception as e:
        logger.error(f"خطأ في حساب النسبة المئوية: {e}")
        return Decimal('0.00')

def format_percentage(percentage: Decimal) -> str:
    """تنسيق النسبة المئوية"""
    try:
        return f"{percentage}%"
    except Exception as e:
        logger.error(f"خطأ في تنسيق النسبة المئوية: {e}")
        return "0%"

def safe_divide(numerator: Decimal, denominator: Decimal, default: Decimal = Decimal('0.00')) -> Decimal:
    """قسمة آمنة مع تجنب القسمة على صفر"""
    try:
        if denominator <= 0:
            return default
        
        result = numerator / denominator
        return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
    except Exception as e:
        logger.error(f"خطأ في القسمة الآمنة: {e}")
        return default

def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """تحويل العملة (يحتاج إلى API حقيقي)"""
    try:
        # هذا مثال بسيط - في التطبيق الحقيقي تحتاج إلى API تحويل العملات
        exchange_rates = {
            'EGP': Decimal('30.00'),
            'JOD': Decimal('0.71'),
            'IQD': Decimal('1310.00'),
            'OMR': Decimal('0.38'),
            'SAR': Decimal('3.75'),
            'AED': Decimal('3.67'),
            'EUR': Decimal('0.85')
        }
        
        if from_currency == to_currency:
            return amount
        
        if from_currency in exchange_rates and to_currency in exchange_rates:
            # تحويل إلى EGP أولاً (العملة الأساسية)
            egp_amount = amount * exchange_rates[from_currency]
            # تحويل إلى العملة المطلوبة
            result = egp_amount / exchange_rates[to_currency]
            return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return amount
        
    except Exception as e:
        logger.error(f"خطأ في تحويل العملة: {e}")
        return amount

def generate_barcode() -> str:
    """إنشاء باركود عشوائي"""
    try:
        import random
        barcode = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        return barcode
    except Exception as e:
        logger.error(f"خطأ في إنشاء الباركود: {e}")
        return ""

def validate_barcode(barcode: str) -> bool:
    """التحقق من صحة الباركود"""
    try:
        if not barcode:
            return False
        
        # التحقق من أن الباركود يحتوي على أرقام فقط
        if not barcode.isdigit():
            return False
        
        # التحقق من الطول (12 أو 13 رقم)
        if len(barcode) not in [12, 13]:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من الباركود: {e}")
        return False

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """قطع النص إذا كان طويلاً"""
    try:
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
        
    except Exception as e:
        logger.error(f"خطأ في قطع النص: {e}")
        return text

def clean_text(text: str) -> str:
    """تنظيف النص من الرموز غير المرغوب فيها"""
    try:
        if not text:
            return ""
        
        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        
        # إزالة الرموز الخاصة
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', text)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"خطأ في تنظيف النص: {e}")
        return text
