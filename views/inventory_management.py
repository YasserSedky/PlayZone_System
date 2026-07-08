"""
واجهة إدارة المخزون
Inventory Management Interface
"""

import sys
import os
from datetime import datetime
from decimal import Decimal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDialogButtonBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QTimeEdit,
    QSplitter, QTabWidget, QProgressBar, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QDate, QTime
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.product_model import ProductModel
from utils.notifications import show_success, show_error

class ProductCard(QFrame):
    """كارت المنتج"""
    
    # إشارات
    product_clicked = Signal(dict)  # بيانات المنتج
    
    def __init__(self, product_data):
        super().__init__()
        self.product_data = product_data
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """إعداد واجهة الكارت"""
        self.setFixedSize(260, 190)  # حجم أصغر قليلاً
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
        
        # عنوان المنتج
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # الفئة
        self.category_label = QLabel("")
        self.category_label.setAlignment(Qt.AlignCenter)
        self.category_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.category_label)
        
        # السعر
        self.price_label = QLabel("")
        self.price_label.setAlignment(Qt.AlignCenter)
        self.price_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.price_label)
        
        # المخزون
        self.stock_label = QLabel("")
        self.stock_label.setAlignment(Qt.AlignCenter)
        self.stock_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.stock_label)
        
        # حالة المخزون
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # إضافة مساحة مرنة
        layout.addStretch()
    
    def update_display(self):
        """تحديث عرض الكارت"""
        # تحديث اسم المنتج
        name = self.product_data.get('name', 'غير محدد')
        self.title_label.setText(f"📦 {name}")
        
        # تحديث الفئة
        category = self.product_data.get('category', 'غير محدد')
        self.category_label.setText(f"الفئة: {category}")
        
        # تحديث السعر
        price = float(self.product_data.get('price', 0))
        self.price_label.setText(f"💰 {price} جنيه")
        
        # تحديث المخزون
        stock = int(self.product_data.get('stock_quantity', 0))
        self.stock_label.setText(f"📊 {stock} قطعة")
        
        # تحديث حالة المخزون واللون
        if stock == 0:
            self.status_label.setText("نفد المخزون!")
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
        elif stock <= 10:
            self.status_label.setText("مخزون منخفض!")
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
        elif stock <= 50:
            self.status_label.setText("مخزون متوسط")
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
        else:
            self.status_label.setText("مخزون جيد")
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
            self.product_clicked.emit(self.product_data)

