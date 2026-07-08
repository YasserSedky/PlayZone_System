"""
واجهات المستخدم لنظام إدارة محل بلايستيشن
User Interface Views for PlayStation Shop Management System
"""

from .login_window import LoginWindow
from .dashboard import DashboardWindow
from .device_panel import DevicePanelWindow
from .invoice_view import InvoiceViewWindow
from .customer_view import CustomerViewWindow
from .expense_view import ExpenseViewWindow
from .reports_view import ReportsViewWindow
from .settings_window import SettingsWindow

__all__ = [
    'LoginWindow',
    'DashboardWindow',
    'DevicePanelWindow',
    'InvoiceViewWindow',
    'CustomerViewWindow',
    'ExpenseViewWindow',
    'ReportsViewWindow',
    'SettingsWindow'
]
