"""
واجهة إدارة الأجهزة
Device Management Interface
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QDialogButtonBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QInputDialog, QListWidget, QListWidgetItem, QMenu
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from utils.helpers import format_currency

logger = logging.getLogger(__name__)

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.shift_model import ShiftModel
from models.invoice_model import InvoiceModel
from models.expense_model import ExpenseModel
from models.device_model import DeviceModel
from models.user_model import UserModel
from models.session_model import SessionModel
from models.product_model import ProductModel
from controllers.session_controller import SessionController

class DeviceCard(QFrame):
    """كارت الجهاز"""
    
    # إشارات
    device_clicked = Signal(dict)  # بيانات الجهاز
    context_menu_requested = Signal(dict, str)  # بيانات الجهاز ونوع الإجراء
    
    def __init__(self, device_data):
        super().__init__()
        self.device_data = device_data
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(165, 155)  # نفس حجم كروت العملاء
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border-radius: 10px;
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        # التخطيط الرئيسي
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # أيقونة الجهاز
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32px; margin-bottom: 5px;")
        layout.addWidget(self.icon_label)
        
        # اسم الجهاز
        self.name_label = QLabel(self.device_data.get('name', 'جهاز'))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(self.name_label)
        
        # عداد الوقت (يظهر فقط عند تشغيل الجهاز)
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.3); border-radius: 8px; padding: 4px;")
        layout.addWidget(self.timer_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
        
        # إخفاء عداد الوقت في البداية
        self.timer_label.hide()
    
    def update_status(self):
        """تحديث حالة الكارت"""
        status = self.device_data.get('status', 'available')
        current_session_id = self.device_data.get('current_session_id')
        device_type = self.device_data.get('type', '')
        
        # تحديث أيقونة الجهاز
        if device_type == 'PS':
            self.icon_label.setText("🎮")
        elif device_type == 'PC':
            self.icon_label.setText("💻")
        elif device_type == 'VR':
            self.icon_label.setText("🥽")
        elif device_type == 'Xbox':
            self.icon_label.setText("🎯")
        elif device_type == 'Nintendo':
            self.icon_label.setText("🎲")
        elif device_type == 'Arcade':
            self.icon_label.setText("🕹️")
        elif device_type == 'PingPong':
            self.icon_label.setText("🏓")
        elif device_type == 'Billiard':
            self.icon_label.setText("🎱")
        elif device_type == 'Pool':
            self.icon_label.setText("🎱")
        elif device_type == 'Foosball':
            self.icon_label.setText("⚽")
        else:
            self.icon_label.setText("🎮")
        
        if status == 'available':
            self.timer_label.hide()
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #2c3e50;
                    color: white;
                    border: 2px solid #34495e;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
            
        elif status == 'busy':
            # الحصول على معلومات الجلسة الحالية
            session_info = self.get_session_time_info()
            
            if session_info:
                time_type = session_info.get('time_type', 'fixed')
                elapsed_minutes = session_info.get('elapsed_minutes_total', 0)
                remaining_minutes = session_info.get('remaining_minutes_total', 0)
                is_expired = session_info.get('is_expired', False)
                is_warning = session_info.get('is_warning', False)
                is_paused = session_info.get('is_paused', False)
                
                # الحصول على الوقت المفصل
                elapsed_time_formatted = session_info.get('elapsed_time_formatted', f"{elapsed_minutes} دقيقة")
                remaining_time_formatted = session_info.get('remaining_time_formatted', f"{remaining_minutes} دقيقة")
                
                # إذا كانت الجلسة متوقفة - أزرق
                if is_paused:
                    self.setStyleSheet("""
                        QFrame {
                            border-radius: 10px;
                            background-color: #3498db;
                            color: white;
                            border: 2px solid #2980b9;
                        }
                        QLabel {
                            color: white;
                            font-weight: bold;
                        }
                    """)
                    self.timer_label.show()
                    if time_type == 'fixed':
                        self.timer_label.setText(f"⏸️ {remaining_time_formatted} (متوقف)")
                    else:
                        self.timer_label.setText(f"⏸️ {elapsed_time_formatted} (متوقف)")
                    self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
                
                elif time_type == 'fixed':
                    # جلسة بوقت محدد
                    if is_expired:
                        # انتهاء الوقت - أحمر
                        self.setStyleSheet("""
                            QFrame {
                                border-radius: 10px;
                                background-color: #e74c3c;
                                color: white;
                                border: 2px solid #c0392b;
                            }
                            QLabel {
                                color: white;
                                font-weight: bold;
                            }
                        """)
                        self.timer_label.show()
                        self.timer_label.setText("⏰ انتهى الوقت! (تم إيقاف العد)")
                        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
                        
                    elif is_warning:
                        # 5 دقائق متبقية - أصفر
                        self.setStyleSheet("""
                            QFrame {
                                border-radius: 10px;
                                background-color: #f39c12;
                                color: white;
                                border: 2px solid #e67e22;
                            }
                            QLabel {
                                color: white;
                                font-weight: bold;
                            }
                        """)
                        self.timer_label.show()
                        self.timer_label.setText(f"⏱️ {remaining_time_formatted}")
                        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
                        
                    else:
                        # قيد الاستخدام - أخضر
                        self.setStyleSheet("""
                            QFrame {
                                border-radius: 10px;
                                background-color: #27ae60;
                                color: white;
                                border: 2px solid #229954;
                            }
                            QLabel {
                                color: white;
                                font-weight: bold;
                            }
                        """)
                        self.timer_label.show()
                        self.timer_label.setText(f"⏱️ {remaining_time_formatted}")
                        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
                else:
                    # جلسة بوقت مفتوح - أخضر
                    self.setStyleSheet("""
                        QFrame {
                            border-radius: 10px;
                            background-color: #27ae60;
                            color: white;
                            border: 2px solid #229954;
                        }
                        QLabel {
                            color: white;
                            font-weight: bold;
                        }
                    """)
                    self.timer_label.show()
                    self.timer_label.setText(f"⏱️ {elapsed_time_formatted}")
                    self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
            else:
                # قيد الاستخدام بدون معلومات جلسة
                self.setStyleSheet("""
                    QFrame {
                        border-radius: 10px;
                        background-color: #27ae60;
                        color: white;
                        border: 2px solid #229954;
                    }
                    QLabel {
                        color: white;
                        font-weight: bold;
                    }
                """)
                self.timer_label.show()
                self.timer_label.setText("⏱️ قيد التشغيل")
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: rgba(0,0,0,0.5); border-radius: 8px; padding: 4px;")
        
        elif status == 'maintenance':
            self.setStyleSheet("""
                QFrame {
                    border-radius: 10px;
                    background-color: #95a5a6;
                    color: white;
                    border: 2px solid #7f8c8d;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
            self.timer_label.hide()
    
    def get_session_time_info(self):
        """الحصول على معلومات الوقت للجلسة الحالية"""
        try:
            current_session_id = self.device_data.get('current_session_id')
            if not current_session_id:
                return None
            
            # إنشاء مثيل SessionModel للحصول على معلومات الوقت
            from models.session_model import SessionModel
            session_model = SessionModel()
            time_info = session_model.get_session_time_info(current_session_id)
            
            # التحقق من حالة الجلسة في قاعدة البيانات
            session = session_model.get_session_by_id(current_session_id)
            if session and session.get('status') == 'paused':
                # الجلسة متوقفة - إضافة معلومة التوقف
                if time_info:
                    time_info['is_paused'] = True
                    time_info['paused_at'] = session.get('paused_at')
                    time_info['total_paused_duration'] = session.get('total_paused_duration', 0)
                else:
                    time_info = {
                        'is_paused': True,
                        'paused_at': session.get('paused_at'),
                        'total_paused_duration': session.get('total_paused_duration', 0)
                    }
            else:
                # الجلسة نشطة
                if time_info:
                    time_info['is_paused'] = False
                    
                    # التحقق من انتهاء الوقت للجلسات المحددة الوقت
                    if session and session.get('time_type') == 'fixed' and time_info.get('is_expired', False):
                        # إيقاف التايمر في نافذة الجلسة إذا كانت مفتوحة
                        if hasattr(self, 'session_window') and self.session_window:
                            if hasattr(self.session_window, 'stop_update_timer'):
                                self.session_window.stop_update_timer()
                                self.session_window.timer_stopped = True
                                print(f"تم إيقاف التايمر للجلسة {current_session_id} - انتهى الوقت المحدد")
            
            return time_info
            
        except Exception as e:
            print(f"خطأ في الحصول على معلومات الوقت: {e}")
            return None
    
    def mousePressEvent(self, event):
        """معالج الضغط على الكارت"""
        if event.button() == Qt.LeftButton:
            self.device_clicked.emit(self.device_data)
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
    
    def show_context_menu(self, position):
        """عرض قائمة السياق"""
        status = self.device_data.get('status', 'available')
        
        # إنشاء قائمة السياق
        context_menu = QMenu(self)
        
        if status == 'busy':
            # خيارات للأجهزة المشغولة
            delete_action = context_menu.addAction("🗑️ حذف الحساب")
            delete_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "delete_session"))
            
            edit_action = context_menu.addAction("✏️ تغيير بيانات الحساب")
            edit_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "edit_session"))
            
            # التحقق من وجود نوعي التسعيرة قبل إضافة خيار تغيير نوع التسعيرة
            device = self.device_data
            if device.get('price_single') and device.get('price_multi'):
                pricing_action = context_menu.addAction("💰 تغيير نوع التسعيرة")
                pricing_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "change_pricing_type"))
            
            transfer_action = context_menu.addAction("🔄 نقل الفاتورة")
            transfer_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "transfer_session"))
            
        elif status == 'available':
            # خيارات للأجهزة المتاحة
            maintenance_action = context_menu.addAction("🔧 وضع الصيانة")
            maintenance_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "maintenance_mode"))
            
            edit_action = context_menu.addAction("✏️ تعديل بيانات الجهاز")
            edit_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "edit_device"))
            
        elif status == 'maintenance':
            # خيارات للأجهزة في وضع الصيانة
            available_action = context_menu.addAction("✅ إزالة وضع الصيانة")
            available_action.triggered.connect(lambda: self.context_menu_requested.emit(self.device_data, "remove_maintenance"))
        
        # عرض القائمة
        context_menu.exec(position)
    
    def update_device_data(self, new_data):
        """تحديث بيانات الجهاز"""
        self.device_data.update(new_data)
        self.update_status()

