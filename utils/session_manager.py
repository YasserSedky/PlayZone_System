"""
مدير الجلسات - إدارة إيقاف واستئناف الجلسات عند إغلاق وفتح التطبيق
Session Manager - Handle session pause/resume on app shutdown/startup
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import get_db_manager

logger = logging.getLogger(__name__)

class SessionManager:
    """مدير الجلسات للتطبيق"""
    
    def __init__(self):
        self.db = get_db_manager()
        self.sessions_file = "data/sessions_state.json"
        self.paused_sessions = []
    
    def pause_all_active_sessions(self) -> Dict[str, Any]:
        """إيقاف جميع الجلسات النشطة عند إغلاق التطبيق"""
        try:
            logger.info("بدء إيقاف جميع الجلسات النشطة...")
            
            # الحصول على جميع الجلسات النشطة
            active_sessions = self.get_all_active_sessions()
            
            if not active_sessions:
                logger.info("لا توجد جلسات نشطة لإيقافها")
                return {
                    'success': True,
                    'message': 'لا توجد جلسات نشطة',
                    'paused_count': 0
                }
            
            paused_count = 0
            failed_sessions = []
            
            for session in active_sessions:
                try:
                    # إيقاف الجلسة
                    if self.pause_session_for_shutdown(session['id']):
                        paused_count += 1
                        logger.info(f"تم إيقاف الجلسة {session['id']} للجهاز {session['device_name']}")
                    else:
                        failed_sessions.append(session['id'])
                        logger.error(f"فشل في إيقاف الجلسة {session['id']}")
                        
                except Exception as e:
                    failed_sessions.append(session['id'])
                    logger.error(f"خطأ في إيقاف الجلسة {session['id']}: {e}")
            
            # حفظ حالة الجلسات الموقوفة
            self.save_sessions_state(active_sessions)
            
            message = f"تم إيقاف {paused_count} جلسة بنجاح"
            if failed_sessions:
                message += f" - فشل في إيقاف {len(failed_sessions)} جلسة"
            
            logger.info(message)
            
            return {
                'success': True,
                'message': message,
                'paused_count': paused_count,
                'failed_count': len(failed_sessions),
                'failed_sessions': failed_sessions
            }
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسات: {e}")
            return {
                'success': False,
                'message': f"خطأ في إيقاف الجلسات: {str(e)}",
                'paused_count': 0
            }
    
    def resume_paused_sessions(self) -> Dict[str, Any]:
        """استئناف الجلسات الموقوفة عند فتح التطبيق"""
        try:
            logger.info("بدء استئناف الجلسات الموقوفة...")
            
            # تحميل حالة الجلسات الموقوفة
            paused_sessions = self.load_sessions_state()
            
            if not paused_sessions:
                logger.info("لا توجد جلسات موقوفة للاستئناف")
                return {
                    'success': True,
                    'message': 'لا توجد جلسات موقوفة',
                    'resumed_count': 0
                }
            
            resumed_count = 0
            failed_sessions = []
            expired_sessions = []
            
            for session_data in paused_sessions:
                try:
                    session_id = session_data['id']
                    
                    # التحقق من وجود الجلسة في قاعدة البيانات
                    current_session = self.get_session_by_id(session_id)
                    
                    if not current_session:
                        logger.warning(f"الجلسة {session_id} غير موجودة في قاعدة البيانات")
                        expired_sessions.append(session_id)
                        continue
                    
                    # التحقق من حالة الجلسة
                    if current_session['status'] not in ['paused', 'active']:
                        logger.warning(f"الجلسة {session_id} في حالة غير صحيحة: {current_session['status']}")
                        expired_sessions.append(session_id)
                        continue
                    
                    # استئناف الجلسة
                    if self.resume_session_for_startup(session_id):
                        resumed_count += 1
                        logger.info(f"تم استئناف الجلسة {session_id} للجهاز {current_session.get('device_name', 'غير محدد')}")
                    else:
                        failed_sessions.append(session_id)
                        logger.error(f"فشل في استئناف الجلسة {session_id}")
                        
                except Exception as e:
                    failed_sessions.append(session_data.get('id', 'غير محدد'))
                    logger.error(f"خطأ في استئناف الجلسة {session_data.get('id', 'غير محدد')}: {e}")
            
            # مسح ملف حالة الجلسات بعد الاستئناف
            self.clear_sessions_state()
            
            message = f"تم استئناف {resumed_count} جلسة بنجاح"
            if failed_sessions:
                message += f" - فشل في استئناف {len(failed_sessions)} جلسة"
            if expired_sessions:
                message += f" - انتهت صلاحية {len(expired_sessions)} جلسة"
            
            logger.info(message)
            
            return {
                'success': True,
                'message': message,
                'resumed_count': resumed_count,
                'failed_count': len(failed_sessions),
                'expired_count': len(expired_sessions),
                'failed_sessions': failed_sessions,
                'expired_sessions': expired_sessions
            }
            
        except Exception as e:
            logger.error(f"خطأ في استئناف الجلسات: {e}")
            return {
                'success': False,
                'message': f"خطأ في استئناف الجلسات: {str(e)}",
                'resumed_count': 0
            }
    
    def get_all_active_sessions(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الجلسات النشطة"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.status = 'active' AND s.is_paused = 0
                   ORDER BY s.start_time DESC"""
            )
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسات النشطة: {e}")
            return []
    
    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على جلسة بالمعرف"""
        try:
            result = self.db.execute_query(
                """SELECT s.*, d.name as device_name, d.type as device_type,
                          u.username as cashier_name
                   FROM sessions s
                   JOIN devices d ON s.device_id = d.id
                   LEFT JOIN users u ON s.cashier_id = u.id
                   WHERE s.id = ?""",
                (session_id,)
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على الجلسة: {e}")
            return None
    
    def pause_session_for_shutdown(self, session_id: int) -> bool:
        """إيقاف جلسة عند إغلاق التطبيق"""
        try:
            # تحديث حالة الجلسة إلى متوقفة
            result = self.db.execute_query(
                """UPDATE sessions SET 
                   status = 'paused',
                   is_paused = 1,
                   paused_at = ?,
                   updated_at = ?
                   WHERE id = ?""",
                (datetime.now(), datetime.now(), session_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسة {session_id}: {e}")
            return False
    
    def resume_session_for_startup(self, session_id: int) -> bool:
        """استئناف جلسة عند فتح التطبيق"""
        try:
            # تحديث حالة الجلسة إلى نشطة
            result = self.db.execute_query(
                """UPDATE sessions SET 
                   status = 'active',
                   is_paused = 0,
                   paused_at = NULL,
                   updated_at = ?
                   WHERE id = ?""",
                (datetime.now(), session_id),
                fetch=False
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"خطأ في استئناف الجلسة {session_id}: {e}")
            return False
    
    def save_sessions_state(self, sessions: List[Dict[str, Any]]):
        """حفظ حالة الجلسات في ملف"""
        try:
            # إنشاء مجلد البيانات إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
            
            # إضافة معلومات إضافية
            sessions_data = {
                'shutdown_time': datetime.now().isoformat(),
                'sessions_count': len(sessions),
                'sessions': sessions
            }
            
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"تم حفظ حالة {len(sessions)} جلسة في الملف")
            
        except Exception as e:
            logger.error(f"خطأ في حفظ حالة الجلسات: {e}")
    
    def load_sessions_state(self) -> List[Dict[str, Any]]:
        """تحميل حالة الجلسات من ملف"""
        try:
            if not os.path.exists(self.sessions_file):
                return []
            
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            sessions = data.get('sessions', [])
            shutdown_time = data.get('shutdown_time', 'غير محدد')
            
            logger.info(f"تم تحميل حالة {len(sessions)} جلسة من وقت الإغلاق: {shutdown_time}")
            
            return sessions
            
        except Exception as e:
            logger.error(f"خطأ في تحميل حالة الجلسات: {e}")
            return []
    
    def clear_sessions_state(self):
        """مسح ملف حالة الجلسات"""
        try:
            if os.path.exists(self.sessions_file):
                os.remove(self.sessions_file)
                logger.info("تم مسح ملف حالة الجلسات")
        except Exception as e:
            logger.error(f"خطأ في مسح ملف حالة الجلسات: {e}")
    
    def get_sessions_status(self) -> Dict[str, Any]:
        """الحصول على حالة الجلسات"""
        try:
            active_sessions = self.get_all_active_sessions()
            paused_sessions = self.load_sessions_state()
            
            return {
                'active_count': len(active_sessions),
                'paused_count': len(paused_sessions),
                'active_sessions': active_sessions,
                'paused_sessions': paused_sessions
            }
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على حالة الجلسات: {e}")
            return {
                'active_count': 0,
                'paused_count': 0,
                'active_sessions': [],
                'paused_sessions': []
            }
