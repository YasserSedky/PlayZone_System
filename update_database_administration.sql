-- ═══════════════════════════════════════════════════════════════
-- سكريبت تحديث قاعدة البيانات - نظام الإداريات
-- Database Update Script - Administration Module
-- ═══════════════════════════════════════════════════════════════

-- جدول الموظفين
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    national_id TEXT UNIQUE,
    address TEXT,
    position TEXT NOT NULL,
    hire_date TEXT NOT NULL,
    monthly_salary REAL NOT NULL DEFAULT 0.00,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- جدول سلف الموظفين
CREATE TABLE IF NOT EXISTS employee_advances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    reason TEXT,
    paid_back INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- جدول خصومات الموظفين
CREATE TABLE IF NOT EXISTS employee_deductions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    reason TEXT NOT NULL,
    deduction_type TEXT DEFAULT 'other' CHECK (deduction_type IN ('absence', 'lateness', 'damage', 'other')),
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- جدول ساعات العمل الإضافية
CREATE TABLE IF NOT EXISTS employee_overtime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    hours REAL NOT NULL,
    hourly_rate REAL NOT NULL,
    total_amount REAL NOT NULL,
    notes TEXT,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- جدول سجل رواتب الموظفين
CREATE TABLE IF NOT EXISTS employee_salary_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    base_salary REAL NOT NULL,
    overtime_amount REAL DEFAULT 0.00,
    advances_amount REAL DEFAULT 0.00,
    deductions_amount REAL DEFAULT 0.00,
    net_salary REAL NOT NULL,
    payment_date TEXT,
    paid INTEGER DEFAULT 0,
    notes TEXT,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(employee_id, month, year)
);

-- جدول المصاريف الإدارية
CREATE TABLE IF NOT EXISTS administrative_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_type TEXT NOT NULL CHECK (expense_type IN ('rent', 'electricity', 'water', 'gas', 'internet', 'phone', 'maintenance', 'taxes', 'fees', 'insurance', 'other')),
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    is_recurring INTEGER DEFAULT 0,
    recurrence_period TEXT CHECK (recurrence_period IN ('monthly', 'quarterly', 'yearly') OR recurrence_period IS NULL),
    notes TEXT,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- إنشاء فهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active);
CREATE INDEX IF NOT EXISTS idx_employees_position ON employees(position);
CREATE INDEX IF NOT EXISTS idx_employee_advances_employee ON employee_advances(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_advances_date ON employee_advances(date);
CREATE INDEX IF NOT EXISTS idx_employee_deductions_employee ON employee_deductions(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_deductions_date ON employee_deductions(date);
CREATE INDEX IF NOT EXISTS idx_employee_overtime_employee ON employee_overtime(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_overtime_date ON employee_overtime(date);
CREATE INDEX IF NOT EXISTS idx_salary_records_employee ON employee_salary_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_salary_records_month_year ON employee_salary_records(month, year);
CREATE INDEX IF NOT EXISTS idx_admin_expenses_type ON administrative_expenses(expense_type);
CREATE INDEX IF NOT EXISTS idx_admin_expenses_date ON administrative_expenses(date);
CREATE INDEX IF NOT EXISTS idx_admin_expenses_recurring ON administrative_expenses(is_recurring);

-- ═══════════════════════════════════════════════════════════════
-- تم التحديث بنجاح!
-- ═══════════════════════════════════════════════════════════════