class DeviceManagementWindow(QMainWindow):
    """نافذة إدارة الأجهزة"""
    
    # إشارات
    device_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.device_cards = {}
        self.device_tabs = {}
        self.shift_model = ShiftModel()
        self.invoice_model = InvoiceModel()
        self.expense_model = ExpenseModel()
        self.device_model = DeviceModel()
        self.user_model = UserModel()
        self.session_model = SessionModel()
        self.session_controller = SessionController(current_user)
        self.setup_ui()
        self.setup_connections()
        # استرداد حالة الأجهزة قبل تحميلها
        self.device_model.recover_device_sessions()
        # تحديث حالة الجلسات من مدير الجلسات
        self.update_sessions_from_manager()
        self.load_devices()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الأجهزة - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1400, 900)
        self.center_window()
        
        # إعداد الخلفية
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # إنشاء منطقة التمرير الرئيسية
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # إنشاء الـ widget الرئيسي
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # شريط الأدوات
        self.create_toolbar(main_layout)
        
        # تبويبات الأجهزة
        self.create_device_tabs(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("🎮 إدارة الأجهزة")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # عرض الكاشير الحالي
        self.current_cashier_label = QLabel(f"الكاشير الحالي: {self.current_user.get('full_name', self.current_user.get('username', 'غير محدد'))}")
        self.current_cashier_label.setStyleSheet("font-size: 14px; color: #2c3e50; font-weight: bold; padding: 5px;")
        toolbar_layout.addWidget(self.current_cashier_label)
        
        # أزرار التحكم
        
        self.add_device_btn = QPushButton("إضافة جهاز")
        self.add_device_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        self.add_device_btn.clicked.connect(self.add_device)
        toolbar_layout.addWidget(self.add_device_btn)
        
        self.delete_device_btn = QPushButton("حذف جهاز")
        self.delete_device_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #a93226, stop: 1 #922b21);
            }
        """)
        self.delete_device_btn.clicked.connect(self.delete_device)
        toolbar_layout.addWidget(self.delete_device_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_device_tabs(self, parent_layout):
        """إنشاء تبويبات الأجهزة"""
        # تبويبات الأجهزة
        self.device_tab_widget = QTabWidget()
        
        # تبويب PlayStation
        self.ps_tab = self.create_device_tab("PS")
        self.device_tab_widget.addTab(self.ps_tab, "🎮 PlayStation")
        self.device_tabs['PS'] = self.ps_tab
        
        # تبويب PC
        self.pc_tab = self.create_device_tab("PC")
        self.device_tab_widget.addTab(self.pc_tab, "💻 PC Gaming")
        self.device_tabs['PC'] = self.pc_tab
        
        # تبويب Ping Pong
        self.pingpong_tab = self.create_device_tab("PingPong")
        self.device_tab_widget.addTab(self.pingpong_tab, "🏓 Ping Pong")
        self.device_tabs['PingPong'] = self.pingpong_tab
        
        # تبويب Billiards
        self.billiard_tab = self.create_device_tab("Billiard")
        self.device_tab_widget.addTab(self.billiard_tab, "🎱 Billiards")
        self.device_tabs['Billiard'] = self.billiard_tab
        
        
        parent_layout.addWidget(self.device_tab_widget)
    
    def create_device_tab(self, device_type):
        """إنشاء تبويب للأجهزة"""
        # إنشاء الـ widget الرئيسي للتبويب
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(10)
        
        # عنوان التبويب
        title_label = QLabel(f"أجهزة {device_type}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(title_label)
        
        # منطقة التمرير للأجهزة
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
        """)
        
        # الـ widget المحتوي للأجهزة
        devices_widget = QWidget()
        devices_layout = QGridLayout(devices_widget)
        devices_layout.setSpacing(8)  # مسافة أقل لتناسب 8 كروت
        devices_layout.setContentsMargins(8, 8, 8, 8)  # هوامش أقل
        devices_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # بدء من أعلى الصفحة
        devices_layout.setColumnMinimumWidth(0, 165)  # عرض عمود محدد
        devices_layout.setColumnStretch(0, 1)  # تمدد الأعمدة
        
        # تخزين التخطيط للاستخدام لاحقاً
        tab_widget.devices_layout = devices_layout
        tab_widget.device_type = device_type
        
        scroll_area.setWidget(devices_widget)
        tab_layout.addWidget(scroll_area)
        
        return tab_widget
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات سريعة")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات الأجهزة
        self.total_devices_label = QLabel("إجمالي الأجهزة: 0")
        self.total_devices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_devices_label)
        
        self.available_devices_label = QLabel("متاحة: 0")
        self.available_devices_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.available_devices_label)
        
        self.busy_devices_label = QLabel("مشغولة: 0")
        self.busy_devices_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.busy_devices_label)
        
        self.maintenance_devices_label = QLabel("صيانة: 0")
        self.maintenance_devices_label.setStyleSheet("font-size: 14px; color: #95a5a6; font-weight: bold;")
        stats_layout.addWidget(self.maintenance_devices_label)
        
        parent_layout.addLayout(stats_layout)
    
    def center_window(self):
        """توسيط النافذة على الشاشة"""
        try:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception as e:
            self.move(200, 200)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        pass
    
    def load_devices(self):
        """تحميل الأجهزة"""
        try:
            # مسح الأجهزة الموجودة من جميع التبويبات
            for device_type, tab in self.device_tabs.items():
                for i in reversed(range(tab.devices_layout.count())):
                    tab.devices_layout.itemAt(i).widget().setParent(None)
            
            self.device_cards.clear()
            
            # تحميل الأجهزة من قاعدة البيانات
            devices = self.device_model.get_all_devices()
            
            if not devices:
                # إذا لم توجد أجهزة في قاعدة البيانات، عرض رسالة في جميع التبويبات
                print("لا توجد أجهزة في قاعدة البيانات")
                self.show_empty_state_message()
                self.update_stats([])
                return
            
            # توزيع الأجهزة على التبويبات
            devices_by_type = {}
            for device in devices:
                device_type = device['type']
                if device_type not in devices_by_type:
                    devices_by_type[device_type] = []
                devices_by_type[device_type].append(device)
            
            # طباعة أنواع الأجهزة الموجودة
            print(f"أنواع الأجهزة الموجودة: {list(devices_by_type.keys())}")
            print(f"التبويبات المتاحة: {list(self.device_tabs.keys())}")
            
            # إنشاء كروت الأجهزة لكل تبويب
            for device_type, devices_list in devices_by_type.items():
                if device_type in self.device_tabs:
                    tab = self.device_tabs[device_type]
                    print(f"إنشاء {len(devices_list)} كروت لـ {device_type}")
                    self.create_device_cards_for_tab(tab, devices_list)
                else:
                    print(f"تحذير: لا يوجد تبويب لـ {device_type}")
            
            # تحديث الإحصائيات
            self.update_stats(devices)
            
        except Exception as e:
            print(f"خطأ في تحميل الأجهزة: {e}")
            # في حالة الخطأ، عرض البيانات التجريبية كبديل
            self.load_sample_devices()
    
    def load_sample_devices(self):
        """تحميل البيانات التجريبية في حالة عدم وجود أجهزة في قاعدة البيانات"""
        try:
            # تم حذف البيانات التجريبية - إرجاع قائمة فارغة
            sample_devices = [
            ]
            
            # توزيع الأجهزة على التبويبات
            devices_by_type = {}
            for device in sample_devices:
                device_type = device['type']
                if device_type not in devices_by_type:
                    devices_by_type[device_type] = []
                devices_by_type[device_type].append(device)
            
            # طباعة أنواع الأجهزة الموجودة
            print(f"أنواع الأجهزة الموجودة: {list(devices_by_type.keys())}")
            print(f"التبويبات المتاحة: {list(self.device_tabs.keys())}")
            
            # إنشاء كروت الأجهزة لكل تبويب
            for device_type, devices in devices_by_type.items():
                if device_type in self.device_tabs:
                    tab = self.device_tabs[device_type]
                    print(f"إنشاء {len(devices)} كروت لـ {device_type}")
                    self.create_device_cards_for_tab(tab, devices)
                else:
                    print(f"تحذير: لا يوجد تبويب لـ {device_type}")
            
            # تحديث الإحصائيات
            self.update_stats(sample_devices)
            
        except Exception as e:
            print(f"خطأ في تحميل البيانات التجريبية: {e}")
    
    def create_device_cards_for_tab(self, tab, devices):
        """إنشاء كروت الأجهزة لتبويب محدد"""
        row = 0
        col = 0
        max_cols = 8  # 8 أجهزة في الصف الواحد
        
        for device in devices:
            card = DeviceCard(device)
            card.device_clicked.connect(self.on_device_clicked)
            card.context_menu_requested.connect(self.on_context_menu_requested)
            self.device_cards[device['id']] = card
            
            # إضافة الكارت مع تمدد لملء المساحة المتاحة
            tab.devices_layout.addWidget(card, row, col, 1, 1)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # تعيين تمدد الأعمدة لملء الصف
        for i in range(max_cols):
            tab.devices_layout.setColumnStretch(i, 1)
    
    def show_empty_state_message(self):
        """عرض رسالة عدم وجود أجهزة في جميع التبويبات"""
        for device_type, tab in self.device_tabs.items():
            # إنشاء رسالة عدم وجود أجهزة
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            # أيقونة فارغة
            icon_label = QLabel("📱")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; margin-bottom: 20px;")
            empty_layout.addWidget(icon_label)
            
            # رسالة عدم وجود أجهزة
            message_label = QLabel("لا توجد أجهزة مضافة")
            message_label.setAlignment(Qt.AlignCenter)
            message_label.setStyleSheet("""
                font-size: 18px; 
                font-weight: bold; 
                color: #7f8c8d; 
                margin-bottom: 10px;
            """)
            empty_layout.addWidget(message_label)
            
            # رسالة توجيهية
            instruction_label = QLabel("يمكنك إضافة جهاز من زر إضافة جهاز")
            instruction_label.setAlignment(Qt.AlignCenter)
            instruction_label.setStyleSheet("""
                font-size: 14px; 
                color: #95a5a6; 
                margin-bottom: 20px;
            """)
            empty_layout.addWidget(instruction_label)
            
            # إضافة الرسالة إلى التبويب
            tab.devices_layout.addWidget(empty_widget, 0, 0, 1, 8, Qt.AlignCenter)
    
    def update_stats(self, devices):
        """تحديث الإحصائيات"""
        total = len(devices)
        available = len([d for d in devices if d['status'] == 'available'])
        busy = len([d for d in devices if d['status'] == 'busy'])
        maintenance = len([d for d in devices if d['status'] == 'maintenance'])
        
        self.total_devices_label.setText(f"إجمالي الأجهزة: {total}")
        self.available_devices_label.setText(f"متاحة: {available}")
        self.busy_devices_label.setText(f"مشغولة: {busy}")
        self.maintenance_devices_label.setText(f"صيانة: {maintenance}")
        
        # تحديث معلومات التخطيط
        if total > 0:
            layout_info = f"تم تحميل {total} جهاز من قاعدة البيانات"
        else:
            layout_info = "لا توجد أجهزة في قاعدة البيانات"
        
        if hasattr(self, 'layout_label'):
            self.layout_label.setText(layout_info)
    
    def on_device_clicked(self, device_data):
        """معالج النقر على الجهاز"""
        print(f"تم النقر على الجهاز: {device_data['name']}")
        self.device_selected.emit(device_data)
        
        # عرض نافذة إدارة الجلسة
        self.show_session_dialog(device_data)
    
    def on_context_menu_requested(self, device_data, action_type):
        """معالج طلب قائمة السياق"""
        print(f"طلب قائمة السياق للجهاز: {device_data['name']} - الإجراء: {action_type}")
        
        if action_type == "delete_session":
            self.delete_session_from_context_menu(device_data)
        elif action_type == "edit_session":
            self.edit_session_from_context_menu(device_data)
        elif action_type == "change_pricing_type":
            self.change_pricing_type_from_context_menu(device_data)
        elif action_type == "transfer_session":
            self.transfer_session_from_context_menu(device_data)
        elif action_type == "maintenance_mode":
            self.set_maintenance_mode(device_data)
        elif action_type == "remove_maintenance":
            self.remove_maintenance_mode(device_data)
        elif action_type == "edit_device":
            self.edit_device_from_context_menu(device_data)
    
    def delete_session_from_context_menu(self, device_data):
        """حذف الجلسة من قائمة السياق"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(device_data['id'])
            
            if not current_session:
                QMessageBox.warning(self, "تحذير", "لا توجد جلسة نشطة على هذا الجهاز")
                return
            
            # التحقق من الصلاحية
            from utils.permission_checker import permission_checker
            
            # إذا كان المستخدم لديه صلاحية حذف الحساب، لا نطلب كلمة مرور المدير
            if permission_checker.check_permission_or_admin(self.current_user, "delete_account"):
                # طلب تأكيد الحذف مباشرة
                reply = QMessageBox.question(
                    self,
                    "تأكيد حذف الجلسة",
                    f"هل أنت متأكد من حذف الجلسة على الجهاز '{device_data['name']}'؟\n\n"
                    "⚠️ تحذير: سيتم حذف الجلسة نهائياً ولا يمكن استردادها!",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # حذف الجلسة
                    result = self.session_controller.end_session(current_session['id'], "تم حذف الجلسة من قائمة السياق")
                    
                    if result['success']:
                        QMessageBox.information(
                            self,
                            "تم الحذف بنجاح",
                            f"تم حذف الجلسة على الجهاز '{device_data['name']}' بنجاح!"
                        )
                        # تحديث عرض الأجهزة
                        self.load_devices()
                    else:
                        QMessageBox.warning(self, "خطأ", f"فشل في حذف الجلسة: {result.get('message', 'خطأ غير معروف')}")
            else:
                # طلب كلمة مرور المدير
                password_dialog = AdminPasswordDialog()
                password_dialog.setWindowTitle("طلب إذن المدير - حذف الجلسة")
                
                # تحديث رسالة النافذة لتكون خاصة بحذف الجلسة
                password_dialog.findChild(QLabel).setText("لحذف الجلسة النشطة، يرجى إدخال كلمة مرور المدير:")
                
                if password_dialog.exec() == QDialog.Accepted:
                    # طلب تأكيد الحذف بعد التحقق من كلمة المرور
                    reply = QMessageBox.question(
                        self,
                        "تأكيد حذف الجلسة",
                        f"هل أنت متأكد من حذف الجلسة على الجهاز '{device_data['name']}'؟\n\n"
                        "⚠️ تحذير: سيتم حذف الجلسة نهائياً ولا يمكن استردادها!",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # حذف الجلسة
                        result = self.session_controller.end_session(current_session['id'], "تم حذف الجلسة من قائمة السياق")
                        
                        if result['success']:
                            QMessageBox.information(
                                self,
                                "تم الحذف بنجاح",
                                f"تم حذف الجلسة على الجهاز '{device_data['name']}' بنجاح!"
                            )
                            # تحديث عرض الأجهزة
                            self.load_devices()
                        else:
                            QMessageBox.warning(self, "خطأ", f"فشل في حذف الجلسة: {result.get('message', 'خطأ غير معروف')}")
                else:
                    # المستخدم ألغى العملية أو كلمة المرور غير صحيحة
                    QMessageBox.information(self, "تم الإلغاء", "تم إلغاء عملية حذف الجلسة")
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حذف الجلسة: {str(e)}")
    
    def edit_session_from_context_menu(self, device_data):
        """تعديل بيانات الجلسة من قائمة السياق"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(device_data['id'])
            
            if not current_session:
                QMessageBox.warning(self, "تحذير", "لا توجد جلسة نشطة على هذا الجهاز")
                return
            
            # عرض نافذة تعديل الجلسة
            dialog = EditSessionDialog(current_session, self.current_user)
            if dialog.exec() == QDialog.Accepted:
                # تحديث عرض الأجهزة
                self.load_devices()
                QMessageBox.information(
                    self,
                    "تم التعديل بنجاح",
                    "تم تعديل بيانات الجلسة بنجاح!"
                )
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تعديل الجلسة: {str(e)}")
    
    def change_pricing_type_from_context_menu(self, device_data):
        """تغيير نوع التسعيرة من قائمة السياق"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(device_data['id'])
            
            if not current_session:
                QMessageBox.warning(self, "خطأ", "لا توجد جلسة نشطة على هذا الجهاز")
                return
            
            # التحقق من أن الجهاز يحتوي على نوعي التسعيرة
            if not device_data.get('price_single') or not device_data.get('price_multi'):
                QMessageBox.warning(self, "خطأ", "هذا الجهاز لا يحتوي على نوعي التسعيرة (فردي وجماعي)")
                return
            
            # إنشاء نافذة حوار لتغيير نوع التسعيرة
            dialog = ChangePricingTypeDialog(device_data, current_session)
            if dialog.exec() == QDialog.Accepted:
                new_pricing_type = dialog.get_selected_pricing_type()
                
                # تغيير نوع التسعيرة
                result = self.session_controller.change_session_pricing_type(
                    current_session['id'], 
                    new_pricing_type
                )
                
                if result['success']:
                    # عرض تفاصيل التسعيرة المتقدمة
                    pricing_summary = result.get('pricing_summary', {})
                    
                    message = f"{result['message']}\n\n"
                    message += f"السعر الجديد: {format_currency(result['new_price'])}\n\n"
                    
                    if pricing_summary:
                        message += "📊 ملخص التسعيرة:\n"
                        
                        if pricing_summary.get('total_single_cost', 0) > 0:
                            message += f"👤 فردي: {pricing_summary['total_single_hours']:.2f} ساعة = {format_currency(pricing_summary['total_single_cost'])}\n"
                        
                        if pricing_summary.get('total_multi_cost', 0) > 0:
                            message += f"👥 جماعي: {pricing_summary['total_multi_hours']:.2f} ساعة = {format_currency(pricing_summary['total_multi_cost'])}\n"
                        
                        message += f"💰 المجموع: {format_currency(pricing_summary['total_cost'])}"
                    
                    QMessageBox.information(
                        self, 
                        "نجح التغيير", 
                        message
                    )
                    
                    # تحديث واجهة الأجهزة
                    self.load_devices()
                else:
                    QMessageBox.warning(self, "خطأ", result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تغيير نوع التسعيرة: {str(e)}")
    
    def transfer_session_from_context_menu(self, device_data):
        """نقل الجلسة من قائمة السياق"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(device_data['id'])
            
            if not current_session:
                QMessageBox.warning(self, "تحذير", "لا توجد جلسة نشطة على هذا الجهاز")
                return
            
            # عرض نافذة اختيار الجهاز الهدف
            dialog = TransferSessionDialog(device_data, current_session, self.current_user)
            if dialog.exec() == QDialog.Accepted:
                # تحديث عرض الأجهزة
                self.load_devices()
                QMessageBox.information(
                    self,
                    "تم النقل بنجاح",
                    f"تم نقل الجلسة من الجهاز '{device_data['name']}' إلى الجهاز الهدف بنجاح!"
                )
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء نقل الجلسة: {str(e)}")
    
    def set_maintenance_mode(self, device_data):
        """تفعيل وضع الصيانة للجهاز"""
        try:
            # تأكيد من المستخدم
            reply = QMessageBox.question(
                self,
                "تأكيد وضع الصيانة",
                f"هل تريد تفعيل وضع الصيانة للجهاز '{device_data['name']}'؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # تحديث حالة الجهاز في قاعدة البيانات
                device_model = DeviceModel()
                success = device_model.update_device_status(device_data['id'], 'maintenance')
                
                if success:
                    # تحديث عرض الأجهزة
                    self.load_devices()
                    QMessageBox.information(
                        self,
                        "تم التفعيل",
                        f"تم تفعيل وضع الصيانة للجهاز '{device_data['name']}' بنجاح!"
                    )
                else:
                    QMessageBox.warning(self, "خطأ", "فشل في تحديث حالة الجهاز")
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تفعيل وضع الصيانة: {str(e)}")
    
    def remove_maintenance_mode(self, device_data):
        """إزالة وضع الصيانة من الجهاز"""
        try:
            # تأكيد من المستخدم
            reply = QMessageBox.question(
                self,
                "تأكيد إزالة وضع الصيانة",
                f"هل تريد إزالة وضع الصيانة من الجهاز '{device_data['name']}'؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # تحديث حالة الجهاز في قاعدة البيانات
                device_model = DeviceModel()
                success = device_model.update_device_status(device_data['id'], 'available')
                
                if success:
                    # تحديث عرض الأجهزة
                    self.load_devices()
                    QMessageBox.information(
                        self,
                        "تم الإزالة",
                        f"تم إزالة وضع الصيانة من الجهاز '{device_data['name']}' بنجاح!"
                    )
                else:
                    QMessageBox.warning(self, "خطأ", "فشل في تحديث حالة الجهاز")
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إزالة وضع الصيانة: {str(e)}")
    
    def edit_device_from_context_menu(self, device_data):
        """تعديل بيانات الجهاز من قائمة السياق"""
        try:
            # طلب كلمة مرور المدير أولاً
            password_dialog = AdminPasswordDialog()
            if password_dialog.exec() == QDialog.Accepted:
                # عرض نافذة تعديل الجهاز
                dialog = EditDeviceDialog(device_data, self.current_user)
                if dialog.exec() == QDialog.Accepted:
                    # تحديث عرض الأجهزة
                    self.load_devices()
                    QMessageBox.information(
                        self,
                        "تم التعديل بنجاح",
                        f"تم تعديل بيانات الجهاز '{device_data['name']}' بنجاح!"
                    )
            else:
                # المستخدم ألغى إدخال كلمة المرور
                QMessageBox.information(
                    self,
                    "تم الإلغاء",
                    "تم إلغاء تعديل بيانات الجهاز"
                )
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تعديل الجهاز: {str(e)}")
    
    def show_session_dialog(self, device_data):
        """عرض نافذة إدارة الجلسة"""
        dialog = SessionDialog(device_data, self.current_user)
        result = dialog.exec()
        
        # تحديث حالة الجهاز دائماً بعد إغلاق النافذة
        self.load_devices()
        
        if result == QDialog.Accepted:
            # تحديث إضافي للتأكد من تحديث الكروت
            self.update_devices_status()
            
            # تحديث نافذة إدارة الفواتير إذا كانت مفتوحة
            self.update_invoice_management_window()
    
    
    def add_device(self):
        """إضافة جهاز جديد"""
        # التحقق من الصلاحية
        from utils.permission_checker import permission_checker
        
        # إذا كان المستخدم لديه صلاحية إضافة جهاز، لا نطلب كلمة مرور المدير
        if permission_checker.check_permission_or_admin(self.current_user, "add_device"):
            # عرض نافذة إضافة الجهاز مباشرة
            dialog = AddDeviceDialog()
            if dialog.exec() == QDialog.Accepted:
                # إضافة الجهاز الجديد
                self.load_devices()
        else:
            # طلب كلمة مرور المدير
            password_dialog = AdminPasswordDialog()
            if password_dialog.exec() == QDialog.Accepted:
                # إذا تم التحقق من كلمة المرور، عرض نافذة إضافة الجهاز
                dialog = AddDeviceDialog()
                if dialog.exec() == QDialog.Accepted:
                    # إضافة الجهاز الجديد
                    self.load_devices()
    
    def delete_device(self):
        """حذف جهاز"""
        # التحقق من الصلاحية
        from utils.permission_checker import permission_checker
        
        # إذا كان المستخدم لديه صلاحية حذف جهاز، لا نطلب كلمة مرور المدير
        if permission_checker.check_permission_or_admin(self.current_user, "delete_device"):
            # عرض نافذة اختيار الجهاز للحذف مباشرة
            dialog = DeleteDeviceDialog()
            if dialog.exec() == QDialog.Accepted:
                # تحديث عرض الأجهزة بعد الحذف
                self.load_devices()
        else:
            # طلب كلمة مرور المدير
            password_dialog = AdminPasswordDialog()
            if password_dialog.exec() == QDialog.Accepted:
                # إذا تم التحقق من كلمة المرور، عرض نافذة اختيار الجهاز للحذف
                dialog = DeleteDeviceDialog()
                if dialog.exec() == QDialog.Accepted:
                    # تحديث عرض الأجهزة بعد الحذف
                    self.load_devices()
    
    def start_timer(self):
        """بدء التايمر لتحديث الأجهزة"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_devices_status)
        self.timer.start(1000)  # كل ثانية
    
    def update_devices_status(self):
        """تحديث حالة الأجهزة"""
        try:
            # تحديث بيانات الأجهزة من قاعدة البيانات أولاً
            devices = self.device_model.get_all_devices()
            device_dict = {device['id']: device for device in devices}
            
            # تحديث كل كارت
            for device_id, card in self.device_cards.items():
                if device_id in device_dict:
                    # تحديث بيانات الكارت
                    card.update_device_data(device_dict[device_id])
                # تحديث حالة الكارت
                card.update_status()
                
                # التحقق من انتهاء الوقت للجلسات المحددة الوقت
                if device_id in device_dict:
                    device = device_dict[device_id]
                    if device.get('status') == 'busy' and device.get('current_session_id'):
                        # التحقق من انتهاء الوقت
                        from controllers.session_controller import SessionController
                        session_controller = SessionController(self.current_user)
                        time_info = session_controller.get_session_time_info(device['current_session_id'])
                        
                        if time_info and time_info.get('is_expired', False):
                            # إيقاف التايمر في نافذة الجلسة إذا كانت مفتوحة
                            if hasattr(card, 'session_window') and card.session_window:
                                if hasattr(card.session_window, 'stop_update_timer'):
                                    card.session_window.stop_update_timer()
                                    card.session_window.timer_stopped = True
                                    print(f"تم إيقاف التايمر للجلسة {device['current_session_id']} - انتهى الوقت المحدد")
                        
                        # التحقق من إيقاف الجلسة
                        session = session_controller.session_model.get_session_by_id(device['current_session_id'])
                        if session and session.get('status') == 'paused':
                            # إيقاف التايمر في نافذة الجلسة إذا كانت مفتوحة
                            if hasattr(card, 'session_window') and card.session_window:
                                if hasattr(card.session_window, 'stop_update_timer'):
                                    card.session_window.stop_update_timer()
                                    card.session_window.timer_stopped = True
                                    print(f"تم إيقاف التايمر للجلسة {device['current_session_id']} - الجلسة متوقفة")
        except Exception as e:
            print(f"خطأ في تحديث حالة الأجهزة: {e}")
    
    def update_sessions_from_manager(self):
        """تحديث حالة الجلسات من مدير الجلسات"""
        try:
            from utils.session_manager import SessionManager
            session_manager = SessionManager()
            
            # الحصول على حالة الجلسات
            status = session_manager.get_sessions_status()
            
            if status['paused_sessions']:
                print(f"تم اكتشاف {len(status['paused_sessions'])} جلسة متوقفة من مدير الجلسات")
                
                # تحديث حالة الأجهزة للجلسات المتوقفة
                for session in status['paused_sessions']:
                    device_id = session['device_id']
                    session_id = session['id']
                    
                    # تحديث الجهاز ليشير إلى الجلسة المتوقفة
                    self.device_model.update_device_status(
                        device_id=device_id,
                        status='busy',
                        current_session_id=session_id
                    )
                    
                    print(f"تم تحديث الجهاز {device_id} للجلسة المتوقفة {session_id}")
            
            if status['active_sessions']:
                print(f"تم اكتشاف {len(status['active_sessions'])} جلسة نشطة من مدير الجلسات")
                
        except Exception as e:
            print(f"خطأ في تحديث الجلسات من مدير الجلسات: {e}")
    
    def update_invoice_management_window(self):
        """تحديث نافذة إدارة الفواتير إذا كانت مفتوحة"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم تحديث نافذة إدارة الفواتير")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في تحديث نافذة إدارة الفواتير: {e}")
    

class SessionDialog(QDialog):
    """نافذة إدارة الجلسة المحسنة"""
    
    def __init__(self, device_data, current_user):
        super().__init__()
        self.device_data = device_data
        self.current_user = current_user
        self.session_controller = SessionController(current_user)
        self.timer_stopped = False  # متغير لتتبع حالة التايمر
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle(f"إدارة الجلسة - {self.device_data['name']}")
        self.setFixedSize(800, 700)  # زيادة الحجم لاستيعاب المعلومات المفصلة
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #4CAF50;
                border-radius: 15px;
                background-color: white;
                selection-background-color: #4CAF50;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.3);
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.7);
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #333;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
                border-top: 2px solid #4CAF50;
                border-left: 1px solid #4CAF50;
                border-right: 1px solid #4CAF50;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: rgba(255, 255, 255, 0.9);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # معلومات الجهاز
        info_label = QLabel(f"الجهاز: {self.device_data['name']}")
        info_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-bottom: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
        layout.addWidget(info_label)
        
        # إنشاء التبويبات
        self.tab_widget = QTabWidget()
        
        # تبويبة إدارة الجلسة
        self.session_tab = QWidget()
        session_layout = QVBoxLayout(self.session_tab)
        
        # حالة الجهاز
        status = self.device_data.get('status', 'available')
        
        try:
            if status == 'available':
                self.setup_start_session(session_layout)
            elif status == 'busy':
                self.setup_active_session(session_layout)
            elif status == 'maintenance':
                self.setup_maintenance_mode(session_layout)
        except Exception as e:
            print(f"خطأ في إعداد واجهة الجلسة: {e}")
            # إضافة رسالة خطأ بسيطة
            error_label = QLabel(f"خطأ في تحميل واجهة الجلسة: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px;")
            session_layout.addWidget(error_label)
        
        self.tab_widget.addTab(self.session_tab, "إدارة الجلسة")
        
        # تبويبة المنتجات (فقط للجلسات النشطة)
        if status == 'busy':
            self.products_tab = ProductTab(self.session_controller, self.device_data, self)
            self.tab_widget.addTab(self.products_tab, "المنتجات")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def setup_start_session(self, layout):
        """إعداد بدء الجلسة الحديث"""
        # نوع التسعيرة
        pricing_label = QLabel("نوع التسعيرة:")
        pricing_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(pricing_label)
        
        self.pricing_combo = QComboBox()
        if self.device_data['type'] == 'PS':
            self.pricing_combo.addItems(['single', 'multi'])
        else:
            self.pricing_combo.addItem('single')
        layout.addWidget(self.pricing_combo)
        
        # نوع الوقت
        time_type_label = QLabel("نوع الوقت:")
        time_type_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px; margin-top: 15px;")
        layout.addWidget(time_type_label)
        
        self.time_type_combo = QComboBox()
        self.time_type_combo.addItems(['وقت محدد', 'وقت مفتوح'])
        self.time_type_combo.currentTextChanged.connect(self.on_time_type_changed)
        layout.addWidget(self.time_type_combo)
        
        # مدة الجلسة (للساعات المحددة)
        duration_label = QLabel("مدة الجلسة:")
        duration_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px; margin-top: 15px;")
        layout.addWidget(duration_label)
        
        # قائمة منسدلة للخيارات السريعة
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['30 دقيقة', '60 دقيقة', '90 دقيقة', '120 دقيقة', 'وقت مخصص'])
        self.duration_combo.currentTextChanged.connect(self.on_duration_changed)
        layout.addWidget(self.duration_combo)
        
        # حقل إدخال الوقت المخصص
        self.custom_duration_input = QLineEdit()
        self.custom_duration_input.setPlaceholderText("أدخل المدة بالدقائق")
        self.custom_duration_input.setVisible(False)
        self.custom_duration_input.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.custom_duration_input)
        
        
        # زر بدء الجلسة
        start_btn = QPushButton("بدء الجلسة")
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        start_btn.clicked.connect(self.start_session)
        layout.addWidget(start_btn)
    
    def setup_active_session(self, layout):
        """إعداد الجلسة النشطة"""
        try:
            # الحصول على معلومات الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
        except Exception as e:
            print(f"خطأ في الحصول على معلومات الجلسة: {e}")
            current_session = None
        
        if current_session:
            # تحديد حالة الجلسة
            is_paused = current_session.get('is_paused', False)
            session_status = current_session.get('status', 'active')
            
            if is_paused or session_status == 'paused':
                info_label = QLabel("الجلسة متوقفة")
                info_label.setStyleSheet("color: #3498db; font-size: 18px; font-weight: bold; margin-bottom: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
            else:
                info_label = QLabel("الجلسة قيد التشغيل")
                info_label.setStyleSheet("color: #27ae60; font-size: 18px; font-weight: bold; margin-bottom: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
            layout.addWidget(info_label)
            # معلومات الجلسة
            time_type = current_session.get('time_type', 'fixed')
            start_time = current_session.get('start_time', datetime.now())
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            elapsed = datetime.now() - start_time
            elapsed_minutes = int(elapsed.total_seconds() / 60)
            
            # عرض معلومات الوقت والتكلفة
            try:
                session_time_info = self.session_controller.get_session_time_info(current_session['id'])
                session_cost_info = self.session_controller.get_session_cost_info(current_session['id'])
            except Exception as e:
                print(f"خطأ في الحصول على معلومات الوقت والتكلفة: {e}")
                session_time_info = None
                session_cost_info = None
            
            if session_time_info and session_cost_info:
                # عرض الوقت المفصل
                elapsed_hours = session_time_info.get('elapsed_hours', 0)
                elapsed_minutes = session_time_info.get('elapsed_minutes', 0)
                elapsed_seconds = session_time_info.get('elapsed_seconds', 0)
                elapsed_formatted = f"{elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d}"
                
                total_cost = session_cost_info.get('total_cost', 0)
                cost_breakdown = session_cost_info.get('cost_breakdown', '')
                
                # عرض الوقت المفصل والتكلفة
                time_info = f"⏱️ الوقت المنقضي: {elapsed_formatted} | 💰 التكلفة الحالية: {format_currency(total_cost)}"
                
                # عرض تفاصيل التسعيرة المتقدمة إذا كانت متوفرة
                pricing_summary = session_cost_info.get('pricing_summary', {})
                if pricing_summary and (pricing_summary.get('total_single_cost', 0) > 0 or pricing_summary.get('total_multi_cost', 0) > 0):
                    pricing_details = "\n📊 تفاصيل التسعيرة:\n"
                    
                    if pricing_summary.get('total_single_cost', 0) > 0:
                        single_hours = pricing_summary.get('total_single_hours', 0)
                        single_cost = pricing_summary.get('total_single_cost', 0)
                        single_h = int(single_hours)
                        single_m = int((single_hours - single_h) * 60)
                        single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                        pricing_details += f"👤 فردي: {single_h:02d}:{single_m:02d}:{single_s:02d} = {format_currency(single_cost)}\n"
                    
                    if pricing_summary.get('total_multi_cost', 0) > 0:
                        multi_hours = pricing_summary.get('total_multi_hours', 0)
                        multi_cost = pricing_summary.get('total_multi_cost', 0)
                        multi_h = int(multi_hours)
                        multi_m = int((multi_hours - multi_h) * 60)
                        multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                        pricing_details += f"👥 جماعي: {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {format_currency(multi_cost)}\n"
                    
                    pricing_details += f"💰 المجموع: {pricing_summary.get('total_cost', 0):.2f} جنيه"
                    time_info += pricing_details
            else:
                # في حالة فشل الحصول على المعلومات - عرض الوقت البسيط
                session_price = current_session.get('session_price', 0)
                cost_per_minute = session_price / 60
                current_cost = elapsed_minutes * cost_per_minute
                
                # تحويل الدقائق إلى ساعات ودقائق وثواني
                total_seconds = elapsed_minutes * 60
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                elapsed_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                time_info = f"⏱️ الوقت المنقضي: {elapsed_formatted} | 💰 التكلفة الحالية: {current_cost:.2f} جنيه"
            
            self.elapsed_label = QLabel(time_info)
            self.elapsed_label.setStyleSheet("""
                font-size: 14px; 
                margin: 10px 0; 
                padding: 10px; 
                background-color: #f8f9fa; 
                border-radius: 5px; 
                border: 1px solid #dee2e6;
                font-family: 'Courier New', monospace;
            """)
            self.elapsed_label.setWordWrap(True)
            layout.addWidget(self.elapsed_label)
            
            # معلومات التسعيرة الحالية
            pricing_type = current_session.get('pricing_type', 'single')
            session_price = current_session.get('session_price', 0)
            
            # عرض نوع التسعيرة الحالي مع أيقونة
            if pricing_type == 'single':
                pricing_icon = "👤"
                pricing_type_text = "فردية"
            else:
                pricing_icon = "👥"
                pricing_type_text = "جماعية"
            
            pricing_info = f"📋 نوع التسعيرة الحالي: {pricing_icon} {pricing_type_text} | 💰 السعر: {session_price:.2f} جنيه/ساعة"
            pricing_label = QLabel(pricing_info)
            pricing_label.setStyleSheet("""
                font-size: 14px; 
                margin: 10px 0; 
                padding: 8px; 
                background-color: #e8f4fd; 
                border-radius: 5px; 
                border: 1px solid #bee5eb;
                font-weight: bold;
            """)
            layout.addWidget(pricing_label)
            
            # السعر الإجمالي للفاتورة (الجلسة + المنتجات)
            self.invoice_total_label = QLabel("جاري حساب السعر الإجمالي...")
            self.invoice_total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; border: 2px solid #e74c3c;")
            layout.addWidget(self.invoice_total_label)
            
            # تحديث السعر الإجمالي
            self.update_invoice_total()
            
            # إضافة timer للتحديث المستمر
            self.setup_update_timer()
        
        # أزرار التحكم
        controls_layout = QHBoxLayout()
        
        add_product_btn = QPushButton("📦 إضافة منتج")
        add_product_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        add_product_btn.clicked.connect(self.switch_to_products_tab)
        controls_layout.addWidget(add_product_btn)
        
        # زر تغيير نوع التسعيرة (فقط للأجهزة التي تحتوي على نوعي التسعيرة)
        if current_session and self.device_data.get('price_single') and self.device_data.get('price_multi'):
            change_pricing_btn = QPushButton("تغيير نوع التسعيرة")
            change_pricing_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #f39c12, stop: 1 #e67e22);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 12px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #e67e22, stop: 1 #d35400);
                }
            """)
            change_pricing_btn.clicked.connect(self.change_pricing_from_session_dialog)
            controls_layout.addWidget(change_pricing_btn)
        
        # أزرار إيقاف واستئناف الجلسة
        if current_session:
            is_paused = current_session.get('is_paused', False)
            session_status = current_session.get('status', 'active')
            
            if is_paused or session_status == 'paused':
                # الجلسة متوقفة - زر الاستئناف
                resume_btn = QPushButton("استئناف الجلسة")
                resume_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #27ae60, stop: 1 #229954);
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        font-size: 12px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #229954, stop: 1 #1e8449);
                    }
                """)
                resume_btn.clicked.connect(self.resume_session)
                controls_layout.addWidget(resume_btn)
            else:
                # الجلسة نشطة - زر الإيقاف
                pause_btn = QPushButton("إيقاف الجلسة")
                pause_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #f39c12, stop: 1 #e67e22);
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        font-size: 12px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #e67e22, stop: 1 #d35400);
                    }
                """)
                pause_btn.clicked.connect(self.pause_session)
                controls_layout.addWidget(pause_btn)
            
            # زر تمديد الجلسة (فقط للجلسات النشطة غير المتوقفة)
            if current_session.get('time_type') == 'fixed' and not (is_paused or session_status == 'paused'):
                extend_btn = QPushButton("تمديد الجلسة")
                extend_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #f39c12, stop: 1 #e67e22);
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        font-size: 12px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 #e67e22, stop: 1 #d35400);
                    }
                """)
                extend_btn.clicked.connect(self.extend_session)
                controls_layout.addWidget(extend_btn)
        
        end_session_btn = QPushButton("إنهاء الجلسة")
        end_session_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 12px;
                border-radius: 20px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
            }
        """)
        end_session_btn.clicked.connect(self.end_session)
        controls_layout.addWidget(end_session_btn)
        
        layout.addLayout(controls_layout)
    
    def setup_maintenance_mode(self, layout):
        """إعداد وضع الصيانة الحديث"""
        info_label = QLabel("الجهاز في وضع الصيانة")
        info_label.setStyleSheet("color: #95a5a6; font-size: 18px; font-weight: bold; margin-bottom: 20px; font-family: 'Segoe UI', Arial, sans-serif;")
        layout.addWidget(info_label)
        
        # زر إنهاء الصيانة
        end_maintenance_btn = QPushButton("إنهاء الصيانة")
        end_maintenance_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        end_maintenance_btn.clicked.connect(self.end_maintenance)
        layout.addWidget(end_maintenance_btn)
    
    def on_time_type_changed(self):
        """تغيير نوع الوقت"""
        time_type = self.time_type_combo.currentText()
        if time_type == 'وقت مفتوح':
            self.duration_layout.setVisible(False)
        else:
            self.duration_layout.setVisible(True)
    
    def on_duration_changed(self):
        """تغيير مدة الجلسة"""
        duration_text = self.duration_combo.currentText()
        if duration_text == 'وقت مخصص':
            self.custom_duration_input.setVisible(True)
            self.custom_duration_input.setFocus()
        else:
            self.custom_duration_input.setVisible(False)
    
    def start_session(self):
        """بدء الجلسة"""
        # التحقق من وجود وردية نشطة
        from utils.shift_validation import validate_shift_required
        if not validate_shift_required(self):
            return
        
        try:
            # جمع البيانات
            pricing_type = self.pricing_combo.currentText()
            time_type_text = self.time_type_combo.currentText()
            time_type = 'fixed' if time_type_text == 'وقت محدد' else 'open'
            customer_phone = None  # إزالة خيار رقم هاتف العميل
            
            # تحديد المدة
            duration_minutes = None
            if time_type == 'fixed':
                duration_text = self.duration_combo.currentText()
                if duration_text == 'وقت مخصص':
                    # استخدام الوقت المخصص
                    custom_duration = self.custom_duration_input.text().strip()
                    if not custom_duration:
                        QMessageBox.warning(self, "خطأ", "يرجى إدخال المدة المخصصة")
                        return
                    try:
                        duration_minutes = int(custom_duration)
                        if duration_minutes <= 0:
                            QMessageBox.warning(self, "خطأ", "يجب أن تكون المدة أكبر من صفر")
                            return
                    except ValueError:
                        QMessageBox.warning(self, "خطأ", "يرجى إدخال رقم صحيح للمدة")
                        return
                else:
                    # استخدام الخيارات المحددة مسبقاً
                    duration_minutes = int(duration_text.split()[0])  # استخراج الرقم من النص
            
            # بدء الجلسة
            result = self.session_controller.start_session(
                device_id=self.device_data['id'],
                pricing_type=pricing_type,
                time_type=time_type,
                duration_minutes=duration_minutes,
                customer_phone=customer_phone
            )
            
            if result['success']:
                # تحديث بيانات الجهاز من قاعدة البيانات أولاً
                try:
                    from models.device_model import DeviceModel
                    device_model = DeviceModel()
                    updated_device = device_model.get_device_by_id(self.device_data['id'])
                    if updated_device:
                        self.device_data.update(updated_device)
                except Exception as e:
                    print(f"خطأ في تحديث بيانات الجهاز: {e}")
                
                # إعادة تحميل الواجهة لإظهار حالة الجلسة النشطة
                try:
                    self.setup_ui()
                except Exception as e:
                    print(f"خطأ في إعادة تحميل الواجهة: {e}")
                
                # تحديث السعر الإجمالي ومعلومات الجلسة (بعد إعادة تحميل الواجهة)
                try:
                    self.update_invoice_total()
                except Exception as e:
                    print(f"خطأ في تحديث السعر الإجمالي: {e}")
                
                # عرض رسالة النجاح وإغلاق النافذة عند الضغط على "تم"
                QMessageBox.information(self, "نجح", result['message'])
                self.accept()  # إغلاق النافذة تلقائياً
            else:
                QMessageBox.warning(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred: {str(e)}")
    
    def end_session(self):
        """إنهاء الجلسة"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            
            if current_session:
                # إيقاف التايمر فوراً عند بدء عملية إنهاء الجلسة
                self.stop_update_timer()
                
                # فتح نافذة إنهاء الجلسة والحساب
                from views.session_checkout_window import SessionCheckoutWindow
                checkout_window = SessionCheckoutWindow(current_session, self)
                checkout_window.payment_completed.connect(self.on_payment_completed)
                
                if checkout_window.exec() == QDialog.Accepted:
                    # تم تأكيد الدفع في النافذة - التايمر يبقى متوقفاً
                    pass
                else:
                    # تم إلغاء العملية - إعادة تشغيل التايمر فقط إذا كانت الجلسة لا تزال نشطة
                    current_session_check = self.session_controller.get_device_session(self.device_data['id'])
                    if current_session_check and current_session_check.get('status') == 'active' and not current_session_check.get('is_paused', False):
                        self.start_update_timer()
            else:
                QMessageBox.warning(self, "خطأ", "لا توجد جلسة نشطة")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")
    
    def on_payment_completed(self, payment_result):
        """معالجة نتيجة الدفع"""
        try:
            if payment_result['success']:
                # معالجة الدفع وإنهاء الجلسة
                from models.payment_model import PaymentModel
                payment_model = PaymentModel()
                
                result = payment_model.process_session_checkout(
                    session_id=payment_result['session_id'],
                    cashier_id=self.session_controller.current_user['id'],
                    payment_method=payment_result['payment_method'],
                    total_amount=payment_result['total_amount'],
                    cash_amount=payment_result['cash_amount'],
                    customer_amount=payment_result['customer_amount'],
                    customer_data=payment_result['customer_data']
                )
                
                if result['success']:
                    # إيقاف التايمر عند إنهاء الجلسة
                    self.stop_update_timer()
                    
                    # عرض رسالة النجاح
                    message = f"تم إنهاء الجلسة والدفع بنجاح\n"
                    message += f"رقم الفاتورة: {result['invoice_id']}\n"
                    message += f"المبلغ الإجمالي: {result['total_amount']:.2f} جنيه\n"
                    message += f"طريقة الدفع: {'نقداً' if result['payment_method'] == 'cash' else 'من حساب العميل'}"
                    
                    QMessageBox.information(self, "نجح", message)
                    
                    # إرسال إشارة لتحديث الفواتير
                    try:
                        self.notify_invoice_created(result['invoice_id'])
                    except Exception as notify_error:
                        print(f"خطأ في إشعار إنشاء الفاتورة: {notify_error}")
                    
                    # إغلاق النافذة بأمان
                    try:
                        self.accept()
                    except Exception as close_error:
                        print(f"خطأ في إغلاق النافذة: {close_error}")
                        # محاولة إغلاق آمنة
                        try:
                            self.hide()  # إخفاء النافذة بدلاً من إغلاقها
                        except Exception as hide_error:
                            print(f"خطأ في إخفاء النافذة: {hide_error}")
                            pass
                else:
                    QMessageBox.warning(self, "خطأ", result['message'])
            else:
                QMessageBox.warning(self, "خطأ", "فشل في معالجة الدفع")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"خطأ مفصل في معالجة الدفع: {error_details}")
            logger.error(f"خطأ في معالجة الدفع: {error_details}")
            
            # عرض رسالة خطأ آمنة
            try:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ في معالجة الدفع: {str(e)}")
            except Exception as msg_error:
                print(f"خطأ في عرض رسالة الخطأ: {msg_error}")
                # لا نغلق النافذة أو البرنامج في حالة الخطأ
                pass
    
    def notify_invoice_created(self, invoice_id):
        """إشعار بإنشاء فاتورة جديدة"""
        try:
            print(f"تم إنشاء فاتورة جديدة: {invoice_id}")
            
            # البحث عن نافذة إدارة الفواتير وتحديثها
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app:
                # البحث في جميع النوافذ المفتوحة
                for widget in app.allWidgets():
                    if hasattr(widget, '__class__') and 'InvoiceManagementWindow' in str(widget.__class__):
                        # وجدنا نافذة إدارة الفواتير
                        print(f"تم العثور على نافذة إدارة الفواتير وتحديثها")
                        widget.load_invoices()  # إعادة تحميل الفواتير
                        break
                        
        except Exception as e:
            print(f"خطأ في إشعار إنشاء الفاتورة: {e}")
    
    def extend_session(self):
        """تمديد الجلسة"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            
            if current_session:
                # طلب المدة الإضافية
                duration, ok = QInputDialog.getInt(
                    self, "تمديد الجلسة", "المدة الإضافية (بالدقائق):", 30, 5, 180, 5
                )
                
                if ok:
                    result = self.session_controller.extend_session(current_session['id'], duration)
                    
                    if result['success']:
                        QMessageBox.information(self, "نجح", result['message'])
                        # تحديث السعر الإجمالي ومعلومات الجلسة
                        self.update_invoice_total()
                        self.accept()
                    else:
                        QMessageBox.warning(self, "خطأ", result['message'])
            else:
                QMessageBox.warning(self, "خطأ", "لا توجد جلسة نشطة")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")
    
    def end_maintenance(self):
        """إنهاء الصيانة"""
        try:
            # تأكيد من المستخدم
            reply = QMessageBox.question(
                self,
                "تأكيد إنهاء الصيانة",
                f"هل تريد إنهاء وضع الصيانة للجهاز '{self.device_data['name']}'؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # تحديث حالة الجهاز في قاعدة البيانات
                from models.device_model import DeviceModel
                device_model = DeviceModel()
                success = device_model.update_device_status(self.device_data['id'], 'available')
                
                if success:
                    # تحديث بيانات الجهاز المحلية
                    self.device_data['status'] = 'available'
                    
                    # إغلاق النافذة
                    self.accept()
                    
                    QMessageBox.information(
                        self,
                        "تم إنهاء الصيانة",
                        f"تم إنهاء وضع الصيانة للجهاز '{self.device_data['name']}' بنجاح!\nالجهاز متاح الآن للاستخدام."
                    )
                else:
                    QMessageBox.warning(self, "خطأ", "فشل في إنهاء وضع الصيانة")
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنهاء وضع الصيانة: {str(e)}")
    
    def pause_session(self):
        """إيقاف الجلسة مؤقتاً"""
        try:
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                QMessageBox.warning(self, "Warning", "No active session found")
                return
            
            # التحقق من أن الجلسة نشطة فعلاً
            session_db = self.session_controller.session_model.get_session_by_id(current_session['id'])
            if not session_db or session_db.get('status') != 'active':
                QMessageBox.warning(self, "Warning", "Session is not active")
                return
            
            # طلب تأكيد
            reply = QMessageBox.question(
                self, "Confirm Pause", 
                "Do you want to pause the session?\nTime counting will stop until resume button is pressed.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                print(f"🔄 Pausing session {current_session['id']}...")
                
                # ==== الخطوة 1: إيقاف التايمر فوراً ====
                print("🛑 Step 1: Stopping timer immediately")
                self.stop_update_timer()
                self.timer_stopped = True
                
                # تأكيد إيقاف التايمر بالكامل
                if hasattr(self, 'update_timer') and self.update_timer:
                    if self.update_timer.isActive():
                        self.update_timer.stop()
                        print("⚠️ Timer was still active, forced stop")
                
                # ==== الخطوة 2: إيقاف الجلسة في قاعدة البيانات ====
                print("💾 Step 2: Pausing session in database")
                result = self.session_controller.pause_session(current_session['id'])
                
                if result['success']:
                    print(f"✅ Session {current_session['id']} paused successfully in database")
                    
                    # ==== الخطوة 3: انتظار قصير وتحقق من الإيقاف ====
                    import time
                    time.sleep(0.1)  # 100ms للتأكد من تحديث قاعدة البيانات في exe
                    
                    session_check = self.session_controller.session_model.get_session_by_id(current_session['id'])
                    if session_check:
                        status = session_check.get('status')
                        is_paused = session_check.get('is_paused')
                        print(f"📊 Session status after pause: status={status}, is_paused={is_paused}")
                        
                        # تحقق إضافي - إذا لم يتم الإيقاف بشكل صحيح
                        if status != 'paused' or not is_paused:
                            print(f"⚠️ WARNING: Session not properly paused! Forcing update...")
                            # محاولة ثانية لضمان الإيقاف
                            self.session_controller.session_model.db.execute_query(
                                """UPDATE sessions SET is_paused = 1, status = 'paused' WHERE id = ?""",
                                (current_session['id'],),
                                fetch=False
                            )
                            time.sleep(0.1)
                    
                    # ==== الخطوة 4: حذف التايمر نهائياً ====
                    if hasattr(self, 'update_timer') and self.update_timer:
                        try:
                            self.update_timer.timeout.disconnect()
                        except:
                            pass
                        self.update_timer.deleteLater()
                        self.update_timer = None
                        print("🗑️ Timer deleted permanently")
                    
                    # ==== الخطوة 5: تأكيد نهائي ====
                    self.timer_stopped = True
                    print("✅ ALL STEPS COMPLETED - Timer is stopped and session is paused")
                    
                    # عرض رسالة النجاح
                    QMessageBox.information(
                        self, 
                        "تم الإيقاف بنجاح", 
                        f"تم إيقاف الجلسة بنجاح!\n\nالجهاز: {self.device_data['name']}\nالحالة: متوقف ⏸️\n\nلن يتم حساب أي تكلفة إضافية حتى استئناف الجلسة."
                    )
                    
                    # إغلاق النافذة
                    self.accept()
                else:
                    print(f"❌ Failed to pause session: {result.get('message')}")
                    # إعادة تشغيل التايمر إذا فشل الإيقاف
                    self.timer_stopped = False
                    self.start_update_timer()
                    QMessageBox.critical(self, "خطأ", f"فشل في إيقاف الجلسة: {result.get('message')}")
                    
        except Exception as e:
            print(f"❌ Error in pause_session: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إيقاف الجلسة: {str(e)}")
    
    def resume_session(self):
        """استئناف الجلسة"""
        try:
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                QMessageBox.warning(self, "Warning", "No paused session found")
                return
            
            # التحقق من أن الجلسة متوقفة فعلاً
            session_db = self.session_controller.session_model.get_session_by_id(current_session['id'])
            if not session_db or session_db.get('status') != 'paused':
                QMessageBox.warning(self, "Warning", "Session is not paused")
                return
            
            # طلب تأكيد
            reply = QMessageBox.question(
                self, "Confirm Resume", 
                "Do you want to resume the session?\nTime counting will continue from where it stopped.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                print(f"🔄 Resuming session {current_session['id']}...")
                
                # استئناف الجلسة في قاعدة البيانات
                result = self.session_controller.resume_session(current_session['id'])
                
                if result['success']:
                    print(f"✅ Session {current_session['id']} resumed successfully")
                    
                    import time
                    
                    # ⭐⭐⭐ تأخير إضافي للتأكد من sync كامل لجميع الجداول في exe ⭐⭐⭐
                    time.sleep(0.3)  # 300ms للتأكد من commit جدول sessions و pricing_segments
                    print("⏱️ Waited 300ms for complete database sync")
                    
                    # إعادة تعيين حالة التايمر
                    self.timer_stopped = False
                    
                    # إعادة إنشاء التايمر
                    self.setup_update_timer()
                    
                    # تحديث الواجهة
                    self.update_invoice_total()
                    
                    print(f"✅ Timer and UI updated for session {current_session['id']}")
                    
                    # عرض رسالة النجاح
                    QMessageBox.information(
                        self, 
                        "تم الاستئناف بنجاح", 
                        f"تم استئناف الجلسة بنجاح!\n\nالجهاز: {self.device_data['name']}\nالحالة: نشط ▶️\n\nسيتم حساب التكلفة من حيث توقفت."
                    )
                    
                    # إغلاق النافذة
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to resume session")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resuming session: {str(e)}")
    
    def update_session_info(self):
        """تحديث معلومات الجلسة (الوقت والتكلفة)"""
        try:
            # التحقق من حالة التايمر - إذا كان متوقفاً، لا تقم بأي تحديث
            if hasattr(self, 'timer_stopped') and self.timer_stopped:
                print("Timer is stopped, skipping update_session_info")
                return
            
            # التحقق من حالة التايمر - إذا لم يكن نشطاً، لا تقم بأي تحديث
            if hasattr(self, 'update_timer') and self.update_timer and not self.update_timer.isActive():
                print("Timer is not active, skipping update_session_info")
                return
            
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                if hasattr(self, 'elapsed_label'):
                    self.elapsed_label.setText("لا توجد جلسة نشطة")
                return
            
            # التحقق من حالة الجلسة - إذا كانت متوقفة، لا تقم بأي تحديث
            if current_session and (current_session.get('is_paused', False) or 
                                  current_session.get('status') in ['paused', 'completed', 'ended']):
                print("Session is paused/ended, skipping update_session_info")
                # إيقاف التايمر عند إيقاف الجلسة
                if current_session.get('status') == 'paused':
                    self.stop_update_timer()
                    self.timer_stopped = True
                    print("Timer stopped due to session pause")
                return
            
            # التحقق من انتهاء الوقت للجلسات المحددة الوقت
            if current_session and current_session.get('time_type') == 'fixed':
                # الحصول على معلومات الوقت من النموذج
                time_info = self.session_controller.get_session_time_info(current_session['id'])
                if time_info and time_info.get('is_expired', False):
                    print("Session time expired, stopping timer and skipping update")
                    # إيقاف التايمر نهائياً عند انتهاء الوقت
                    self.stop_update_timer()
                    self.timer_stopped = True
                    
                    # عرض رسالة تنبيهية في عداد الوقت
                    if hasattr(self, 'elapsed_label'):
                        self.elapsed_label.setText("⏰ انتهى الوقت المحدد للجلسة - تم إيقاف العد")
                    
                    return
            
            # حساب الوقت المنقضي - إصلاح فوري للمشكلة
            start_time = current_session['start_time']
            if isinstance(start_time, str):
                from datetime import datetime
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')
            elif isinstance(start_time, str) and '.' not in start_time:
                from datetime import datetime
                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            
            # إصلاح فوري: استخدام معلومات الوقت من النموذج بدلاً من الحساب المباشر
            time_info = self.session_controller.get_session_time_info(current_session['id'])
            if time_info and 'elapsed_minutes_total' in time_info:
                elapsed_minutes = time_info['elapsed_minutes_total']
                print(f"استخدام الوقت من النموذج: {elapsed_minutes} دقيقة")
            else:
                # حساب بديل إذا فشل الحصول على معلومات الوقت
                now = datetime.now()
                elapsed = now - start_time
                elapsed_minutes = int(elapsed.total_seconds() / 60)
                print(f"استخدام الحساب البديل: {elapsed_minutes} دقيقة")
            
            # حساب تكلفة الجلسة
            session_cost_info = self.session_controller.get_session_cost_info(current_session['id'])
            
            if session_cost_info:
                elapsed_formatted = session_cost_info.get('elapsed_time_formatted', f"{elapsed_minutes} دقيقة")
                total_cost = session_cost_info.get('total_cost', 0)
                billable_minutes = session_cost_info.get('billable_minutes', elapsed_minutes)
                is_expired = session_cost_info.get('is_expired', False)
                
                # عرض معلومات مختلفة حسب حالة الجلسة
                if is_expired and current_session.get('time_type') == 'fixed':
                    time_info = f"الوقت المنقضي: {elapsed_formatted} | التكلفة النهائية: {total_cost:.2f} جنيه (انتهى الوقت المحدد)"
                else:
                    time_info = f"الوقت المنقضي: {elapsed_formatted} | التكلفة الحالية: {total_cost:.2f} جنيه"
            else:
                # حساب بديل - إصلاح فوري للمشكلة
                time_type = current_session.get('time_type', 'open')
                session_price = current_session.get('session_price', 0)
                
                # إصلاح فوري: استخدام معلومات الوقت من النموذج بدلاً من الحساب المباشر
                if time_info and 'elapsed_minutes_total' in time_info:
                    elapsed_minutes = time_info['elapsed_minutes_total']
                    print(f"استخدام الوقت من النموذج في الحساب البديل: {elapsed_minutes} دقيقة")
                
                if time_type == 'fixed':
                    duration_minutes = current_session.get('duration_minutes', 60)
                    cost_per_minute = session_price / 60
                    # استخدام الوقت المحتسب (لا يتجاوز المدة المحددة)
                    billable_minutes = min(elapsed_minutes, duration_minutes)
                    current_cost = billable_minutes * cost_per_minute
                    
                    # التحقق من انتهاء الوقت
                    is_expired = elapsed_minutes >= duration_minutes
                    if is_expired:
                        time_info = f"الوقت المنقضي: {elapsed_minutes} دقيقة | التكلفة النهائية: {current_cost:.2f} جنيه (انتهى الوقت المحدد)"
                    else:
                        time_info = f"الوقت المنقضي: {elapsed_minutes} دقيقة | التكلفة الحالية: {current_cost:.2f} جنيه"
                else:
                    cost_per_minute = session_price / 60
                    current_cost = elapsed_minutes * cost_per_minute
                    time_info = f"الوقت المنقضي: {elapsed_minutes} دقيقة | التكلفة الحالية: {current_cost:.2f} جنيه"
            
            # تحديث التسمية
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText(time_info)
            
        except Exception as e:
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText(f"خطأ في تحديث معلومات الجلسة: {str(e)}")
    
    def update_invoice_total(self):
        """تحديث السعر الإجمالي للفاتورة والوقت المفصل"""
        try:
            # ===== الفحص الأول: حالة التايمر =====
            if hasattr(self, 'timer_stopped') and self.timer_stopped:
                print("⏹️ Timer is marked as stopped, forcing stop and skipping update")
                if hasattr(self, 'update_timer') and self.update_timer and self.update_timer.isActive():
                    self.update_timer.stop()
                    print("🛑 Forced timer stop due to timer_stopped flag")
                return
            
            # ===== الفحص الثاني: حالة التايمر الفعلية =====
            if hasattr(self, 'update_timer') and self.update_timer and not self.update_timer.isActive():
                print("⏹️ Timer is not active, skipping update")
                self.timer_stopped = True
                return
            
            # ===== الفحص الثالث: وجود الجلسة =====
            device_session = self.session_controller.get_device_session(self.device_data['id'])
            if not device_session:
                print("❌ No session found, stopping timer immediately")
                self.stop_update_timer()
                return
            
            # ===== الفحص الرابع: حالة الجلسة من قاعدة البيانات مباشرة =====
            # نحصل على الجلسة مباشرة من قاعدة البيانات لضمان أحدث حالة
            current_session = self.session_controller.session_model.get_session_by_id(device_session['id'])
            if not current_session:
                print("❌ Session not found in database, stopping timer")
                self.stop_update_timer()
                return
            
            session_status = current_session.get('status', '')
            is_paused = current_session.get('is_paused', False)
            
            # ===== الفحص الخامس: التحقق الصارم من حالة الإيقاف =====
            # إيقاف التايمر فوراً إذا كانت الجلسة متوقفة أو منتهية
            if is_paused or session_status in ['paused', 'completed', 'ended']:
                print(f"🛑 Session is {session_status} with is_paused={is_paused}, stopping timer IMMEDIATELY")
                self.stop_update_timer()
                return
            
            # ===== الفحص السادس: التحقق من حالة النشاط =====
            if session_status != 'active':
                print(f"🛑 Session status is '{session_status}' (not active), stopping timer")
                self.stop_update_timer()
                return
            
            # ===== الفحص السابع: انتهاء الوقت للجلسات المحددة =====
            if current_session and current_session.get('time_type') == 'fixed':
                # الحصول على معلومات الوقت من النموذج
                time_info = self.session_controller.get_session_time_info(current_session['id'])
                if time_info and time_info.get('is_expired', False):
                    print("⏱️ Session time expired, stopping timer immediately")
                    print(f"   - Elapsed: {time_info.get('elapsed_minutes_total')} minutes")
                    print(f"   - Duration: {current_session.get('duration_minutes')} minutes")
                    
                    # إيقاف التايمر نهائياً عند انتهاء الوقت
                    self.stop_update_timer()
                    self.timer_stopped = True
                    
                    # ⭐⭐⭐ تحديث الواجهة بالقيم النهائية الثابتة ⭐⭐⭐
                    # حساب التكلفة النهائية
                    session_cost_info = self.session_controller.get_session_cost_info(current_session['id'])
                    session_cost = session_cost_info.get('total_cost', 0) if session_cost_info else 0
                    
                    # حساب تكلفة المنتجات
                    products_result = self.session_controller.get_session_products(current_session['id'])
                    products_cost = 0
                    if products_result['success']:
                        for product in products_result['products']:
                            products_cost += product.get('total_price', 0)
                    
                    total_cost = session_cost + products_cost
                    
                    # عرض الوقت والتكلفة النهائية الثابتة
                    duration_minutes = current_session.get('duration_minutes', 0)
                    duration_formatted = f"{duration_minutes // 60:02d}:{duration_minutes % 60:02d}:00"
                    
                    if hasattr(self, 'elapsed_label'):
                        self.elapsed_label.setText(
                            f"⏰ انتهى الوقت المحدد!\n"
                            f"الوقت النهائي: {duration_formatted}\n"
                            f"التكلفة النهائية: {session_cost:.2f} جنيه"
                        )
                    
                    if hasattr(self, 'invoice_total_label'):
                        self.invoice_total_label.setText(
                            f"💰 السعر الإجمالي للفاتورة: {total_cost:.2f} جنيه (انتهى الوقت المحدد)"
                        )
                    
                    return
            
            # تحديث معلومات الجلسة أولاً
            self.update_session_info()
            
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                self.invoice_total_label.setText("لا توجد جلسة نشطة")
                if hasattr(self, 'elapsed_label'):
                    self.elapsed_label.setText("لا توجد جلسة نشطة")
                # إيقاف التايمر إذا لم توجد جلسة نشطة
                self.stop_update_timer()
                return
            
            # التحقق من حالة الجلسة - إيقاف التايمر إذا كانت متوقفة أو منتهية
            if (current_session.get('status') in ['paused', 'completed', 'ended'] or 
                current_session.get('is_paused', False)):
                # إيقاف التايمر إذا كانت الجلسة متوقفة أو منتهية
                print(f"الجلسة {current_session['id']} متوقفة أو منتهية - إيقاف التايمر")
                self.stop_update_timer()
                self.timer_stopped = True
                
                # عرض التكلفة الثابتة للجلسة المتوقفة
                session_cost_info = self.session_controller.get_session_cost_info(current_session['id'])
                session_cost = session_cost_info.get('total_cost', 0) if session_cost_info else 0
                
                # حساب تكلفة المنتجات
                products_result = self.session_controller.get_session_products(current_session['id'])
                products_cost = 0
                if products_result['success']:
                    for product in products_result['products']:
                        products_cost += product.get('total_price', 0)
                
                total_cost = session_cost + products_cost
                
                # عرض التكلفة الثابتة
                if current_session.get('status') == 'paused':
                    total_text = f"💰 السعر الإجمالي للفاتورة: {total_cost:.2f} جنيه (الجلسة متوقفة)"
                else:
                    total_text = f"💰 السعر الإجمالي للفاتورة: {total_cost:.2f} جنيه (الجلسة منتهية)"
                
                self.invoice_total_label.setText(total_text)
                return
            
            # حساب تكلفة الجلسة
            session_cost_info = self.session_controller.get_session_cost_info(current_session['id'])
            session_cost = session_cost_info.get('total_cost', 0) if session_cost_info else 0
            
            # التحقق من انتهاء الوقت من معلومات التكلفة
            if session_cost_info and session_cost_info.get('is_expired', False):
                # إيقاف التايمر نهائياً عند انتهاء الوقت المحدد
                self.stop_update_timer()
                self.timer_stopped = True
                
                # عرض رسالة تنبيهية
                if hasattr(self, 'elapsed_label'):
                    self.elapsed_label.setText("⏰ انتهى الوقت المحدد للجلسة - تم إيقاف العد")
                
                # حساب التكلفة النهائية للمنتجات أيضاً
                products_result = self.session_controller.get_session_products(current_session['id'])
                products_cost = 0
                if products_result['success']:
                    for product in products_result['products']:
                        products_cost += product.get('total_price', 0)
                
                total_cost = session_cost + products_cost
                
                # عرض رسالة تنبيهية في السعر الإجمالي
                total_text = f"💰 السعر الإجمالي للفاتورة: {total_cost:.2f} جنيه (انتهى الوقت المحدد)"
                self.invoice_total_label.setText(total_text)
                return
            
            
            
            # حساب تكلفة المنتجات
            products_result = self.session_controller.get_session_products(current_session['id'])
            products_cost = 0
            if products_result['success']:
                for product in products_result['products']:
                    products_cost += product['total_price']
            
            # السعر الإجمالي
            total_invoice = session_cost + products_cost
            
            # عرض السعر الإجمالي
            total_text = f"💰 السعر الإجمالي للفاتورة: {total_invoice:.2f} جنيه"
            total_text += f"\n📊 (الجلسة: {session_cost:.2f} جنيه + المنتجات: {products_cost:.2f} جنيه)"
            
            self.invoice_total_label.setText(total_text)
            
            # تحديث عرض الوقت المفصل
            self.update_detailed_time_display(current_session, session_cost_info)
            
        except Exception as e:
            self.invoice_total_label.setText(f"خطأ في حساب السعر الإجمالي: {str(e)}")
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText(f"خطأ في تحديث الوقت: {str(e)}")
    
    def update_detailed_time_display(self, current_session, session_cost_info):
        """تحديث عرض الوقت المفصل"""
        try:
            # التحقق من حالة التايمر - إذا كان متوقفاً، لا تقم بأي تحديث
            if hasattr(self, 'timer_stopped') and self.timer_stopped:
                print("Timer is stopped, skipping update_detailed_time_display")
                return
            
            # التحقق من حالة الجلسة - إذا كانت متوقفة، لا تقم بأي تحديث
            if current_session and (current_session.get('is_paused', False) or 
                                  current_session.get('status') in ['paused', 'completed', 'ended']):
                print("Session is paused/ended, skipping update_detailed_time_display")
                return
            
            # ⭐⭐⭐ التحقق من انتهاء الوقت للجلسات المحددة الوقت (بشكل صحيح) ⭐⭐⭐
            if current_session and current_session.get('time_type') == 'fixed':
                # ⭐ استخدم معلومات الوقت من النموذج (مع خصم وقت التوقف)
                time_check_info = self.session_controller.get_session_time_info(current_session['id'])
                
                if time_check_info:
                    elapsed_minutes_actual = time_check_info.get('elapsed_minutes_total', 0)
                    duration_minutes = current_session.get('duration_minutes', 60)
                    is_expired = time_check_info.get('is_expired', False)
                    
                    # التحقق من انتهاء الوقت
                    if is_expired or elapsed_minutes_actual >= duration_minutes:
                        print(f"⏰ Session time expired, skipping update_detailed_time_display")
                        print(f"   - Elapsed (actual): {elapsed_minutes_actual} minutes")
                        print(f"   - Duration: {duration_minutes} minutes")
                        return
            
            if not session_cost_info:
                return
            
            # الحصول على معلومات الوقت المفصل
            session_time_info = self.session_controller.get_session_time_info(current_session['id'])
            if not session_time_info:
                return
            
            # عرض الوقت المفصل
            elapsed_hours = session_time_info.get('elapsed_hours', 0)
            elapsed_minutes = session_time_info.get('elapsed_minutes', 0)
            elapsed_seconds = session_time_info.get('elapsed_seconds', 0)
            elapsed_formatted = f"{elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d}"
            
            total_cost = session_cost_info.get('total_cost', 0)
            
            # عرض الوقت المفصل والتكلفة
            time_info = f"⏱️ الوقت المنقضي: {elapsed_formatted} | 💰 التكلفة الحالية: {total_cost:.2f} جنيه"
            
            # عرض تفاصيل التسعيرة المتقدمة إذا كانت متوفرة
            pricing_summary = session_cost_info.get('pricing_summary', {})
            if pricing_summary and (pricing_summary.get('total_single_cost', 0) > 0 or pricing_summary.get('total_multi_cost', 0) > 0):
                pricing_details = "\n📊 تفاصيل التسعيرة:\n"
                
                if pricing_summary.get('total_single_cost', 0) > 0:
                    single_hours = pricing_summary.get('total_single_hours', 0)
                    single_cost = pricing_summary.get('total_single_cost', 0)
                    single_h = int(single_hours)
                    single_m = int((single_hours - single_h) * 60)
                    single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                    pricing_details += f"👤 فردي: {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه\n"
                
                if pricing_summary.get('total_multi_cost', 0) > 0:
                    multi_hours = pricing_summary.get('total_multi_hours', 0)
                    multi_cost = pricing_summary.get('total_multi_cost', 0)
                    multi_h = int(multi_hours)
                    multi_m = int((multi_hours - multi_h) * 60)
                    multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                    pricing_details += f"👥 جماعي: {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه\n"
                
                pricing_details += f"💰 المجموع: {pricing_summary.get('total_cost', 0):.2f} جنيه"
                time_info += pricing_details
            
            # تحديث التسمية
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText(time_info)
                
        except Exception as e:
            logger.error(f"خطأ في تحديث عرض الوقت المفصل: {e}")
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText(f"خطأ في تحديث الوقت: {str(e)}")
    
    def change_pricing_from_session_dialog(self):
        """تغيير نوع التسعيرة من نافذة إدارة الجلسة"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            
            if not current_session:
                QMessageBox.warning(self, "خطأ", "لا توجد جلسة نشطة على هذا الجهاز")
                return
            
            # إنشاء نافذة حوار لتغيير نوع التسعيرة
            dialog = ChangePricingTypeDialog(self.device_data, current_session)
            if dialog.exec() == QDialog.Accepted:
                new_pricing_type = dialog.get_selected_pricing_type()
                
                # إيقاف التايمر القديم أولاً قبل تغيير التسعيرة
                print("Stopping old timer before changing pricing type")
                self.stop_update_timer()
                
                # تغيير نوع التسعيرة
                result = self.session_controller.change_session_pricing_type(
                    current_session['id'], 
                    new_pricing_type
                )
                
                if result['success']:
                    # عرض تفاصيل التسعيرة المتقدمة
                    pricing_summary = result.get('pricing_summary', {})
                    
                    message = f"✅ {result['message']}\n\n"
                    message += f"💰 السعر الجديد: {result['new_price']:.2f} جنيه/ساعة\n\n"
                    
                    if pricing_summary:
                        message += "📊 ملخص التسعيرة المحدث:\n"
                        
                        if pricing_summary.get('total_single_cost', 0) > 0:
                            single_hours = pricing_summary.get('total_single_hours', 0)
                            single_cost = pricing_summary.get('total_single_cost', 0)
                            single_h = int(single_hours)
                            single_m = int((single_hours - single_h) * 60)
                            single_s = int(((single_hours - single_h) * 60 - single_m) * 60)
                            message += f"👤 فردي: {single_h:02d}:{single_m:02d}:{single_s:02d} = {single_cost:.2f} جنيه\n"
                        
                        if pricing_summary.get('total_multi_cost', 0) > 0:
                            multi_hours = pricing_summary.get('total_multi_hours', 0)
                            multi_cost = pricing_summary.get('total_multi_cost', 0)
                            multi_h = int(multi_hours)
                            multi_m = int((multi_hours - multi_h) * 60)
                            multi_s = int(((multi_hours - multi_h) * 60 - multi_m) * 60)
                            message += f"👥 جماعي: {multi_h:02d}:{multi_m:02d}:{multi_s:02d} = {multi_cost:.2f} جنيه\n"
                        
                        message += f"💰 المجموع: {format_currency(pricing_summary['total_cost'])}"
                    
                    QMessageBox.information(
                        self, 
                        "نجح التغيير", 
                        message
                    )
                    
                    # إعادة إنشاء التايمر بعد تغيير التسعيرة
                    print("Re-setting up timer after pricing type change")
                    self.setup_update_timer()
                    
                    # تحديث عرض النافذة فوراً
                    self.update_invoice_total()
                else:
                    QMessageBox.warning(self, "خطأ", result['message'])
                    # إعادة تشغيل التايمر حتى في حالة الفشل
                    self.start_update_timer()
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تغيير نوع التسعيرة: {str(e)}")
            # إعادة تشغيل التايمر في حالة حدوث خطأ
            try:
                self.start_update_timer()
            except:
                pass
    
    def setup_update_timer(self):
        """إعداد timer للتحديث المستمر للسعر الإجمالي"""
        try:
            from PySide6.QtCore import QTimer
            
            # إيقاف وحذف أي تايمر قديم أولاً لتجنب تايمرات متعددة
            if hasattr(self, 'update_timer') and self.update_timer:
                try:
                    self.update_timer.stop()
                    self.update_timer.timeout.disconnect()
                except:
                    pass
                self.update_timer.deleteLater()
                self.update_timer = None
                print("Old timer stopped and deleted")
            
            # الحصول على حالة الجلسة الحالية بشكل محدث من قاعدة البيانات
            current_session = self.session_controller.session_model.get_session_by_id(
                self.session_controller.get_device_session(self.device_data['id'])['id']
            ) if self.session_controller.get_device_session(self.device_data['id']) else None
            
            # التحقق الصارم من حالة الجلسة قبل تشغيل التايمر
            if not current_session:
                self.timer_stopped = True
                print("❌ No session found - timer not created")
                return
            
            session_status = current_session.get('status', '')
            is_paused = current_session.get('is_paused', False)
            
            # تحقق صارم: فقط الجلسات النشطة وغير المتوقفة
            if session_status != 'active' or is_paused:
                self.timer_stopped = True
                print(f"❌ Session status is '{session_status}' with is_paused={is_paused} - timer not started")
                return
            
            # إنشاء تايمر جديد فقط للجلسات النشطة
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.update_invoice_total)
            self.update_timer.setSingleShot(False)  # تكرار مستمر
            
            # تحديث حالة التايمر
            self.timer_stopped = False
            
            # تشغيل التايمر
            self.update_timer.start(1000)  # تحديث كل ثانية
            
            print(f"✅ Timer setup and started for active session {current_session['id']}")
                
        except Exception as e:
            self.timer_stopped = True
            print(f"❌ Error setting up update timer: {e}")
    
    def start_update_timer(self):
        """تشغيل timer التحديث"""
        try:
            # التأكد من إيقاف أي تايمر قديم أولاً
            if hasattr(self, 'update_timer') and self.update_timer:
                if self.update_timer.isActive():
                    self.update_timer.stop()
                    print("Stopped existing active timer before starting new one")
            
            if hasattr(self, 'update_timer') and self.update_timer:
                # إعادة تعيين حالة التايمر
                self.timer_stopped = False
                
                # التحقق من وجود جلسة نشطة قبل تشغيل التايمر
                current_session = self.session_controller.get_device_session(self.device_data['id'])
                if (current_session and 
                    current_session.get('status') == 'active' and 
                    not current_session.get('is_paused', False) and
                    current_session.get('status') not in ['completed', 'ended']):
                    
                    # تحديث حالة التايمر أولاً
                    self.timer_stopped = False
                    
                    # تشغيل التايمر
                    self.update_timer.start(1000)  # تحديث كل ثانية
                    
                    print("Timer started and marked as running")
                    
                    # تحديث العرض
                    if hasattr(self, 'elapsed_label'):
                        self.elapsed_label.setText("▶️ الجلسة نشطة - العد يعمل")
                else:
                    self.timer_stopped = True  # تحديث حالة التايمر
                    print("Cannot start timer: no active session or session is paused/ended")
            else:
                self.timer_stopped = True  # تحديث حالة التايمر
                print("Cannot start timer: no timer object")
        except Exception as e:
            print(f"Error starting update timer: {e}")
            self.timer_stopped = True  # تحديث حالة التايمر في حالة الخطأ
    
    def stop_update_timer(self):
        """إيقاف timer التحديث"""
        try:
            # إيقاف التايمر فوراً وفصل الاتصال
            if hasattr(self, 'update_timer') and self.update_timer:
                # التحقق من حالة التايمر قبل الإيقاف
                was_active = self.update_timer.isActive()
                
                # إيقاف التايمر
                self.update_timer.stop()
                
                # فصل الاتصال لمنع أي استدعاءات إضافية
                try:
                    self.update_timer.timeout.disconnect(self.update_invoice_total)
                    print("Timer disconnected from update_invoice_total")
                except:
                    pass  # في حالة عدم وجود اتصال
                
                print(f"Timer stopped (was {'active' if was_active else 'inactive'})")
            
            # تحديث حالة التايمر بشكل فوري
            self.timer_stopped = True
            print("Timer marked as stopped")
            
            # إيقاف أي عمليات تحديث أخرى
            if hasattr(self, 'elapsed_label'):
                self.elapsed_label.setText("⏸️ الجلسة متوقفة - تم إيقاف العد")
                
        except Exception as e:
            print(f"Error stopping update timer: {e}")
            self.timer_stopped = True  # تحديث حالة التايمر في حالة الخطأ
    
    def closeEvent(self, event):
        """إيقاف timer عند إغلاق النافذة"""
        try:
            # إيقاف التايمر باستخدام الدالة الجديدة
            self.stop_update_timer()
        except Exception as e:
            print(f"Error stopping timer: {e}")
        
        try:
            # حذف التايمر نهائياً
            if hasattr(self, 'update_timer') and self.update_timer:
                try:
                    self.update_timer.timeout.disconnect()
                except:
                    pass
                self.update_timer.deleteLater()
                self.update_timer = None
                print("Timer deleted in closeEvent")
        except Exception as e:
            print(f"Error deleting timer: {e}")
        
        try:
            # تنظيف أي موارد أخرى
            if hasattr(self, 'session_controller'):
                self.session_controller = None
        except Exception as e:
            print(f"Error cleaning up resources: {e}")
            
        event.accept()
    
    def switch_to_products_tab(self):
        """الانتقال إلى تبويبة المنتجات"""
        try:
            # التحقق من وجود تبويبة المنتجات
            if hasattr(self, 'tab_widget') and hasattr(self, 'products_tab'):
                # العثور على فهرس تبويبة المنتجات
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "المنتجات":
                        self.tab_widget.setCurrentIndex(i)
                        break
                else:
                    QMessageBox.warning(self, "تحذير", "تبويبة المنتجات غير متاحة")
            else:
                QMessageBox.warning(self, "تحذير", "تبويبة المنتجات غير متاحة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الانتقال إلى تبويبة المنتجات: {str(e)}")

