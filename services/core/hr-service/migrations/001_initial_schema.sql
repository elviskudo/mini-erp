-- HR Service Database Migration
-- Version: 001
-- Description: Initial tables for HR Service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========== DEPARTMENTS ==========
CREATE TABLE IF NOT EXISTS hr_departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    manager_id UUID,
    parent_id UUID REFERENCES hr_departments(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_hr_dept_tenant ON hr_departments(tenant_id);

-- ========== POSITIONS ==========
CREATE TABLE IF NOT EXISTS hr_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    department_id UUID NOT NULL REFERENCES hr_departments(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    level INTEGER DEFAULT 1,
    min_salary DECIMAL(18, 2),
    max_salary DECIMAL(18, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_hr_pos_tenant ON hr_positions(tenant_id);
CREATE INDEX idx_hr_pos_dept ON hr_positions(department_id);

-- ========== EMPLOYEES ==========
CREATE TYPE employee_status AS ENUM ('ACTIVE', 'INACTIVE', 'ON_LEAVE', 'PROBATION', 'TERMINATED', 'RESIGNED');
CREATE TYPE employment_type AS ENUM ('PERMANENT', 'CONTRACT', 'PROBATION', 'INTERNSHIP', 'FREELANCE');

CREATE TABLE IF NOT EXISTS hr_employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_code VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Indonesia',
    id_number VARCHAR(50),
    tax_id VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_account_holder VARCHAR(255),
    department_id UUID REFERENCES hr_departments(id) ON DELETE SET NULL,
    position_id UUID REFERENCES hr_positions(id) ON DELETE SET NULL,
    manager_id UUID REFERENCES hr_employees(id) ON DELETE SET NULL,
    hire_date DATE NOT NULL,
    contract_start DATE,
    contract_end DATE,
    termination_date DATE,
    status employee_status DEFAULT 'ACTIVE',
    employment_type employment_type DEFAULT 'PERMANENT',
    basic_salary DECIMAL(18, 2) DEFAULT 0,
    profile_photo_url TEXT,
    id_card_photo_url TEXT,
    face_encoding TEXT,
    fingerprint_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, employee_code),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_hr_emp_tenant ON hr_employees(tenant_id);
CREATE INDEX idx_hr_emp_dept ON hr_employees(department_id);
CREATE INDEX idx_hr_emp_pos ON hr_employees(position_id);
CREATE INDEX idx_hr_emp_status ON hr_employees(status);

-- ========== EMPLOYEE DOCUMENTS ==========
CREATE TABLE IF NOT EXISTS hr_employee_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_name VARCHAR(255),
    document_url TEXT NOT NULL,
    expiry_date DATE,
    uploaded_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hr_doc_employee ON hr_employee_documents(employee_id);

-- ========== SHIFTS ==========
CREATE TABLE IF NOT EXISTS hr_shifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_duration_minutes INTEGER DEFAULT 60,
    late_tolerance_minutes INTEGER DEFAULT 15,
    early_leave_tolerance_minutes INTEGER DEFAULT 0,
    is_overnight BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_hr_shift_tenant ON hr_shifts(tenant_id);

-- ========== EMPLOYEE SCHEDULES ==========
CREATE TABLE IF NOT EXISTS hr_employee_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    shift_id UUID NOT NULL REFERENCES hr_shifts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(employee_id, date)
);

CREATE INDEX idx_hr_schedule_emp ON hr_employee_schedules(employee_id);
CREATE INDEX idx_hr_schedule_date ON hr_employee_schedules(date);

-- ========== ATTENDANCE ==========
CREATE TYPE attendance_status AS ENUM ('PRESENT', 'LATE', 'HALF_DAY', 'ABSENT', 'ON_LEAVE');
CREATE TYPE check_in_method AS ENUM ('FACE', 'FINGERPRINT', 'QR', 'MANUAL', 'GPS');

CREATE TABLE IF NOT EXISTS hr_attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    shift_id UUID REFERENCES hr_shifts(id),
    date DATE NOT NULL,
    check_in TIMESTAMP WITH TIME ZONE,
    check_out TIMESTAMP WITH TIME ZONE,
    check_in_method check_in_method,
    check_out_method check_in_method,
    check_in_photo_url TEXT,
    check_out_photo_url TEXT,
    check_in_location TEXT,
    check_out_location TEXT,
    check_in_device VARCHAR(255),
    status attendance_status DEFAULT 'PRESENT',
    late_minutes INTEGER DEFAULT 0,
    early_leave_minutes INTEGER DEFAULT 0,
    overtime_minutes INTEGER DEFAULT 0,
    work_hours DECIMAL(5, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(employee_id, date)
);

CREATE INDEX idx_hr_att_tenant ON hr_attendance(tenant_id);
CREATE INDEX idx_hr_att_emp ON hr_attendance(employee_id);
CREATE INDEX idx_hr_att_date ON hr_attendance(date);

-- ========== LEAVE TYPES ==========
CREATE TABLE IF NOT EXISTS hr_leave_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    default_days INTEGER DEFAULT 0,
    is_paid BOOLEAN DEFAULT TRUE,
    requires_approval BOOLEAN DEFAULT TRUE,
    requires_attachment BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_hr_lt_tenant ON hr_leave_types(tenant_id);

-- ========== LEAVE REQUESTS ==========
CREATE TYPE leave_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');

CREATE TABLE IF NOT EXISTS hr_leave_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    leave_type_id UUID NOT NULL REFERENCES hr_leave_types(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days DECIMAL(5, 1) NOT NULL,
    reason TEXT,
    attachment_url TEXT,
    status leave_status DEFAULT 'PENDING',
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hr_lr_tenant ON hr_leave_requests(tenant_id);
CREATE INDEX idx_hr_lr_emp ON hr_leave_requests(employee_id);
CREATE INDEX idx_hr_lr_status ON hr_leave_requests(status);
CREATE INDEX idx_hr_lr_dates ON hr_leave_requests(start_date, end_date);

-- ========== LEAVE BALANCES ==========
CREATE TABLE IF NOT EXISTS hr_leave_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    leave_type_id UUID NOT NULL REFERENCES hr_leave_types(id),
    year INTEGER NOT NULL,
    total_days DECIMAL(5, 1) DEFAULT 0,
    used_days DECIMAL(5, 1) DEFAULT 0,
    remaining_days DECIMAL(5, 1) DEFAULT 0,
    carried_over_days DECIMAL(5, 1) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(employee_id, leave_type_id, year)
);

CREATE INDEX idx_hr_lb_emp ON hr_leave_balances(employee_id);

-- ========== PAYROLL PERIODS ==========
CREATE TYPE payroll_status AS ENUM ('OPEN', 'PROCESSING', 'REVIEWED', 'APPROVED', 'PAID', 'CLOSED');

CREATE TABLE IF NOT EXISTS hr_payroll_periods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status payroll_status DEFAULT 'OPEN',
    total_employees INTEGER DEFAULT 0,
    total_gross DECIMAL(18, 2) DEFAULT 0,
    total_deductions DECIMAL(18, 2) DEFAULT 0,
    total_net DECIMAL(18, 2) DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_hr_pp_tenant ON hr_payroll_periods(tenant_id);
CREATE INDEX idx_hr_pp_status ON hr_payroll_periods(status);

-- ========== PAYSLIPS ==========
CREATE TYPE payslip_status AS ENUM ('DRAFT', 'GENERATED', 'APPROVED', 'PAID');

CREATE TABLE IF NOT EXISTS hr_payslips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    period_id UUID NOT NULL REFERENCES hr_payroll_periods(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    basic_salary DECIMAL(18, 2) DEFAULT 0,
    position_allowance DECIMAL(18, 2) DEFAULT 0,
    transport_allowance DECIMAL(18, 2) DEFAULT 0,
    meal_allowance DECIMAL(18, 2) DEFAULT 0,
    overtime_pay DECIMAL(18, 2) DEFAULT 0,
    bonus DECIMAL(18, 2) DEFAULT 0,
    other_income DECIMAL(18, 2) DEFAULT 0,
    gross_salary DECIMAL(18, 2) DEFAULT 0,
    bpjs_kesehatan DECIMAL(18, 2) DEFAULT 0,
    bpjs_ketenagakerjaan DECIMAL(18, 2) DEFAULT 0,
    pph21 DECIMAL(18, 2) DEFAULT 0,
    loan_deduction DECIMAL(18, 2) DEFAULT 0,
    other_deduction DECIMAL(18, 2) DEFAULT 0,
    total_deductions DECIMAL(18, 2) DEFAULT 0,
    net_salary DECIMAL(18, 2) DEFAULT 0,
    work_days INTEGER DEFAULT 0,
    present_days INTEGER DEFAULT 0,
    absent_days INTEGER DEFAULT 0,
    late_count INTEGER DEFAULT 0,
    overtime_hours DECIMAL(5, 2) DEFAULT 0,
    status payslip_status DEFAULT 'DRAFT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(period_id, employee_id)
);

CREATE INDEX idx_hr_ps_period ON hr_payslips(period_id);
CREATE INDEX idx_hr_ps_emp ON hr_payslips(employee_id);

-- ========== TRIGGERS ==========
CREATE OR REPLACE FUNCTION update_hr_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hr_dept_updated_at BEFORE UPDATE ON hr_departments
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_pos_updated_at BEFORE UPDATE ON hr_positions
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_emp_updated_at BEFORE UPDATE ON hr_employees
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_shift_updated_at BEFORE UPDATE ON hr_shifts
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_att_updated_at BEFORE UPDATE ON hr_attendance
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_lt_updated_at BEFORE UPDATE ON hr_leave_types
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_lr_updated_at BEFORE UPDATE ON hr_leave_requests
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_lb_updated_at BEFORE UPDATE ON hr_leave_balances
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_pp_updated_at BEFORE UPDATE ON hr_payroll_periods
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();

CREATE TRIGGER update_hr_ps_updated_at BEFORE UPDATE ON hr_payslips
    FOR EACH ROW EXECUTE FUNCTION update_hr_updated_at_column();
