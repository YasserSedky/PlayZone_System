"""
اختبار تشخيصي بسيط لمشكلة pause/resume
"""
import sqlite3
from datetime import datetime

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('data/ps_system.db')
cursor = conn.cursor()

print("="*70)
print("اختبار تشخيصي - قراءة مباشرة من قاعدة البيانات")
print("="*70)

# اختر معرف الجلسة (استبدله بالمعرف الفعلي عندك)
session_id = int(input("\nأدخل معرف الجلسة (session_id): "))

print(f"\n{'='*70}")
print(f"قراءة بيانات الجلسة {session_id}")
print(f"{'='*70}")

# قراءة بيانات الجلسة
cursor.execute("""
    SELECT id, status, is_paused, start_time, paused_at, total_paused_duration
    FROM sessions 
    WHERE id = ?
""", (session_id,))

session_row = cursor.fetchone()

if session_row:
    print(f"\n📊 بيانات الجلسة:")
    print(f"   ID: {session_row[0]}")
    print(f"   Status: {session_row[1]}")
    print(f"   is_paused: {session_row[2]}")
    print(f"   start_time: {session_row[3]}")
    print(f"   paused_at: {session_row[4]}")
    print(f"   total_paused_duration: {session_row[5]} ثانية ({session_row[5] / 60 if session_row[5] else 0:.2f} دقيقة)")
    
    # حساب الوقت
    start_time = datetime.strptime(session_row[3], '%Y-%m-%d %H:%M:%S.%f') if '.' in session_row[3] else datetime.strptime(session_row[3], '%Y-%m-%d %H:%M:%S')
    current_time = datetime.now()
    
    total_seconds = int((current_time - start_time).total_seconds())
    paused_seconds = session_row[5] if session_row[5] else 0
    actual_seconds = total_seconds - paused_seconds
    
    print(f"\n⏱️ حساب الوقت:")
    print(f"   الوقت الإجمالي: {total_seconds} ثانية ({total_seconds / 60:.2f} دقيقة)")
    print(f"   الوقت المتوقف: {paused_seconds} ثانية ({paused_seconds / 60:.2f} دقيقة)")
    print(f"   الوقت الفعلي: {actual_seconds} ثانية ({actual_seconds / 60:.2f} دقيقة)")
else:
    print(f"❌ الجلسة {session_id} غير موجودة!")

print(f"\n{'='*70}")
print(f"قراءة أجزاء التسعيرة للجلسة {session_id}")
print(f"{'='*70}")

# قراءة أجزاء التسعيرة
cursor.execute("""
    SELECT id, pricing_type, start_time, end_time, is_active, is_paused, 
           paused_at, paused_duration_seconds
    FROM pricing_segments
    WHERE session_id = ?
    ORDER BY start_time
""", (session_id,))

segments = cursor.fetchall()

print(f"\nعدد الأجزاء: {len(segments)}")

for i, seg in enumerate(segments, 1):
    print(f"\n📍 جزء {i}:")
    print(f"   ID: {seg[0]}")
    print(f"   النوع: {seg[1]}")
    print(f"   start_time: {seg[2]}")
    print(f"   end_time: {seg[3]}")
    print(f"   is_active: {seg[4]}")
    print(f"   is_paused: {seg[5]}")
    print(f"   paused_at: {seg[6]}")
    print(f"   paused_duration_seconds: {seg[7]} ثانية ({seg[7] / 60 if seg[7] else 0:.2f} دقيقة)")
    
    # حساب الوقت للجزء النشط
    if seg[4] == 1:  # is_active
        start_time = datetime.strptime(seg[2], '%Y-%m-%d %H:%M:%S.%f') if '.' in seg[2] else datetime.strptime(seg[2], '%Y-%m-%d %H:%M:%S')
        
        if seg[3]:  # has end_time
            end_time = datetime.strptime(seg[3], '%Y-%m-%d %H:%M:%S.%f') if '.' in seg[3] else datetime.strptime(seg[3], '%Y-%m-%d %H:%M:%S')
            total_dur = int((end_time - start_time).total_seconds())
        else:
            total_dur = int((current_time - start_time).total_seconds())
        
        paused_dur = seg[7] if seg[7] else 0
        actual_dur = total_dur - paused_dur
        
        print(f"\n   📊 الحساب:")
        print(f"      المدة الإجمالية: {total_dur} ثانية ({total_dur / 60:.2f} دقيقة)")
        print(f"      المدة المتوقفة: {paused_dur} ثانية ({paused_dur / 60:.2f} دقيقة)")
        print(f"      المدة الفعلية: {actual_dur} ثانية ({actual_dur / 60:.2f} دقيقة)")
        print(f"      المدة الفعلية بالساعات: {actual_dur / 3600:.4f} ساعة")

conn.close()

print(f"\n{'='*70}")
print("انتهى الاختبار")
print("="*70)
print("\n⚠️ يرجى إرسال جميع النتائج أعلاه!")