class ProductTab(QWidget):
    """تبويبة المنتجات في نافذة إدارة الجلسة"""
    
    def __init__(self, session_controller, device_data, session_dialog=None, parent=None):
        super().__init__(parent)
        self.session_controller = session_controller
        self.device_data = device_data
        self.session_dialog = session_dialog  # مرجع مباشر إلى SessionDialog
        self.product_model = ProductModel()
        self.invoice_model = InvoiceModel()
        self.setup_ui()
        self.load_products()
        self.load_session_products()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # عنوان التبويبة
        title_label = QLabel("إدارة المنتجات")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # إنشاء تخطيط أفقي للمحتوى
        main_layout = QHBoxLayout()
        
        # الجانب الأيسر - قائمة المنتجات المتاحة
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("المنتجات المتاحة:"))
        
        # قائمة المنتجات
        self.products_list = QListWidget()
        self.products_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        left_layout.addWidget(self.products_list)
        
        # زر إضافة منتج
        self.add_product_btn = QPushButton("إضافة منتج للجلسة")
        self.add_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.add_product_btn.clicked.connect(self.add_product_to_session)
        left_layout.addWidget(self.add_product_btn)
        
        main_layout.addLayout(left_layout)
        
        # الجانب الأيمن - منتجات الجلسة الحالية
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("منتجات الجلسة الحالية:"))
        
        # جدول منتجات الجلسة
        self.session_products_table = QTableWidget()
        self.session_products_table.setColumnCount(4)
        self.session_products_table.setHorizontalHeaderLabels([
            "المنتج", "الكمية", "السعر", "الإجمالي"
        ])
        self.session_products_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # تحسين عرض الجدول
        header = self.session_products_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        right_layout.addWidget(self.session_products_table)
        
        # زر حذف منتج
        self.remove_product_btn = QPushButton("حذف المنتج المحدد")
        self.remove_product_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.remove_product_btn.clicked.connect(self.remove_product_from_session)
        right_layout.addWidget(self.remove_product_btn)
        
        main_layout.addLayout(right_layout)
        layout.addLayout(main_layout)
        
        # إجمالي منتجات الجلسة
        self.total_label = QLabel("إجمالي المنتجات: 0.00 جنيه")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; margin-top: 10px;")
        layout.addWidget(self.total_label)
    
    def load_products(self):
        """تحميل المنتجات المتاحة"""
        try:
            products = self.product_model.get_available_products()
            self.products_list.clear()
            
            for product in products:
                # التحقق من توفر المنتج (كمية أكبر من 0)
                if product['stock_quantity'] > 0:
                    item_text = f"{product['name']} - {product['price']} جنيه (متوفر: {product['stock_quantity']})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, product)
                    self.products_list.addItem(item)
                else:
                    # إضافة المنتج مع إشارة إلى عدم التوفر
                    item_text = f"{product['name']} - {product['price']} جنيه (غير متوفر)"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, product)
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # تعطيل العنصر
                    item.setForeground(QColor(128, 128, 128))  # لون رمادي
                    self.products_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading products: {e}")
            import traceback
            traceback.print_exc()
    
    def load_session_products(self):
        """تحميل منتجات الجلسة الحالية"""
        try:
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                self.session_products_table.setRowCount(0)
                self.total_label.setText("إجمالي المنتجات: 0.00 جنيه")
                return
            
            # الحصول على منتجات الجلسة
            result = self.session_controller.get_session_products(current_session['id'])
            
            if result['success']:
                products = result['products']
                self.session_products_table.setRowCount(len(products))
                
                total_cost = 0.0
                for row, product in enumerate(products):
                    self.session_products_table.setItem(row, 0, QTableWidgetItem(product['product_name']))
                    self.session_products_table.setItem(row, 1, QTableWidgetItem(str(product['quantity'])))
                    self.session_products_table.setItem(row, 2, QTableWidgetItem(f"{product['unit_price']:.2f}"))
                    self.session_products_table.setItem(row, 3, QTableWidgetItem(f"{product['total_price']:.2f}"))
                    
                    # حفظ معرف منتج الجلسة للاستخدام عند الحذف
                    self.session_products_table.item(row, 0).setData(Qt.UserRole, product['id'])
                    
                    total_cost += product['total_price']
                
                self.total_label.setText(f"إجمالي المنتجات: {total_cost:.2f} جنيه")
            else:
                self.session_products_table.setRowCount(0)
                self.total_label.setText("إجمالي المنتجات: 0.00 جنيه")
            
        except Exception as e:
            print(f"Error loading session products: {e}")
            self.session_products_table.setRowCount(0)
            self.total_label.setText("إجمالي المنتجات: 0.00 جنيه")
    
    def add_product_to_session(self):
        """إضافة منتج للجلسة"""
        try:
            current_item = self.products_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار منتج أولاً")
                return
            
            product = current_item.data(Qt.UserRole)
            if not product:
                QMessageBox.warning(self, "تحذير", "بيانات المنتج غير صحيحة")
                return
            
            # الحصول على الجلسة الحالية
            current_session = self.session_controller.get_device_session(self.device_data['id'])
            if not current_session:
                QMessageBox.warning(self, "تحذير", "لا توجد جلسة نشطة")
                return
            
            # طلب الكمية
            quantity, ok = QInputDialog.getInt(
                self, 
                "إدخال الكمية", 
                f"كمية {product['name']} (الحد الأقصى: {product['stock_quantity']}):",
                1,  # القيمة الافتراضية
                1,  # الحد الأدنى
                product['stock_quantity']  # الحد الأقصى
            )
            
            if ok and quantity > 0:
                # التحقق من أن الكمية لا تتجاوز المتوفر
                if quantity > product['stock_quantity']:
                    QMessageBox.warning(
                        self, 
                        "تحذير", 
                        f"الكمية المطلوبة ({quantity}) تتجاوز المتوفر ({product['stock_quantity']})"
                    )
                    return
                
                # إضافة المنتج للجلسة
                result = self.session_controller.add_product_to_session(
                    current_session['id'], 
                    product['id'], 
                    quantity
                )
                
                if result['success']:
                    QMessageBox.information(
                        self, 
                        "تم الإضافة بنجاح", 
                        f"تم إضافة {result['quantity']} من {result['product_name']} للجلسة\n"
                        f"السعر الوحدة: {result['unit_price']} جنيه\n"
                        f"الإجمالي: {result['total_price']} جنيه"
                    )
                    
                    # تحديث قائمة منتجات الجلسة أولاً
                    self.load_session_products()
                    
                    # تحديث قائمة المنتجات المتاحة
                    self.load_products()
                    
                    # تحديث فوري للسعر الإجمالي ومعلومات الجلسة
                    if self.session_dialog:
                        if hasattr(self.session_dialog, 'update_invoice_total'):
                            self.session_dialog.update_invoice_total()
                        if hasattr(self.session_dialog, 'update_session_info'):
                            self.session_dialog.update_session_info()
                        
                        # تحديث إضافي فوري للتأكد
                        self.session_dialog.repaint()
                        
                        # تحديث فوري إضافي
                        self.force_update_session_info()
                else:
                    QMessageBox.critical(self, "خطأ", result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في إضافة المنتج: {str(e)}")
    
    def remove_product_from_session(self):
        """حذف منتج من الجلسة"""
        try:
            current_row = self.session_products_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار منتج للحذف")
                return
            
            # الحصول على معرف منتج الجلسة
            session_product_id = self.session_products_table.item(current_row, 0).data(Qt.UserRole)
            if not session_product_id:
                QMessageBox.warning(self, "تحذير", "معرف المنتج غير صحيح")
                return
            
            # طلب تأكيد الحذف
            product_name = self.session_products_table.item(current_row, 0).text()
            quantity = self.session_products_table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self, 
                "تأكيد الحذف", 
                f"هل تريد حذف {quantity} من {product_name} من الجلسة؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # حذف المنتج من الجلسة
                result = self.session_controller.remove_product_from_session(session_product_id)
                
                if result['success']:
                    QMessageBox.information(self, "تم الحذف", result['message'])
                    
                    # تحديث قائمة منتجات الجلسة أولاً
                    self.load_session_products()
                    
                    # تحديث قائمة المنتجات المتاحة
                    self.load_products()
                    
                    # تحديث فوري للسعر الإجمالي ومعلومات الجلسة
                    if self.session_dialog:
                        if hasattr(self.session_dialog, 'update_invoice_total'):
                            self.session_dialog.update_invoice_total()
                        if hasattr(self.session_dialog, 'update_session_info'):
                            self.session_dialog.update_session_info()
                        
                        # تحديث إضافي فوري للتأكد
                        self.session_dialog.repaint()
                        
                        # تحديث فوري إضافي
                        self.force_update_session_info()
                else:
                    QMessageBox.critical(self, "خطأ", result['message'])
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حذف المنتج: {str(e)}")
    
    def force_update_session_info(self):
        """تحديث فوري إضافي لمعلومات الجلسة"""
        try:
            if self.session_dialog:
                # تحديث السعر الإجمالي
                if hasattr(self.session_dialog, 'update_invoice_total'):
                    self.session_dialog.update_invoice_total()
                
                # تحديث معلومات الجلسة
                if hasattr(self.session_dialog, 'update_session_info'):
                    self.session_dialog.update_session_info()
                
                # إجبار التحديث المرئي
                self.session_dialog.repaint()
                if hasattr(self.session_dialog, 'invoice_total_label'):
                    self.session_dialog.invoice_total_label.repaint()
                if hasattr(self.session_dialog, 'elapsed_label'):
                    self.session_dialog.elapsed_label.repaint()
        except Exception as e:
            print(f"Error in force_update_session_info: {e}")

class AdminPasswordDialog(QDialog):
    """نافذة طلب كلمة مرور المدير"""
    
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("طلب إذن المدير")
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان النافذة
        title_label = QLabel("🔐 طلب إذن المدير")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # رسالة توضيحية
        message_label = QLabel("لإضافة جهاز جديد، يرجى إدخال كلمة مرور المدير:")
        message_label.setStyleSheet("font-size: 12px; color: #7f8c8d; margin-bottom: 10px;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # حقل كلمة المرور
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("كلمة المرور:"))
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("أدخل كلمة مرور المدير")
        self.password_input.returnPressed.connect(self.verify_password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.verify_btn = QPushButton("تحقق")
        self.verify_btn.setStyleSheet("background-color: #3498db; font-size: 14px; padding: 8px;")
        self.verify_btn.clicked.connect(self.verify_password)
        button_layout.addWidget(self.verify_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; font-size: 14px; padding: 8px;")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # التركيز على حقل كلمة المرور
        self.password_input.setFocus()
    
    def verify_password(self):
        """التحقق من كلمة مرور المدير"""
        password = self.password_input.text().strip()
        
        if not password:
            self.show_error("يرجى إدخال كلمة المرور")
            return
        
        # التحقق من كلمة المرور
        if self.user_model.verify_admin_password(password):
            self.accept()
        else:
            self.show_error("كلمة المرور غير صحيحة")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def get_password(self):
        """الحصول على كلمة المرور المدخلة"""
        return self.password_input.text().strip()

class AddDeviceDialog(QDialog):
    """نافذة إضافة جهاز جديد"""
    
    def __init__(self):
        super().__init__()
        self.device_model = DeviceModel()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("إضافة جهاز جديد")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #4CAF50;
                border-radius: 15px;
                background-color: white;
                selection-background-color: #4CAF50;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel("إضافة جهاز جديد")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        # اسم الجهاز
        name_label = QLabel("اسم الجهاز:")
        name_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: PS5 - 1")
        layout.addWidget(self.name_input)
        
        # نوع الجهاز
        type_label = QLabel("نوع الجهاز:")
        type_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px; margin-top: 15px;")
        layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['PS', 'PC', 'PingPong', 'Billiard'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)
        
        # سعر Single
        price_single_label = QLabel("سعر Single:")
        price_single_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px; margin-top: 15px;")
        layout.addWidget(price_single_label)
        
        self.price_single_input = QLineEdit()
        self.price_single_input.setPlaceholderText("15.00")
        self.price_single_input.setText("15.00")
        layout.addWidget(self.price_single_input)
        
        # سعر Multi
        price_multi_label = QLabel("سعر Multi:")
        price_multi_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 8px; margin-top: 15px;")
        layout.addWidget(price_multi_label)
        
        self.price_multi_input = QLineEdit()
        self.price_multi_input.setPlaceholderText("25.00")
        self.price_multi_input.setText("25.00")
        layout.addWidget(self.price_multi_input)
        
        # ملاحظة حول التسعير
        note_label = QLabel("ملاحظة: إذا تم تعيين أحد الأسعار بصفر، فسيتم إلغاء هذا النوع من التسعير لهذا الجهاز")
        note_label.setStyleSheet("color: white; font-size: 14px; background-color: rgba(255, 255, 255, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #229954);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #229954, stop: 1 #1e8449);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1e8449, stop: 1 #196f3d);
            }
        """)
        self.save_btn.clicked.connect(self.save_device)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6e);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # تعيين القيم الافتراضية حسب نوع الجهاز
        self.on_type_changed()
        
        # التركيز على حقل الاسم
        self.name_input.setFocus()
    
    def on_type_changed(self):
        """تحديث الأسعار الافتراضية حسب نوع الجهاز"""
        device_type = self.type_combo.currentText()
        
        if device_type == 'PS':
            self.price_single_input.setText("15.00")
            self.price_multi_input.setText("25.00")
        elif device_type == 'PC':
            self.price_single_input.setText("20.00")
            self.price_multi_input.setText("20.00")
        elif device_type == 'PingPong':
            self.price_single_input.setText("10.00")
            self.price_multi_input.setText("10.00")
        elif device_type == 'Billiard':
            self.price_single_input.setText("25.00")
            self.price_multi_input.setText("25.00")
    
    def save_device(self):
        """حفظ الجهاز الجديد"""
        # التحقق من صحة البيانات
        name = self.name_input.text().strip()
        device_type = self.type_combo.currentText()
        
        # التحقق من الاسم
        if not name:
            self.show_error("يرجى إدخال اسم الجهاز")
            self.name_input.setFocus()
            return
        
        # التحقق من صحة الأسعار
        try:
            price_single_text = self.price_single_input.text().strip()
            price_multi_text = self.price_multi_input.text().strip()
            
            if not price_single_text and not price_multi_text:
                self.show_error("يرجى إدخال سعر واحد على الأقل")
                return
            
            price_single = float(price_single_text) if price_single_text else 0.0
            price_multi = float(price_multi_text) if price_multi_text else 0.0
            
            if price_single < 0 or price_multi < 0:
                self.show_error("لا يمكن أن تكون الأسعار سالبة")
                return
                
            if price_single == 0 and price_multi == 0:
                self.show_error("لا يمكن أن يكون كلا السعرين صفر. يجب تحديد سعر واحد على الأقل")
                return
                
        except ValueError:
            self.show_error("يرجى إدخال أسعار صحيحة (أرقام فقط)")
            return
        
        try:
            # حفظ الجهاز في قاعدة البيانات
            device_id = self.device_model.create_device(
                name=name,
                device_type=device_type,
                price_single=price_single,
                price_multi=price_multi
            )
            
            if device_id:
                QMessageBox.information(
                    self, 
                    "نجح الحفظ", 
                    f"تم إضافة الجهاز '{name}' بنجاح!\n\n"
                    f"نوع الجهاز: {device_type}\n"
                    f"سعر Single: {price_single} جنيه\n"
                    f"سعر Multi: {price_multi} جنيه"
                )
                self.accept()
            else:
                self.show_error("فشل في حفظ الجهاز. يرجى المحاولة مرة أخرى")
                
        except Exception as e:
            self.show_error(f"حدث خطأ أثناء الحفظ: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()

class DeleteDeviceDialog(QDialog):
    """نافذة حذف جهاز"""
    
    def __init__(self):
        super().__init__()
        self.device_model = DeviceModel()
        self.user_model = UserModel()
        self.selected_device = None
        self.all_devices = []  # تخزين جميع الأجهزة للفلترة
        self.setup_ui()
        self.load_devices()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("حذف جهاز")
        self.setFixedSize(700, 600)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة الاحترافية
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
            }
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #4CAF50;
                border-radius: 15px;
                background-color: white;
                selection-background-color: #4CAF50;
                font-size: 16px;
                padding: 8px;
            }
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: rgba(255, 255, 255, 0.9);
                alternate-background-color: rgba(248, 249, 250, 0.9);
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(236, 240, 241, 0.5);
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QHeaderView::section {
                background-color: rgba(52, 73, 94, 0.9);
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QPushButton:disabled {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel("حذف جهاز")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-bottom: 20px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # رسالة توضيحية
        message_label = QLabel("اختر الجهاز الذي تريد حذفه من القائمة أدناه:")
        message_label.setStyleSheet("color: white; font-size: 16px; margin-bottom: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # فلتر الأجهزة حسب النوع
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        filter_label = QLabel("فلترة حسب النوع:")
        filter_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif;")
        filter_layout.addWidget(filter_label)
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(['جميع الأنواع', 'PS', 'PC', 'PingPong', 'Billiard'])
        self.type_filter_combo.currentTextChanged.connect(self.filter_devices)
        filter_layout.addWidget(self.type_filter_combo)
        
        # عداد الأجهزة المفلترة
        self.device_count_label = QLabel("")
        self.device_count_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif;")
        filter_layout.addWidget(self.device_count_label)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # قائمة الأجهزة
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels(["اسم الجهاز", "النوع", "سعر Single", "سعر Multi"])
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setSelectionMode(QTableWidget.SingleSelection)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.itemSelectionChanged.connect(self.on_device_selected)
        
        # تعيين عرض الأعمدة
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # اسم الجهاز
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # النوع
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # سعر Single
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # سعر Multi
        
        layout.addWidget(self.devices_table)
        
        # معلومات الجهاز المحدد
        self.device_info_label = QLabel("")
        self.device_info_label.setStyleSheet("color: white; font-size: 14px; background-color: rgba(255, 255, 255, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif;")
        self.device_info_label.setWordWrap(True)
        self.device_info_label.hide()
        layout.addWidget(self.device_info_label)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px; margin-top: 15px; font-family: 'Segoe UI', Arial, sans-serif; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.delete_btn = QPushButton("حذف الجهاز")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #a93226, stop: 1 #922b21);
            }
        """)
        self.delete_btn.clicked.connect(self.confirm_delete)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
                color: white;
                border: none;
                padding: 18px 40px;
                font-size: 12px;
                border-radius: 25px;
                font-weight: bold;
                min-height: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6e);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # ربط اختيار الصف بتحديث المعلومات
        self.devices_table.itemSelectionChanged.connect(self.on_device_selected)
    
    def load_devices(self):
        """تحميل الأجهزة في الجدول"""
        try:
            self.all_devices = self.device_model.get_all_devices()
            
            if not self.all_devices:
                self.show_error("لا توجد أجهزة في النظام")
                return
            
            # تطبيق الفلتر الحالي
            self.filter_devices()
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
        except Exception as e:
            self.show_error(f"خطأ في تحميل الأجهزة: {str(e)}")
    
    def filter_devices(self):
        """فلترة الأجهزة حسب النوع المحدد"""
        try:
            selected_type = self.type_filter_combo.currentText()
            
            # فلترة الأجهزة
            if selected_type == 'جميع الأنواع':
                filtered_devices = self.all_devices
            else:
                filtered_devices = [device for device in self.all_devices if device['type'] == selected_type]
            
            # تحديث الجدول
            self.update_devices_table(filtered_devices)
            
        except Exception as e:
            self.show_error(f"خطأ في فلترة الأجهزة: {str(e)}")
    
    def update_devices_table(self, devices):
        """تحديث جدول الأجهزة"""
        try:
            self.devices_table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                # اسم الجهاز
                name_item = QTableWidgetItem(device['name'])
                name_item.setData(Qt.UserRole, device)  # حفظ بيانات الجهاز
                self.devices_table.setItem(row, 0, name_item)
                
                # نوع الجهاز
                type_item = QTableWidgetItem(device['type'])
                self.devices_table.setItem(row, 1, type_item)
                
                # سعر Single
                price_single = device.get('price_single', 0)
                if price_single == 0:
                    price_single_text = "ملغي"
                else:
                    price_single_text = f"{price_single} جنيه"
                single_item = QTableWidgetItem(price_single_text)
                self.devices_table.setItem(row, 2, single_item)
                
                # سعر Multi
                price_multi = device.get('price_multi', 0)
                if price_multi == 0:
                    price_multi_text = "ملغي"
                else:
                    price_multi_text = f"{price_multi} جنيه"
                multi_item = QTableWidgetItem(price_multi_text)
                self.devices_table.setItem(row, 3, multi_item)
            
            # تحديث عداد الأجهزة
            selected_type = self.type_filter_combo.currentText()
            if selected_type == 'جميع الأنواع':
                self.device_count_label.setText(f"({len(devices)} جهاز)")
            else:
                self.device_count_label.setText(f"({len(devices)} جهاز من نوع {selected_type})")
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
        except Exception as e:
            self.show_error(f"خطأ في تحديث الجدول: {str(e)}")
    
    def on_device_selected(self):
        """عند اختيار جهاز من الجدول"""
        current_row = self.devices_table.currentRow()
        
        if current_row >= 0:
            # الحصول على بيانات الجهاز المحدد
            name_item = self.devices_table.item(current_row, 0)
            if name_item:
                self.selected_device = name_item.data(Qt.UserRole)
                
                # عرض معلومات الجهاز
                device = self.selected_device
                info_text = f"الجهاز المحدد: {device['name']}\n"
                info_text += f"النوع: {device['type']}\n"
                info_text += f"الحالة: {device.get('status', 'غير محدد')}\n"
                
                price_single = device.get('price_single', 0)
                price_multi = device.get('price_multi', 0)
                
                if price_single > 0:
                    info_text += f"سعر Single: {price_single} جنيه\n"
                else:
                    info_text += "سعر Single: ملغي\n"
                
                if price_multi > 0:
                    info_text += f"سعر Multi: {price_multi} جنيه"
                else:
                    info_text += "سعر Multi: ملغي"
                
                self.device_info_label.setText(info_text)
                self.device_info_label.show()
                
                # تفعيل زر الحذف
                self.delete_btn.setEnabled(True)
        else:
            self.selected_device = None
            self.device_info_label.hide()
            self.delete_btn.setEnabled(False)
    
    def confirm_delete(self):
        """تأكيد حذف الجهاز"""
        if not self.selected_device:
            self.show_error("يرجى اختيار جهاز للحذف")
            return
        
        device_name = self.selected_device['name']
        
        # طلب كلمة مرور المدير مرة أخرى للتأكيد
        password_dialog = AdminPasswordDialog()
        if password_dialog.exec() == QDialog.Accepted:
            # عرض رسالة تأكيد
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف الجهاز '{device_name}'؟\n\n"
                "⚠️ تحذير: لا يمكن التراجع عن هذه العملية!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.delete_selected_device()
    
    def delete_selected_device(self):
        """حذف الجهاز المحدد"""
        try:
            device_id = self.selected_device['id']
            device_name = self.selected_device['name']
            
            # حذف الجهاز من قاعدة البيانات
            success = self.device_model.delete_device(device_id)
            
            if success:
                QMessageBox.information(
                    self,
                    "تم الحذف بنجاح",
                    f"تم حذف الجهاز '{device_name}' بنجاح!"
                )
                self.accept()
            else:
                self.show_error("فشل في حذف الجهاز. يرجى المحاولة مرة أخرى")
                
        except Exception as e:
            self.show_error(f"حدث خطأ أثناء الحذف: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()


class EditSessionDialog(QDialog):
    """نافذة تعديل بيانات الجلسة"""
    
    def __init__(self, session_data, current_user):
        super().__init__()
        self.session_data = session_data
        self.current_user = current_user
        self.session_controller = SessionController(current_user)
        self.setup_ui()
        self.load_session_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تعديل بيانات الجلسة")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان النافذة
        title_label = QLabel("✏️ تعديل بيانات الجلسة")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # معلومات الجلسة الحالية
        info_label = QLabel("معلومات الجلسة الحالية:")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e; margin-bottom: 10px;")
        form_layout.addRow("", info_label)
        
        # اسم الجهاز (غير قابل للتعديل)
        self.device_name_label = QLabel("")
        self.device_name_label.setStyleSheet("font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 8px; border-radius: 5px;")
        form_layout.addRow("الجهاز:", self.device_name_label)
        
        # وقت بدء الجلسة (غير قابل للتعديل)
        self.start_time_label = QLabel("")
        self.start_time_label.setStyleSheet("font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 8px; border-radius: 5px;")
        form_layout.addRow("وقت البداية:", self.start_time_label)
        
        # نوع التسعيرة
        self.pricing_type_combo = QComboBox()
        self.pricing_type_combo.addItems(['single', 'multi'])
        self.pricing_type_combo.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow("نوع التسعيرة:", self.pricing_type_combo)
        
        # نوع الوقت
        self.time_type_combo = QComboBox()
        self.time_type_combo.addItems(['وقت محدد', 'وقت مفتوح'])
        self.time_type_combo.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow("نوع الوقت:", self.time_type_combo)
        
        # مدة الجلسة (للساعات المحددة)
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 480)  # من دقيقة واحدة إلى 8 ساعات
        self.duration_input.setValue(60)
        self.duration_input.setSuffix(" دقيقة")
        self.duration_input.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow("مدة الجلسة:", self.duration_input)
        
        # رقم العميل
        self.customer_phone_input = QLineEdit()
        self.customer_phone_input.setPlaceholderText("مثال: 01234567890")
        self.customer_phone_input.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow("رقم العميل:", self.customer_phone_input)
        
        # ملاحظات
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات إضافية (اختياري)")
        self.notes_input.setStyleSheet("padding: 8px; font-size: 14px;")
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px; background-color: #fadbd8; padding: 8px; border-radius: 5px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 حفظ التعديلات")
        self.save_btn.setStyleSheet("background-color: #27ae60; font-size: 14px; padding: 10px; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("❌ إلغاء")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; font-size: 14px; padding: 10px;")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_session_data(self):
        """تحميل بيانات الجلسة الحالية"""
        try:
            # معلومات الجهاز
            device_name = self.session_data.get('device_name', 'غير محدد')
            self.device_name_label.setText(device_name)
            
            # وقت البداية
            start_time = self.session_data.get('start_time', '')
            if start_time:
                if isinstance(start_time, str):
                    try:
                        from datetime import datetime
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    except:
                        pass
                if hasattr(start_time, 'strftime'):
                    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    start_time_str = str(start_time)
            else:
                start_time_str = 'غير محدد'
            self.start_time_label.setText(start_time_str)
            
            # نوع التسعيرة
            pricing_type = self.session_data.get('pricing_type', 'single')
            if pricing_type == 'single':
                self.pricing_type_combo.setCurrentIndex(0)
            else:
                self.pricing_type_combo.setCurrentIndex(1)
            
            # نوع الوقت
            time_type = self.session_data.get('time_type', 'fixed')
            if time_type == 'fixed':
                self.time_type_combo.setCurrentIndex(0)
            else:
                self.time_type_combo.setCurrentIndex(1)
            
            # مدة الجلسة
            duration = self.session_data.get('duration_minutes', 60)
            self.duration_input.setValue(duration)
            
            # رقم العميل
            customer_phone = self.session_data.get('customer_phone', '')
            self.customer_phone_input.setText(customer_phone or '')
            
            # ملاحظات
            notes = self.session_data.get('notes', '')
            self.notes_input.setText(notes or '')
            
        except Exception as e:
            self.show_error(f"خطأ في تحميل بيانات الجلسة: {str(e)}")
    
    def save_changes(self):
        """حفظ التعديلات"""
        try:
            # جمع البيانات المحدثة
            pricing_type = self.pricing_type_combo.currentText()
            time_type_text = self.time_type_combo.currentText()
            time_type = 'fixed' if time_type_text == 'وقت محدد' else 'open'
            duration_minutes = self.duration_input.value()
            customer_phone = self.customer_phone_input.text().strip() or None
            notes = self.notes_input.text().strip() or None
            
            # التحقق من صحة البيانات
            if time_type == 'fixed' and duration_minutes <= 0:
                self.show_error("يجب أن تكون مدة الجلسة أكبر من صفر")
                return
            
            # تحديث بيانات الجلسة
            result = self.session_controller.update_session_data(
                session_id=self.session_data['id'],
                pricing_type=pricing_type,
                time_type=time_type,
                duration_minutes=duration_minutes,
                customer_phone=customer_phone,
                notes=notes
            )
            
            if result['success']:
                # عرض رسالة النجاح
                QMessageBox.information(
                    self,
                    "تم التحديث بنجاح",
                    "تم تحديث بيانات الجلسة بنجاح!"
                )
                
                # إغلاق النافذة
                self.accept()
            else:
                self.show_error(result['message'])
            
        except Exception as e:
            self.show_error(f"خطأ في حفظ التعديلات: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()


class TransferSessionDialog(QDialog):
    """نافذة نقل الجلسة إلى جهاز آخر"""
    
    def __init__(self, source_device, session_data, current_user):
        super().__init__()
        self.source_device = source_device
        self.session_data = session_data
        self.current_user = current_user
        self.session_controller = SessionController(current_user)
        self.device_model = DeviceModel()
        self.setup_ui()
        self.load_available_devices()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("نقل الجلسة")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # عنوان النافذة
        title_label = QLabel("🔄 نقل الجلسة")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الجلسة الحالية
        info_group = QGroupBox("معلومات الجلسة الحالية")
        info_layout = QVBoxLayout(info_group)
        
        # الجهاز المصدر
        source_info = QLabel(f"الجهاز المصدر: {self.source_device['name']} ({self.source_device['type']})")
        source_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c; margin-bottom: 5px;")
        info_layout.addWidget(source_info)
        
        # معلومات الجلسة
        session_info = f"نوع التسعيرة: {self.session_data.get('pricing_type', 'غير محدد')} | "
        session_info += f"نوع الوقت: {self.session_data.get('time_type', 'غير محدد')} | "
        session_info += f"وقت البداية: {self.session_data.get('start_time', 'غير محدد')}"
        
        session_label = QLabel(session_info)
        session_label.setStyleSheet("font-size: 12px; color: #7f8c8d; margin-bottom: 5px;")
        session_label.setWordWrap(True)
        info_layout.addWidget(session_label)
        
        # رقم العميل
        customer_phone = self.session_data.get('customer_phone', '')
        if customer_phone:
            customer_info = QLabel(f"رقم العميل: {customer_phone}")
            customer_info.setStyleSheet("font-size: 12px; color: #27ae60; margin-bottom: 5px;")
            info_layout.addWidget(customer_info)
        
        layout.addWidget(info_group)
        
        # اختيار الجهاز الهدف
        target_group = QGroupBox("اختيار الجهاز الهدف")
        target_layout = QVBoxLayout(target_group)
        
        # رسالة توضيحية
        instruction_label = QLabel("اختر الجهاز الذي تريد نقل الجلسة إليه:")
        instruction_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e; margin-bottom: 10px;")
        target_layout.addWidget(instruction_label)
        
        # فلتر الأجهزة حسب النوع
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("فلترة حسب النوع:"))
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(['جميع الأنواع', 'PS', 'PC', 'PingPong', 'Billiard'])
        self.type_filter_combo.setStyleSheet("padding: 5px; font-size: 12px;")
        self.type_filter_combo.currentTextChanged.connect(self.filter_devices)
        filter_layout.addWidget(self.type_filter_combo)
        
        filter_layout.addStretch()
        target_layout.addLayout(filter_layout)
        
        # قائمة الأجهزة المتاحة
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels(["اسم الجهاز", "النوع", "الحالة", "السعر"])
        self.devices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.devices_table.setSelectionMode(QTableWidget.SingleSelection)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # تعيين عرض الأعمدة
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # اسم الجهاز
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # النوع
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # الحالة
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # السعر
        
        target_layout.addWidget(self.devices_table)
        
        # معلومات الجهاز المحدد
        self.device_info_label = QLabel("")
        self.device_info_label.setStyleSheet("font-size: 12px; color: #2c3e50; background-color: #ecf0f1; padding: 10px; border-radius: 5px;")
        self.device_info_label.setWordWrap(True)
        self.device_info_label.hide()
        target_layout.addWidget(self.device_info_label)
        
        layout.addWidget(target_group)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px; background-color: #fadbd8; padding: 8px; border-radius: 5px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.transfer_btn = QPushButton("🔄 نقل الجلسة")
        self.transfer_btn.setStyleSheet("background-color: #f39c12; font-size: 14px; padding: 10px; font-weight: bold;")
        self.transfer_btn.clicked.connect(self.transfer_session)
        self.transfer_btn.setEnabled(False)
        button_layout.addWidget(self.transfer_btn)
        
        self.cancel_btn = QPushButton("❌ إلغاء")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; font-size: 14px; padding: 10px;")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # ربط اختيار الصف بتحديث المعلومات
        self.devices_table.itemSelectionChanged.connect(self.on_device_selected)
    
    def load_available_devices(self):
        """تحميل الأجهزة المتاحة للنقل"""
        try:
            # الحصول على جميع الأجهزة
            all_devices = self.device_model.get_all_devices()
            
            # فلترة الأجهزة المتاحة (استبعاد الجهاز المصدر والأجهزة المشغولة)
            self.available_devices = []
            for device in all_devices:
                if (device['id'] != self.source_device['id'] and 
                    device['status'] == 'available'):
                    self.available_devices.append(device)
            
            if not self.available_devices:
                self.show_error("لا توجد أجهزة متاحة للنقل")
                return
            
            # تطبيق الفلتر الحالي
            self.filter_devices()
            
        except Exception as e:
            self.show_error(f"خطأ في تحميل الأجهزة: {str(e)}")
    
    def filter_devices(self):
        """فلترة الأجهزة حسب النوع المحدد"""
        try:
            selected_type = self.type_filter_combo.currentText()
            
            # فلترة الأجهزة
            if selected_type == 'جميع الأنواع':
                filtered_devices = self.available_devices
            else:
                filtered_devices = [device for device in self.available_devices if device['type'] == selected_type]
            
            # تحديث الجدول
            self.update_devices_table(filtered_devices)
            
        except Exception as e:
            self.show_error(f"خطأ في فلترة الأجهزة: {str(e)}")
    
    def update_devices_table(self, devices):
        """تحديث جدول الأجهزة"""
        try:
            self.devices_table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                # اسم الجهاز
                name_item = QTableWidgetItem(device['name'])
                name_item.setData(Qt.UserRole, device)  # حفظ بيانات الجهاز
                self.devices_table.setItem(row, 0, name_item)
                
                # نوع الجهاز
                type_item = QTableWidgetItem(device['type'])
                self.devices_table.setItem(row, 1, type_item)
                
                # الحالة
                status_item = QTableWidgetItem("متاح")
                status_item.setForeground(QColor(39, 174, 96))  # أخضر
                self.devices_table.setItem(row, 2, status_item)
                
                # السعر
                pricing_type = self.session_data.get('pricing_type', 'single')
                if pricing_type == 'single':
                    price = device.get('price_single', 0)
                else:
                    price = device.get('price_multi', 0)
                
                if price > 0:
                    price_text = f"{price} جنيه"
                else:
                    price_text = "غير متاح"
                
                price_item = QTableWidgetItem(price_text)
                self.devices_table.setItem(row, 3, price_item)
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
        except Exception as e:
            self.show_error(f"خطأ في تحديث الجدول: {str(e)}")
    
    def on_device_selected(self):
        """عند اختيار جهاز من الجدول"""
        current_row = self.devices_table.currentRow()
        
        if current_row >= 0:
            # الحصول على بيانات الجهاز المحدد
            name_item = self.devices_table.item(current_row, 0)
            if name_item:
                self.selected_target_device = name_item.data(Qt.UserRole)
                
                # عرض معلومات الجهاز
                device = self.selected_target_device
                info_text = f"الجهاز المحدد: {device['name']}\n"
                info_text += f"النوع: {device['type']}\n"
                info_text += f"الحالة: متاح\n"
                
                pricing_type = self.session_data.get('pricing_type', 'single')
                if pricing_type == 'single':
                    price = device.get('price_single', 0)
                    price_type = "Single"
                else:
                    price = device.get('price_multi', 0)
                    price_type = "Multi"
                
                if price > 0:
                    info_text += f"سعر {price_type}: {price} جنيه"
                else:
                    info_text += f"سعر {price_type}: غير متاح"
                
                self.device_info_label.setText(info_text)
                self.device_info_label.show()
                
                # تفعيل زر النقل
                self.transfer_btn.setEnabled(True)
        else:
            self.selected_target_device = None
            self.device_info_label.hide()
            self.transfer_btn.setEnabled(False)
    
    def transfer_session(self):
        """نقل الجلسة إلى الجهاز المحدد"""
        if not hasattr(self, 'selected_target_device') or not self.selected_target_device:
            self.show_error("يرجى اختيار جهاز هدف للنقل")
            return
        
        target_device = self.selected_target_device
        
        # التحقق من توافق نوع التسعيرة
        pricing_type = self.session_data.get('pricing_type', 'single')
        if pricing_type == 'single':
            target_price = target_device.get('price_single', 0)
        else:
            target_price = target_device.get('price_multi', 0)
        
        if target_price == 0:
            self.show_error(f"الجهاز الهدف لا يدعم تسعيرة {pricing_type}")
            return
        
        # طلب تأكيد النقل
        reply = QMessageBox.question(
            self,
            "تأكيد النقل",
            f"هل أنت متأكد من نقل الجلسة من الجهاز '{self.source_device['name']}' إلى الجهاز '{target_device['name']}'؟\n\n"
            f"⚠️ تحذير: سيتم نقل الجلسة بالكامل بما في ذلك المنتجات المضافة!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.execute_transfer(target_device)
    
    def execute_transfer(self, target_device):
        """تنفيذ عملية النقل"""
        try:
            # تنفيذ عملية النقل
            result = self.session_controller.transfer_session(
                session_id=self.session_data['id'],
                target_device_id=target_device['id']
            )
            
            if result['success']:
                # عرض رسالة النجاح
                QMessageBox.information(
                    self,
                    "تم النقل بنجاح",
                    f"تم نقل الجلسة بنجاح!\n\n"
                    f"من الجهاز: {result['session_info']['source_device']}\n"
                    f"إلى الجهاز: {result['session_info']['target_device']}\n"
                    f"السعر الجديد: {result['session_info']['new_price']} جنيه"
                )
                
                # إغلاق النافذة
                self.accept()
            else:
                self.show_error(result['message'])
            
        except Exception as e:
            self.show_error(f"خطأ في نقل الجلسة: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()




class EditDeviceDialog(QDialog):
    """نافذة تعديل بيانات الجهاز"""
    
    def __init__(self, device_data, current_user):
        super().__init__()
        self.device_data = device_data
        self.current_user = current_user
        self.device_model = DeviceModel()
        self.setup_ui()
        self.load_device_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(f"تعديل بيانات الجهاز - {self.device_data['name']}")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # عنوان
        title_label = QLabel("تعديل بيانات الجهاز")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اسم الجهاز
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم الجهاز")
        form_layout.addRow("اسم الجهاز:", self.name_edit)
        
        # نوع الجهاز
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "PS", "PC", "VR", "Xbox", "Nintendo", 
            "Arcade", "PingPong", "Billiard", "Pool", "Foosball"
        ])
        form_layout.addRow("نوع الجهاز:", self.type_combo)
        
        # السعر الفردي
        self.price_single_spin = QDoubleSpinBox()
        self.price_single_spin.setRange(0, 1000)
        self.price_single_spin.setSuffix(" جنيه/ساعة")
        self.price_single_spin.setDecimals(2)
        form_layout.addRow("السعر الفردي:", self.price_single_spin)
        
        # السعر الجماعي
        self.price_multi_spin = QDoubleSpinBox()
        self.price_multi_spin.setRange(0, 1000)
        self.price_multi_spin.setSuffix(" جنيه/ساعة")
        self.price_multi_spin.setDecimals(2)
        form_layout.addRow("السعر الجماعي:", self.price_multi_spin)
        
        # حالة الجهاز
        self.status_combo = QComboBox()
        self.status_combo.addItems(["available", "maintenance", "disabled"])
        form_layout.addRow("حالة الجهاز:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        # أزرار
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ التعديلات")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-size: 14px;")
        save_btn.clicked.connect(self.save_changes)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def load_device_data(self):
        """تحميل بيانات الجهاز الحالية"""
        try:
            # الحصول على بيانات الجهاز من قاعدة البيانات
            device = self.device_model.get_device_by_id(self.device_data['id'])
            if device:
                self.name_edit.setText(device.get('name', ''))
                self.type_combo.setCurrentText(device.get('type', 'PS'))
                self.price_single_spin.setValue(device.get('price_single', 0))
                self.price_multi_spin.setValue(device.get('price_multi', 0))
                self.status_combo.setCurrentText(device.get('status', 'available'))
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل بيانات الجهاز: {str(e)}")
    
    def save_changes(self):
        """حفظ التعديلات"""
        try:
            # التحقق من صحة البيانات
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "تحذير", "يجب إدخال اسم الجهاز")
                return
            
            # جمع البيانات
            updated_data = {
                'name': name,
                'type': self.type_combo.currentText(),
                'price_single': self.price_single_spin.value(),
                'price_multi': self.price_multi_spin.value(),
                'status': self.status_combo.currentText()
            }
            
            # تحديث الجهاز في قاعدة البيانات
            success = self.device_model.update_device(self.device_data['id'], **updated_data)
            
            if success:
                # تحديث البيانات المحلية
                self.device_data.update(updated_data)
                QMessageBox.information(self, "نجح", "تم حفظ التعديلات بنجاح!")
                self.accept()
            else:
                QMessageBox.warning(self, "خطأ", "فشل في حفظ التعديلات - تحقق من البيانات المدخلة")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ التعديلات: {str(e)}")


