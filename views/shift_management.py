"""
واجهة إدارة الورديات الجديدة
New Shift Management Interface
"""

import sys
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ShiftCard(QFrame):
    """كارت الوردية"""
    
    # إشارات
    shift_clicked = Signal(dict)  # بيانات الوردية
    
    def __init__(self, shift_data):
        super().__init__()
        self.shift_data = shift_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(300, 200)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border-radius: 10px;
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        # التخطيط الرئيسي
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # عنوان الوردية
        self.title_label = QLabel("وردية")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # اسم الكاشير
        self.cashier_label = QLabel("")
        self.cashier_label.setAlignment(Qt.AlignCenter)
        self.cashier_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.cashier_label)
        
        # وقت البداية
        self.start_time_label = QLabel("")
        self.start_time_label.setAlignment(Qt.AlignCenter)
        self.start_time_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.start_time_label)
        
        # وقت النهاية أو المدة
        self.end_time_label = QLabel("")
        self.end_time_label.setAlignment(Qt.AlignCenter)
        self.end_time_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.end_time_label)
        
        # حالة الوردية
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
    
    def update_display(self):
        """تحديث عرض الكارت"""
        cashier_name = self.shift_data.get('cashier_name', 'غير محدد')
        start_time = self.shift_data.get('start_time')
        end_time = self.shift_data.get('end_time')
        status = self.shift_data.get('status', 'active')
        
        # تحديث اسم الكاشير
        self.cashier_label.setText(f"الكاشير: {cashier_name}")
        
        # تحديث وقت البداية
        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            self.start_time_label.setText(f"البداية: {start_time.strftime('%H:%M')}")
        
        # تحديث وقت النهاية أو المدة
        if end_time:
            # وردية منتهية
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            self.end_time_label.setText(f"النهاية: {end_time.strftime('%H:%M')}")
            
            # حساب المدة
            duration = end_time - start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            self.status_label.setText(f"مدة: {hours}س {minutes}د")
            
            # لون الوردية المنتهية
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
        else:
            # وردية نشطة
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                
                # حساب المدة الحالية
                duration = datetime.now() - start_time
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                self.end_time_label.setText(f"المدة الحالية: {hours}س {minutes}د")
            
            self.status_label.setText("نشطة")
            
            # لون الوردية النشطة
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
    
    def mousePressEvent(self, event):
        """معالج الضغط على الكارت"""
        if event.button() == Qt.LeftButton:
            self.shift_clicked.emit(self.shift_data)

