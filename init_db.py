#!/usr/bin/env python3
"""
سكريبت تهيئة قاعدة البيانات
Database Initialization Script
"""

import sys
import os
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """تهيئة قاعدة البيانات"""
    try:
        print("🔧 بدء تهيئة قاعدة البيانات...")
        
        # استيراد مدير قاعدة البيانات
        from database import get_db_manager, init_database
        
        # تهيئة قاعدة البيانات
        print("📊 إنشاء الجداول...")
        success = init_database()
        
        if success:
            print("✅ تم إنشاء قاعدة البيانات بنجاح!")
            
            # اختبار الاتصال
            db = get_db_manager()
            status = db.get_connection_status()
            print(f"🔗 حالة الاتصال: {status}")
            
            # التحقق من الجداول
            tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            print(f"📋 الجداول المنشأة: {len(tables)}")
            for table in tables:
                print(f"   - {table['name']}")
            
            # التحقق من قوالب الورديات
            shift_templates = db.execute_query("SELECT COUNT(*) as count FROM shift_templates")
            if shift_templates:
                print(f"⏰ قوالب الورديات: {shift_templates[0]['count']}")
            
            # التحقق من المستخدمين
            users = db.execute_query("SELECT COUNT(*) as count FROM users")
            if users:
                print(f"👥 المستخدمين: {users[0]['count']}")
            
            print("\n🎉 تم تهيئة قاعدة البيانات بنجاح!")
            return True
            
        else:
            print("❌ فشل في إنشاء قاعدة البيانات")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ يمكنك الآن تشغيل التطبيق الرئيسي")
    else:
        print("\n❌ يرجى مراجعة الأخطاء أعلاه")
    
    input("\nاضغط Enter للخروج...")

