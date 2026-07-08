@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║         🎮 نظام إدارة محل البلايستيشن v2.0 🎮           ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 🚀 جاري تشغيل البرنامج...
echo.
echo ✨ المميزات الجديدة:
echo    • نظام الإداريات المتكامل
echo    • إدارة الموظفين والرواتب
echo    • المصاريف الإدارية
echo    • تقارير صافي الربح
echo.
echo ═══════════════════════════════════════════════════════════
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ❌ حدث خطأ في تشغيل البرنامج
    echo.
    echo 💡 تأكد من:
    echo    1. تثبيت Python
    echo    2. تثبيت المكتبات: pip install -r requirements.txt
    echo    3. وجود ملف main.py
    echo.
    pause
) else (
    echo.
    echo ✅ تم إغلاق البرنامج بنجاح
    echo.
)

pause