class InventoryManagementWindow(QMainWindow):
    """نافذة إدارة المخزون"""
    
    # إشارات
    product_selected = Signal(dict)
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.product_cards = {}
        self.product_model = ProductModel()
        self.selected_product = None  # المنتج المحدد للحذف
        self.setup_ui()
        self.setup_connections()
        self.load_products()
        self.start_timer()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("إدارة المخزون - نظام إدارة محل بلايستيشن")
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
        
        # منطقة البحث والفلترة
        self.create_search_area(main_layout)
        
        # منطقة المنتجات
        self.create_products_area(main_layout)
        
        # إحصائيات سريعة
        self.create_stats_area(main_layout)
    
    def create_toolbar(self, parent_layout):
        """إنشاء شريط الأدوات"""
        toolbar_layout = QHBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("📦 إدارة المخزون")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # أزرار التحكم
        self.add_product_btn = QPushButton("إضافة منتج")
        self.add_product_btn.setStyleSheet("background-color: #27ae60;")
        self.add_product_btn.clicked.connect(self.add_product)
        toolbar_layout.addWidget(self.add_product_btn)
        
        self.delete_product_btn = QPushButton("حذف منتج")
        self.delete_product_btn.setStyleSheet("background-color: #e74c3c;")
        self.delete_product_btn.clicked.connect(self.delete_selected_product)
        self.delete_product_btn.setEnabled(False)  # معطل حتى يتم اختيار منتج
        toolbar_layout.addWidget(self.delete_product_btn)
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setStyleSheet("background-color: #3498db;")
        self.refresh_btn.clicked.connect(self.refresh_products)  # ⭐ استخدام دالة refresh_products بدلاً من load_products
        toolbar_layout.addWidget(self.refresh_btn)
        
        parent_layout.addLayout(toolbar_layout)
    
    def create_search_area(self, parent_layout):
        """إنشاء منطقة البحث والفلترة"""
        search_group = QGroupBox("البحث والفلترة")
        search_layout = QHBoxLayout(search_group)
        
        # حقل البحث
        search_layout.addWidget(QLabel("البحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالاسم أو الفئة...")
        self.search_input.textChanged.connect(self.search_products)
        search_layout.addWidget(self.search_input)
        
        # فلتر الفئة
        search_layout.addWidget(QLabel("الفئة:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["جميع الفئات", "مشروبات", "طعام"])
        self.category_filter.currentTextChanged.connect(self.filter_products)
        search_layout.addWidget(self.category_filter)
        
        # فلتر المخزون
        search_layout.addWidget(QLabel("المخزون:"))
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["جميع المنتجات", "نفد المخزون", "مخزون منخفض", "مخزون جيد"])
        self.stock_filter.currentTextChanged.connect(self.filter_products)
        search_layout.addWidget(self.stock_filter)
        
        parent_layout.addWidget(search_group)
    
    def create_products_area(self, parent_layout):
        """إنشاء منطقة المنتجات"""
        # مجموعة المنتجات
        products_group = QGroupBox("المنتجات")
        products_layout = QVBoxLayout(products_group)
        
        # منطقة التمرير للمنتجات
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # الـ widget المحتوي للمنتجات
        self.products_widget = QWidget()
        self.products_layout = QGridLayout(self.products_widget)
        self.products_layout.setSpacing(15)
        self.products_layout.setContentsMargins(15, 15, 15, 15)  # هوامش مناسبة
        self.products_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # بدء من أعلى الصفحة
        
        scroll_area.setWidget(self.products_widget)
        products_layout.addWidget(scroll_area)
        
        parent_layout.addWidget(products_group)
    
    def create_stats_area(self, parent_layout):
        """إنشاء منطقة الإحصائيات"""
        stats_group = QGroupBox("إحصائيات المخزون")
        stats_layout = QHBoxLayout(stats_group)
        
        # إحصائيات المخزون
        self.total_products_label = QLabel("إجمالي المنتجات: 0")
        self.total_products_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_products_label)
        
        self.out_of_stock_label = QLabel("نفد المخزون: 0")
        self.out_of_stock_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.out_of_stock_label)
        
        self.low_stock_label = QLabel("مخزون منخفض: 0")
        self.low_stock_label.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(self.low_stock_label)
        
        self.good_stock_label = QLabel("مخزون جيد: 0")
        self.good_stock_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.good_stock_label)
        
        self.total_value_label = QLabel("إجمالي القيمة: 0 جنيه")
        self.total_value_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
        stats_layout.addWidget(self.total_value_label)
        
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
    
    def refresh_products(self):
        """⭐ تحديث المنتجات مع رسالة تأكيد"""
        try:
            # إعادة تحميل المنتجات
            self.load_products()
            
            # عرض رسالة نجاح
            from utils.notifications import show_success
            show_success("✅ تم تحديث قائمة المنتجات بنجاح")
            
        except Exception as e:
            from utils.notifications import show_error
            show_error(f"خطأ في تحديث المنتجات: {str(e)}")
    
    def load_products(self):
        """تحميل المنتجات"""
        try:
            # مسح المنتجات الموجودة
            for i in reversed(range(self.products_layout.count())):
                self.products_layout.itemAt(i).widget().setParent(None)
            
            self.product_cards.clear()
            
            # تحميل المنتجات من قاعدة البيانات
            products = self.product_model.get_all_products()
            
            # إضافة رسالة ترحيب إذا لم تكن موجودة
            if len(products) == 0:
                if not hasattr(self, 'welcome_label'):
                    self.welcome_label = QLabel("مرحباً بك في قسم المخزون!\n\nلا توجد منتجات في الوقت الحالي.\nيمكنك إضافة منتجات جديدة باستخدام زر 'إضافة منتج'.")
                    self.welcome_label.setStyleSheet("""
                        font-size: 18px;
                        color: #7f8c8d;
                        font-weight: bold;
                        padding: 40px;
                        text-align: center;
                        background-color: #ecf0f1;
                        border: 2px dashed #bdc3c7;
                        border-radius: 10px;
                    """)
                    self.welcome_label.setAlignment(Qt.AlignCenter)
                    self.welcome_label.setMinimumHeight(200)
                    self.products_layout.addWidget(self.welcome_label, 0, 0, 1, 5)  # يمتد على 5 أعمدة
                else:
                    self.welcome_label.setVisible(True)
            
            # إنشاء كروت المنتجات
            row = 1 if len(products) > 0 else 0  # البدء من الصف الثاني إذا كان هناك منتجات
            col = 0
            max_cols = 5
            
            for product in products:
                card = ProductCard(product)
                card.product_clicked.connect(self.on_product_clicked)
                self.product_cards[product['id']] = card
                
                self.products_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # تحديث الإحصائيات
            self.update_stats(products)
            
            # إعادة تعيين المنتج المحدد
            self.selected_product = None
            self.delete_product_btn.setEnabled(False)
            
        except Exception as e:
            print(f"Error loading products: {e}")
    
    def update_stats(self, products):
        """تحديث الإحصائيات"""
        total = len(products)
        out_of_stock = len([p for p in products if p['stock_quantity'] == 0])
        low_stock = len([p for p in products if 0 < p['stock_quantity'] <= 10])
        good_stock = len([p for p in products if p['stock_quantity'] > 10])
        total_value = sum(float(p['price']) * p['stock_quantity'] for p in products)
        
        self.total_products_label.setText(f"إجمالي المنتجات: {total}")
        self.out_of_stock_label.setText(f"نفد المخزون: {out_of_stock}")
        self.low_stock_label.setText(f"مخزون منخفض: {low_stock}")
        self.good_stock_label.setText(f"مخزون جيد: {good_stock}")
        self.total_value_label.setText(f"إجمالي القيمة: {total_value} جنيه")
    
    def on_product_clicked(self, product_data):
        """معالج النقر على المنتج"""
        print(f"تم النقر على المنتج: {product_data['name']}")
        self.product_selected.emit(product_data)
        
        # تحديد المنتج المحدد
        self.selected_product = product_data
        
        # تفعيل زر الحذف
        self.delete_product_btn.setEnabled(True)
        
        # عرض نافذة تفاصيل المنتج
        self.show_product_details(product_data)
    
    def show_product_details(self, product_data):
        """عرض نافذة تفاصيل المنتج"""
        dialog = ProductDetailsDialog(product_data, self.current_user)
        dialog.product_deleted.connect(self.load_products)  # ربط الإشارة لتحديث قائمة المنتجات عند الحذف
        dialog.product_updated.connect(self.load_products)  # ⭐ إعادة تحميل المنتجات بعد التحديث (طريقة أبسط وأكثر موثوقية)
        dialog.exec()
    
    def update_product_card(self, updated_product_data):
        """⭐ تحديث كارت منتج معين بالبيانات الجديدة"""
        try:
            product_id = updated_product_data.get('id')
            
            # التحقق من وجود الكارت
            if product_id in self.product_cards:
                # تحديث بيانات الكارت
                card = self.product_cards[product_id]
                card.product_data.update(updated_product_data)
                
                # تحديث عرض الكارت فوراً
                card.update_display()
                
                # تحديث الإحصائيات
                products = [card.product_data for card in self.product_cards.values()]
                self.update_stats(products)
                
                # إجبار التخطيط على التحديث الفوري
                card.update()
                card.repaint()
                self.update()
                self.repaint()
                
                # إجبار معالجة الأحداث
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                
                print(f"✅ تم تحديث الكارت للمنتج: {updated_product_data.get('name')}")
            else:
                print(f"⚠️ الكارت غير موجود للمنتج ID: {product_id}")
                
        except Exception as e:
            print(f"❌ خطأ في تحديث الكارت: {e}")
            import traceback
            traceback.print_exc()
    
    def add_product(self):
        """إضافة منتج جديد"""
        try:
            # التحقق من الصلاحية
            from utils.permission_checker import permission_checker
            
            # إذا كان المستخدم لديه صلاحية إضافة منتج، لا نطلب كلمة مرور المدير
            if permission_checker.check_permission_or_admin(self.current_user, "add_product"):
                # فتح نافذة إضافة المنتج مباشرة
                dialog = AddProductDialog()
                if dialog.exec() == QDialog.Accepted:
                    product_data = dialog.get_product_data()
                
                # التحقق من صحة البيانات
                if not self.validate_product_data(product_data):
                    return
                
                try:
                    # إضافة المنتج إلى قاعدة البيانات
                    from decimal import Decimal
                    product_id = self.product_model.create_product(
                        name=product_data['name'],
                        price=Decimal(str(product_data['price'])),
                        stock_quantity=product_data['stock_quantity'],
                        category=product_data['category']
                    )
                    
                    if product_id:
                        show_success("تم إضافة المنتج بنجاح")
                        
                        # تحديث الواجهة فوراً
                        self.load_products()
                        
                        # إجبار التخطيط على التحديث
                        self.update()
                        self.products_widget.update()
                        self.products_layout.update()
                        
                        # إجبار معالجة الأحداث
                        from PySide6.QtWidgets import QApplication
                        QApplication.processEvents()
                    else:
                        show_error("فشل في إضافة المنتج")
                        
                except Exception as e:
                    show_error(f"خطأ في إضافة المنتج: {str(e)}")
            else:
                # طلب كلمة مرور المدير
                from PySide6.QtWidgets import QInputDialog, QLineEdit
                password, ok = QInputDialog.getText(
                    self,
                    "تأكيد الإضافة",
                    "إضافة المنتج تتطلب كلمة مرور المدير:\n\nأدخل كلمة مرور المدير:",
                    QLineEdit.Password
                )
                
                if not ok:
                    return  # المستخدم ألغى العملية
                
                if not password:
                    show_error("كلمة المرور مطلوبة")
                    return
                
                # التحقق من كلمة مرور المدير
                from models.user_model import UserModel
                user_model = UserModel()
                
                # البحث عن مدير في النظام
                admin_user = user_model.get_admin_user()
                if not admin_user:
                    show_error("لا يوجد مدير في النظام")
                    return
                
                # التحقق من كلمة المرور
                from utils.security import verify_password
                if not verify_password(password, admin_user['password_hash']):
                    show_error("كلمة المرور غير صحيحة")
                    return
                
                # فتح نافذة إضافة المنتج
                dialog = AddProductDialog()
                if dialog.exec() == QDialog.Accepted:
                    product_data = dialog.get_product_data()
                    
                    # التحقق من صحة البيانات
                    if not self.validate_product_data(product_data):
                        return
                    
                    try:
                        # إضافة المنتج إلى قاعدة البيانات
                        from decimal import Decimal
                        product_id = self.product_model.create_product(
                            name=product_data['name'],
                            price=Decimal(str(product_data['price'])),
                            stock_quantity=product_data['stock_quantity'],
                            category=product_data['category']
                        )
                        
                        if product_id:
                            show_success("تم إضافة المنتج بنجاح")
                            
                            # تحديث الواجهة فوراً
                            self.load_products()
                            
                            # إجبار التخطيط على التحديث
                            self.update()
                            self.products_widget.update()
                            self.products_layout.update()
                            
                            # إجبار معالجة الأحداث
                            from PySide6.QtWidgets import QApplication
                            QApplication.processEvents()
                        else:
                            show_error("فشل في إضافة المنتج")
                            
                    except Exception as e:
                        show_error(f"خطأ في إضافة المنتج: {str(e)}")
                    
        except Exception as e:
            show_error(f"خطأ في التحقق من كلمة المرور: {str(e)}")
    
    def delete_selected_product(self):
        """حذف المنتج المحدد"""
        try:
            if not self.selected_product:
                show_error("يرجى اختيار منتج للحذف أولاً")
                return
            
            product_name = self.selected_product.get('name', 'غير محدد')
            product_id = self.selected_product.get('id')
            
            # طلب كلمة مرور المدير
            from PySide6.QtWidgets import QInputDialog, QLineEdit
            password, ok = QInputDialog.getText(
                self,
                "تأكيد الحذف",
                f"حذف المنتج '{product_name}' يتطلب كلمة مرور المدير:\n\nأدخل كلمة مرور المدير:",
                QLineEdit.Password
            )
            
            if not ok:
                return  # المستخدم ألغى العملية
            
            if not password:
                show_error("كلمة المرور مطلوبة")
                return
            
            # التحقق من كلمة مرور المدير
            from models.user_model import UserModel
            user_model = UserModel()
            
            # البحث عن مدير في النظام
            admin_user = user_model.get_admin_user()
            if not admin_user:
                show_error("لا يوجد مدير في النظام")
                return
            
            # التحقق من كلمة المرور
            from utils.security import verify_password
            if not verify_password(password, admin_user['password_hash']):
                show_error("كلمة المرور غير صحيحة")
                return
            
            # تأكيد الحذف
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف المنتج '{product_name}'؟\n\n"
                "⚠️ تحذير: هذا الإجراء لا يمكن التراجع عنه!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # حذف المنتج
                success = self.product_model.delete_product(product_id, password)
                
                if success:
                    show_success(f"تم حذف المنتج '{product_name}' بنجاح")
                    
                    # إعادة تعيين المنتج المحدد
                    self.selected_product = None
                    self.delete_product_btn.setEnabled(False)
                    
                    # تحديث قائمة المنتجات
                    self.load_products()
                else:
                    show_error("فشل في حذف المنتج")
                    
        except Exception as e:
            show_error(f"خطأ في حذف المنتج: {str(e)}")
    
    def validate_product_data(self, product_data):
        """التحقق من صحة بيانات المنتج"""
        if not product_data['name'].strip():
            show_error("اسم المنتج مطلوب")
            return False
        
        if product_data['price'] <= 0:
            show_error("السعر يجب أن يكون أكبر من صفر")
            return False
        
        if product_data['stock_quantity'] < 0:
            show_error("الكمية يجب أن تكون أكبر من أو تساوي صفر")
            return False
        
        if not product_data['category']:
            show_error("الفئة مطلوبة")
            return False
        
        return True
    
    def search_products(self):
        """البحث في المنتجات"""
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_products()
            return
        
        # فلترة المنتجات حسب البحث
        filtered_products = []
        for card in self.product_cards.values():
            product_data = card.product_data
            if (search_term.lower() in product_data['name'].lower() or 
                search_term.lower() in product_data['category'].lower()):
                filtered_products.append(product_data)
        
        # عرض المنتجات المفلترة
        self.display_filtered_products(filtered_products)
    
    def filter_products(self):
        """فلترة المنتجات"""
        category_filter = self.category_filter.currentText()
        stock_filter = self.stock_filter.currentText()
        
        if category_filter == "جميع الفئات" and stock_filter == "جميع المنتجات":
            self.load_products()
            return
        
        # فلترة المنتجات
        filtered_products = []
        for card in self.product_cards.values():
            product_data = card.product_data
            stock = product_data['stock_quantity']
            category = product_data['category']
            
            # فلتر الفئة
            category_match = (category_filter == "جميع الفئات" or 
                            (category_filter == "مشروبات" and category == "drink") or
                            (category_filter == "طعام" and category == "food"))
            
            # فلتر المخزون
            stock_match = (stock_filter == "جميع المنتجات" or
                          (stock_filter == "نفد المخزون" and stock == 0) or
                          (stock_filter == "مخزون منخفض" and 0 < stock <= 10) or
                          (stock_filter == "مخزون جيد" and stock > 10))
            
            if category_match and stock_match:
                filtered_products.append(product_data)
        
        # عرض المنتجات المفلترة
        self.display_filtered_products(filtered_products)
    
    def display_filtered_products(self, products):
        """عرض المنتجات المفلترة"""
        # مسح المنتجات الموجودة
        for i in reversed(range(self.products_layout.count())):
            self.products_layout.itemAt(i).widget().setParent(None)
        
        # عرض المنتجات المفلترة
        row = 0
        col = 0
        max_cols = 5
        
        for product in products:
            card = ProductCard(product)
            card.product_clicked.connect(self.on_product_clicked)
            
            self.products_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # تحديث الإحصائيات
        self.update_stats(products)
    
    def start_timer(self):
        """بدء التايمر لتحديث المنتجات"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_products_status)
        self.timer.start(30000)  # كل 30 ثانية
    
    def update_products_status(self):
        """تحديث حالة المنتجات"""
        for card in self.product_cards.values():
            card.update_display()

class ProductDetailsDialog(QDialog):
    """نافذة تفاصيل المنتج"""
    
    # إشارات
    product_deleted = Signal()
    product_updated = Signal(dict)  # ⭐ إشارة جديدة لإرسال البيانات المحدثة
    
    def __init__(self, product_data, current_user):
        super().__init__()
        self.product_data = product_data
        self.current_user = current_user
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle(f"تفاصيل المنتج - {self.product_data['name']}")
        self.setFixedSize(600, 500)
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
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #21618c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #21618c, stop: 1 #1b4f72);
            }
            QPushButton#edit_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
            }
            QPushButton#edit_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #21618c);
            }
            QPushButton#delete_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
            }
            QPushButton#delete_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a93226);
            }
            QPushButton#close_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
            }
            QPushButton#close_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel(f"تفاصيل المنتج - {self.product_data['name']}")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # إنشاء إطار للمعلومات
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)
        
        # معلومات المنتج
        product_info = [
            self.product_data.get('name', 'غير محدد'),
            self.product_data.get('category', 'غير محدد'),
            f"{self.product_data.get('price', 0)} جنيه",
            f"{self.product_data.get('stock_quantity', 0)} قطعة"
        ]
        
        # حساب قيمة المخزون
        stock_value = float(self.product_data.get('price', 0)) * self.product_data.get('stock_quantity', 0)
        product_info.append(f"{stock_value} جنيه")
        
        for value_text in product_info:
            # القيمة فقط بدون تسمية
            value_label = QLabel(value_text)
            value_label.setStyleSheet("""
                color: #333;
                font-size: 14px;
                background-color: rgba(102, 126, 234, 0.1);
                padding: 8px 12px;
                border-radius: 10px;
                min-height: 20px;
                margin-bottom: 10px;
            """)
            info_layout.addWidget(value_label)
        
        layout.addWidget(info_frame)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # زر تعديل المنتج وتحديث المخزون
        edit_btn = QPushButton("تعديل المنتج وتحديث المخزون")
        edit_btn.setObjectName("edit_btn")
        edit_btn.clicked.connect(self.edit_product)
        button_layout.addWidget(edit_btn)
        
        if self.current_user.get('role') == 'admin':
            # المدير يمكنه حذف المنتج
            delete_btn = QPushButton("حذف المنتج")
            delete_btn.setObjectName("delete_btn")
            delete_btn.clicked.connect(self.delete_product)
            button_layout.addWidget(delete_btn)
        
        # زر إغلاق
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def delete_product(self):
        """حذف المنتج (يتطلب كلمة مرور المدير)"""
        try:
            # طلب كلمة مرور المدير
            from PySide6.QtWidgets import QInputDialog, QLineEdit
            password, ok = QInputDialog.getText(
                self,
                "تأكيد الحذف",
                f"حذف المنتج '{self.product_data['name']}' يتطلب كلمة مرور المدير:\n\nأدخل كلمة مرور المدير:",
                QLineEdit.Password
            )
            
            if not ok:
                return  # المستخدم ألغى العملية
            
            if not password:
                from utils.notifications import show_error
                show_error("كلمة المرور مطلوبة")
                return
            
            # التحقق من كلمة مرور المدير
            from models.user_model import UserModel
            user_model = UserModel()
            
            # البحث عن مدير في النظام
            admin_user = user_model.get_admin_user()
            if not admin_user:
                from utils.notifications import show_error
                show_error("لا يوجد مدير في النظام")
                return
            
            # التحقق من كلمة المرور
            from utils.security import verify_password
            if not verify_password(password, admin_user['password_hash']):
                from utils.notifications import show_error
                show_error("كلمة المرور غير صحيحة")
                return
            
            # تأكيد الحذف
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف المنتج '{self.product_data['name']}'؟\n\nهذا الإجراء لا يمكن التراجع عنه!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # حذف المنتج
                from models.product_model import ProductModel
                product_model = ProductModel()
                
                success = product_model.delete_product(self.product_data['id'], password)
                
                if success:
                    from utils.notifications import show_success
                    show_success(f"تم حذف المنتج '{self.product_data['name']}' بنجاح")
                    
                    # إرسال إشارة لتحديث قائمة المنتجات في النافذة الرئيسية
                    self.product_deleted.emit()
                    
                    # إغلاق النافذة
                    self.accept()
                else:
                    from utils.notifications import show_error
                    show_error("فشل في حذف المنتج")
                    
        except Exception as e:
            from utils.notifications import show_error
            show_error(f"خطأ في حذف المنتج: {str(e)}")
    
    def edit_product(self):
        """تعديل المنتج"""
        try:
            # التحقق من الصلاحية
            from utils.permission_checker import permission_checker
            
            # إذا كان المستخدم لديه صلاحية تعديل منتج، لا نطلب كلمة مرور المدير
            if permission_checker.check_permission_or_admin(self.current_user, "edit_product"):
                # فتح نافذة تعديل المنتج مباشرة
                dialog = EditProductDialog(self.product_data)
                if dialog.exec() == QDialog.Accepted:
                    updated_data = dialog.get_product_data()
                    
                    # التحقق من صحة البيانات (استخدام validate_product_data الموجودة)
                    if not updated_data.get('name') or not updated_data.get('name').strip():
                        from utils.notifications import show_error
                        show_error("اسم المنتج مطلوب")
                        return
                    
                    if updated_data.get('price', 0) <= 0:
                        from utils.notifications import show_error
                        show_error("السعر يجب أن يكون أكبر من صفر")
                        return
                    
                    # تحديث المنتج في قاعدة البيانات
                    from models.product_model import ProductModel
                    product_model = ProductModel()
                    
                    # ⭐ تحديث البيانات الأساسية فقط (بدون المخزون)
                    success = product_model.update_product(
                        product_id=self.product_data['id'],
                        name=updated_data['name'],
                        price=updated_data['price'],
                        stock_quantity=None,  # ⭐ لا نحدث المخزون هنا
                        category=updated_data['category']
                    )
                    
                    if success:
                        # ⭐ التحقق من وجود تحديث للمخزون من التبويب الثاني
                        stock_data = dialog.get_stock_update_data()
                        stock_success = True  # افتراض النجاح إذا لم يكن هناك تحديث للمخزون
                        
                        if stock_data['quantity'] > 0:
                            # ⭐ تطبيق عملية تحديث المخزون (إضافة/خصم/تعيين)
                            # في حالة "تعيين"، نستخدم new_stock مباشرة
                            quantity_to_use = stock_data['new_stock'] if stock_data['operation'] == "تعيين" else stock_data['quantity']
                            
                            stock_success = product_model.update_stock_with_password(
                                product_id=self.product_data['id'],
                                quantity_change=quantity_to_use,
                                operation=stock_data['operation'],
                                admin_password=None  # لا نحتاج كلمة مرور لأن لدينا الصلاحية
                            )
                        
                        if stock_success:
                            from utils.notifications import show_success
                            show_success("تم تحديث المنتج بنجاح")
                            
                            # تحديث البيانات المحلية
                            self.product_data.update(updated_data)
                            
                            # ⭐ إذا تم تحديث المخزون، نحدث المخزون في البيانات المحلية
                            if stock_data['quantity'] > 0:
                                self.product_data['stock_quantity'] = stock_data['new_stock']
                            
                            # ⭐ إرسال إشارة مع البيانات المحدثة لتحديث الكارت مباشرة
                            self.product_updated.emit(self.product_data)
                            
                            # إغلاق النافذة
                            self.accept()
                        else:
                            from utils.notifications import show_error
                            show_error("تم تحديث بيانات المنتج لكن فشل في تحديث المخزون")
                    else:
                        from utils.notifications import show_error
                        show_error("فشل في تحديث المنتج")
            else:
                # طلب كلمة مرور المدير
                from PySide6.QtWidgets import QInputDialog, QLineEdit
                password, ok = QInputDialog.getText(
                    self,
                    "تأكيد التعديل",
                    f"تعديل المنتج '{self.product_data['name']}' يتطلب كلمة مرور المدير:\n\nأدخل كلمة مرور المدير:",
                    QLineEdit.Password
                )
                
                if not ok:
                    return  # المستخدم ألغى العملية
                
                if not password:
                    from utils.notifications import show_error
                    show_error("كلمة المرور مطلوبة")
                    return
                
                # التحقق من كلمة مرور المدير
                from models.user_model import UserModel
                user_model = UserModel()
                
                # البحث عن مدير في النظام
                admin_user = user_model.get_admin_user()
                if not admin_user:
                    from utils.notifications import show_error
                    show_error("لا يوجد مدير في النظام")
                    return
            
            # التحقق من كلمة المرور
            from utils.security import verify_password
            if not verify_password(password, admin_user['password_hash']):
                from utils.notifications import show_error
                show_error("كلمة المرور غير صحيحة")
                return
            
            # فتح نافذة تعديل المنتج وتحديث المخزون
            dialog = EditProductDialog(self.product_data)
            if dialog.exec() == QDialog.Accepted:
                # الحصول على بيانات المنتج
                product_data = dialog.get_product_data()
                
                # التحقق من صحة البيانات
                if not self.validate_product_data(product_data):
                    return
                
                try:
                    from decimal import Decimal
                    from models.product_model import ProductModel
                    product_model = ProductModel()
                    
                    # تحديث بيانات المنتج الأساسية
                    success = product_model.update_product(
                        product_id=self.product_data['id'],
                        name=product_data['name'],
                        price=Decimal(str(product_data['price'])),
                        category=product_data['category'],
                        stock_quantity=None,  # لا نحدث المخزون هنا
                        admin_password=password
                    )
                    
                    if success:
                        # التحقق من وجود تحديث للمخزون
                        stock_data = dialog.get_stock_update_data()
                        stock_success = True  # افتراض النجاح إذا لم يكن هناك تحديث للمخزون
                        
                        if stock_data['quantity'] > 0:
                            # ⭐ تطبيق عملية تحديث المخزون (إضافة/خصم/تعيين)
                            # في حالة "تعيين"، نستخدم new_stock مباشرة
                            quantity_to_use = stock_data['new_stock'] if stock_data['operation'] == "تعيين" else stock_data['quantity']
                            
                            stock_success = product_model.update_stock_with_password(
                                product_id=self.product_data['id'],
                                quantity_change=quantity_to_use,
                                operation=stock_data['operation'],
                                admin_password=password
                            )
                        
                        if stock_success:
                            # تحديث بيانات المنتج المحلية
                            self.product_data.update(product_data)
                            
                            # إذا تم تحديث المخزون، نحدث المخزون في البيانات المحلية
                            if stock_data['quantity'] > 0:
                                self.product_data['stock_quantity'] = stock_data['new_stock']
                            
                            from utils.notifications import show_success
                            show_success(f"تم تحديث المنتج '{product_data['name']}' بنجاح")
                            
                            # ⭐ إرسال إشارة مع البيانات المحدثة لتحديث الكارت مباشرة
                            self.product_updated.emit(self.product_data)
                            
                            # إغلاق النافذة
                            self.accept()
                        else:
                            from utils.notifications import show_error
                            show_error("تم تحديث بيانات المنتج لكن فشل في تحديث المخزون")
                    else:
                        from utils.notifications import show_error
                        show_error("فشل في تحديث المنتج")
                        
                except Exception as e:
                    from utils.notifications import show_error
                    show_error(f"خطأ في تحديث المنتج: {str(e)}")
                    
        except Exception as e:
            from utils.notifications import show_error
            show_error(f"خطأ في التحقق من كلمة المرور: {str(e)}")
    
    def validate_product_data(self, product_data):
        """التحقق من صحة بيانات المنتج"""
        if not product_data['name'].strip():
            from utils.notifications import show_error
            show_error("اسم المنتج مطلوب")
            return False
        
        if product_data['price'] <= 0:
            from utils.notifications import show_error
            show_error("السعر يجب أن يكون أكبر من صفر")
            return False
        
        if not product_data['category']:
            from utils.notifications import show_error
            show_error("الفئة مطلوبة")
            return False
        
        return True

class AddProductDialog(QDialog):
    """نافذة إضافة منتج جديد"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle("إضافة منتج جديد")
        self.setFixedSize(500, 650)
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
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QPushButton#cancel_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
            }
            QPushButton#cancel_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
            }
            QPushButton#cancel_btn:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6d);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # عنوان النافذة
        title_label = QLabel("إضافة منتج جديد")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # اسم المنتج
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المنتج")
        self.name_input.setMinimumHeight(45)
        layout.addWidget(self.name_input)
        
        # الفئة
        self.category_combo = QComboBox()
        self.category_combo.addItems(["drink", "food"])
        self.category_combo.setMinimumHeight(45)
        layout.addWidget(self.category_combo)
        
        # السعر
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("السعر (جنيه)")
        self.price_input.setText("5")
        self.price_input.setMinimumHeight(45)
        layout.addWidget(self.price_input)
        
        # المخزون الأولي
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("المخزون الأولي")
        self.stock_input.setText("50")
        self.stock_input.setMinimumHeight(45)
        layout.addWidget(self.stock_input)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("إضافة المنتج")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # تعيين التركيز على حقل اسم المنتج
        self.name_input.setFocus()
    
    def validate_and_accept(self):
        """التحقق من صحة البيانات وقبول النافذة"""
        try:
            # التحقق من اسم المنتج
            name = self.name_input.text().strip()
            if not name:
                self.show_error("يرجى إدخال اسم المنتج")
                return
            
            # التحقق من السعر
            try:
                price_text = self.price_input.text().strip()
                if not price_text:
                    self.show_error("يرجى إدخال سعر المنتج")
                    return
                
                price = float(price_text)
                if price <= 0:
                    self.show_error("السعر يجب أن يكون أكبر من صفر")
                    return
                    
                if price > 1000:
                    self.show_error("السعر لا يمكن أن يكون أكبر من 1000 جنيه")
                    return
                    
            except ValueError:
                self.show_error("يرجى إدخال سعر صحيح")
                return
            
            # التحقق من المخزون
            try:
                stock_text = self.stock_input.text().strip()
                if not stock_text:
                    self.show_error("يرجى إدخال المخزون الأولي")
                    return
                
                stock = int(stock_text)
                if stock < 0:
                    self.show_error("المخزون لا يمكن أن يكون سالب")
                    return
                    
                if stock > 10000:
                    self.show_error("المخزون لا يمكن أن يكون أكبر من 10000 قطعة")
                    return
                    
            except ValueError:
                self.show_error("يرجى إدخال مخزون صحيح")
                return
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
            # قبول النافذة
            self.accept()
            
        except Exception as e:
            self.show_error(f"خطأ في التحقق من البيانات: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
        self.error_label.setStyleSheet("""
            color: #ff6b6b; 
            font-size: 14px; 
            background-color: rgba(255, 107, 107, 0.2); 
            padding: 15px; 
            border-radius: 15px;
            border: 2px solid rgba(255, 107, 107, 0.3);
        """)
    
    def get_product_data(self):
        """الحصول على بيانات المنتج"""
        try:
            price = float(self.price_input.text().strip()) if self.price_input.text().strip() else 0.0
        except ValueError:
            price = 0.0
            
        try:
            stock = int(self.stock_input.text().strip()) if self.stock_input.text().strip() else 0
        except ValueError:
            stock = 0
            
        return {
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'price': price,
            'stock_quantity': stock
        }

class EditProductDialog(QDialog):
    """نافذة تعديل منتج"""
    
    def __init__(self, product_data):
        super().__init__()
        self.product_data = product_data
        self.setup_ui()
        self.load_product_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الحديثة"""
        self.setWindowTitle(f"تعديل المنتج - {self.product_data['name']}")
        self.setFixedSize(600, 700)
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
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
            QSpinBox {
                padding: 15px 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 25px;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QSpinBox:focus {
                border-color: #4CAF50;
                background-color: rgba(255, 255, 255, 1.0);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: none;
                width: 0px;
            }
            QTabWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                padding: 10px;
            }
            QTabWidget::pane {
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #333;
                padding: 12px 20px;
                margin-right: 5px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #667eea, stop: 1 #764ba2);
                color: white;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e3f2fd, stop: 1 #bbdefb);
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 20px;
                font-weight: bold;
                min-height: 25px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
            QPushButton#cancel_btn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #95a5a6, stop: 1 #7f8c8d);
            }
            QPushButton#cancel_btn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #7f8c8d, stop: 1 #6c7b7d);
            }
            QPushButton#cancel_btn:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6c7b7d, stop: 1 #5d6d6d);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # عنوان النافذة
        title_label = QLabel("تعديل المنتج وتحديث المخزون")
        title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-bottom: 25px; font-family: 'Segoe UI', Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # إنشاء التبويبات
        self.tab_widget = QTabWidget()
        
        # تبويب تعديل البيانات الأساسية
        self.basic_tab = QWidget()
        self.setup_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "البيانات الأساسية")
        
        # تبويب تحديث المخزون
        self.stock_tab = QWidget()
        self.setup_stock_tab()
        self.tab_widget.addTab(self.stock_tab, "تحديث المخزون")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # زر حفظ التغييرات
        self.save_btn = QPushButton("حفظ التغييرات")
        self.save_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.save_btn)
        
        # زر إلغاء
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # رسالة الخطأ
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; background-color: rgba(255, 107, 107, 0.2); padding: 15px; border-radius: 15px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def validate_and_accept(self):
        """التحقق من صحة البيانات وقبول النافذة"""
        try:
            # التحقق من اسم المنتج
            name = self.name_input.text().strip()
            if not name:
                self.show_error("يرجى إدخال اسم المنتج")
                return
            
            # التحقق من السعر
            try:
                price_text = self.price_input.text().strip()
                if not price_text:
                    self.show_error("يرجى إدخال سعر المنتج")
                    return
                
                price = float(price_text)
                if price <= 0:
                    self.show_error("السعر يجب أن يكون أكبر من صفر")
                    return
                    
                if price > 1000:
                    self.show_error("السعر لا يمكن أن يكون أكبر من 1000 جنيه")
                    return
                    
            except ValueError:
                self.show_error("يرجى إدخال سعر صحيح")
                return
            
            # إخفاء رسالة الخطأ إذا كانت موجودة
            self.error_label.hide()
            
            # قبول النافذة
            self.accept()
            
        except Exception as e:
            self.show_error(f"خطأ في التحقق من البيانات: {str(e)}")
    
    def show_error(self, message):
        """عرض رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
        self.error_label.setStyleSheet("""
            color: #ff6b6b; 
            font-size: 14px; 
            background-color: rgba(255, 107, 107, 0.2); 
            padding: 15px; 
            border-radius: 15px;
            border: 2px solid rgba(255, 107, 107, 0.3);
        """)
    
    def setup_basic_tab(self):
        """إعداد تبويب البيانات الأساسية"""
        layout = QVBoxLayout(self.basic_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # اسم المنتج
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المنتج")
        self.name_input.setMinimumHeight(45)
        layout.addWidget(self.name_input)
        
        # الفئة
        self.category_combo = QComboBox()
        self.category_combo.addItems(["drink", "food"])
        self.category_combo.setMinimumHeight(45)
        layout.addWidget(self.category_combo)
        
        # السعر
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("السعر (جنيه)")
        self.price_input.setMinimumHeight(45)
        layout.addWidget(self.price_input)
        
        # المخزون الحالي (للعرض فقط)
        self.current_stock_label = QLabel()
        self.current_stock_label.setStyleSheet("""
            color: #667eea;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(102, 126, 234, 0.1);
            padding: 15px 20px;
            border-radius: 25px;
            margin-top: 10px;
            margin-bottom: 10px;
            min-height: 25px;
            border: 2px solid rgba(102, 126, 234, 0.3);
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        self.current_stock_label.setMinimumHeight(45)
        layout.addWidget(self.current_stock_label)
        
        layout.addStretch()
    
    def setup_stock_tab(self):
        """إعداد تبويب تحديث المخزون"""
        layout = QVBoxLayout(self.stock_tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # المخزون الحالي
        self.current_stock_display = QLabel()
        self.current_stock_display.setStyleSheet("""
            color: #667eea;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(102, 126, 234, 0.1);
            padding: 15px 20px;
            border-radius: 25px;
            margin-top: 10px;
            margin-bottom: 10px;
            min-height: 25px;
            border: 2px solid rgba(102, 126, 234, 0.3);
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        self.current_stock_display.setMinimumHeight(45)
        layout.addWidget(self.current_stock_display)
        
        # نوع التحديث
        self.update_type_combo = QComboBox()
        self.update_type_combo.addItems(["إضافة", "خصم", "تعيين"])
        self.update_type_combo.setMinimumHeight(45)
        layout.addWidget(self.update_type_combo)
        
        # الكمية
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(10)
        self.quantity_input.setMinimumHeight(45)
        layout.addWidget(self.quantity_input)
        
        # المخزون الجديد (للعرض)
        self.new_stock_label = QLabel("0")
        self.new_stock_label.setStyleSheet("""
            color: #27ae60;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(39, 174, 96, 0.1);
            padding: 15px 20px;
            border-radius: 25px;
            margin-top: 10px;
            margin-bottom: 10px;
            min-height: 25px;
            border: 2px solid rgba(39, 174, 96, 0.3);
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        self.new_stock_label.setMinimumHeight(45)
        layout.addWidget(self.new_stock_label)
        
        # ربط تغيير القيم لحساب المخزون الجديد
        self.update_type_combo.currentTextChanged.connect(self.calculate_new_stock)
        self.quantity_input.valueChanged.connect(self.calculate_new_stock)
        
        layout.addStretch()
    
    def load_product_data(self):
        """تحميل بيانات المنتج الحالي"""
        self.name_input.setText(self.product_data.get('name', ''))
        self.price_input.setText(str(self.product_data.get('price', 0)))
        
        # تحديد الفئة
        category = self.product_data.get('category', 'drink')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        # تحديث عرض المخزون الحالي
        current_stock = int(self.product_data.get('stock_quantity', 0))
        self.current_stock_label.setText(f"المخزون الحالي: {current_stock} قطعة")
        self.current_stock_display.setText(f"المخزون الحالي: {current_stock} قطعة")
        
        # حساب المخزون الجديد
        self.calculate_new_stock()
    
    def calculate_new_stock(self):
        """حساب المخزون الجديد بناءً على نوع التحديث والكمية"""
        try:
            current_stock = int(self.product_data.get('stock_quantity', 0))
            quantity = self.quantity_input.value()
            operation = self.update_type_combo.currentText()
            
            if operation == "إضافة":
                new_stock = current_stock + quantity
            elif operation == "خصم":
                new_stock = max(0, current_stock - quantity)
            else:  # تعيين
                new_stock = quantity
            
            self.new_stock_label.setText(f"المخزون الجديد: {new_stock} قطعة")
            
            # تغيير لون النص حسب نوع العملية
            if operation == "إضافة":
                self.new_stock_label.setStyleSheet("""
                    color: #27ae60;
                    font-size: 18px;
                    font-weight: bold;
                    background-color: rgba(39, 174, 96, 0.1);
                    padding: 15px 20px;
                    border-radius: 25px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                    min-height: 25px;
                    border: 2px solid rgba(39, 174, 96, 0.3);
                    font-family: 'Segoe UI', Arial, sans-serif;
                """)
            elif operation == "خصم":
                self.new_stock_label.setStyleSheet("""
                    color: #e74c3c;
                    font-size: 18px;
                    font-weight: bold;
                    background-color: rgba(231, 76, 60, 0.1);
                    padding: 15px 20px;
                    border-radius: 25px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                    min-height: 25px;
                    border: 2px solid rgba(231, 76, 60, 0.3);
                    font-family: 'Segoe UI', Arial, sans-serif;
                """)
            else:  # تعيين
                self.new_stock_label.setStyleSheet("""
                    color: #3498db;
                    font-size: 18px;
                    font-weight: bold;
                    background-color: rgba(52, 152, 219, 0.1);
                    padding: 15px 20px;
                    border-radius: 25px;
                    margin-top: 10px;
                    margin-bottom: 10px;
                    min-height: 25px;
                    border: 2px solid rgba(52, 152, 219, 0.3);
                    font-family: 'Segoe UI', Arial, sans-serif;
                """)
                
        except Exception as e:
            self.new_stock_label.setText("خطأ في الحساب")
    
    def get_product_data(self):
        """الحصول على بيانات المنتج المحدثة"""
        try:
            price = float(self.price_input.text().strip()) if self.price_input.text().strip() else 0.0
        except ValueError:
            price = 0.0
            
        return {
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'price': price,
            'stock_quantity': self.product_data.get('stock_quantity', 0)  # نستخدم المخزون الحالي كقيمة افتراضية
        }
    
    def get_stock_update_data(self):
        """الحصول على بيانات تحديث المخزون"""
        current_stock = int(self.product_data.get('stock_quantity', 0))
        quantity = self.quantity_input.value()
        operation = self.update_type_combo.currentText()
        
        # حساب المخزون الجديد
        if operation == "إضافة":
            new_stock = current_stock + quantity
        elif operation == "خصم":
            new_stock = max(0, current_stock - quantity)
        else:  # تعيين
            new_stock = quantity
        
        return {
            'operation': operation,
            'quantity': quantity,
            'new_stock': new_stock
        }

class UpdateStockDialog(QDialog):
    """نافذة تحديث المخزون"""
    
    def __init__(self, current_user, product_data=None):
        super().__init__()
        self.current_user = current_user
        self.product_data = product_data
        self.product_model = ProductModel()
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تحديث المخزون")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("تحديث المخزون")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # نموذج البيانات
        form_layout = QFormLayout()
        
        # اختيار المنتج
        if self.product_data:
            # إذا كان المنتج محدد مسبقاً، اعرض اسمه فقط
            product_label = QLabel(f"{self.product_data['name']} (المخزون الحالي: {self.product_data['stock_quantity']})")
            product_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            form_layout.addRow("المنتج:", product_label)
        else:
            # إذا لم يكن المنتج محدد، اعرض قائمة الاختيار
            self.product_combo = QComboBox()
            self.load_products_for_stock_update()
            form_layout.addRow("المنتج:", self.product_combo)
        
        # نوع التحديث
        self.update_type_combo = QComboBox()
        self.update_type_combo.addItems(["إضافة", "خصم", "تعيين"])
        form_layout.addRow("نوع التحديث:", self.update_type_combo)
        
        # الكمية
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(10)
        form_layout.addRow("الكمية:", self.quantity_input)
        
        # ملاحظات
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)...")
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # أزرار التحكم
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_products_for_stock_update(self):
        """تحميل المنتجات لتحديث المخزون"""
        try:
            products = self.product_model.get_all_products()
            if products:
                product_names = [f"{p['name']} (المخزون: {p['stock_quantity']})" for p in products]
                self.product_combo.addItems(product_names)
            else:
                self.product_combo.addItems(["لا توجد منتجات"])
        except Exception as e:
            self.product_combo.addItems(["خطأ في تحميل المنتجات"])
            print(f"Error loading products: {e}")
    
    def get_update_data(self):
        """الحصول على بيانات التحديث"""
        if self.product_data:
            # إذا كان المنتج محدد مسبقاً
            return {
                'product_id': self.product_data['id'],
                'product_name': self.product_data['name'],
                'update_type': self.update_type_combo.currentText(),
                'quantity': self.quantity_input.value(),
                'notes': self.notes_input.toPlainText().strip()
            }
        else:
            # إذا كان المنتج من قائمة الاختيار
            return {
                'product': self.product_combo.currentText(),
                'update_type': self.update_type_combo.currentText(),
                'quantity': self.quantity_input.value(),
                'notes': self.notes_input.toPlainText().strip()
            }
