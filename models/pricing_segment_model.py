"""
موديل أجزاء التسعيرة المتقدمة
Advanced Pricing Segment Model
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database import get_db_manager
import logging

logger = logging.getLogger(__name__)

class PricingSegmentModel:
    """موديل إدارة أجزاء التسعيرة المتقدمة"""
    
    def __init__(self):
        self.db = get_db_manager()
    
    def create_pricing_segment(self, session_id: int, pricing_type: str, 
                              session_price: Decimal, start_time: datetime = None) -> Optional[int]:
        """إنشاء جزء تسعيرة جديد"""
        try:
            if start_time is None:
                start_time = datetime.now()
            
            segment_data = {
                'session_id': session_id,
                'pricing_type': pricing_type,
                'session_price': float(session_price),
                'start_time': start_time,
                'duration_seconds': 0,
                'paused_duration_seconds': 0,
                'actual_duration_seconds': 0,
                'cost': 0.0,
                'is_active': True
            }
            
            segment_id = self.db.execute_query(
                """INSERT INTO pricing_segments (session_id, pricing_type, session_price, 
                   start_time, duration_seconds, paused_duration_seconds, actual_duration_seconds, 
                   cost, is_active) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                tuple(segment_data.values()),
                fetch=False
            )
            
            logger.info(f"تم إنشاء جزء تسعيرة جديد: {segment_id} للجلسة {session_id}")
            return segment_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء جزء التسعيرة: {e}")
            return None
    
    def end_pricing_segment(self, segment_id: int, end_time: datetime = None) -> bool:
        """إنهاء جزء التسعيرة"""
        try:
            if end_time is None:
                end_time = datetime.now()
            
            # الحصول على بيانات الجزء
            segment = self.get_segment_by_id(segment_id)
            if not segment:
                logger.error(f"جزء التسعيرة {segment_id} غير موجود")
                return False
            
            # ⭐ تسجيل تفصيلي لعملية الإنهاء
            logger.info(f"🔚 بدء إنهاء جزء التسعيرة {segment_id} - نوع: {segment.get('pricing_type')}, نشط: {segment.get('is_active')}")
            
            # حساب المدة الفعلية
            start_time = segment['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            total_duration = int((end_time - start_time).total_seconds())
            actual_duration = total_duration - segment.get('paused_duration_seconds', 0)
            
            # حساب التكلفة
            cost = (actual_duration / 3600) * segment['session_price']  # السعر بالساعة
            
            # ⭐ تحديث الجزء مع تأكيد صريح على is_active = 0
            result = self.db.execute_query(
                """UPDATE pricing_segments SET 
                   end_time = ?, duration_seconds = ?, actual_duration_seconds = ?, 
                   cost = ?, is_active = 0, updated_at = ?
                   WHERE id = ?""",
                (end_time, total_duration, actual_duration, cost, datetime.now(), segment_id),
                fetch=False
            )
            
            # ⭐ إضافة تأخير صغير في exe للتأكد من commit
            import time
            time.sleep(0.05)  # 50 ميلي ثانية
            
            # ⭐ التحقق الفوري من نجاح التحديث
            if result:
                verification = self.get_segment_by_id(segment_id)
                if verification:
                    logger.info(f"✅ تم التحقق من إنهاء جزء التسعيرة {segment_id}: is_active={verification.get('is_active')}, end_time={verification.get('end_time')}")
                    
                    # ⭐ إذا لم يتم التحديث بشكل صحيح، حاول مرة أخرى
                    if verification.get('is_active') != 0 and verification.get('is_active') != False:
                        logger.warning(f"⚠️ التحديث لم يتم بشكل صحيح، محاولة ثانية...")
                        self.db.execute_query(
                            """UPDATE pricing_segments SET is_active = 0, end_time = ?, updated_at = ?
                               WHERE id = ?""",
                            (end_time, datetime.now(), segment_id),
                            fetch=False
                        )
                        time.sleep(0.05)
                        verification = self.get_segment_by_id(segment_id)
                        logger.info(f"🔄 بعد المحاولة الثانية: is_active={verification.get('is_active')}")
                
                logger.info(f"✅ تم إنهاء جزء التسعيرة {segment_id} بنجاح")
                return True
            else:
                logger.error(f"❌ فشل في إنهاء جزء التسعيرة {segment_id}")
                return False
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"خطأ في إنهاء جزء التسعيرة: {error_details}")
            return False
    
    def pause_pricing_segment(self, segment_id: int, pause_time: datetime = None) -> bool:
        """إيقاف جزء التسعيرة مؤقتاً"""
        try:
            if pause_time is None:
                pause_time = datetime.now()
            
            # تحديث الجزء
            result = self.db.execute_query(
                """UPDATE pricing_segments SET paused_at = ?, is_paused = TRUE, updated_at = ?
                   WHERE id = ?""",
                (pause_time, datetime.now(), segment_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف جزء التسعيرة: {e}")
            return False
    
    def resume_pricing_segment(self, segment_id: int, resume_time: datetime = None) -> bool:
        """استئناف جزء التسعيرة - مع قراءة RAW من قاعدة البيانات"""
        try:
            if resume_time is None:
                resume_time = datetime.now()
            
            # ⭐⭐⭐ قراءة RAW مباشرة من قاعدة البيانات (بدون cache) ⭐⭐⭐
            try:
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "SELECT paused_at, paused_duration_seconds FROM pricing_segments WHERE id = ?",
                    (segment_id,)
                )
                segment_row = cursor.fetchone()
                
                if not segment_row:
                    logger.warning(f"جزء التسعيرة {segment_id} غير موجود")
                    return False
                
                # قراءة القيم مباشرة من DB
                paused_at_raw = segment_row[0]
                old_paused_duration = segment_row[1] if segment_row[1] is not None else 0
                
                logger.info(f"📖 قراءة RAW من DB للجزء {segment_id}:")
                logger.info(f"   - paused_at: {paused_at_raw}")
                logger.info(f"   - paused_duration_seconds: {old_paused_duration}s")
                
            except Exception as db_error:
                logger.error(f"❌ خطأ في قراءة RAW من DB: {db_error}")
                # fallback للطريقة القديمة
                segment = self.get_segment_by_id(segment_id)
                if not segment:
                    return False
                paused_at_raw = segment.get('paused_at')
                old_paused_duration = segment.get('paused_duration_seconds', 0)
            
            # حساب مدة التوقف
            if paused_at_raw:
                # تحويل paused_at بطريقة آمنة
                paused_at = paused_at_raw
                if isinstance(paused_at, str):
                    try:
                        paused_at = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S')
                
                pause_duration = int((resume_time - paused_at).total_seconds())
                new_paused_duration = old_paused_duration + pause_duration
                
                logger.info(f"🔄 استئناف جزء التسعيرة {segment_id}:")
                logger.info(f"   - وقت الإيقاف: {paused_at}")
                logger.info(f"   - وقت الاستئناف: {resume_time}")
                logger.info(f"   - مدة التوقف الحالية: {pause_duration} ثانية ({pause_duration / 60:.2f} دقيقة)")
                logger.info(f"   - مدة التوقف السابقة: {old_paused_duration} ثانية ({old_paused_duration / 60:.2f} دقيقة)")
                logger.info(f"   - مدة التوقف الإجمالية الجديدة: {new_paused_duration} ثانية ({new_paused_duration / 60:.2f} دقيقة)")
                
                # ⭐⭐⭐ EXE FIX: تحديث الجزء مع قيم واضحة (0/1 بدلاً من TRUE/FALSE) ⭐⭐⭐
                result = self.db.execute_query(
                    """UPDATE pricing_segments SET 
                       paused_at = NULL, paused_duration_seconds = ?, is_paused = 0, updated_at = ?
                       WHERE id = ?""",
                    (new_paused_duration, datetime.now(), segment_id),
                    fetch=False
                )
                
                # ⭐⭐⭐ EXE FIX: commit صريح للتأكد ⭐⭐⭐
                try:
                    if self.db.connection:
                        self.db.connection.commit()
                        logger.info(f"✅ تم عمل commit صريح لجزء التسعيرة {segment_id}")
                except Exception as commit_error:
                    logger.warning(f"⚠️ خطأ في commit الصريح: {commit_error}")
                
                # ⭐⭐⭐ EXE FIX: تأخير وتحقق RAW من التحديث ⭐⭐⭐
                if result:
                    import time
                    time.sleep(0.1)  # 100 ميلي ثانية
                    
                    # ⭐⭐⭐ التحقق باستخدام cursor مباشر (بدون cache) ⭐⭐⭐
                    try:
                        cursor = self.db.connection.cursor()
                        cursor.execute(
                            "SELECT paused_duration_seconds, is_paused FROM pricing_segments WHERE id = ?",
                            (segment_id,)
                        )
                        verify_row = cursor.fetchone()
                        
                        if verify_row:
                            verified_paused = verify_row[0] if verify_row[0] is not None else 0
                            verified_is_paused = verify_row[1]
                            
                            logger.info(f"✅ تحقق RAW من جزء التسعيرة {segment_id}:")
                            logger.info(f"   - paused_duration: {verified_paused}s (expected: {new_paused_duration}s)")
                            logger.info(f"   - is_paused: {verified_is_paused}")
                    except Exception as verify_error:
                        logger.error(f"❌ خطأ في التحقق: {verify_error}")
                        verified_paused = -1  # قيمة خطأ
                    
                    logger.info(f"القيمة المتوقعة: {new_paused_duration}")
                    
                    # ⭐⭐⭐ إذا القيمة خاطئة، محاولات إضافية ⭐⭐⭐
                    if verified_paused != new_paused_duration:
                        logger.warning(f"⚠️ القيمة لم تُحدث بشكل صحيح - محاولات إضافية...")
                        
                        for attempt in range(3):
                            self.db.execute_query(
                                """UPDATE pricing_segments SET 
                                   paused_at = NULL, paused_duration_seconds = ?, is_paused = 0, updated_at = ?
                                   WHERE id = ?""",
                                (new_paused_duration, datetime.now(), segment_id),
                                fetch=False
                            )
                            
                            try:
                                if self.db.connection:
                                    self.db.connection.commit()
                            except:
                                pass
                            
                            time.sleep(0.1)
                            
                            # تحقق RAW مرة أخرى
                            cursor = self.db.connection.cursor()
                            cursor.execute(
                                "SELECT paused_duration_seconds FROM pricing_segments WHERE id = ?",
                                (segment_id,)
                            )
                            retry_row = cursor.fetchone()
                            if retry_row and retry_row[0] == new_paused_duration:
                                logger.info(f"✅ المحاولة {attempt + 2} نجحت!")
                                break
                    
                    return True
                else:
                    logger.error(f"❌ فشل في تحديث جزء التسعيرة {segment_id}")
                    return False
            else:
                # تحديث الجزء بدون حساب مدة التوقف
                logger.info(f"⚠️ لا يوجد paused_at لجزء التسعيرة {segment_id}")
                result = self.db.execute_query(
                    """UPDATE pricing_segments SET is_paused = 0, updated_at = ?
                       WHERE id = ?""",
                    (datetime.now(), segment_id),
                    fetch=False
                )
                
                # commit صريح
                try:
                    if self.db.connection:
                        self.db.connection.commit()
                except:
                    pass
                
                import time
                time.sleep(0.1)
                
                return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في استئناف جزء التسعيرة: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_segment_by_id(self, segment_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على جزء التسعيرة بالمعرف"""
        try:
            result = self.db.execute_query(
                "SELECT * FROM pricing_segments WHERE id = ?",
                (segment_id,)
            )
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جزء التسعيرة: {e}")
            return None
    
    def get_active_segment(self, session_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على جزء التسعيرة النشط للجلسة"""
        try:
            # ⭐ استخدام is_active = 1 بدلاً من TRUE للتوافق
            result = self.db.execute_query(
                """SELECT * FROM pricing_segments 
                   WHERE session_id = ? AND is_active = 1
                   ORDER BY start_time DESC LIMIT 1""",
                (session_id,)
            )
            
            # ⭐ تسجيل تفصيلي
            if result:
                logger.info(f"📌 تم العثور على جزء نشط: {result[0]['id']} - نوع: {result[0]['pricing_type']}")
            else:
                logger.info(f"📌 لا يوجد جزء نشط للجلسة {session_id}")
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على جزء التسعيرة النشط: {e}")
            return None
    
    def get_all_segments_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """الحصول على جميع أجزاء التسعيرة للجلسة"""
        try:
            result = self.db.execute_query(
                """SELECT * FROM pricing_segments 
                   WHERE session_id = ?
                   ORDER BY start_time ASC""",
                (session_id,)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على أجزاء التسعيرة: {e}")
            return []
    
    def get_segments_by_pricing_type(self, session_id: int, pricing_type: str) -> List[Dict[str, Any]]:
        """الحصول على أجزاء التسعيرة حسب النوع"""
        try:
            result = self.db.execute_query(
                """SELECT * FROM pricing_segments 
                   WHERE session_id = ? AND pricing_type = ?
                   ORDER BY start_time ASC""",
                (session_id, pricing_type)
            )
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على أجزاء التسعيرة حسب النوع: {e}")
            return []
    
    def calculate_segment_cost(self, segment_id: int) -> Dict[str, Any]:
        """حساب تكلفة جزء التسعيرة"""
        try:
            segment = self.get_segment_by_id(segment_id)
            if not segment:
                return {}
            
            start_time = segment['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            current_time = datetime.now()
            
            # ⭐⭐ إصلاح حاسم: التحقق من حالة الجلسة أولاً قبل حالة الجزء
            session_id = segment.get('session_id')
            is_session_paused = False
            session_paused_at = None
            session = None  # تعريف المتغير
            
            if session_id:
                # ⭐⭐⭐ قراءة RAW مباشرة لبيانات الجلسة (مهم للتأكد من أحدث البيانات) ⭐⭐⭐
                try:
                    # ⭐ إجبار commit لضمان flush في WAL mode ⭐
                    try:
                        self.db.connection.commit()
                    except:
                        pass
                    
                    cursor = self.db.connection.cursor()
                    cursor.execute(
                        "SELECT status, is_paused, paused_at, total_paused_duration FROM sessions WHERE id = ?",
                        (session_id,)
                    )
                    session_row = cursor.fetchone()
                    
                    if session_row:
                        session_status_raw = session_row[0]
                        session_is_paused_raw = bool(session_row[1])
                        session_paused_at_raw = session_row[2]
                        session_total_paused_raw = session_row[3] if session_row[3] is not None else 0
                        
                        logger.info(f"📖 قراءة RAW للجلسة {session_id}: status={session_status_raw}, is_paused={session_is_paused_raw}, total_paused={session_total_paused_raw}s")
                        
                        # استخدام القيم المقروءة مباشرة
                        is_session_paused = (session_status_raw == 'paused') or session_is_paused_raw
                        
                        if is_session_paused and session_paused_at_raw:
                            session_paused_at = session_paused_at_raw
                            if isinstance(session_paused_at, str):
                                try:
                                    session_paused_at = datetime.fromisoformat(session_paused_at.replace('Z', '+00:00'))
                                except ValueError:
                                    try:
                                        session_paused_at = datetime.strptime(session_paused_at, '%Y-%m-%d %H:%M:%S.%f')
                                    except ValueError:
                                        session_paused_at = datetime.strptime(session_paused_at, '%Y-%m-%d %H:%M:%S')
                        else:
                            session_paused_at = None
                    else:
                        logger.warning(f"⚠️ لم يتم العثور على الجلسة {session_id}")
                        is_session_paused = False
                        session_paused_at = None
                except Exception as session_error:
                    logger.error(f"❌ خطأ في قراءة بيانات الجلسة: {session_error}")
                    # Fallback للطريقة القديمة
                    from models.session_model import SessionModel
                    session_model = SessionModel()
                    session = session_model.get_session_by_id(session_id)
                    
                    if session:
                        is_session_paused = (session.get('status') == 'paused') or (session.get('is_paused', False) == True)
                        if is_session_paused and session.get('paused_at'):
                            session_paused_at = session['paused_at']
                            if isinstance(session_paused_at, str):
                                session_paused_at = datetime.fromisoformat(session_paused_at.replace('Z', '+00:00'))
            
            # ⭐⭐⭐ إصلاح جذري: تحديد الوقت المرجعي بشكل صحيح ⭐⭐⭐
            # الأولوية: 1) الجلسة متوقفة 2) الجلسة انتهى وقتها 3) الجزء متوقف 4) نشط
            
            # أولاً: التحقق من انتهاء الوقت المحدد للجلسة
            session_time_expired = False
            session_end_time = None
            
            if session_id and session:
                if session.get('time_type') == 'fixed' and session.get('end_time'):
                    session_end_time = session['end_time']
                    if isinstance(session_end_time, str):
                        try:
                            session_end_time = datetime.fromisoformat(session_end_time.replace('Z', '+00:00'))
                        except:
                            try:
                                session_end_time = datetime.strptime(session_end_time, '%Y-%m-%d %H:%M:%S.%f')
                            except:
                                session_end_time = datetime.strptime(session_end_time, '%Y-%m-%d %H:%M:%S')
                    
                    # التحقق: هل انتهى الوقت المحدد؟
                    if current_time >= session_end_time:
                        session_time_expired = True
                        logger.info(f"⏰ الجلسة {session_id} انتهى وقتها المحدد!")
            
            # تحديد الوقت المرجعي
            if is_session_paused and session_paused_at:
                # 1) الجلسة متوقفة - استخدم وقت الإيقاف
                reference_time = session_paused_at
                logger.info(f"🛑 الجلسة متوقفة - استخدام وقت الإيقاف: {session_paused_at}")
            elif session_time_expired and session_end_time:
                # 2) ⭐⭐⭐ الجلسة انتهى وقتها - استخدم end_time (لا تزيد!) ⭐⭐⭐
                reference_time = session_end_time
                logger.info(f"⏰ الجلسة انتهى وقتها - استخدام end_time: {session_end_time}")
            elif segment.get('is_paused') and segment.get('paused_at'):
                # 3) الجزء متوقف - استخدم وقت إيقاف الجزء
                paused_at = segment['paused_at']
                if isinstance(paused_at, str):
                    paused_at = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                reference_time = paused_at
                logger.info(f"⏸️ الجزء متوقف - استخدام وقت الإيقاف: {paused_at}")
            else:
                # 4) نشط - استخدم الوقت الحالي
                reference_time = current_time
                logger.info(f"▶️ نشط - استخدام الوقت الحالي: {current_time}")
            
            # حساب المدة الإجمالية
            if segment.get('end_time'):
                end_time = segment['end_time']
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                total_duration = int((end_time - start_time).total_seconds())
            else:
                total_duration = int((reference_time - start_time).total_seconds())
                logger.info(f"الجزء {segment_id} - المدة الإجمالية: {total_duration} ثانية")
            
            # ⭐⭐⭐ قراءة RAW مباشرة لـ paused_duration_seconds من قاعدة البيانات ⭐⭐⭐
            # هذا حاسم في exe لأن القيمة قد تكون قديمة في segment object
            try:
                # ⭐ إجبار commit لضمان flush جميع البيانات المعلقة (مهم في WAL mode)
                try:
                    self.db.connection.commit()
                except:
                    pass  # قد يكون autocommit نشط
                
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "SELECT paused_duration_seconds FROM pricing_segments WHERE id = ?",
                    (segment_id,)
                )
                paused_row = cursor.fetchone()
                
                if paused_row and paused_row[0] is not None:
                    paused_duration = paused_row[0]
                    logger.info(f"📖 قراءة RAW للجزء {segment_id}: paused_duration = {paused_duration}s")
                else:
                    paused_duration = 0
                    logger.info(f"⚠️ لم يتم العثور على paused_duration للجزء {segment_id}")
            except Exception as db_error:
                logger.error(f"❌ خطأ في قراءة paused_duration: {db_error}")
                paused_duration = segment.get('paused_duration_seconds', 0)
            
            # حساب مدة التوقف الحالية إذا كان الجزء متوقف
            if segment.get('is_paused') and segment.get('paused_at'):
                paused_at = segment['paused_at']
                if isinstance(paused_at, str):
                    try:
                        paused_at = datetime.fromisoformat(paused_at.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            paused_at = datetime.strptime(paused_at, '%Y-%m-%d %H:%M:%S')
                
                # حساب مدة التوقف الحالية (فقط إذا كان الجزء نشط)
                if not segment.get('is_paused', False):
                    current_pause = int((current_time - paused_at).total_seconds())
                    paused_duration += current_pause
                    logger.info(f"الجزء {segment_id} نشط - إضافة مدة التوقف الحالية: {current_pause} ثانية")
                else:
                    # الجزء متوقف - لا نضيف مدة توقف إضافية
                    logger.info(f"الجزء {segment_id} متوقف - لا توجد مدة توقف إضافية")
            
            # ⭐⭐⭐ إصلاح جذري: استخدام total_paused_duration من الجلسة الأم أيضاً ⭐⭐⭐
            # في exe، paused_duration للجزء قد لا يُحدث بشكل صحيح
            # لذلك نستخدم total_paused_duration من الجلسة كبديل/تأكيد
            session_total_paused = 0
            if session_id:
                try:
                    # قراءة RAW لـ total_paused_duration من الجلسة
                    self.db.connection.commit()
                    cursor_session = self.db.connection.cursor()
                    cursor_session.execute(
                        "SELECT total_paused_duration FROM sessions WHERE id = ?",
                        (session_id,)
                    )
                    session_pause_row = cursor_session.fetchone()
                    if session_pause_row and session_pause_row[0] is not None:
                        session_total_paused = session_pause_row[0]
                        logger.info(f"📖 total_paused_duration من الجلسة {session_id}: {session_total_paused}s ({session_total_paused / 60:.2f} دقيقة)")
                except Exception as e:
                    logger.error(f"خطأ في قراءة total_paused_duration من الجلسة: {e}")
            
            # استخدام القيمة الأكبر (أكثر دقة)
            final_paused_duration = max(paused_duration, session_total_paused)
            
            if final_paused_duration != paused_duration:
                logger.warning(f"⚠️ استخدام total_paused_duration من الجلسة ({session_total_paused}s) بدلاً من الجزء ({paused_duration}s)")
                paused_duration = final_paused_duration
            
            # حساب المدة الفعلية (بدون الوقت المتوقف)
            actual_duration = max(0, total_duration - paused_duration)
            
            logger.info(f"💰 الجزء {segment_id} - الحساب النهائي:")
            logger.info(f"   - المدة الإجمالية: {total_duration} ثانية ({total_duration / 60:.2f} دقيقة)")
            logger.info(f"   - المدة المتوقفة (الجزء): {segment.get('paused_duration_seconds', 0)} ثانية")
            logger.info(f"   - المدة المتوقفة (الجلسة): {session_total_paused} ثانية")
            logger.info(f"   - المدة المتوقفة (المُستخدمة): {paused_duration} ثانية ({paused_duration / 60:.2f} دقيقة)")
            logger.info(f"   - المدة الفعلية: {actual_duration} ثانية ({actual_duration / 60:.2f} دقيقة)")
            
            # التحقق من انتهاء الوقت للجلسات المحددة الوقت
            # استخدام session التي تم جلبها سابقاً بدلاً من جلبها مرة أخرى
            if session_id and session_id == segment.get('session_id') and session:
                # استخدام session الموجودة بالفعل من السطر 243
                if session.get('time_type') == 'fixed' and session.get('duration_minutes'):
                    # جلسة بوقت محدد - التحقق من انتهاء الوقت
                    duration_minutes = session['duration_minutes']
                    duration_total_seconds = duration_minutes * 60
                    
                    # حساب الوقت المنقضي من بداية الجلسة
                    session_start_time = session['start_time']
                    if isinstance(session_start_time, str):
                        session_start_time = datetime.fromisoformat(session_start_time.replace('Z', '+00:00'))
                    
                    # ⭐⭐⭐ حساب الوقت الفعلي للجلسة (بدون وقت التوقف) ⭐⭐⭐
                    session_reference_time = reference_time
                    session_total_seconds = int((session_reference_time - session_start_time).total_seconds())
                    
                    # خصم وقت التوقف من الجلسة الأم
                    session_elapsed_seconds = max(0, session_total_seconds - session_total_paused)
                    
                    logger.info(f"💰 الجلسة {session_id} - حساب الوقت للتحقق من الانتهاء:")
                    logger.info(f"   - الوقت الإجمالي: {session_total_seconds} ثانية")
                    logger.info(f"   - وقت التوقف: {session_total_paused} ثانية")
                    logger.info(f"   - الوقت الفعلي: {session_elapsed_seconds} ثانية ({session_elapsed_seconds / 60:.2f} دقيقة)")
                    logger.info(f"   - المدة المحددة: {duration_total_seconds} ثانية ({duration_minutes} دقيقة)")
                    
                    # ⭐⭐⭐ إذا انتهى الوقت المحدد للجلسة، حدد actual_duration عند المتاح فقط ⭐⭐⭐
                    if session_elapsed_seconds >= duration_total_seconds:
                        logger.info(f"⏰ انتهى الوقت المحدد للجلسة {session_id}!")
                        logger.info(f"   - الوقت الفعلي للجلسة: {session_elapsed_seconds}s ({session_elapsed_seconds / 60:.2f} دقيقة)")
                        logger.info(f"   - المدة المحددة: {duration_total_seconds}s ({duration_minutes} دقيقة)")
                        
                        # حدد actual_duration بحيث لا يتجاوز الوقت المحدد الكلي للجلسة
                        # نحسب: كم استُخدم من الوقت المحدد قبل هذا الجزء؟
                        
                        # الحل البسيط: actual_duration يجب ألا يتجاوز ما تبقى من duration_total_seconds
                        # لكن بما أن الجلسة انتهت، actual_duration يجب أن يكون محدوداً
                        
                        logger.info(f"   - actual_duration الحالي: {actual_duration}s ({actual_duration / 60:.2f} دقيقة)")
                        
                        # ⭐ حل بسيط: حدد actual_duration بحيث لا يسبب تجاوز المدة الكلية
                        # نحتاج أن نعرف: كم مدة الأجزاء الأخرى؟
                        # لكن هذا معقد. الحل الأبسط:
                        # إذا كان الجزء الوحيد أو الأول، حدد عند duration_total_seconds
                        # إذا كان هناك أجزاء سابقة، سيتم التعامل معها في get_session_pricing_summary
                        
                        # ⭐⭐ حل مباشر: لا نغير actual_duration هنا
                        # بل نتأكد فقط أنه لا يتجاوز المدة الإجمالية المتاحة
                        # سيتم التعامل مع هذا في get_session_pricing_summary
                        
                        logger.info(f"   ℹ️ سيتم التحقق النهائي من المجموع في get_session_pricing_summary")
            
            # ⭐⭐⭐ حساب التكلفة (السعر بالساعة) مع ضمان عدم تجاوز الوقت المحدد ⭐⭐⭐
            session_price = segment['session_price']
            
            # ⭐ ضمان أن actual_duration لا يتجاوز الوقت المحدد (double-check)
            if session_id and session:
                if session.get('time_type') == 'fixed' and session.get('duration_minutes'):
                    duration_minutes = session['duration_minutes']
                    duration_total_seconds = duration_minutes * 60
                    
                    # حساب كم من الوقت المحدد يخص هذا الجزء
                    segment_start_time = segment['start_time']
                    if isinstance(segment_start_time, str):
                        segment_start_time = datetime.fromisoformat(segment_start_time.replace('Z', '+00:00'))
                    
                    session_start_time = session['start_time']
                    if isinstance(session_start_time, str):
                        session_start_time = datetime.fromisoformat(session_start_time.replace('Z', '+00:00'))
                    
                    # الوقت من بداية الجلسة حتى بداية هذا الجزء
                    segment_offset = int((segment_start_time - session_start_time).total_seconds())
                    
                    # الوقت المتاح لهذا الجزء من الوقت المحدد
                    available_duration = max(0, duration_total_seconds - segment_offset)
                    
                    # التأكد من أن actual_duration لا يتجاوز المتاح
                    if actual_duration > available_duration:
                        logger.warning(f"⚠️ actual_duration ({actual_duration}s) > available ({available_duration}s) - تحديد عند المتاح")
                        actual_duration = available_duration
            
            cost = (actual_duration / 3600) * session_price
            
            logger.info(f"💰 حساب التكلفة النهائية:")
            logger.info(f"   - actual_duration: {actual_duration}s ({actual_duration / 60:.2f} دقيقة)")
            logger.info(f"   - session_price: {session_price} جنيه/ساعة")
            logger.info(f"   - cost: {cost:.2f} جنيه")
            
            return {
                'segment_id': segment_id,
                'pricing_type': segment['pricing_type'],
                'session_price': session_price,
                'total_duration_seconds': total_duration,
                'paused_duration_seconds': paused_duration,
                'actual_duration_seconds': actual_duration,
                'actual_duration_hours': actual_duration / 3600,
                'cost': cost,
                'is_active': segment.get('is_active', True),
                'is_paused': segment.get('is_paused', False)
            }
            
        except Exception as e:
            logger.error(f"خطأ في حساب تكلفة جزء التسعيرة: {e}")
            return {}
    
    def get_session_pricing_summary(self, session_id: int) -> Dict[str, Any]:
        """الحصول على ملخص التسعيرة للجلسة"""
        try:
            segments = self.get_all_segments_for_session(session_id)
            
            # ⭐ تسجيل تفصيلي لعدد الأجزاء
            logger.info(f"📊 حساب ملخص التسعيرة للجلسة {session_id} - عدد الأجزاء: {len(segments) if segments else 0}")
            
            summary = {
                'session_id': session_id,
                'single_segments': [],
                'multi_segments': [],
                'total_single_duration': 0,
                'total_multi_duration': 0,
                'total_single_cost': 0.0,
                'total_multi_cost': 0.0,
                'total_cost': 0.0,
                'total_duration': 0
            }
            
            for segment in segments:
                # ⭐ تسجيل تفصيلي لكل جزء
                logger.info(f"   📍 جزء {segment['id']}: نوع={segment['pricing_type']}, نشط={segment.get('is_active')}, start={segment.get('start_time')}, end={segment.get('end_time')}")
                
                cost_info = self.calculate_segment_cost(segment['id'])
                if not cost_info:
                    logger.warning(f"   ⚠️ فشل في حساب تكلفة الجزء {segment['id']}")
                    continue
                
                segment_summary = {
                    'segment_id': segment['id'],
                    'start_time': segment['start_time'],
                    'end_time': segment.get('end_time'),
                    'duration_seconds': cost_info['actual_duration_seconds'],
                    'duration_hours': cost_info['actual_duration_hours'],
                    'cost': cost_info['cost'],
                    'is_active': cost_info['is_active'],
                    'is_paused': cost_info['is_paused']
                }
                
                if segment['pricing_type'] == 'single':
                    summary['single_segments'].append(segment_summary)
                    summary['total_single_duration'] += cost_info['actual_duration_seconds']
                    summary['total_single_cost'] += cost_info['cost']
                else:
                    summary['multi_segments'].append(segment_summary)
                    summary['total_multi_duration'] += cost_info['actual_duration_seconds']
                    summary['total_multi_cost'] += cost_info['cost']
                
                summary['total_cost'] += cost_info['cost']
                summary['total_duration'] += cost_info['actual_duration_seconds']
            
            # ⭐⭐⭐ حل بسيط: حدد التكلفة مباشرة إذا كانت جلسة fixed time ⭐⭐⭐
            try:
                from models.session_model import SessionModel
                session_model = SessionModel()
                session = session_model.get_session_by_id(session_id)
                
                if session and session.get('time_type') == 'fixed' and session.get('duration_minutes'):
                    duration_minutes = session['duration_minutes']
                    duration_hours = duration_minutes / 60
                    session_price = session.get('session_price', 0)
                    max_cost = duration_hours * session_price
                    
                    logger.info(f"⏰ جلسة محددة الوقت:")
                    logger.info(f"   - المدة المحددة: {duration_minutes} دقيقة")
                    logger.info(f"   - التكلفة القصوى: {max_cost:.2f} جنيه")
                    logger.info(f"   - المجموع الحالي: {summary['total_cost']:.2f} جنيه")
                    
                    # ⭐⭐⭐ الحل البسيط: إذا تجاوز، حدد عند الحد الأقصى ⭐⭐⭐
                    if summary['total_cost'] > max_cost:
                        logger.warning(f"⚠️ التكلفة تجاوزت! تحديد عند {max_cost:.2f} جنيه")
                        summary['total_cost'] = max_cost
                        
                        # تحديد الساعات أيضاً
                        summary['total_hours'] = duration_hours
                    
                    logger.info(f"✅ التكلفة النهائية: {summary['total_cost']:.2f} جنيه")
            except Exception as e:
                logger.error(f"خطأ في تحديد التكلفة: {e}")
            
            # تحويل المدة إلى ساعات ودقائق (إذا لم يتم حسابها بالفعل)
            if 'total_single_hours' not in summary or summary.get('total_single_hours') is None:
                summary['total_single_hours'] = summary['total_single_duration'] / 3600
            if 'total_multi_hours' not in summary or summary.get('total_multi_hours') is None:
                summary['total_multi_hours'] = summary['total_multi_duration'] / 3600
            if 'total_hours' not in summary or summary.get('total_hours') is None:
                summary['total_hours'] = summary['total_duration'] / 3600
            
            # ⭐ تسجيل الملخص النهائي
            logger.info(f"📊 ملخص التسعيرة النهائي للجلسة {session_id}:")
            logger.info(f"   👤 فردي: {summary['total_single_hours']:.2f} ساعة = {summary['total_single_cost']:.2f} جنيه")
            logger.info(f"   👥 جماعي: {summary['total_multi_hours']:.2f} ساعة = {summary['total_multi_cost']:.2f} جنيه")
            logger.info(f"   💰 الإجمالي: {summary['total_hours']:.2f} ساعة = {summary['total_cost']:.2f} جنيه")
            
            return summary
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على ملخص التسعيرة: {e}")
            return {}
    
    def update_segment_cost(self, segment_id: int) -> bool:
        """تحديث تكلفة جزء التسعيرة"""
        try:
            cost_info = self.calculate_segment_cost(segment_id)
            if not cost_info:
                return False
            
            result = self.db.execute_query(
                """UPDATE pricing_segments SET 
                   duration_seconds = ?, paused_duration_seconds = ?, 
                   actual_duration_seconds = ?, cost = ?, updated_at = ?
                   WHERE id = ?""",
                (cost_info['total_duration_seconds'], 
                 cost_info['paused_duration_seconds'],
                 cost_info['actual_duration_seconds'],
                 cost_info['cost'],
                 datetime.now(),
                 segment_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في تحديث تكلفة جزء التسعيرة: {e}")
            return False
