"""
أداة تنظيف ملفات السجلات القديمة الكبيرة
Cleanup Tool for Old Large Log Files

هذا السكريبت يساعد في تنظيف ملفات السجلات القديمة الكبيرة
التي تم إنشاؤها قبل تطبيق RotatingFileHandler
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def format_size(size_bytes):
    """تحويل الحجم من بايت إلى وحدات قابلة للقراءة"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def scan_log_files(base_path="."):
    """فحص جميع ملفات السجلات"""
    log_files = []
    
    # الأنماط المطلوب البحث عنها
    patterns = [
        "*.log",
        "logs/*.log",
        "error_log.txt",
        "critical_errors.txt",
        "ps_system.log"
    ]
    
    base_path = Path(base_path)
    
    # البحث عن ملفات السجلات
    for pattern in patterns:
        for file_path in base_path.glob(pattern):
            if file_path.is_file():
                size = file_path.stat().st_size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                log_files.append({
                    'path': file_path,
                    'size': size,
                    'size_str': format_size(size),
                    'modified': modified,
                    'name': file_path.name
                })
    
    return sorted(log_files, key=lambda x: x['size'], reverse=True)


def display_log_files(log_files):
    """عرض ملفات السجلات"""
    print("\n" + "=" * 80)
    print("📊 ملفات السجلات الموجودة")
    print("=" * 80)
    
    if not log_files:
        print("✅ لا توجد ملفات سجلات")
        return
    
    total_size = 0
    large_files = []
    
    for idx, file_info in enumerate(log_files, 1):
        size = file_info['size']
        total_size += size
        
        # وضع علامة على الملفات الكبيرة (أكبر من 10 ميجابايت)
        marker = "🔴" if size > 10 * 1024 * 1024 else "🟢" if size > 5 * 1024 * 1024 else "⚪"
        
        print(f"{marker} {idx}. {file_info['name']}")
        print(f"   الحجم: {file_info['size_str']}")
        print(f"   التاريخ: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   المسار: {file_info['path']}")
        print()
        
        if size > 10 * 1024 * 1024:
            large_files.append(file_info)
    
    print("-" * 80)
    print(f"📦 إجمالي الحجم: {format_size(total_size)}")
    print(f"🔴 ملفات كبيرة (>10MB): {len(large_files)}")
    print("=" * 80)
    
    return large_files


def confirm_deletion():
    """طلب تأكيد الحذف"""
    while True:
        response = input("\n⚠️ هل تريد حذف هذه الملفات؟ (yes/no): ").strip().lower()
        if response in ['yes', 'y', 'نعم']:
            return True
        elif response in ['no', 'n', 'لا']:
            return False
        else:
            print("❌ إجابة غير صحيحة. يرجى الإجابة بـ yes أو no")


def delete_files(files_to_delete):
    """حذف الملفات"""
    deleted_count = 0
    deleted_size = 0
    failed = []
    
    print("\n" + "=" * 80)
    print("🗑️ بدء عملية الحذف...")
    print("=" * 80)
    
    for file_info in files_to_delete:
        try:
            file_path = file_info['path']
            size = file_info['size']
            
            # حذف الملف
            file_path.unlink()
            
            deleted_count += 1
            deleted_size += size
            
            print(f"✅ تم حذف: {file_info['name']} ({file_info['size_str']})")
            
        except Exception as e:
            failed.append({
                'file': file_info['name'],
                'error': str(e)
            })
            print(f"❌ فشل حذف: {file_info['name']} - الخطأ: {e}")
    
    # عرض النتائج
    print("\n" + "=" * 80)
    print("📊 ملخص عملية الحذف")
    print("=" * 80)
    print(f"✅ تم الحذف: {deleted_count} ملف")
    print(f"💾 تم توفير: {format_size(deleted_size)}")
    
    if failed:
        print(f"❌ فشل الحذف: {len(failed)} ملف")
        for item in failed:
            print(f"   - {item['file']}: {item['error']}")
    
    print("=" * 80)


def cleanup_old_logs():
    """الدالة الرئيسية للتنظيف"""
    print("\n" + "=" * 80)
    print("🧹 أداة تنظيف ملفات السجلات القديمة")
    print("=" * 80)
    print("هذه الأداة تساعد في تنظيف ملفات السجلات الكبيرة القديمة")
    print("=" * 80)
    
    # فحص الملفات
    print("\n🔍 جاري فحص ملفات السجلات...")
    log_files = scan_log_files()
    
    # عرض الملفات
    large_files = display_log_files(log_files)
    
    if not large_files:
        print("\n✅ لا توجد ملفات كبيرة للحذف!")
        return
    
    # عرض الملفات المقترحة للحذف
    print("\n" + "=" * 80)
    print("🗑️ الملفات المقترحة للحذف (أكبر من 10 ميجابايت):")
    print("=" * 80)
    
    total_to_delete = 0
    for file_info in large_files:
        print(f"🔴 {file_info['name']} - {file_info['size_str']}")
        total_to_delete += file_info['size']
    
    print("-" * 80)
    print(f"📦 سيتم توفير: {format_size(total_to_delete)}")
    print("=" * 80)
    
    # طلب التأكيد
    if confirm_deletion():
        delete_files(large_files)
    else:
        print("\n❌ تم إلغاء عملية الحذف")
    
    print("\n✅ انتهت عملية التنظيف")


def main():
    """نقطة البداية"""
    try:
        # تغيير المجلد الحالي إلى مجلد المشروع
        script_dir = Path(__file__).parent.parent
        os.chdir(script_dir)
        
        print(f"📁 مجلد العمل: {os.getcwd()}")
        
        # تشغيل التنظيف
        cleanup_old_logs()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ تم إيقاف البرنامج بواسطة المستخدم")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

