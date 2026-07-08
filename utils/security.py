"""
نظام الأمان والتشفير
Security and Encryption System
"""

import hashlib
import secrets
import string
from typing import Optional
import logging
from datetime import datetime
import platform
import uuid
import os
import json
import base64
import time
import subprocess

logger = logging.getLogger(__name__)

def generate_salt(length: int = 32) -> str:
    """إنشاء ملح عشوائي للتشفير"""
    try:
        alphabet = string.ascii_letters + string.digits
        salt = ''.join(secrets.choice(alphabet) for _ in range(length))
        return salt
    except Exception as e:
        logger.error(f"خطأ في إنشاء الملح: {e}")
        return ""

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """تشفير كلمة المرور"""
    try:
        if salt is None:
            salt = generate_salt()
        
        # استخدام SHA-256 مع الملح
        password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        # إرجاع الهاش مع الملح
        return f"{salt}:{password_hash}"
        
    except Exception as e:
        logger.error(f"خطأ في تشفير كلمة المرور: {e}")
        return ""

def verify_password(password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    try:
        if ':' not in hashed_password:
            return False
        
        salt, stored_hash = hashed_password.split(':', 1)
        password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        
        return password_hash == stored_hash
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من كلمة المرور: {e}")
        return False

def generate_secure_token(length: int = 32) -> str:
    """إنشاء رمز أمان عشوائي"""
    try:
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        return token
    except Exception as e:
        logger.error(f"خطأ في إنشاء الرمز الأمني: {e}")
        return ""

def validate_password_strength(password: str) -> dict:
    """التحقق من قوة كلمة المرور"""
    result = {
        'valid': True,
        'score': 0,
        'issues': []
    }
    
    try:
        # طول كلمة المرور
        if len(password) < 8:
            result['issues'].append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
            result['valid'] = False
        else:
            result['score'] += 1
        
        # وجود أحرف كبيرة
        if not any(c.isupper() for c in password):
            result['issues'].append("يجب أن تحتوي على حرف كبير واحد على الأقل")
        else:
            result['score'] += 1
        
        # وجود أحرف صغيرة
        if not any(c.islower() for c in password):
            result['issues'].append("يجب أن تحتوي على حرف صغير واحد على الأقل")
        else:
            result['score'] += 1
        
        # وجود أرقام
        if not any(c.isdigit() for c in password):
            result['issues'].append("يجب أن تحتوي على رقم واحد على الأقل")
        else:
            result['score'] += 1
        
        # وجود رموز خاصة
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            result['issues'].append("يجب أن تحتوي على رمز خاص واحد على الأقل")
        else:
            result['score'] += 1
        
        # تحديد مستوى القوة
        if result['score'] >= 4:
            result['strength'] = 'قوي'
        elif result['score'] >= 3:
            result['strength'] = 'متوسط'
        elif result['score'] >= 2:
            result['strength'] = 'ضعيف'
        else:
            result['strength'] = 'ضعيف جداً'
            result['valid'] = False
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من قوة كلمة المرور: {e}")
        result['valid'] = False
        result['issues'].append("خطأ في التحقق من كلمة المرور")
    
    return result

def sanitize_input(text: str) -> str:
    """تنظيف النص المدخل من الرموز الخطيرة"""
    try:
        if not text:
            return ""
        
        # إزالة الرموز الخطيرة
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # إزالة المسافات الزائدة
        text = ' '.join(text.split())
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"خطأ في تنظيف النص: {e}")
        return ""

def validate_username(username: str) -> dict:
    """التحقق من صحة اسم المستخدم"""
    result = {
        'valid': True,
        'issues': []
    }
    
    try:
        if not username:
            result['valid'] = False
            result['issues'].append("اسم المستخدم مطلوب")
            return result
        
        # طول اسم المستخدم
        if len(username) < 3:
            result['valid'] = False
            result['issues'].append("اسم المستخدم يجب أن يكون 3 أحرف على الأقل")
        
        if len(username) > 50:
            result['valid'] = False
            result['issues'].append("اسم المستخدم يجب أن يكون أقل من 50 حرف")
        
        # الأحرف المسموحة
        allowed_chars = string.ascii_letters + string.digits + '_'
        if not all(c in allowed_chars for c in username):
            result['valid'] = False
            result['issues'].append("اسم المستخدم يمكن أن يحتوي على أحرف وأرقام و _ فقط")
        
        # يجب أن يبدأ بحرف
        if username and not username[0].isalpha():
            result['valid'] = False
            result['issues'].append("اسم المستخدم يجب أن يبدأ بحرف")
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من اسم المستخدم: {e}")
        result['valid'] = False
        result['issues'].append("خطأ في التحقق من اسم المستخدم")
    
    return result