class ChangePricingTypeDialog(QDialog):
    """نافذة حوار لتغيير نوع التسعيرة"""
    
    def __init__(self, device_data, session_data):
        super().__init__()
        self.device_data = device_data
        self.session_data = session_data
        self.selected_pricing_type = None
        self.setup_ui()
        self.load_current_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تغيير نوع التسعيرة")
        self.setModal(True)
        self.resize(450, 350)
        
        # التخطيط الرئيسي
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # العنوان
        title_label = QLabel("💰 تغيير نوع التسعيرة")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الجهاز والجلسة
        info_group = QGroupBox("معلومات الجلسة الحالية")
        info_layout = QFormLayout(info_group)
        
        self.device_label = QLabel()
        self.device_label.setStyleSheet("font-weight: bold; color: #34495e;")
        info_layout.addRow("الجهاز:", self.device_label)
        
        self.current_pricing_label = QLabel()
        self.current_pricing_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        info_layout.addRow("نوع التسعيرة الحالي:", self.current_pricing_label)
        
        self.current_price_label = QLabel()
        self.current_price_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        info_layout.addRow("السعر الحالي:", self.current_price_label)
        
        layout.addWidget(info_group)
        
        # اختيار نوع التسعيرة الجديد
        pricing_group = QGroupBox("اختر نوع التسعيرة الجديد")
        pricing_layout = QVBoxLayout(pricing_group)
        
        # زر التسعيرة الفردية
        self.single_radio = QPushButton("👤 تسعيرة فردية")
        self.single_radio.setCheckable(True)
        self.single_radio.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #2980b9;
                border: 2px solid #2c3e50;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.single_radio.clicked.connect(self.on_single_selected)
        pricing_layout.addWidget(self.single_radio)
        
        # زر التسعيرة الجماعية
        self.multi_radio = QPushButton("👥 تسعيرة جماعية")
        self.multi_radio.setCheckable(True)
        self.multi_radio.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #d35400;
                border: 2px solid #2c3e50;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
        """)
        self.multi_radio.clicked.connect(self.on_multi_selected)
        pricing_layout.addWidget(self.multi_radio)
        
        layout.addWidget(pricing_group)
        
        # معلومات السعر الجديد
        self.new_price_label = QLabel()
        self.new_price_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e74c3c;
            padding: 10px;
            background-color: #fdf2e9;
            border-radius: 5px;
            border: 1px solid #e67e22;
        """)
        self.new_price_label.setAlignment(Qt.AlignCenter)
        self.new_price_label.hide()
        layout.addWidget(self.new_price_label)
        
        # ملخص التسعيرة الحالية
        self.pricing_summary_label = QLabel()
        self.pricing_summary_label.setStyleSheet("""
            font-size: 12px;
            color: #34495e;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 5px;
            border: 1px solid #bdc3c7;
        """)
        self.pricing_summary_label.setWordWrap(True)
        self.pricing_summary_label.hide()
        layout.addWidget(self.pricing_summary_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
        
        # أزرار
        button_layout = QHBoxLayout()
        
        change_btn = QPushButton("✅ تغيير نوع التسعيرة")
        change_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 12px; font-size: 14px; font-weight: bold; border-radius: 5px;")
        change_btn.clicked.connect(self.accept_change)
        change_btn.setEnabled(False)
        self.change_btn = change_btn
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 12px; font-size: 14px; font-weight: bold; border-radius: 5px;")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(change_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def load_current_data(self):
        """تحميل البيانات الحالية"""
        try:
            # معلومات الجهاز
            self.device_label.setText(f"{self.device_data.get('name', 'جهاز')} ({self.device_data.get('type', 'PS')})")
            
            # نوع التسعيرة الحالي
            current_type = self.session_data.get('pricing_type', 'single')
            if current_type == 'single':
                self.current_pricing_label.setText("👤 فردية")
            else:
                self.current_pricing_label.setText("👥 جماعية")
            
            # السعر الحالي
            current_price = self.session_data.get('session_price', 0)
            self.current_price_label.setText(f"{current_price:.2f} جنيه/ساعة")
            
            # تعطيل الخيار الحالي
            if current_type == 'single':
                self.single_radio.setEnabled(False)
                self.single_radio.setText("👤 تسعيرة فردية (الحالية)")
                self.single_radio.setStyleSheet("""
                    QPushButton {
                        background-color: #95a5a6;
                        color: white;
                        border: none;
                        padding: 15px;
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 8px;
                        text-align: left;
                    }
                """)
            else:
                self.multi_radio.setEnabled(False)
                self.multi_radio.setText("👥 تسعيرة جماعية (الحالية)")
                self.multi_radio.setStyleSheet("""
                    QPushButton {
                        background-color: #95a5a6;
                        color: white;
                        border: none;
                        padding: 15px;
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 8px;
                        text-align: left;
                    }
                """)
            
            # تحميل ملخص التسعيرة الحالية
            self.load_pricing_summary()
                
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل البيانات: {str(e)}")
    
    def load_pricing_summary(self):
        """تحميل ملخص التسعيرة الحالية"""
        try:
            from models.pricing_segment_model import PricingSegmentModel
            
            pricing_model = PricingSegmentModel()
            pricing_summary = pricing_model.get_session_pricing_summary(self.session_data['id'])
            
            if pricing_summary and (pricing_summary.get('total_single_cost', 0) > 0 or pricing_summary.get('total_multi_cost', 0) > 0):
                summary_text = "📊 ملخص التسعيرة الحالية:\n"
                
                if pricing_summary.get('total_single_cost', 0) > 0:
                    summary_text += f"👤 فردي: {pricing_summary['total_single_hours']:.2f} ساعة = {pricing_summary['total_single_cost']:.2f} جنيه\n"
                
                if pricing_summary.get('total_multi_cost', 0) > 0:
                    summary_text += f"👥 جماعي: {pricing_summary['total_multi_hours']:.2f} ساعة = {pricing_summary['total_multi_cost']:.2f} جنيه\n"
                
                summary_text += f"💰 المجموع: {pricing_summary['total_cost']:.2f} جنيه"
                
                self.pricing_summary_label.setText(summary_text)
                self.pricing_summary_label.show()
            else:
                self.pricing_summary_label.hide()
                
        except Exception as e:
            logger.error(f"خطأ في تحميل ملخص التسعيرة: {e}")
            self.pricing_summary_label.hide()
    
    def on_single_selected(self):
        """عند اختيار التسعيرة الفردية"""
        self.multi_radio.setChecked(False)
        self.selected_pricing_type = 'single'
        self.update_new_price_display()
        self.change_btn.setEnabled(True)
    
    def on_multi_selected(self):
        """عند اختيار التسعيرة الجماعية"""
        self.single_radio.setChecked(False)
        self.selected_pricing_type = 'multi'
        self.update_new_price_display()
        self.change_btn.setEnabled(True)
    
    def update_new_price_display(self):
        """تحديث عرض السعر الجديد"""
        try:
            if self.selected_pricing_type == 'single':
                new_price = self.device_data.get('price_single', 0)
                self.new_price_label.setText(f"السعر الجديد: {new_price:.2f} جنيه/ساعة (فردي)")
            elif self.selected_pricing_type == 'multi':
                new_price = self.device_data.get('price_multi', 0)
                self.new_price_label.setText(f"السعر الجديد: {new_price:.2f} جنيه/ساعة (جماعي)")
            
            self.new_price_label.show()
        except Exception as e:
            self.new_price_label.hide()
    
    def get_selected_pricing_type(self):
        """الحصول على نوع التسعيرة المختار"""
        return self.selected_pricing_type
    
    def accept_change(self):
        """قبول التغيير"""
        if self.selected_pricing_type:
            self.accept()
        else:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار نوع التسعيرة الجديد")
