"""
موديل الجلسات المحسن
Enhanced Session Model

⭐ إصلاحات مهمة:
-----------------
✅ إصلاح مشكلة حساب الوقت المتوقف عند استئناف الجلسة
   - عند إيقاف الجلسة ثم استئنافها، يتم الآن حساب الوقت الفعلي بشكل صحيح
   - الوقت المتوقف لا يُحسب ضمن الوقت المنقضي أو التكلفة
   
🔧 التحسينات:
   1. resume_session: تحويل آمن للتواريخ من قاعدة البيانات مع معالجة شاملة للأخطاء
   2. get_session_time_info: حساب دقيق للوقت المنقضي مع خصم الوقت المتوقف
   3. دعم جميع تنسيقات التواريخ: ISO format, SQLite format with/without microseconds
   
📊 آلية العمل:
   - عند الإيقاف: يُحفظ وقت الإيقاف في paused_at
   - عند الاستئناف: يُحسب الفرق ويُضاف إلى total_paused_duration
   - عند حساب الوقت: الوقت الفعلي = (الوقت الإجمالي - الوقت المتوقف)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

def format_time_detailed(hours: int, minutes: int, seconds: int) -> str:
    """تنسيق الوقت بالتفصيل - الساعات على اليسار والدقائق في الوسط والثواني على اليمين"""
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_time_remaining(hours: int, minutes: int, seconds: int) -> str:
    """تنسيق الوقت المتبقي - الساعات على اليسار والدقائق في الوسط والثواني على اليمين"""
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

class SessionModel:
    """موديل إدارة الجلسات المحسن"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_session(self, device_id: int, cashier_id: int, shift_id: int, 
                      pricing_type: str, session_price: Decimal, 
                      time_type: str, duration_minutes: Optional[int] = None,
                      customer_phone: str = None) -> Optional[int]:
        """إنشاء جلسة جديدة"""
        try:
            # تحديد وقت البداية والنهاية
            start_time = datetime.now()
            end_time = None
            
            if time_type == 'fixed' and duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
            
            # إنشاء الجلسة
            session_data = {
                'device_id': device_id,
                'cashier_id': cashier_id,
                'shift_id': shift_id,
                'pricing_type': pricing_type,
                'session_price': float(session_price),  # تحويل Decimal إلى float
                'time_type': time_type,  # 'fixed' أو 'open'
                'duration_minutes': duration_minutes,
                'start_time': start_time,
                'end_time': end_time,
                'status': 'active',
                'is_paused': False,
                'paused_at': None,
                'total_paused_duration': 0,
                'customer_phone': customer_phone
            }
            
            session_id = self.db.execute_query(
                """INSERT INTO sessions (device_id, cashier_id, shift_id, pricing_type, 
                   session_price, time_type, duration_minutes, start_time, end_time, 
                   status, is_paused, paused_at, total_paused_duration, customer_phone) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                tuple(session_data.values()),
                fetch=False
            )
            
            if session_id:
                # إنشاء جزء التسعيرة الأول
                from models.pricing_segment_model import PricingSegmentModel
                pricing_model = PricingSegmentModel()
                pricing_model.create_pricing_segment(
                    session_id=session_id,
                    pricing_type=pricing_type,
                    session_price=session_price,
                    start_time=start_time
                )
            
            logger.info(f"تم إنشاء جلسة جديدة: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الجلسة: {e}")
            return None
    
    def get_active_session(self, device_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على الجلسة النشطة أو المتوقفة للجهاز"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.device_id = ? AND s.status IN ('active', 'paused')
                   ORDER BY s.start_time DESC LIMIT 1""",
                (device_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسة النشطة: {e}")
            return None
    
    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        الحصول على جلسة بالمعرف
        ⭐ مع AutoCommit mode، هذه الدالة تقرأ أحدث البيانات مباشرة من قاعدة البيانات
        """
        try:
            # ⭐ قراءة مباشرة من قاعدة البيانات - تحصل على أحدث الحالة بفضل AutoCommit
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.id = ?""",
                (session_id,)
            )
            
            if result:
                session = result[0]
                # تسجيل حالة الجلسة للتشخيص
                logger.debug(f"📖 قراءة الجلسة {session_id}: status={session.get('status')}, is_paused={session.get('is_paused')}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسة: {e}")
            return None
    
    def end_session(self, session_id: int, cashier_id: int, notes: str = "") -> bool:
        """إنهاء الجلسة"""
        try:
            # التحقق من وجود الجلسة
            session = self.get_session_by_id(session_id)
            if not session:
                logger.error(f"الجلسة {session_id} غير موجودة")
                return False
            
            if session['status'] != 'active':
                logger.warning(f"الجلسة {session_id} غير نشطة")
                return False
            
            # إنهاء الجزء النشط من التسعيرة قبل إنهاء الجلسة
            try:
                from models.pricing_segment_model import PricingSegmentModel
                pricing_model = PricingSegmentModel()
                
                # الحصول على الجزء النشط
                active_segment = pricing_model.get_active_segment(session_id)
                if active_segment:
                    # إنهاء الجزء النشط
                    end_time = datetime.now()
                    pricing_model.end_pricing_segment(active_segment['id'], end_time)
                    logger.info(f"تم إنهاء الجزء النشط من التسعيرة {active_segment['id']} للجلسة {session_id}")
                    
            except Exception as pricing_error:
                logger.warning(f"خطأ في إنهاء جزء التسعيرة النشط: {pricing_error}")
                # لا نوقف عملية إنهاء الجلسة بسبب هذا الخطأ
            
            # إنهاء الجلسة
            end_time = datetime.now()
            result = self.db.execute_query(
                """UPDATE sessions SET end_time = ?, status = ?, notes = ? WHERE id = ?""",
                (end_time, 'completed', notes, session_id),
                fetch=False
            )
            
            if result:
                logger.info(f"تم إنهاء الجلسة {session_id}")
                return True
            else:
                logger.error(f"فشل في إنهاء الجلسة {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في إنهاء الجلسة: {e}")
            return False
    
    def get_session_time_info(self, session_id: int) -> Dict[str, Any]:
        """الحصول على معلومات الوقت للجلسة"""
        try:
            
            session = self.get_session_by_id(session_id)
            if not session:
                return {}
            
            # ⭐ تحويل start_time بطريقة آمنة
            start_time = session['start_time']
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            
            current_time = datetime.now()
            
            # ⭐ إصلاح حاسم: التحقق الصارم من حالة الإيقاف
            # التحقق المزدوج: إما status=='paused' أو is_paused==True
            is_session_paused = (session.get('status') == 'paused') or (session.get('is_paused', False) == True)
            
            # ⭐⭐⭐ قراءة مباشرة ULTRA من قاعدة البيانات مع تجاوز أي cache ⭐⭐⭐
            # نستخدم استعلام خام مباشر للتأكد من عدم وجود أي caching
            try:
                # ⭐ إجبار commit لضمان flush في WAL mode ⭐
                try:
                    self.db.connection.commit()
                except:
                    pass
                
                # الوصول المباشر للاتصال وتنفيذ الاستعلام
                import sqlite3
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "SELECT total_paused_duration, status, is_paused, paused_at FROM sessions WHERE id = ?",
                    (session_id,)
                )
                db_row = cursor.fetchone()
                
                if db_row:
                    # قراءة القيم مباشرة من الصف
                    db_total_paused_duration = db_row[0] if db_row[0] is not None else 0
                    db_status = db_row[1]
                    db_is_paused = bool(db_row[2])
                    db_paused_at = db_row[3]
                    
                    logger.info(f"📖 قراءة مباشرة RAW من DB للجلسة {session_id}:")
                    logger.info(f"   - total_paused_duration: {db_total_paused_duration} ثانية")
                    logger.info(f"   - status: {db_status}")
                    logger.info(f"   - is_paused: {db_is_paused}")
                    
                    # تحديث القيم في session object
                    session['total_paused_duration'] = db_total_paused_duration
                    session['status'] = db_status
                    session['is_paused'] = db_is_paused
                    session['paused_at'] = db_paused_at
                    
                    # تحديث حالة التوقف
                    is_session_paused = (db_status == 'paused') or db_is_paused
                else:
                    logger.warning(f"⚠️ لم يتم العثور على الجلسة {session_id} في القراءة المباشرة")
            except Exception as db_error:
                logger.error(f"❌ خطأ في القراءة المباشرة من DB: {db_error}")
            
            # إصلاح جذري: تحديد الوقت المرجعي بناءً على حالة الجلسة
            if is_session_paused and session.get('paused_at'):
                # ⭐⭐ الجلسة متوقفة - استخدم وقت الإيقاف كمرجع (بدون استثناءات!)
                paused_at = session['paused_at']
                if isinstance(paused_at, str):
                    try:
                        paused_at = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S')
                reference_time = paused_at
                logger.debug(f"🛑 الجلسة {session_id} متوقفة - استخدام وقت الإيقاف الثابت: {paused_at}")
                logger.debug(f"🛑 status={session.get('status')}, is_paused={session.get('is_paused')}")
            else:
                # الجلسة نشطة - استخدم الوقت الحالي كمرجع
                reference_time = current_time
                logger.debug(f"▶️ الجلسة {session_id} نشطة - استخدام الوقت الحالي كمرجع: {current_time}")
            
            # حساب الوقت المنقضي بالتفصيل باستخدام الوقت المرجعي
            elapsed_time = reference_time - start_time
            total_seconds = int(elapsed_time.total_seconds())
            
            # ⭐⭐⭐ إصلاح حاسم: خصم الوقت المتوقف بشكل صحيح ⭐⭐⭐
            # نحصل على total_paused_duration من session (الذي تم تحديثه من القراءة المباشرة)
            total_paused_duration = session.get('total_paused_duration', 0)
            
            logger.debug(f"📊 الجلسة {session_id} - حساب الوقت:")
            logger.debug(f"   - start_time: {start_time}")
            logger.debug(f"   - reference_time: {reference_time}")
            logger.debug(f"   - الوقت الإجمالي: {total_seconds} ثانية ({total_seconds / 60:.2f} دقيقة)")
            logger.debug(f"   - total_paused_duration (محدث من DB): {total_paused_duration} ثانية ({total_paused_duration / 60:.2f} دقيقة)")
            
            # ملاحظة مهمة: لا نحتاج لإضافة مدة توقف إضافية هنا!
            # عند إيقاف الجلسة: reference_time = paused_at (لا يتقدم الوقت)
            # عند استئناف الجلسة: total_paused_duration يتم تحديثه في resume_session
            # عند الجلسة النشطة: reference_time = current_time و total_paused_duration من DB
            
            # حساب الوقت الفعلي (بدون الوقت المتوقف)
            actual_elapsed_seconds = max(0, total_seconds - total_paused_duration)
            
            logger.debug(f"   - الوقت الفعلي (بعد خصم التوقف): {actual_elapsed_seconds} ثانية ({actual_elapsed_seconds / 60:.2f} دقيقة)")
            
            # حساب الساعات والدقائق والثواني
            elapsed_hours = actual_elapsed_seconds // 3600
            elapsed_minutes = (actual_elapsed_seconds % 3600) // 60
            elapsed_seconds = actual_elapsed_seconds % 60
            
            time_info = {
                'session_id': session_id,
                'time_type': session['time_type'],
                'start_time': start_time,
                'elapsed_total_seconds': actual_elapsed_seconds,
                'elapsed_hours': elapsed_hours,
                'elapsed_minutes': elapsed_minutes,
                'elapsed_seconds': elapsed_seconds,
                'elapsed_minutes_total': int(actual_elapsed_seconds / 60),  # للتوافق مع الكود القديم
                'status': session['status'],
                'is_paused': session.get('is_paused', False),
                'total_paused_duration': total_paused_duration
            }
            
            if session['time_type'] == 'fixed' and session['duration_minutes']:
                # جلسة بوقت محدد
                duration_minutes = session['duration_minutes']
                duration_total_seconds = duration_minutes * 60
                
                # ⭐⭐⭐ حساب الوقت المتبقي بشكل صحيح ⭐⭐⭐
                remaining_total_seconds = max(0, duration_total_seconds - actual_elapsed_seconds)
                
                # ⭐⭐⭐ إذا انتهى الوقت أو تجاوزه، حدد الوقت المنقضي عند المدة المحددة ⭐⭐⭐
                if actual_elapsed_seconds >= duration_total_seconds:
                    # انتهى الوقت - حدد الوقت عند المدة المحددة فقط
                    actual_elapsed_seconds = duration_total_seconds
                    remaining_total_seconds = 0
                    
                    # إعادة حساب الساعات والدقائق والثواني
                    elapsed_hours = actual_elapsed_seconds // 3600
                    elapsed_minutes = (actual_elapsed_seconds % 3600) // 60
                    elapsed_seconds = actual_elapsed_seconds % 60
                    
                    logger.info(f"⏰ انتهى الوقت المحدد للجلسة {session_id}!")
                    logger.info(f"   - الوقت المحدد: {duration_total_seconds}s ({duration_minutes} دقيقة)")
                    logger.info(f"   - تم تحديد الوقت المنقضي عند: {actual_elapsed_seconds}s")
                    
                    # تحديث time_info بالوقت المحدد فقط
                    time_info.update({
                        'elapsed_total_seconds': actual_elapsed_seconds,
                        'elapsed_hours': elapsed_hours,
                        'elapsed_minutes': elapsed_minutes,
                        'elapsed_seconds': elapsed_seconds,
                        'elapsed_minutes_total': int(actual_elapsed_seconds / 60),
                    })
                
                # حساب الوقت المتبقي بالتفصيل
                remaining_hours = remaining_total_seconds // 3600
                remaining_minutes = (remaining_total_seconds % 3600) // 60
                remaining_seconds = remaining_total_seconds % 60
                
                time_info.update({
                    'duration_minutes': duration_minutes,
                    'duration_total_seconds': duration_total_seconds,
                    'remaining_total_seconds': remaining_total_seconds,
                    'remaining_hours': remaining_hours,
                    'remaining_minutes': remaining_minutes,
                    'remaining_seconds': remaining_seconds,
                    'remaining_minutes_total': int(remaining_total_seconds / 60),  # للتوافق مع الكود القديم
                    'is_expired': remaining_total_seconds <= 0,
                    'is_warning': 0 < remaining_total_seconds <= 300,  # تحذير آخر 5 دقائق (300 ثانية)
                    'end_time': session['end_time'],
                    # تنسيق الوقت المفصل
                    'elapsed_time_formatted': format_time_detailed(elapsed_hours, elapsed_minutes, elapsed_seconds),
                    'remaining_time_formatted': format_time_remaining(remaining_hours, remaining_minutes, remaining_seconds)
                })
            else:
                # جلسة بوقت مفتوح
                time_info.update({
                    'duration_minutes': None,
                    'remaining_minutes': None,
                    'is_expired': False,
                    'is_warning': False,
                    'end_time': None,
                    # تنسيق الوقت المفصل للجلسة المفتوحة
                    'elapsed_time_formatted': format_time_detailed(elapsed_hours, elapsed_minutes, elapsed_seconds)
                })
            
            return time_info
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات الوقت: {e}")
            return {}
    
    def calculate_session_cost(self, session_id: int) -> Dict[str, Any]:
        """حساب تكلفة الجلسة مع النظام المتقدم"""
        try:
            from models.pricing_segment_model import PricingSegmentModel
            
            session = self.get_session_by_id(session_id)
            if not session:
                return None
            
            # ⭐⭐⭐ قراءة مباشرة RAW لـ total_paused_duration للتأكد المطلق ⭐⭐⭐
            try:
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "SELECT total_paused_duration FROM sessions WHERE id = ?",
                    (session_id,)
                )
                db_row = cursor.fetchone()
                if db_row and db_row[0] is not None:
                    session['total_paused_duration'] = db_row[0]
                    logger.info(f"💰 قراءة مباشرة: total_paused_duration = {db_row[0]} ثانية")
            except Exception as e:
                logger.error(f"خطأ في القراءة المباشرة: {e}")
            
            # ⭐ تحقق صارم: إذا كانت الجلسة متوقفة، سجل ذلك
            is_session_paused = (session.get('status') == 'paused') or (session.get('is_paused', False) == True)
            if is_session_paused:
                logger.info(f"💰 حساب تكلفة الجلسة {session_id} - الجلسة متوقفة، التكلفة ثابتة")
                logger.info(f"💰 status={session.get('status')}, is_paused={session.get('is_paused')}")
            
            # الحصول على ملخص التسعيرة المتقدمة
            pricing_model = PricingSegmentModel()
            pricing_summary = pricing_model.get_session_pricing_summary(session_id)
            
            if not pricing_summary:
                # إذا لم توجد أجزاء تسعيرة، استخدم الطريقة القديمة
                time_info = self.get_session_time_info(session_id)
                if not time_info:
                    return None
                
                session_price = session.get('session_price', 0)
                time_type = session.get('time_type', 'fixed')
                
                if time_type == 'fixed':
                    elapsed_minutes = time_info.get('elapsed_minutes_total', 0)
                    duration_minutes = session.get('duration_minutes', 1)
                    cost_per_minute = session_price / 60
                    is_expired = time_info.get('is_expired', False)
                    
                    # إصلاح المشكلة الأولى: إذا انتهى الوقت، استخدم فقط الوقت المحدد
                    if is_expired:
                        billable_minutes = duration_minutes  # استخدم فقط الوقت المحدد
                        total_cost = billable_minutes * cost_per_minute
                    else:
                        billable_minutes = min(elapsed_minutes, duration_minutes)
                        total_cost = billable_minutes * cost_per_minute
                    
                    cost_info = {
                        'session_id': session_id,
                        'time_type': time_type,
                        'session_price': session_price,
                        'total_cost': total_cost,
                        'cost_per_minute': cost_per_minute,
                        'elapsed_minutes': elapsed_minutes,
                        'billable_minutes': billable_minutes,
                        'duration_minutes': duration_minutes,
                        'remaining_minutes': time_info.get('remaining_minutes_total', 0),
                        'is_expired': is_expired,
                        'cost_breakdown': f"الوقت المحتسب: {billable_minutes} دقيقة × {cost_per_minute:.2f} جنيه/دقيقة = {total_cost:.2f} جنيه" + (" (انتهى الوقت المحدد)" if is_expired else ""),
                        'pricing_summary': pricing_summary
                    }
                else:
                    elapsed_minutes = time_info.get('elapsed_minutes_total', 0)
                    cost_per_minute = session_price / 60
                    total_cost = elapsed_minutes * cost_per_minute
                    
                    cost_info = {
                        'session_id': session_id,
                        'time_type': time_type,
                        'session_price': session_price,
                        'total_cost': total_cost,
                        'cost_per_minute': cost_per_minute,
                        'elapsed_minutes': elapsed_minutes,
                        'remaining_minutes': None,
                        'cost_breakdown': f"الوقت المنقضي: {elapsed_minutes} دقيقة × {cost_per_minute:.2f} جنيه/دقيقة = {total_cost:.2f} جنيه",
                        'pricing_summary': pricing_summary
                    }
            else:
                # استخدام النظام المتقدم
                cost_info = {
                    'session_id': session_id,
                    'time_type': session.get('time_type', 'fixed'),
                    'total_cost': pricing_summary['total_cost'],
                    'total_duration': pricing_summary['total_duration'],
                    'total_hours': pricing_summary['total_hours'],
                    'single_cost': pricing_summary['total_single_cost'],
                    'multi_cost': pricing_summary['total_multi_cost'],
                    'single_hours': pricing_summary['total_single_hours'],
                    'multi_hours': pricing_summary['total_multi_hours'],
                    'single_segments': pricing_summary['single_segments'],
                    'multi_segments': pricing_summary['multi_segments'],
                    'pricing_summary': pricing_summary,
                    'cost_breakdown': self._create_advanced_cost_breakdown(pricing_summary)
                }
            
            return cost_info
            
        except Exception as e:
            logger.error(f"خطأ في حساب تكلفة الجلسة: {e}")
            return None
    
    def _create_advanced_cost_breakdown(self, pricing_summary: Dict[str, Any]) -> str:
        """إنشاء تفصيل التكلفة المتقدم"""
        try:
            breakdown = []
            
            if pricing_summary['total_single_cost'] > 0:
                breakdown.append(f"فردي: {pricing_summary['total_single_hours']:.2f} ساعة = {pricing_summary['total_single_cost']:.2f} جنيه")
            
            if pricing_summary['total_multi_cost'] > 0:
                breakdown.append(f"جماعي: {pricing_summary['total_multi_hours']:.2f} ساعة = {pricing_summary['total_multi_cost']:.2f} جنيه")
            
            if breakdown:
                breakdown.append(f"المجموع: {pricing_summary['total_cost']:.2f} جنيه")
                return " | ".join(breakdown)
            else:
                return "لا توجد تكلفة محسوبة"
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء تفصيل التكلفة: {e}")
            return "خطأ في حساب التكلفة"
    
    def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الجلسات النشطة والمتوقفة"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.status IN ('active', 'paused')
                   ORDER BY s.start_time DESC"""
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسات النشطة: {e}")
            return []
    
    def get_sessions_by_shift(self, shift_id: int) -> List[Dict[str, Any]]:
        """الحصول على جلسات الوردية"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.shift_id = ?
                   ORDER BY s.start_time DESC""",
                (shift_id,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جلسات الوردية: {e}")
            return []
    
    def get_session_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """الحصول على إحصائيات الجلسات"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_sessions,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions,
                    SUM(CASE WHEN time_type = 'fixed' THEN 1 ELSE 0 END) as fixed_time_sessions,
                    SUM(CASE WHEN time_type = 'open' THEN 1 ELSE 0 END) as open_time_sessions,
                    COALESCE(SUM(session_price), 0) as total_revenue
                FROM sessions
            """
            
            params = []
            if start_date:
                query += " WHERE start_time >= ?"
                params.append(start_date)
            if end_date:
                if start_date:
                    query += " AND start_time <= ?"
                else:
                    query += " WHERE start_time <= ?"
                params.append(end_date)
            
            result = self.db.execute_query(query, tuple(params) if params else None)
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات الجلسات: {e}")
            return {}
    
    def update_session_duration(self, session_id: int, new_duration_minutes: int) -> bool:
        """تحديث مدة الجلسة (للساعات المفتوحة)"""
        try:
            session = self.get_session_by_id(session_id)
            if not session or session['time_type'] != 'open':
                return False
            
            # تحديث المدة
            result = self.db.execute_query(
                """UPDATE sessions SET duration_minutes = ? WHERE id = ?""",
                (new_duration_minutes, session_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث مدة الجلسة: {e}")
            return False
    
    def extend_session(self, session_id: int, additional_minutes: int) -> bool:
        """تمديد الجلسة (للساعات المحددة)"""
        try:
            session = self.get_session_by_id(session_id)
            if not session or session['time_type'] != 'fixed':
                return False
            
            # تحديث المدة والوقت النهائي
            new_duration = session['duration_minutes'] + additional_minutes
            start_time = session['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            new_end_time = start_time + timedelta(minutes=new_duration)
            
            result = self.db.execute_query(
                """UPDATE sessions SET duration_minutes = ?, end_time = ? WHERE id = ?""",
                (new_duration, new_end_time, session_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تمديد الجلسة: {e}")
            return False
    
    def pause_session(self, session_id: int) -> bool:
        """إيقاف الجلسة مؤقتاً"""
        try:
            session = self.get_session_by_id(session_id)
            if not session or session['status'] != 'active':
                logger.warning(f"فشل في إيقاف الجلسة {session_id}: الجلسة غير موجودة أو غير نشطة")
                return False
            
            if session.get('is_paused', False):
                logger.warning(f"الجلسة {session_id} متوقفة بالفعل")
                return False  # الجلسة متوقفة بالفعل
            
            # إيقاف جزء التسعيرة النشط
            try:
                from models.pricing_segment_model import PricingSegmentModel
                pricing_model = PricingSegmentModel()
                
                # الحصول على الجزء النشط
                active_segment = pricing_model.get_active_segment(session_id)
                if active_segment:
                    # إيقاف الجزء النشط
                    pricing_model.pause_pricing_segment(active_segment['id'])
                    logger.info(f"تم إيقاف جزء التسعيرة النشط {active_segment['id']} للجلسة {session_id}")
                    
            except Exception as pricing_error:
                logger.warning(f"خطأ في إيقاف جزء التسعيرة النشط: {pricing_error}")
                # لا نوقف عملية إيقاف الجلسة بسبب هذا الخطأ
            
            # تحديث حالة الجلسة - مع تسجيل مفصل
            pause_time = datetime.now()
            logger.info(f"🛑 إيقاف الجلسة {session_id} في الوقت: {pause_time}")
            
            result = self.db.execute_query(
                """UPDATE sessions SET is_paused = ?, paused_at = ?, status = ? WHERE id = ?""",
                (True, pause_time, 'paused', session_id),
                fetch=False
            )
            
            # التحقق الفوري من نجاح التحديث
            if result:
                # قراءة فورية للتحقق من أن التحديث تم
                import time
                time.sleep(0.05)  # انتظار 50 ميلي ثانية للتأكد من commit في exe
                
                verification = self.get_session_by_id(session_id)
                if verification:
                    logger.info(f"✅ تم التحقق من إيقاف الجلسة {session_id}: status={verification.get('status')}, is_paused={verification.get('is_paused')}")
                    
                    # إذا لم يتم التحديث بشكل صحيح، حاول مرة أخرى
                    if verification.get('status') != 'paused' or not verification.get('is_paused'):
                        logger.warning(f"⚠️ التحديث لم يتم بشكل صحيح، محاولة ثانية...")
                        self.db.execute_query(
                            """UPDATE sessions SET is_paused = 1, paused_at = ?, status = 'paused' WHERE id = ?""",
                            (pause_time, session_id),
                            fetch=False
                        )
                        time.sleep(0.05)
                        verification = self.get_session_by_id(session_id)
                        logger.info(f"🔄 بعد المحاولة الثانية: status={verification.get('status')}, is_paused={verification.get('is_paused')}")
                
                return True
            else:
                logger.error(f"❌ فشل في تحديث حالة الجلسة {session_id}")
                return False
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسة: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def resume_session(self, session_id: int) -> bool:
        """استئناف الجلسة - مع إصلاح EXE الكامل"""
        try:
            session = self.get_session_by_id(session_id)
            if not session or session['status'] != 'paused':
                logger.warning(f"فشل في استئناف الجلسة {session_id}: الجلسة غير موجودة أو غير متوقفة")
                return False
            
            if not session.get('is_paused', False):
                logger.warning(f"الجلسة {session_id} ليست متوقفة (is_paused = False)")
                return False  # الجلسة غير متوقفة
            
            # استئناف جزء التسعيرة المتوقف
            try:
                from models.pricing_segment_model import PricingSegmentModel
                pricing_model = PricingSegmentModel()
                
                # الحصول على الجزء المتوقف
                active_segment = pricing_model.get_active_segment(session_id)
                
                logger.info(f"🔍 البحث عن جزء تسعيرة نشط للجلسة {session_id}:")
                if active_segment:
                    logger.info(f"   - وُجد جزء {active_segment['id']}: is_paused={active_segment.get('is_paused')}, paused_duration={active_segment.get('paused_duration_seconds', 0)}s")
                else:
                    logger.info(f"   - لم يُوجد جزء نشط")
                
                if active_segment and active_segment.get('is_paused', False):
                    # استئناف الجزء المتوقف
                    logger.info(f"▶️ استئناف جزء التسعيرة المتوقف {active_segment['id']}")
                    success = pricing_model.resume_pricing_segment(active_segment['id'])
                    
                    if success:
                        logger.info(f"✅ تم استئناف جزء التسعيرة {active_segment['id']} بنجاح")
                        
                        # ⭐⭐⭐ تأخير إضافي وتحقق RAW من التحديث ⭐⭐⭐
                        import time
                        time.sleep(0.2)  # 200ms للتأكد من commit كامل لجدول pricing_segments
                        
                        # تحقق RAW من أن paused_duration تم تحديثه
                        try:
                            cursor = self.db.connection.cursor()
                            cursor.execute(
                                "SELECT paused_duration_seconds FROM pricing_segments WHERE id = ?",
                                (active_segment['id'],)
                            )
                            check_row = cursor.fetchone()
                            if check_row:
                                final_paused_duration = check_row[0] if check_row[0] is not None else 0
                                logger.info(f"📖 تحقق RAW من جزء التسعيرة {active_segment['id']}: paused_duration={final_paused_duration}s")
                                
                                # ⭐⭐⭐ إذا لم تُحدث، محاولة قوية لإجبار التحديث ⭐⭐⭐
                                if final_paused_duration == 0:
                                    logger.error(f"❌❌ CRITICAL: paused_duration لا يزال 0 بعد الاستئناف!")
                                    logger.error(f"   سنحاول إجبار التحديث...")
                                    
                                    # إعادة قراءة الجزء القديم لحساب القيمة الصحيحة
                                    cursor.execute("SELECT paused_at, paused_duration_seconds FROM pricing_segments WHERE id = ?", (active_segment['id'],))
                                    old_data = cursor.fetchone()
                                    
                                    if old_data and old_data[0]:
                                        # حساب القيمة الصحيحة
                                        old_paused_at = old_data[0]
                                        old_paused_duration = old_data[1] if old_data[1] else 0
                                        
                                        if isinstance(old_paused_at, str):
                                            try:
                                                old_paused_at = datetime.fromisoformat(old_paused_at.replace('Z', '+00:00'))
                                            except:
                                                try:
                                                    old_paused_at = datetime.strptime(old_paused_at, '%Y-%m-%d %H:%M:%S.%f')
                                                except:
                                                    old_paused_at = datetime.strptime(old_paused_at, '%Y-%m-%d %H:%M:%S')
                                        
                                        correct_pause_duration = int((datetime.now() - old_paused_at).total_seconds())
                                        correct_total = old_paused_duration + correct_pause_duration
                                        
                                        logger.info(f"🔧 إجبار التحديث: القيمة الصحيحة = {correct_total}s")
                                        
                                        # تحديث قوي
                                        for force_attempt in range(3):
                                            self.db.execute_query(
                                                """UPDATE pricing_segments SET paused_duration_seconds = ?, paused_at = NULL, is_paused = 0 WHERE id = ?""",
                                                (correct_total, active_segment['id']),
                                                fetch=False
                                            )
                                            self.db.connection.commit()
                                            time.sleep(0.1)
                                            
                                            # تحقق
                                            cursor.execute("SELECT paused_duration_seconds FROM pricing_segments WHERE id = ?", (active_segment['id'],))
                                            final_check = cursor.fetchone()
                                            if final_check and final_check[0] == correct_total:
                                                logger.info(f"✅ إجبار التحديث نجح في المحاولة {force_attempt + 1}")
                                                break
                        except Exception as check_error:
                            logger.error(f"❌ خطأ في التحقق من جزء التسعيرة: {check_error}")
                    else:
                        logger.error(f"❌ فشل في استئناف جزء التسعيرة {active_segment['id']}")
                else:
                    # إنشاء جزء جديد للتسعيرة
                    logger.info(f"🆕 إنشاء جزء تسعيرة جديد للجلسة {session_id}")
                    pricing_model.create_pricing_segment(
                        session_id=session_id,
                        pricing_type=session['pricing_type'],
                        session_price=session['session_price']
                    )
                    logger.info(f"✅ تم إنشاء جزء تسعيرة جديد للجلسة {session_id}")
                    
            except Exception as pricing_error:
                logger.warning(f"خطأ في استئناف جزء التسعيرة: {pricing_error}")
                import traceback
                traceback.print_exc()
                # لا نوقف عملية استئناف الجلسة بسبب هذا الخطأ
            
            # ⭐⭐⭐ إصلاح حاسم: حساب مدة التوقف بشكل صحيح ⭐⭐⭐
            paused_at = session.get('paused_at')
            if paused_at:
                # تحويل paused_at إلى datetime بطريقة آمنة
                if isinstance(paused_at, str):
                    try:
                        # محاولة التحويل باستخدام fromisoformat أولاً
                        paused_at = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                    except ValueError:
                        # إذا فشل، جرب تنسيق SQLite القياسي
                        try:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            try:
                                paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                logger.error(f"فشل في تحويل paused_at: {paused_at}")
                                paused_at = None
                
                if paused_at:
                    # حساب مدة التوقف الحالية
                    resume_time = datetime.now()
                    current_pause_duration = int((resume_time - paused_at).total_seconds())
                    total_paused_duration = session.get('total_paused_duration', 0) + current_pause_duration
                    
                    logger.info(f"🔄 استئناف الجلسة {session_id}:")
                    logger.info(f"   - وقت الإيقاف: {paused_at}")
                    logger.info(f"   - وقت الاستئناف: {resume_time}")
                    logger.info(f"   - مدة التوقف الحالية: {current_pause_duration} ثانية ({current_pause_duration / 60:.2f} دقيقة)")
                    logger.info(f"   - مدة التوقف السابقة: {session.get('total_paused_duration', 0)} ثانية")
                    logger.info(f"   - مدة التوقف الإجمالية: {total_paused_duration} ثانية ({total_paused_duration / 60:.2f} دقيقة)")
                    
                    # ⭐ إصلاح EXE محسّن: تحديث مع commit وتحقق سريع ⭐
                    import time
                    
                    # تحديث مع commit صريح
                    result = self.db.execute_query(
                        """UPDATE sessions SET is_paused = 0, paused_at = NULL, 
                           total_paused_duration = ?, status = 'active' WHERE id = ?""",
                        (total_paused_duration, session_id),
                        fetch=False
                    )
                    
                    # commit صريح
                    try:
                        if self.db.connection:
                            self.db.connection.commit()
                            logger.info(f"✅ Committed resume for session {session_id}")
                    except Exception as commit_error:
                        logger.warning(f"⚠️ Commit warning: {commit_error}")
                    
                    # ⭐⭐⭐ تأخير أطول قليلاً لـ I/O في exe (100ms) ⭐⭐⭐
                    time.sleep(0.1)
                    
                    # ⭐⭐⭐ التحقق باستخدام cursor مباشر (بدون cache) ⭐⭐⭐
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute(
                            "SELECT total_paused_duration, status FROM sessions WHERE id = ?",
                            (session_id,)
                        )
                        verify_row = cursor.fetchone()
                        
                        if verify_row:
                            verified_paused = verify_row[0] if verify_row[0] is not None else 0
                            verified_status = verify_row[1]
                            
                            logger.info(f"✅ Resume verified (RAW read):")
                            logger.info(f"   - status: {verified_status}")
                            logger.info(f"   - total_paused_duration: {verified_paused}s")
                            logger.info(f"   - expected: {total_paused_duration}s")
                            
                            if verified_paused == total_paused_duration:
                                logger.info(f"✅✅ SUCCESS! القيمة صحيحة 100%")
                                return True
                            else:
                                logger.error(f"❌ القيمة خاطئة! verified={verified_paused}, expected={total_paused_duration}")
                                return False
                        else:
                            logger.error(f"❌ Failed to verify - session not found")
                            return False
                    except Exception as verify_error:
                        logger.error(f"❌ Verification error: {verify_error}")
                        return False
                else:
                    logger.error(f"❌ فشل في تحويل paused_at للجلسة {session_id}")
                    return False
            else:
                logger.warning(f"⚠️ لا يوجد paused_at للجلسة {session_id} - تحديث الحالة فقط")
                # تحديث حالة الجلسة بدون حساب مدة التوقف
                import time
                
                for attempt in range(3):
                    result = self.db.execute_query(
                        """UPDATE sessions SET is_paused = 0, paused_at = NULL, status = 'active' WHERE id = ?""",
                        (session_id,),
                        fetch=False
                    )
                    
                    # commit صريح
                    try:
                        if self.db.connection:
                            self.db.connection.commit()
                    except:
                        pass
                    
                    time.sleep(0.2)
                
                return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في استئناف الجلسة: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def add_product_to_session(self, session_id: int, product_id: int, quantity: int, unit_price: float) -> bool:
        """إضافة منتج للجلسة"""
        try:
            total_price = unit_price * quantity
            
            result = self.db.execute_query(
                """INSERT INTO session_products (session_id, product_id, quantity, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, product_id, quantity, unit_price, total_price),
                fetch=False
            )
            
            logger.info(f"تم إضافة منتج للجلسة {session_id}: {product_id} x {quantity}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في إضافة منتج للجلسة: {e}")
            return False
    
    def remove_product_from_session(self, session_product_id: int) -> bool:
        """حذف منتج من الجلسة"""
        try:
            result = self.db.execute_query(
                "DELETE FROM session_products WHERE id = ?",
                (session_product_id,),
                fetch=False
            )
            
            logger.info(f"تم حذف منتج من الجلسة: {session_product_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في حذف منتج من الجلسة: {e}")
            return False
    
    def get_session_products(self, session_id: int) -> List[Dict[str, Any]]:
        """الحصول على منتجات الجلسة"""
        try:
            result = self.db.execute_query(
                """SELECT sp.*, p.name as product_name, p.category
                   FROM session_products sp
                   JOIN products p ON sp.product_id = p.id
                   WHERE sp.session_id = ?
                   ORDER BY sp.added_at""",
                (session_id,)
            )
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتجات الجلسة: {e}")
            return []
    
    def get_session_product_by_id(self, session_product_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على منتج الجلسة بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT sp.*, p.name as product_name
                   FROM session_products sp
                   JOIN products p ON sp.product_id = p.id
                   WHERE sp.id = ?""",
                (session_product_id,)
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على منتج الجلسة: {e}")
            return None
    
    def get_session_products_total(self, session_id: int) -> float:
        """الحصول على إجمالي منتجات الجلسة"""
        try:
            result = self.db.execute_query(
                "SELECT SUM(total_price) as total FROM session_products WHERE session_id = ?",
                (session_id,)
            )
            
            return float(result[0]['total']) if result and result[0]['total'] else 0.0
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على إجمالي منتجات الجلسة: {e}")
            return 0.0
    
    def transfer_session(self, session_id: int, target_device_id: int, new_session_price: float) -> bool:
        """نقل الجلسة إلى جهاز آخر"""
        try:
            # تحديث بيانات الجلسة
            result = self.db.execute_query(
                """UPDATE sessions 
                   SET device_id = ?, session_price = ?, updated_at = ?
                   WHERE id = ?""",
                (target_device_id, new_session_price, datetime.now(), session_id),
                fetch=False
            )
            
            logger.info(f"تم نقل الجلسة {session_id} إلى الجهاز {target_device_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في نقل الجلسة: {e}")
            return False
    
    def update_session(self, session_id: int, **kwargs) -> bool:
        """تحديث بيانات الجلسة"""
        try:
            # بناء استعلام التحديث
            update_fields = []
            values = []
            
            allowed_fields = [
                'pricing_type', 'session_price', 'time_type', 'duration_minutes',
                'customer_phone', 'notes'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            # إضافة وقت التحديث
            update_fields.append("updated_at = ?")
            values.append(datetime.now())
            
            # إضافة معرف الجلسة
            values.append(session_id)
            
            # تنفيذ التحديث
            query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE id = ?"
            result = self.db.execute_query(query, tuple(values), fetch=False)
            
            logger.info(f"تم تحديث الجلسة {session_id}: {', '.join(update_fields)}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث الجلسة: {e}")
            return False
    
    def change_session_pricing_type(self, session_id: int, new_pricing_type: str) -> Dict[str, Any]:
        """تغيير نوع التسعيرة للجلسة النشطة مع التتبع المتقدم"""
        try:
            from models.pricing_segment_model import PricingSegmentModel
            
            # التحقق من وجود الجلسة
            session = self.get_session_by_id(session_id)
            if not session:
                return {
                    'success': False,
                    'message': 'الجلسة غير موجودة'
                }
            
            # التحقق من أن الجلسة نشطة أو متوقفة
            if session['status'] not in ['active', 'paused']:
                return {
                    'success': False,
                    'message': 'يمكن تغيير نوع التسعيرة للجلسات النشطة أو المتوقفة فقط'
                }
            
            # التحقق من أن النوع الجديد مختلف عن الحالي
            current_pricing_type = session['pricing_type']
            if current_pricing_type == new_pricing_type:
                return {
                    'success': False,
                    'message': 'نوع التسعيرة الجديد مطابق للنوع الحالي'
                }
            
            # الحصول على بيانات الجهاز لحساب السعر الجديد
            from models.device_model import DeviceModel
            device_model = DeviceModel()
            device = device_model.get_device_by_id(session['device_id'])
            
            if not device:
                return {
                    'success': False,
                    'message': 'الجهاز غير موجود'
                }
            
            # تحديد السعر الجديد حسب نوع التسعيرة
            if new_pricing_type == 'single':
                new_session_price = device['price_single']
            elif new_pricing_type == 'multi':
                new_session_price = device['price_multi']
            else:
                return {
                    'success': False,
                    'message': 'نوع التسعيرة غير صحيح. يجب أن يكون single أو multi'
                }
            
            # ⭐ إدارة أجزاء التسعيرة المتقدمة - مع تحسينات لـ exe
            pricing_model = PricingSegmentModel()
            
            # ⭐ خطوة 1: الحصول على جميع الأجزاء النشطة للجلسة (قد يكون هناك أكثر من جزء نشط في exe)
            all_active_segments = self.db.execute_query(
                """SELECT * FROM pricing_segments 
                   WHERE session_id = ? AND is_active = 1
                   ORDER BY start_time DESC""",
                (session_id,)
            )
            
            logger.info(f"📊 عدد الأجزاء النشطة قبل التغيير: {len(all_active_segments) if all_active_segments else 0}")
            
            # ⭐ خطوة 2: إنهاء جميع الأجزاء النشطة (وليس الجزء الأول فقط)
            if all_active_segments:
                for segment in all_active_segments:
                    logger.info(f"🔚 إنهاء الجزء النشط {segment['id']} - نوع: {segment['pricing_type']}")
                    pricing_model.end_pricing_segment(segment['id'])
            
            # ⭐ خطوة 3: التأكد من عدم وجود أي جزء نشط متبقي
            import time
            time.sleep(0.1)  # انتظار 100 ميلي ثانية للتأكد من commit في exe
            
            remaining_active = self.db.execute_query(
                """SELECT COUNT(*) as count FROM pricing_segments 
                   WHERE session_id = ? AND is_active = 1""",
                (session_id,)
            )
            
            if remaining_active and remaining_active[0]['count'] > 0:
                logger.warning(f"⚠️ لا يزال هناك {remaining_active[0]['count']} جزء نشط! محاولة إنهاء جميع الأجزاء النشطة...")
                # ⭐ محاولة أخيرة لإنهاء جميع الأجزاء النشطة بشكل صريح
                self.db.execute_query(
                    """UPDATE pricing_segments SET is_active = 0, end_time = ?, updated_at = ?
                       WHERE session_id = ? AND is_active = 1""",
                    (datetime.now(), datetime.now(), session_id),
                    fetch=False
                )
                time.sleep(0.05)
            
            # ⭐ خطوة 4: إنشاء جزء جديد للتسعيرة الجديدة
            logger.info(f"🆕 إنشاء جزء تسعيرة جديد - نوع: {new_pricing_type}")
            new_segment_id = pricing_model.create_pricing_segment(
                session_id=session_id,
                pricing_type=new_pricing_type,
                session_price=new_session_price
            )
            
            if not new_segment_id:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء جزء التسعيرة الجديد'
                }
            
            # ⭐ خطوة 5: التحقق النهائي من أن هناك جزء نشط واحد فقط
            import time
            time.sleep(0.1)
            
            final_check = self.db.execute_query(
                """SELECT id, pricing_type, is_active FROM pricing_segments 
                   WHERE session_id = ? AND is_active = 1
                   ORDER BY start_time DESC""",
                (session_id,)
            )
            
            if final_check:
                logger.info(f"🔍 عدد الأجزاء النشطة بعد التغيير: {len(final_check)}")
                for seg in final_check:
                    logger.info(f"   - جزء {seg['id']}: نوع={seg['pricing_type']}, نشط={seg['is_active']}")
                
                # ⭐ إذا كان هناك أكثر من جزء نشط، أنهِ جميع الأجزاء القديمة
                if len(final_check) > 1:
                    logger.warning(f"⚠️ وُجد {len(final_check)} أجزاء نشطة! سيتم إنهاء جميع الأجزاء عدا الجزء الجديد...")
                    for seg in final_check:
                        if seg['id'] != new_segment_id:
                            logger.info(f"🔚 إنهاء الجزء القديم {seg['id']}")
                            self.db.execute_query(
                                """UPDATE pricing_segments SET is_active = 0, end_time = ?, updated_at = ?
                                   WHERE id = ?""",
                                (datetime.now(), datetime.now(), seg['id']),
                                fetch=False
                            )
                    time.sleep(0.05)
            
            # تحديث نوع التسعيرة والسعر في الجلسة الرئيسية
            success = self.update_session(
                session_id=session_id,
                pricing_type=new_pricing_type,
                session_price=float(new_session_price)
            )
            
            if success:
                # الحصول على ملخص التسعيرة
                pricing_summary = pricing_model.get_session_pricing_summary(session_id)
                
                logger.info(f"تم تغيير نوع التسعيرة للجلسة {session_id} من {current_pricing_type} إلى {new_pricing_type}")
                return {
                    'success': True,
                    'message': f'تم تغيير نوع التسعيرة من {current_pricing_type} إلى {new_pricing_type} بنجاح',
                    'old_pricing_type': current_pricing_type,
                    'new_pricing_type': new_pricing_type,
                    'new_session_price': float(new_session_price),
                    'new_segment_id': new_segment_id,
                    'pricing_summary': pricing_summary
                }
            else:
                return {
                    'success': False,
                    'message': 'فشل في تحديث نوع التسعيرة'
                }
                
        except Exception as e:
            logger.error(f"خطأ في تغيير نوع التسعيرة: {e}")
            return {
                'success': False,
                'message': f'خطأ في تغيير نوع التسعيرة: {str(e)}'
            }