class ShiftManagementWindow(QMainWindow):
    """نافذة إدارة الورديات الجديدة"""
    
    # إشارات
    shift_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.shift_cards = {}
        self.setup_ui()
        self.setup_connections()
        self.load_shifts()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة الورديات - نظام إدارة محل بلايستيشن")
        self.setMinimumSize(1200, 800)
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
        
        # منطقة الورديات
        self.create_shifts_area(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("⏰ إدارة الورديات")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # أزرار التحكم
        self.start_shift_btn = QPushButton("بدء وردية")
        self.start_shift_btn.setStyleSheet("background-color: #27ae60;")
        self.start_shift_btn.clicked.connect(self.start_shift)
        toolbar_layout.addWidget(self.start_shift_btn)
        
        self.end_shift_btn = QPushButton("إنهاء وردية")
        self.end_shift_btn.setStyleSheet("background-color: #e74c3c;")
        self.end_shift_btn.clicked.connect(self.end_shift)
        toolbar_layout.addWidget(self.end_shift_btn)
        
        self.refresh_btn = QPushButton("تحديث")
        self.refresh_btn.setStyleSheet("background-color: #f39c12;")
        self.refresh_btn.clicked.connect(self.load_shifts)
        toolbar_layout.addWidget(self.refresh_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_shifts_area(self, parent_layout):
        """إنشاء منطقة الورديات"""
        # مجموعة الورديات
        shifts_group = QGroupBox("الورديات")
        shifts_layout = QVBoxLayout(shifts_group)
        
        # منطقة التمرير للورديات
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # الـ widget المحتوي للورديات
        self.shifts_widget = QWidget()
        self.shifts_layout = QGridLayout(self.shifts_widget)
        self.shifts_layout.setSpacing(15)
        
        scroll_area.setWidget(self.shifts_widget)
        shifts_layout.addWidget(scroll_area)
        
        parent_layout.addWidget(shifts_group)
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات الورديات")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات الورديات
        self.total_shifts_label = QLabel("إجمالي الورديات: 0")
        self.total_shifts_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_shifts_label)
        
        self.active_shifts_label = QLabel("نشطة: 0")
        self.active_shifts_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.active_shifts_label)
        
        self.completed_shifts_label = QLabel("منتهية: 0")
        self.completed_shifts_label.setStyleSheet("font-size: 14px; color: #95a5a6; font-weight: bold;")
        stats_layout.addWidget(self.completed_shifts_label)
        
        self.today_shifts_label = QLabel("اليوم: 0")
        self.today_shifts_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.today_shifts_label)
        
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
    
    def load_shifts(self):
        """تحميل الورديات"""
        try:
            # مسح الورديات الموجودة
            for i in reversed(range(self.shifts_layout.count())):
                self.shifts_layout.itemAt(i).widget().setParent(None)
            
            self.shift_cards.clear()
            
            # تحميل الورديات من قاعدة البيانات
            from models.shift_model import ShiftModel
            shift_model = ShiftModel()
            
            # الحصول على ورديات اليوم
            shifts = shift_model.get_today_shifts()
            
            # إذا لم توجد ورديات، استخدم بيانات تجريبية
            if not shifts:
                shifts = [
                    {
                        'id': 1,
                        'cashier_id': 1,
                        'cashier_name': 'أحمد محمد',
                        'start_time': datetime.now() - timedelta(hours=2),
                        'end_time': None,
                        'status': 'active',
                        'notes': 'وردية صباحية'
                    },
                    {
                        'id': 2,
                        'cashier_id': 2,
                        'cashier_name': 'فاطمة علي',
                        'start_time': datetime.now() - timedelta(hours=6),
                        'end_time': datetime.now() - timedelta(hours=1),
                        'status': 'completed',
                        'notes': 'وردية ليلية'
                    }
                ]
            
            # إنشاء كروت الورديات
            row = 0
            col = 0
            max_cols = 3
            
            for shift in shifts:
                card = ShiftCard(shift)
                card.shift_clicked.connect(self.on_shift_clicked)
                self.shift_cards[shift['id']] = card
                
                self.shifts_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # تحديث الإحصائيات
            self.update_stats(shifts)
            
        except Exception as e:
            print(f"خطأ في تحميل الورديات: {e}")
    
    def update_stats(self, shifts):
        """تحديث الإحصائيات"""
        total = len(shifts)
        active = len([s for s in shifts if s['status'] == 'active'])
        completed = len([s for s in shifts if s['status'] == 'completed'])
        
        # ورديات اليوم
        today = datetime.now().date()
        today_shifts = len([s for s in shifts if 
                           (s['start_time'].date() == today if isinstance(s['start_time'], datetime) 
                           else datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')).date() == today)])
        
        self.total_shifts_label.setText(f"إجمالي الورديات: {total}")
        self.active_shifts_label.setText(f"نشطة: {active}")
        self.completed_shifts_label.setText(f"منتهية: {completed}")
        self.today_shifts_label.setText(f"اليوم: {today_shifts}")
    
    def on_shift_clicked(self, shift_data):
        """معالج النقر على الوردية"""
        print(f"تم النقر على الوردية: {shift_data['id']}")
        self.shift_selected.emit(shift_data)
        
        # عرض نافذة تفاصيل الوردية
        self.show_shift_details(shift_data)
    
    def show_shift_details(self, shift_data):
        """عرض نافذة تفاصيل الوردية"""
        dialog = ShiftDetailsDialog(shift_data, self.current_user)
        dialog.exec()
    
    def start_shift(self):
        """بدء وردية جديدة"""
        # التحقق من الصلاحيات
        from utils.permissions import check_permission, Permission
        if not check_permission(self.current_user.get('role', ''), Permission.SHIFT_ADD):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "خطأ في الصلاحيات", "ليس لديك صلاحية لبدء وردية جديدة")
            return
        
        dialog = StartShiftDialog(self.current_user)
        if dialog.exec() == QDialog.Accepted:
            # بدء الوردية الجديدة
            try:
                from controllers.shift_controller import ShiftController
                shift_controller = ShiftController()
                
                cashier_id = dialog.get_cashier_id()
                notes = dialog.get_notes()
                
                result = shift_controller.start_shift(
                    cashier_id=cashier_id,
                    shift_name=f"وردية {datetime.now().strftime('%Y-%m-%d')}",
                    notes=notes
                )
                
                if result['success']:
                    from utils.notifications import show_success
                    show_success("تم بدء الوردية", result['message'])
                    self.load_shifts()
                else:
                    from utils.notifications import show_error
                    show_error("خطأ في بدء الوردية", result['message'])
                    
            except Exception as e:
                logger.error(f"خطأ في بدء الوردية: {e}")
                from utils.notifications import show_error
                show_error("خطأ في بدء الوردية", str(e))
    
    def end_shift(self):
        """إنهاء وردية"""
        # التحقق من الصلاحيات
        from utils.permissions import check_permission, Permission
        if not check_permission(self.current_user.get('role', ''), Permission.SHIFT_EDIT):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "خطأ في الصلاحيات", "ليس لديك صلاحية لإنهاء وردية")
            return
        
        # البحث عن وردية نشطة للكاشير الحالي
        active_shift = None
        for shift_data in self.shift_cards.values():
            if (shift_data.shift_data.get('cashier_id') == self.current_user.get('id') and 
                shift_data.shift_data.get('status') == 'active'):
                active_shift = shift_data.shift_data
                break
        
        if not active_shift:
            QMessageBox.warning(self, "تحذير", "لا توجد وردية نشطة للكاشير الحالي")
            return
        
        dialog = EndShiftDialog(active_shift, self.current_user)
        if dialog.exec() == QDialog.Accepted:
            # إنهاء الوردية
            try:
                from controllers.shift_controller import ShiftController
                shift_controller = ShiftController()
                
                notes = dialog.get_notes()
                
                result = shift_controller.end_shift(
                    shift_id=active_shift['id'],
                    notes=notes
                )
                
                if result['success']:
                    from utils.notifications import show_success
                    show_success("تم إنهاء الوردية", result['message'])
                    self.load_shifts()
                else:
                    from utils.notifications import show_error
                    show_error("خطأ في إنهاء الوردية", result['message'])
                    
            except Exception as e:
                logger.error(f"خطأ في إنهاء الوردية: {e}")
                from utils.notifications import show_error
                show_error("خطأ في إنهاء الوردية", str(e))
    
    def start_timer(self):
        """بدء التايمر لتحديث الورديات"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_shifts_status)
        self.timer.start(60000)  # كل دقيقة
    
    def update_shifts_status(self):
        """تحديث حالة الورديات"""
        for card in self.shift_cards.values():
            card.update_display()

class StartShiftDialog(QDialog):
    """نافذة بدء وردية جديدة"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("بدء وردية جديدة")
        self.setFixedSize(550, 650)
        self.setModal(True)
        
        # إعداد الخلفية المتدرجة
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 2px solid rgba(255, 255, 255, 0.6);
                background-color: rgba(255, 255, 255, 0.95);
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QTextEdit:hover {
                border: 2px solid rgba(255, 255, 255, 0.6);
                background-color: rgba(255, 255, 255, 0.95);
            }
            QTextEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("⏰ بدء وردية جديدة")
        title_label.setStyleSheet("""
            color: white;
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 25px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # اختيار الكاشير (للمدير فقط)
        from utils.permissions import check_permission, Permission
        if check_permission(self.current_user.get('role', ''), Permission.ADMIN_OVERRIDE):
            cashier_label = QLabel("👤 اختر الكاشير:")
            cashier_label.setStyleSheet("""
                color: white;
                font-size: 18px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 10px;
            """)
            layout.addWidget(cashier_label)
            
            self.cashier_combo = QComboBox()
            self.cashier_combo.setPlaceholderText("اختر الكاشير...")
            self.cashier_combo.setMinimumHeight(45)
            self.load_cashiers()
            layout.addWidget(self.cashier_combo)
        else:
            # للكاشير العادي، استخدام المستخدم الحالي
            cashier_frame = QFrame()
            cashier_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.15);
                    border-radius: 15px;
                    padding: 15px;
                }
            """)
            cashier_layout = QVBoxLayout(cashier_frame)
            cashier_layout.setContentsMargins(15, 10, 15, 10)
            
            cashier_title = QLabel("👤 الكاشير")
            cashier_title.setStyleSheet("""
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 5px;
            """)
            cashier_layout.addWidget(cashier_title)
            
            cashier_label = QLabel(self.current_user.get('username', 'غير محدد'))
            cashier_label.setStyleSheet("""
                color: white;
                font-size: 16px;
                font-weight: bold;
            """)
            cashier_label.setAlignment(Qt.AlignCenter)
            cashier_layout.addWidget(cashier_label)
            layout.addWidget(cashier_frame)
            self.cashier_combo = None
        
        # وقت البداية
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        time_layout = QVBoxLayout(time_frame)
        time_layout.setContentsMargins(15, 10, 15, 10)
        
        time_title = QLabel("🕐 وقت البداية")
        time_title.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
        """)
        time_layout.addWidget(time_title)
        
        start_time_label = QLabel(datetime.now().strftime('%Y-%m-%d %H:%M'))
        start_time_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        start_time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(start_time_label)
        layout.addWidget(time_frame)
        
        # ملاحظات
        notes_label = QLabel("📝 ملاحظات (اختياري)")
        notes_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 10px;
        """)
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(120)
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات حول الوردية...")
        layout.addWidget(self.notes_input)
        
        # رسالة خطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ff6b6b;
            font-size: 14px;
            background-color: rgba(255, 107, 107, 0.2);
            padding: 15px;
            border-radius: 15px;
            margin-top: 10px;
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        start_btn = QPushButton("✅ بدء الوردية")
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: #1e8449;
            }
        """)
        start_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(start_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 20px;
                padding: 12px 25px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: #6c7b7d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # تحديد التركيز الأولي
        if self.cashier_combo:
            self.cashier_combo.setFocus()
        else:
            self.notes_input.setFocus()
    
    def load_cashiers(self):
        """تحميل قائمة الكاشيرات"""
        try:
            from models.user_model import UserModel
            user_model = UserModel()
            cashiers = user_model.get_cashiers()
            
            self.cashier_combo.clear()
            for cashier in cashiers:
                if cashier.get('enabled', True):  # فقط الكاشيرات النشطة
                    display_name = f"{cashier.get('username', '')} - {cashier.get('full_name', '')}"
                    self.cashier_combo.addItem(display_name, cashier['id'])
            
            # تحديد الكاشير الحالي إذا كان في القائمة
            current_user_id = self.current_user.get('id')
            for i in range(self.cashier_combo.count()):
                if self.cashier_combo.itemData(i) == current_user_id:
                    self.cashier_combo.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            logger.error(f"خطأ في تحميل الكاشيرات: {e}")
    
    def get_cashier_id(self):
        """الحصول على معرف الكاشير المختار"""
        if self.cashier_combo:
            return self.cashier_combo.currentData()
        else:
            return self.current_user.get('id')
    
    def validate_and_accept(self):
        """التحقق من صحة البيانات وقبول النافذة"""
        # التحقق من اختيار الكاشير (للمدير فقط)
        if self.cashier_combo and self.cashier_combo.currentIndex() == -1:
            self.show_error("يرجى اختيار الكاشير")
            return
        
        self.accept()
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def get_notes(self):
        """الحصول على الملاحظات"""
        return self.notes_input.toPlainText().strip()

class EndShiftDialog(QDialog):
    """نافذة إنهاء وردية"""
    
    def __init__(self, shift_data, current_user):
        super().__init__()
        self.shift_data = shift_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إنهاء وردية")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("إنهاء وردية")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الوردية
        shift_info = QLabel(f"الوردية رقم: {self.shift_data['id']}")
        shift_info.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(shift_info)
        
        # وقت البداية
        start_time = self.shift_data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        start_time_label = QLabel(f"وقت البداية: {start_time.strftime('%Y-%m-%d %H:%M')}")
        start_time_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(start_time_label)
        
        # المدة الحالية
        duration = datetime.now() - start_time
        hours = int(duration.total_seconds() / 3600)
        minutes = int((duration.total_seconds() % 3600) / 60)
        duration_label = QLabel(f"المدة الحالية: {hours}س {minutes}د")
        duration_label.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(duration_label)
        
        # ملاحظات النهاية
        notes_label = QLabel("ملاحظات إنهاء الوردية (اختياري):")
        notes_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات حول إنهاء الوردية...")
        layout.addWidget(self.notes_input)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_notes(self):
        """الحصول على الملاحظات"""
        return self.notes_input.toPlainText().strip()

class ShiftDetailsDialog(QDialog):
    """نافذة تفاصيل الوردية"""
    
    def __init__(self, shift_data, current_user):
        super().__init__()
        self.shift_data = shift_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(f"تفاصيل الوردية رقم {self.shift_data['id']}")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل الوردية رقم {self.shift_data['id']}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات التفاصيل
        tab_widget = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_info_tab = QWidget()
        basic_layout = QFormLayout(basic_info_tab)
        
        # معلومات الوردية
        basic_layout.addRow("رقم الوردية:", QLabel(str(self.shift_data['id'])))
        basic_layout.addRow("الكاشير:", QLabel(self.shift_data.get('cashier_name', 'غير محدد')))
        
        start_time = self.shift_data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        basic_layout.addRow("وقت البداية:", QLabel(start_time.strftime('%Y-%m-%d %H:%M')))
        
        end_time = self.shift_data.get('end_time')
        if end_time:
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            basic_layout.addRow("وقت النهاية:", QLabel(end_time.strftime('%Y-%m-%d %H:%M')))
            
            # حساب المدة
            duration = end_time - start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            basic_layout.addRow("المدة:", QLabel(f"{hours}س {minutes}د"))
        else:
            basic_layout.addRow("وقت النهاية:", QLabel("لم تنته بعد"))
            
            # المدة الحالية
            duration = datetime.now() - start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            basic_layout.addRow("المدة الحالية:", QLabel(f"{hours}س {minutes}د"))
        
        basic_layout.addRow("الملاحظات:", QLabel(self.shift_data.get('notes', 'لا توجد ملاحظات')))
        
        tab_widget.addTab(basic_info_tab, "المعلومات الأساسية")
        
        # تبويب الإحصائيات
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_label = QLabel("إحصائيات الوردية - قيد التطوير")
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        stats_layout.addWidget(stats_label)
        
        tab_widget.addTab(stats_tab, "الإحصائيات")
        
        layout.addWidget(tab_widget)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