def validate_phone_number(phone: str) -> dict:
    """التحقق من صحة رقم الهاتف"""
    result = {
        'valid': True,
        'issues': [],
        'formatted': phone
    }
    
    try:
        if not phone:
            result['valid'] = False
            result['issues'].append("رقم الهاتف مطلوب")
            return result
        
        # إزالة المسافات والرموز
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # التحقق من الطول
        if len(clean_phone) < 10:
            result['valid'] = False
            result['issues'].append("رقم الهاتف قصير جداً")
        elif len(clean_phone) > 15:
            result['valid'] = False
            result['issues'].append("رقم الهاتف طويل جداً")
        
        # تنسيق رقم الهاتف المصري
        if clean_phone.startswith('01') and len(clean_phone) == 11:
            result['formatted'] = f"+20{clean_phone}"
        elif clean_phone.startswith('1') and len(clean_phone) == 10:
            result['formatted'] = f"+201{clean_phone}"
        elif clean_phone.startswith('20') and len(clean_phone) == 12:
            result['formatted'] = f"+{clean_phone}"
        else:
            result['formatted'] = clean_phone
        
    except Exception as e:
        logger.error(f"خطأ في التحقق من رقم الهاتف: {e}")
        result['valid'] = False
        result['issues'].append("خطأ في التحقق من رقم الهاتف")
    
    return result

def encrypt_sensitive_data(data: str, key: str) -> str:
    """تشفير البيانات الحساسة"""
    try:
        # استخدام XOR بسيط للتشفير (يمكن تحسينه لاحقاً)
        encrypted = ""
        key_len = len(key)
        
        for i, char in enumerate(data):
            key_char = key[i % key_len]
            encrypted += chr(ord(char) ^ ord(key_char))
        
        # تحويل إلى base64
        import base64
        return base64.b64encode(encrypted.encode()).decode()
        
    except Exception as e:
        logger.error(f"خطأ في تشفير البيانات: {e}")
        return ""

def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """فك تشفير البيانات الحساسة"""
    try:
        # تحويل من base64
        import base64
        encrypted = base64.b64decode(encrypted_data.encode()).decode()
        
        # فك التشفير XOR
        decrypted = ""
        key_len = len(key)
        
        for i, char in enumerate(encrypted):
            key_char = key[i % key_len]
            decrypted += chr(ord(char) ^ ord(key_char))
        
        return decrypted
        
    except Exception as e:
        logger.error(f"خطأ في فك تشفير البيانات: {e}")
        return ""

def generate_session_id() -> str:
    """إنشاء معرف جلسة فريد"""
    try:
        import uuid
        return str(uuid.uuid4())
    except Exception as e:
        logger.error(f"خطأ في إنشاء معرف الجلسة: {e}")
        return generate_secure_token(32)

def validate_session_id(session_id: str) -> bool:
    """التحقق من صحة معرف الجلسة"""
    try:
        import uuid
        uuid.UUID(session_id)
        return True
    except:
        return False

def create_backup_key() -> str:
    """إنشاء مفتاح للنسخ الاحتياطية"""
    try:
        timestamp = str(int(time.time()))
        random_part = generate_secure_token(16)
        return f"backup_{timestamp}_{random_part}"
    except Exception as e:
        logger.error(f"خطأ في إنشاء مفتاح النسخة الاحتياطية: {e}")
        return generate_secure_token(32)

def log_security_event(event_type: str, user_id: Optional[int], details: str):
    """تسجيل حدث أمني"""
    try:
        logger.warning(f"Security Event - {event_type}: User {user_id} - {details}")
    except Exception as e:
        logger.error(f"خطأ في تسجيل الحدث الأمني: {e}")

