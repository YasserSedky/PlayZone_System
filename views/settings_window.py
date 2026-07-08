"""
نافذة إعدادات النظام
System Settings Window
"""

import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDialogButtonBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QTextEdit, QSlider, QFileDialog, QListWidget,
    QListWidgetItem, QMenu, QSplitter, QTreeWidget, QTreeWidgetItem,
    QInputDialog
)
from PySide6.QtGui import QIntValidator, QFont, QPixmap, QIcon, QPalette, QColor
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user_model import UserModel
from models.device_model import DeviceModel
from utils.helpers import format_currency
from utils.notifications import show_error, show_success
import logging

logger = logging.getLogger(__name__)

class SettingsWindow(QMainWindow):
    """نافذة إعدادات النظام"""
    
    # إشارة لتحديث الإعدادات
    settings_changed = Signal()
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.settings_file = "config/system_settings.json"
        self.settings = self.load_settings()
        self.backup_scheduler = None
        self.setup_ui()
        self.load_current_settings()
        self.initialize_auto_backup()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إعدادات النظام - PS System")
        self.setGeometry(100, 100, 1000, 700)
        
        # المركز الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        
        # شريط العنوان
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        
        title_label = QLabel("⚙️ إعدادات النظام")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        main_layout.addWidget(title_frame)
        
        # تبويبات الإعدادات
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5dade2;
                color: white;
            }
        """)
        
        # إنشاء التبويبات
        self.create_password_change_tab()
        self.create_backup_settings_tab()
        self.create_permissions_tab()
        
        main_layout.addWidget(self.tab_widget)
    
    
    def create_password_change_tab(self):
        """إنشاء تبويب تغيير كلمة مرور المدير"""
        password_widget = QWidget()
        layout = QVBoxLayout(password_widget)
        
        # عنوان التبويب
        title_label = QLabel("🔐 تغيير كلمة مرور المدير")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # إرشادات
        instructions_label = QLabel("لأمان النظام، يرجى اختيار كلمة مرور قوية تحتوي على أرقام وحروف")
        instructions_label.setAlignment(Qt.AlignCenter)
        instructions_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 30px;")
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
        
        # مجموعة تغيير كلمة المرور
        password_group = QGroupBox("تغيير كلمة المرور")
        password_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        password_layout = QFormLayout(password_group)
        
        # كلمة المرور الحالية
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.Password)
        self.current_password_edit.setPlaceholderText("أدخل كلمة المرور الحالية")
        password_layout.addRow("كلمة المرور الحالية:", self.current_password_edit)
        
        # كلمة المرور الجديدة
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        self.new_password_edit.setPlaceholderText("أدخل كلمة المرور الجديدة")
        password_layout.addRow("كلمة المرور الجديدة:", self.new_password_edit)
        
        # تأكيد كلمة المرور
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("أعد إدخال كلمة المرور الجديدة")
        password_layout.addRow("تأكيد كلمة المرور:", self.confirm_password_edit)
        
        layout.addWidget(password_group)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        change_password_btn = QPushButton("🔐 تغيير كلمة المرور")
        change_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        change_password_btn.clicked.connect(self.change_admin_password)
        
        clear_btn = QPushButton("🗑️ مسح الحقول")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        clear_btn.clicked.connect(self.clear_password_fields)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(change_password_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(password_widget, "🔐 تغيير كلمة المرور")
    
    
    def create_backup_settings_tab(self):
        """إنشاء تبويب إعدادات النسخ الاحتياطي"""
        backup_widget = QWidget()
        layout = QVBoxLayout(backup_widget)
        
        # إعدادات النسخ الاحتياطي
        backup_group = QGroupBox("إعدادات النسخ الاحتياطي")
        backup_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        backup_layout = QFormLayout(backup_group)
        
        # النسخ الاحتياطي التلقائي
        self.auto_backup_checkbox = QCheckBox("تفعيل النسخ الاحتياطي التلقائي")
        self.auto_backup_checkbox.stateChanged.connect(self.on_auto_backup_changed)
        backup_layout.addRow("", self.auto_backup_checkbox)
        
        # تردد النسخ الاحتياطي
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["يومياً", "أسبوعياً", "شهرياً"])
        self.backup_frequency_combo.currentTextChanged.connect(self.save_backup_settings)
        backup_layout.addRow("تردد النسخ الاحتياطي:", self.backup_frequency_combo)
        
        # عدد النسخ الاحتياطية المحفوظة
        self.keep_backups_spinbox = QSpinBox()
        self.keep_backups_spinbox.setMinimum(1)
        self.keep_backups_spinbox.setMaximum(100)
        self.keep_backups_spinbox.setValue(10)
        self.keep_backups_spinbox.valueChanged.connect(self.save_backup_settings)
        backup_layout.addRow("عدد النسخ المحفوظة:", self.keep_backups_spinbox)
        
        # مجلد النسخ الاحتياطي
        backup_folder_layout = QHBoxLayout()
        self.backup_folder_edit = QLineEdit()
        self.backup_folder_edit.setPlaceholderText("مجلد النسخ الاحتياطي")
        backup_folder_edit_btn = QPushButton("📁 استعراض")
        backup_folder_edit_btn.clicked.connect(self.select_backup_folder)
        backup_folder_layout.addWidget(self.backup_folder_edit)
        backup_folder_layout.addWidget(backup_folder_edit_btn)
        backup_layout.addRow("مجلد النسخ الاحتياطي:", backup_folder_layout)
        
        layout.addWidget(backup_group)
        
        # أزرار النسخ الاحتياطي
        backup_actions_group = QGroupBox("إجراءات النسخ الاحتياطي")
        backup_actions_group.setStyleSheet(backup_group.styleSheet())
        backup_actions_layout = QHBoxLayout(backup_actions_group)
        
        create_backup_btn = QPushButton("💾 إنشاء نسخة احتياطية")
        create_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        create_backup_btn.clicked.connect(self.create_backup)
        
        
        refresh_backups_btn = QPushButton("🔄 تحديث القائمة")
        refresh_backups_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        refresh_backups_btn.clicked.connect(self.load_backups)
        
        test_auto_backup_btn = QPushButton("🧪 اختبار النسخ التلقائي")
        test_auto_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        test_auto_backup_btn.clicked.connect(self.test_auto_backup)
        
        backup_actions_layout.addWidget(create_backup_btn)
        backup_actions_layout.addWidget(refresh_backups_btn)
        backup_actions_layout.addWidget(test_auto_backup_btn)
        backup_actions_layout.addStretch()
        
        layout.addWidget(backup_actions_group)
        
        # قائمة النسخ الاحتياطية
        backups_group = QGroupBox("النسخ الاحتياطية المتاحة")
        backups_group.setStyleSheet(backup_group.styleSheet())
        backups_layout = QVBoxLayout(backups_group)
        
        self.backups_list = QListWidget()
        backups_layout.addWidget(self.backups_list)
        
        layout.addWidget(backups_group)
        
        # تحديث قائمة النسخ الاحتياطية
        self.load_backups()
        
        self.tab_widget.addTab(backup_widget, "💾 النسخ الاحتياطية")
    
    def load_settings(self):
        """تحميل الإعدادات من الملف"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.get_default_settings()
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
            return self.get_default_settings()
    
    def get_default_settings(self):
        """الحصول على الإعدادات الافتراضية"""
        return {
            "backup": {
                "auto_backup": False,
                "frequency": "يومياً",
                "folder": "backups/",
                "keep_count": 10
            }
        }
    
    def load_current_settings(self):
        """تحميل الإعدادات الحالية في الواجهة"""
        try:
            # إعدادات النسخ الاحتياطي
            self.auto_backup_checkbox.setChecked(self.settings.get("backup", {}).get("auto_backup", False))
            self.backup_frequency_combo.setCurrentText(self.settings.get("backup", {}).get("frequency", "يومياً"))
            self.backup_folder_edit.setText(self.settings.get("backup", {}).get("folder", "backups/"))
            self.keep_backups_spinbox.setValue(self.settings.get("backup", {}).get("keep_count", 10))
            
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
    
    def on_auto_backup_changed(self):
        """عند تغيير حالة النسخ الاحتياطي التلقائي"""
        try:
            self.save_backup_settings()
            
            if self.auto_backup_checkbox.isChecked():
                from utils.backup_manager import BackupManager
                from utils.auto_backup_scheduler import AutoBackupScheduler
                
                backup_folder = self.backup_folder_edit.text().strip() or "backups"
                backup_manager = BackupManager(backup_folder)
                frequency = self.backup_frequency_combo.currentText()
                
                # إنشاء مدير النسخ الاحتياطي التلقائي
                scheduler = AutoBackupScheduler(backup_manager, self.on_backup_callback)
                success, message = scheduler.start_scheduler(frequency, True)
                
                if success:
                    show_success(f"تم تفعيل النسخ الاحتياطي التلقائي: {frequency}")
                    # حفظ مرجع الجدولة
                    self.backup_scheduler = scheduler
                else:
                    show_error(message)
            else:
                if hasattr(self, 'backup_scheduler') and self.backup_scheduler:
                    self.backup_scheduler.stop_scheduler()
                    show_success("تم إلغاء النسخ الاحتياطي التلقائي")
                
        except Exception as e:
            show_error(f"خطأ في تحديث إعدادات النسخ الاحتياطي التلقائي: {str(e)}")
    
    def on_backup_callback(self, success: bool, message: str):
        """callback للنسخ الاحتياطي التلقائي"""
        try:
            if success:
                show_success(f"نسخة احتياطية تلقائية: {message}")
            else:
                show_error(f"خطأ في النسخة الاحتياطية التلقائية: {message}")
        except Exception as e:
            logger.error(f"خطأ في callback النسخة الاحتياطية: {e}")
    
    def initialize_auto_backup(self):
        """تهيئة النسخ الاحتياطي التلقائي"""
        try:
            # التحقق من تفعيل النسخ الاحتياطي التلقائي
            auto_backup_enabled = self.settings.get("backup", {}).get("auto_backup", False)
            
            if auto_backup_enabled:
                from utils.backup_manager import BackupManager
                from utils.auto_backup_scheduler import AutoBackupScheduler
                
                backup_folder = self.settings.get("backup", {}).get("folder", "backups/")
                frequency = self.settings.get("backup", {}).get("frequency", "شهرياً")
                
                backup_manager = BackupManager(backup_folder)
                scheduler = AutoBackupScheduler(backup_manager, self.on_backup_callback)
                success, message = scheduler.start_scheduler(frequency, True)
                
                if success:
                    self.backup_scheduler = scheduler
                    logger.info(f"تم تهيئة النسخ الاحتياطي التلقائي: {frequency}")
                else:
                    logger.error(f"فشل في تهيئة النسخ الاحتياطي التلقائي: {message}")
                    
        except Exception as e:
            logger.error(f"خطأ في تهيئة النسخ الاحتياطي التلقائي: {e}")
    
    def closeEvent(self, event):
        """عند إغلاق النافذة"""
        try:
            # إيقاف الجدولة عند إغلاق النافذة
            if hasattr(self, 'backup_scheduler') and self.backup_scheduler:
                self.backup_scheduler.stop_scheduler()
            event.accept()
        except Exception as e:
            logger.error(f"خطأ في إغلاق نافذة الإعدادات: {e}")
            event.accept()
    
    def change_admin_password(self):
        """تغيير كلمة مرور المدير"""
        try:
            current_password = self.current_password_edit.text()
            new_password = self.new_password_edit.text()
            confirm_password = self.confirm_password_edit.text()
            
            # التحقق من صحة البيانات
            if not current_password:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة المرور الحالية")
                return
            
            if not new_password:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة المرور الجديدة")
                return
            
            if len(new_password) < 6:
                QMessageBox.warning(self, "خطأ", "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                return
            
            if new_password != confirm_password:
                QMessageBox.warning(self, "خطأ", "كلمة المرور الجديدة وتأكيدها غير متطابقتين")
                return
            
            user_model = UserModel()
            
            # التحقق من كلمة المرور الحالية
            if not user_model.verify_password(self.current_user['username'], current_password):
                # إذا فشل التحقق، قد تكون كلمة المرور تستخدم النظام القديم
                # نحاول تحديث كلمة مرور المدير للنظام الجديد أولاً
                if user_model.update_admin_password_to_new_system(current_password):
                    # الآن نحاول التحقق مرة أخرى
                    if not user_model.verify_password(self.current_user['username'], current_password):
                        QMessageBox.warning(self, "خطأ", "كلمة المرور الحالية غير صحيحة")
                        return
                else:
                    QMessageBox.warning(self, "خطأ", "كلمة المرور الحالية غير صحيحة")
                    return
            
            # تغيير كلمة المرور
            if user_model.change_password(self.current_user['id'], new_password):
                QMessageBox.information(self, "نجح", "تم تغيير كلمة المرور بنجاح")
                self.clear_password_fields()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تغيير كلمة المرور")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تغيير كلمة المرور: {str(e)}")
    
    def clear_password_fields(self):
        """مسح حقول كلمة المرور"""
        self.current_password_edit.clear()
        self.new_password_edit.clear()
        self.confirm_password_edit.clear()
    
    def select_backup_folder(self):
        """اختيار مجلد النسخ الاحتياطي"""
        folder = QFileDialog.getExistingDirectory(self, "اختيار مجلد النسخ الاحتياطي")
        if folder:
            self.backup_folder_edit.setText(folder)
            # حفظ الإعداد الجديد
            self.save_backup_settings()
            show_success(f"تم اختيار مجلد النسخ الاحتياطي: {folder}")
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            from utils.backup_manager import BackupManager
            
            # الحصول على مجلد النسخ الاحتياطي
            backup_folder = self.backup_folder_edit.text().strip()
            if not backup_folder:
                backup_folder = "backups"
            
            # إظهار رسالة بدء العملية
            show_success("جاري إنشاء النسخة الاحتياطية...")
            
            # إنشاء مدير النسخ الاحتياطي
            backup_manager = BackupManager(backup_folder)
            
            # طلب اسم النسخة الاحتياطية
            backup_name, ok = QInputDialog.getText(
                self, 
                "اسم النسخة الاحتياطية", 
                "أدخل اسم النسخة الاحتياطية (اختياري):",
                text=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not ok:
                return
            
            # إنشاء النسخة الاحتياطية
            success, message = backup_manager.create_backup(backup_name if backup_name.strip() else None)
            
            if success:
                show_success(message)
                # تنظيف النسخ القديمة
                keep_count = self.keep_backups_spinbox.value()
                cleanup_success, cleanup_message = backup_manager.cleanup_old_backups(keep_count)
                if cleanup_success and "تم حذف" in cleanup_message:
                    show_success(f"{message}\n{cleanup_message}")
                else:
                    show_success(message)
                # تحديث قائمة النسخ الاحتياطية
                self.load_backups()
            else:
                show_error(message)
                
        except Exception as e:
            show_error(f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")
    
    def load_backups(self):
        """تحميل قائمة النسخ الاحتياطية"""
        try:
            from utils.backup_manager import BackupManager
            
            # مسح القائمة الحالية
            self.backups_list.clear()
            
            # الحصول على مجلد النسخ الاحتياطي
            backup_folder = self.backup_folder_edit.text().strip()
            if not backup_folder:
                backup_folder = "backups"
            
            # إنشاء مدير النسخ الاحتياطي
            backup_manager = BackupManager(backup_folder)
            
            # الحصول على قائمة النسخ الاحتياطية
            backups = backup_manager.get_backups_list()
            
            if not backups:
                item = QListWidgetItem("لا توجد نسخ احتياطية متاحة")
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.backups_list.addItem(item)
                show_success("تم تحديث قائمة النسخ الاحتياطية - لا توجد نسخ متاحة")
                return
            
            # إضافة النسخ الاحتياطية إلى القائمة
            for backup in backups:
                # تنسيق النص المعروض
                created_date = datetime.fromisoformat(backup['created_at']).strftime("%Y-%m-%d %H:%M")
                display_text = f"{backup['backup_name']} - {created_date} ({backup['file_size']})"
                
                item = QListWidgetItem(display_text)
                item.setData(1, backup)  # تخزين معلومات النسخة الاحتياطية
                self.backups_list.addItem(item)
            
            show_success(f"تم تحديث قائمة النسخ الاحتياطية - {len(backups)} نسخة متاحة")
                
        except Exception as e:
            show_error(f"خطأ في تحميل قائمة النسخ الاحتياطية: {str(e)}")
    
    def save_backup_settings(self):
        """حفظ إعدادات النسخ الاحتياطي"""
        try:
            # تحديث الإعدادات
            self.settings["backup"] = {
                "auto_backup": self.auto_backup_checkbox.isChecked(),
                "frequency": self.backup_frequency_combo.currentText(),
                "folder": self.backup_folder_edit.text(),
                "keep_count": self.keep_backups_spinbox.value()
            }
            
            # حفظ في الملف
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"خطأ في حفظ إعدادات النسخ الاحتياطي: {e}")
    
    def test_auto_backup(self):
        """اختبار النسخ الاحتياطي التلقائي"""
        try:
            if not hasattr(self, 'backup_scheduler') or not self.backup_scheduler:
                show_error("النسخ الاحتياطي التلقائي غير مفعل")
                return
            
            # تأكيد الاختبار
            reply = QMessageBox.question(
                self,
                "تأكيد الاختبار",
                "هل تريد إنشاء نسخة احتياطية تلقائية للاختبار؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = self.backup_scheduler.force_backup()
                
                if success:
                    show_success("تم إنشاء النسخة الاحتياطية التلقائية للاختبار بنجاح")
                    # تحديث قائمة النسخ الاحتياطية
                    self.load_backups()
                else:
                    show_error(f"فشل في إنشاء النسخة الاحتياطية للاختبار: {message}")
                    
        except Exception as e:
            show_error(f"خطأ في اختبار النسخ الاحتياطي التلقائي: {str(e)}")
    
    def create_permissions_tab(self):
        """إنشاء تبويب إدارة الصلاحيات"""
        permissions_widget = QWidget()
        layout = QVBoxLayout(permissions_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # عنوان التبويب
        title_label = QLabel("🔐 إدارة صلاحيات الكاشيرز")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #2c3e50;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            border-left: 5px solid #3498db;
        """)
        layout.addWidget(title_label)
        
        # إرشادات
        instructions_label = QLabel("اختر كاشير من القائمة المنسدلة ثم حدد الصلاحيات التي تريد منحها له")
        instructions_label.setAlignment(Qt.AlignCenter)
        instructions_label.setStyleSheet("""
            font-size: 14px; 
            color: #7f8c8d; 
            margin-bottom: 30px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
        """)
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
        
        # إطار اختيار الكاشير
        cashier_frame = QFrame()
        cashier_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e9ecef;
                padding: 20px;
            }
        """)
        cashier_layout = QVBoxLayout(cashier_frame)
        cashier_layout.setSpacing(15)
        
        # عنوان اختيار الكاشير
        cashier_title = QLabel("👤 اختيار الكاشير")
        cashier_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        cashier_layout.addWidget(cashier_title)
        
        # قائمة منسدلة للكاشيرز
        cashier_selection_layout = QHBoxLayout()
        cashier_selection_layout.setSpacing(15)
        
        cashier_label = QLabel("الكاشير:")
        cashier_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; min-width: 80px;")
        cashier_selection_layout.addWidget(cashier_label)
        
        self.cashier_combo = QComboBox()
        self.cashier_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background: white;
                min-width: 250px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #6c757d;
                margin-right: 8px;
            }
        """)
        self.cashier_combo.currentTextChanged.connect(self.on_cashier_selected)
        cashier_selection_layout.addWidget(self.cashier_combo)
        cashier_selection_layout.addStretch()
        
        cashier_layout.addLayout(cashier_selection_layout)
        layout.addWidget(cashier_frame)
        
        # إطار الصلاحيات
        permissions_frame = QFrame()
        permissions_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e9ecef;
                padding: 20px;
            }
        """)
        permissions_layout = QVBoxLayout(permissions_frame)
        permissions_layout.setSpacing(15)
        
        # عنوان الصلاحيات
        permissions_title = QLabel("🔑 الصلاحيات المتاحة")
        permissions_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        permissions_layout.addWidget(permissions_title)
        
        # معلومات الكاشير المحدد
        self.selected_cashier_info = QLabel("اختر كاشير من القائمة المنسدلة أعلاه")
        self.selected_cashier_info.setStyleSheet("""
            font-size: 13px; 
            color: #6c757d; 
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 15px;
        """)
        self.selected_cashier_info.setWordWrap(True)
        permissions_layout.addWidget(self.selected_cashier_info)
        
        # الصلاحيات
        self.permissions_layout = QVBoxLayout()
        self.permissions_layout.setSpacing(10)
        
        # إنشاء الصلاحيات المحددة
        self.create_permission_checkboxes()
        
        permissions_layout.addLayout(self.permissions_layout)
        layout.addWidget(permissions_frame)
        
        # أزرار التحكم
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e9ecef;
                padding: 20px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(15)
        
        save_permissions_btn = QPushButton("💾 حفظ الصلاحيات")
        save_permissions_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #20c997);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1ea085);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        save_permissions_btn.clicked.connect(self.save_cashier_permissions)
        save_permissions_btn.setEnabled(False)
        self.save_permissions_btn = save_permissions_btn
        
        reset_permissions_btn = QPushButton("🔄 إعادة تعيين")
        reset_permissions_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e67e22, stop:1 #d35400);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d35400, stop:1 #c0392b);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        reset_permissions_btn.clicked.connect(self.reset_cashier_permissions)
        reset_permissions_btn.setEnabled(False)
        self.reset_permissions_btn = reset_permissions_btn
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(reset_permissions_btn)
        buttons_layout.addWidget(save_permissions_btn)
        
        layout.addWidget(buttons_frame)
        layout.addStretch()
        
        # تحميل الكاشيرز
        self.load_cashiers()
        
        self.tab_widget.addTab(permissions_widget, "🔐 إدارة الصلاحيات")
    
    def create_permission_checkboxes(self):
        """إنشاء checkboxes الصلاحيات المحددة"""
        # الصلاحيات المحددة كما طلب المستخدم
        permissions = [
            ("إضافة جهاز", "add_device"),
            ("حذف جهاز", "delete_device"),
            ("حذف فاتورة", "delete_invoice"),
            ("حذف مصروف", "delete_expense"),
            ("إضافة منتج", "add_product"),
            ("تعديل منتج", "edit_product"),
            ("حذف الحساب", "delete_account")
        ]
        
        self.permission_checkboxes = {}
        
        for permission_name, permission_key in permissions:
            checkbox = QCheckBox(permission_name)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 12px;
                    margin: 5px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #e9ecef;
                }
                QCheckBox:hover {
                    background-color: #e9ecef;
                    border-color: #3498db;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #bdc3c7;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #27ae60;
                    border-color: #27ae60;
                    image: none;
                }
                QCheckBox::indicator:checked:after {
                    content: "✓";
                    color: white;
                    font-weight: bold;
                }
            """)
            
            self.permission_checkboxes[permission_key] = checkbox
            self.permissions_layout.addWidget(checkbox)
    
    def load_cashiers(self):
        """تحميل قائمة الكاشيرز في القائمة المنسدلة"""
        try:
            from models.user_model import UserModel
            
            # مسح القائمة الحالية
            self.cashier_combo.clear()
            
            # إضافة خيار افتراضي
            self.cashier_combo.addItem("اختر كاشير...", None)
            
            # الحصول على الكاشيرز
            user_model = UserModel()
            cashiers = user_model.get_cashiers()
            
            if not cashiers:
                self.cashier_combo.addItem("لا يوجد كاشيرز في النظام", None)
                return
            
            # إضافة الكاشيرز إلى القائمة المنسدلة
            for cashier in cashiers:
                status = "مفعل" if cashier.get('enabled', True) else "معطل"
                display_text = f"{cashier['username']} ({status})"
                
                self.cashier_combo.addItem(display_text, cashier)
                
        except Exception as e:
            show_error(f"خطأ في تحميل قائمة الكاشيرز: {str(e)}")
    
    def on_cashier_selected(self, text):
        """عند اختيار كاشير من القائمة المنسدلة"""
        try:
            # الحصول على بيانات الكاشير المحدد
            current_index = self.cashier_combo.currentIndex()
            cashier_data = self.cashier_combo.itemData(current_index)
            
            if not cashier_data:
                # إعادة تعيين المعلومات
                self.selected_cashier_info.setText("اختر كاشير من القائمة المنسدلة أعلاه")
                self.reset_permission_checkboxes()
                self.save_permissions_btn.setEnabled(False)
                self.reset_permissions_btn.setEnabled(False)
                return
            
            # عرض معلومات الكاشير
            self.selected_cashier_info.setText(
                f"الكاشير: {cashier_data['username']}\n"
                f"الاسم الكامل: {cashier_data.get('full_name', 'غير محدد')}\n"
                f"الهاتف: {cashier_data.get('phone', 'غير محدد')}\n"
                f"الحالة: {'مفعل' if cashier_data.get('enabled', True) else 'معطل'}"
            )
            
            # تحميل صلاحيات الكاشير
            self.load_cashier_permissions(cashier_data)
            
            # تفعيل الأزرار
            self.save_permissions_btn.setEnabled(True)
            self.reset_permissions_btn.setEnabled(True)
            
        except Exception as e:
            show_error(f"خطأ في اختيار الكاشير: {str(e)}")
    
    def load_cashier_permissions(self, cashier_data):
        """تحميل صلاحيات الكاشير"""
        try:
            # إعادة تعيين جميع الصلاحيات إلى غير محددة
            self.reset_permission_checkboxes()
            
            # تحميل الصلاحيات المحفوظة من قاعدة البيانات
            from models.user_permissions_model import UserPermissionsModel
            permissions_model = UserPermissionsModel()
            
            # الحصول على صلاحيات الكاشير
            user_permissions = permissions_model.get_user_permissions(cashier_data['id'])
            
            # تحديد الصلاحيات الممنوحة
            for permission_key, checkbox in self.permission_checkboxes.items():
                if permission_key in user_permissions:
                    checkbox.setChecked(True)
            
        except Exception as e:
            show_error(f"خطأ في تحميل صلاحيات الكاشير: {str(e)}")
    
    def reset_permission_checkboxes(self):
        """إعادة تعيين جميع الصلاحيات إلى غير محددة"""
        try:
            for checkbox in self.permission_checkboxes.values():
                checkbox.setChecked(False)
        except Exception as e:
            show_error(f"خطأ في إعادة تعيين الصلاحيات: {str(e)}")
    
    
    def save_cashier_permissions(self):
        """حفظ صلاحيات الكاشير"""
        try:
            # الحصول على الكاشير المحدد
            current_index = self.cashier_combo.currentIndex()
            cashier_data = self.cashier_combo.itemData(current_index)
            
            if not cashier_data:
                show_error("يرجى اختيار كاشير أولاً")
                return
            
            # جمع الصلاحيات المحددة
            selected_permissions = []
            for permission_key, checkbox in self.permission_checkboxes.items():
                if checkbox.isChecked():
                    selected_permissions.append(permission_key)
            
            # حفظ الصلاحيات في قاعدة البيانات
            from models.user_permissions_model import UserPermissionsModel
            permissions_model = UserPermissionsModel()
            
            # تعيين الصلاحيات للمستخدم
            success = permissions_model.set_user_permissions(
                cashier_data['id'], 
                selected_permissions, 
                self.current_user.get('id')
            )
            
            if success:
                # عرض الصلاحيات المحددة
                if selected_permissions:
                    permissions_text = "، ".join(selected_permissions)
                    show_success(f"تم حفظ الصلاحيات التالية للكاشير {cashier_data['username']}:\n{permissions_text}")
                else:
                    show_success(f"تم إزالة جميع الصلاحيات من الكاشير {cashier_data['username']}")
            else:
                show_error("فشل في حفظ الصلاحيات. يرجى المحاولة مرة أخرى")
            
        except Exception as e:
            show_error(f"خطأ في حفظ صلاحيات الكاشير: {str(e)}")
    
    def reset_cashier_permissions(self):
        """إعادة تعيين صلاحيات الكاشير"""
        try:
            # الحصول على الكاشير المحدد
            current_index = self.cashier_combo.currentIndex()
            cashier_data = self.cashier_combo.itemData(current_index)
            
            if not cashier_data:
                show_error("يرجى اختيار كاشير أولاً")
                return
            
            # تأكيد إعادة التعيين
            reply = QMessageBox.question(
                self,
                "تأكيد إعادة التعيين",
                f"هل تريد إزالة جميع الصلاحيات من الكاشير {cashier_data['username']}؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # إعادة تعيين جميع الصلاحيات
                self.reset_permission_checkboxes()
                show_success("تم إزالة جميع الصلاحيات من الكاشير")
            
        except Exception as e:
            show_error(f"خطأ في إعادة تعيين صلاحيات الكاشير: {str(e)}")
    