class DeviceFingerprint:
    """نظام بصمة الجهاز لحماية البرنامج من النقل"""
    
    def __init__(self):
        try:
            from config import get_app_config
            app_config = get_app_config()
            
            self.fingerprint_file = app_config.get('security.device_fingerprint_file', 'config/device_fingerprint.json')
            self.encryption_key = app_config.get('security.device_protection_key', 'PS_DEVICE_PROTECTION_2024')
            self.protection_enabled = app_config.get('security.device_protection_enabled', True)
            self.allow_transfer = app_config.get('security.allow_device_transfer', False)
            self.mismatch_action = app_config.get('security.device_mismatch_action', 'block')
            
        except Exception as e:
            logger.error(f"خطأ في تحميل إعدادات حماية الجهاز: {e}")
            # إعدادات افتراضية في حالة الخطأ
            self.fingerprint_file = "config/device_fingerprint.json"
            self.encryption_key = "PS_DEVICE_PROTECTION_2024"
            self.protection_enabled = True
            self.allow_transfer = False
            self.mismatch_action = "block"
    
    def generate_device_fingerprint(self) -> str:
        """إنشاء بصمة الجهاز الحالية"""
        try:
            # جمع معلومات الجهاز
            device_info = {
                'machine_id': self._get_machine_id(),
                'platform': platform.system(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node(),
                'system_version': platform.version(),
                'python_version': platform.python_version(),
                'cpu_count': os.cpu_count(),
                'disk_serial': self._get_disk_serial(),
                'mac_address': self._get_mac_address(),
                'bios_serial': self._get_bios_serial()
            }
            
            # تحويل إلى JSON وتشفير
            device_json = json.dumps(device_info, sort_keys=True)
            encrypted_fingerprint = encrypt_sensitive_data(device_json, self.encryption_key)
            
            # إنشاء هاش من البصمة المشفرة
            fingerprint_hash = hashlib.sha256(encrypted_fingerprint.encode()).hexdigest()
            
            logger.info("تم إنشاء بصمة الجهاز بنجاح")
            return fingerprint_hash
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء بصمة الجهاز: {e}")
            return ""
    
    def _get_machine_id(self) -> str:
        """الحصول على معرف الجهاز"""
        try:
            if platform.system() == "Windows":
                # استخدام wmic للحصول على معرف الجهاز
                import subprocess
                result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line != 'UUID':
                            return line
            else:
                # استخدام /etc/machine-id على Linux
                try:
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                except:
                    pass
            
            # استخدام uuid.getnode() كبديل
            return str(uuid.getnode())
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معرف الجهاز: {e}")
            return str(uuid.getnode())
    
    def _get_disk_serial(self) -> str:
        """الحصول على الرقم التسلسلي للقرص الصلب"""
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line != 'SerialNumber':
                            return line
            else:
                # على Linux، استخدام lsblk أو fdisk
                import subprocess
                try:
                    result = subprocess.run(['lsblk', '-o', 'SERIAL'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            return lines[1].strip()
                except:
                    pass
            
            return "unknown_disk"
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على رقم القرص التسلسلي: {e}")
            return "unknown_disk"
    
    def _get_mac_address(self) -> str:
        """الحصول على عنوان MAC"""
        try:
            mac = uuid.getnode()
            return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except Exception as e:
            logger.error(f"خطأ في الحصول على عنوان MAC: {e}")
            return "unknown_mac"
    
    def _get_bios_serial(self) -> str:
        """الحصول على الرقم التسلسلي للـ BIOS"""
        try:
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(['wmic', 'bios', 'get', 'serialnumber'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line != 'SerialNumber':
                            return line
            else:
                # على Linux، استخدام dmidecode
                import subprocess
                try:
                    result = subprocess.run(['dmidecode', '-s', 'baseboard-serial-number'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    pass
            
            return "unknown_bios"
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على رقم BIOS التسلسلي: {e}")
            return "unknown_bios"
    
    def save_device_fingerprint(self, fingerprint: str) -> bool:
        """حفظ بصمة الجهاز"""
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.fingerprint_file), exist_ok=True)
            
            fingerprint_data = {
                'fingerprint': fingerprint,
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # تشفير البيانات قبل الحفظ
            encrypted_data = encrypt_sensitive_data(json.dumps(fingerprint_data), self.encryption_key)
            
            with open(self.fingerprint_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            logger.info(f"تم حفظ بصمة الجهاز في: {self.fingerprint_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حفظ بصمة الجهاز: {e}")
            return False
    
    def load_device_fingerprint(self) -> Optional[str]:
        """تحميل بصمة الجهاز المحفوظة"""
        try:
            if not os.path.exists(self.fingerprint_file):
                return None
            
            with open(self.fingerprint_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # فك تشفير البيانات
            decrypted_data = decrypt_sensitive_data(encrypted_data, self.encryption_key)
            fingerprint_data = json.loads(decrypted_data)
            
            return fingerprint_data.get('fingerprint')
            
        except Exception as e:
            logger.error(f"خطأ في تحميل بصمة الجهاز: {e}")
            return None
    
    def verify_device_fingerprint(self) -> dict:
        """التحقق من مطابقة بصمة الجهاز"""
        try:
            # التحقق من تفعيل نظام الحماية
            if not self.protection_enabled:
                logger.info("نظام حماية الجهاز معطل")
                return {
                    'valid': True,
                    'is_first_run': False,
                    'protection_disabled': True
                }
            
            # إنشاء بصمة الجهاز الحالية
            current_fingerprint = self.generate_device_fingerprint()
            
            # تحميل البصمة المحفوظة
            saved_fingerprint = self.load_device_fingerprint()
            
            if not current_fingerprint:
                return {
                    'valid': False,
                    'error': 'فشل في إنشاء بصمة الجهاز الحالية',
                    'is_first_run': False
                }
            
            if not saved_fingerprint:
                # هذا هو التشغيل الأول
                logger.info("التشغيل الأول - سيتم حفظ بصمة الجهاز")
                return {
                    'valid': True,
                    'is_first_run': True,
                    'fingerprint': current_fingerprint
                }
            
            # مقارنة البصمات
            if current_fingerprint == saved_fingerprint:
                logger.info("بصمة الجهاز مطابقة - التشغيل مسموح")
                return {
                    'valid': True,
                    'is_first_run': False,
                    'fingerprint': current_fingerprint
                }
            else:
                logger.warning("بصمة الجهاز غير مطابقة - تم نقل البرنامج!")
                log_security_event("DEVICE_MISMATCH", None, "تم نقل البرنامج إلى جهاز آخر")
                
                # التعامل مع عدم مطابقة البصمة حسب الإعدادات
                if self.allow_transfer:
                    logger.info("السماح بنقل البرنامج حسب الإعدادات")
                    return {
                        'valid': True,
                        'is_first_run': False,
                        'fingerprint': current_fingerprint,
                        'device_transferred': True
                    }
                elif self.mismatch_action == "warn":
                    logger.warning("تحذير من نقل البرنامج")
                    return {
                        'valid': True,
                        'is_first_run': False,
                        'fingerprint': current_fingerprint,
                        'warning': 'تم نقل البرنامج إلى جهاز آخر'
                    }
                else:  # block (افتراضي)
                    return {
                        'valid': False,
                        'error': 'تم نقل البرنامج إلى جهاز آخر',
                        'is_first_run': False,
                        'current_fingerprint': current_fingerprint,
                        'saved_fingerprint': saved_fingerprint
                    }
                
        except Exception as e:
            logger.error(f"خطأ في التحقق من بصمة الجهاز: {e}")
            return {
                'valid': False,
                'error': f'خطأ في التحقق من بصمة الجهاز: {str(e)}',
                'is_first_run': False
            }
    
    def initialize_device_protection(self) -> dict:
        """تهيئة نظام حماية الجهاز"""
        try:
            verification_result = self.verify_device_fingerprint()
            
            if not verification_result['valid']:
                return verification_result
            
            # التحقق من إيقاف نظام الحماية
            if verification_result.get('protection_disabled'):
                logger.info("نظام حماية الجهاز معطل - التشغيل مسموح")
                return {
                    'success': True,
                    'message': 'نظام حماية الجهاز معطل',
                    'is_first_run': False,
                    'protection_disabled': True
                }
            
            if verification_result['is_first_run']:
                # حفظ البصمة في التشغيل الأول
                if self.save_device_fingerprint(verification_result['fingerprint']):
                    logger.info("تم تهيئة نظام حماية الجهاز بنجاح")
                    return {
                        'success': True,
                        'message': 'تم تسجيل الجهاز بنجاح',
                        'is_first_run': True
                    }
                else:
                    return {
                        'success': False,
                        'error': 'فشل في حفظ بصمة الجهاز'
                    }
            else:
                # التحقق من نقل الجهاز
                if verification_result.get('device_transferred'):
                    logger.info("تم نقل البرنامج إلى جهاز جديد - مسموح حسب الإعدادات")
                    return {
                        'success': True,
                        'message': 'تم نقل البرنامج إلى جهاز جديد',
                        'is_first_run': False,
                        'device_transferred': True
                    }
                elif verification_result.get('warning'):
                    logger.warning(f"تحذير: {verification_result['warning']}")
                    return {
                        'success': True,
                        'message': 'الجهاز مسجل مسبقاً مع تحذير',
                        'is_first_run': False,
                        'warning': verification_result['warning']
                    }
                else:
                    logger.info("الجهاز مسجل مسبقاً - التشغيل مسموح")
                    return {
                        'success': True,
                        'message': 'الجهاز مسجل مسبقاً',
                        'is_first_run': False
                    }
                
        except Exception as e:
            logger.error(f"خطأ في تهيئة نظام حماية الجهاز: {e}")
            return {
                'success': False,
                'error': f'خطأ في تهيئة نظام حماية الجهاز: {str(e)}'
            }

# إنشاء مثيل عام لنظام بصمة الجهاز
device_fingerprint = DeviceFingerprint()
