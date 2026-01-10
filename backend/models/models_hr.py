"""
HR & Payroll Models
Complete module for employee management, attendance, payroll, leave, and performance tracking
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Date, Time, Text, Integer, Enum as SQLEnum, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
import uuid
from database import Base
from datetime import datetime
import enum


# ==================== ENUMS ====================

class EmployeeStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"
    PROBATION = "PROBATION"


class ContractType(str, enum.Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    PROBATION = "PROBATION"
    INTERNSHIP = "INTERNSHIP"
    PART_TIME = "PART_TIME"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MaritalStatus(str, enum.Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"


class CheckInMethod(str, enum.Enum):
    FACE = "FACE"
    FINGERPRINT = "FINGERPRINT"
    MANUAL = "MANUAL"
    QR_CODE = "QR_CODE"
    MOBILE = "MOBILE"


class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PayrollStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class CameraType(str, enum.Enum):
    WEBCAM = "WEBCAM"
    CCTV = "CCTV"
    IP_CAMERA = "IP_CAMERA"
    USB_CAMERA = "USB_CAMERA"


class ActivityType(str, enum.Enum):
    WORKING = "WORKING"
    IDLE = "IDLE"
    AWAY = "AWAY"
    MEETING = "MEETING"
    BREAK = "BREAK"


# ==================== ORGANIZATION ====================

class HRDepartment(Base):
    """Department/Division in the organization"""
    __tablename__ = "hr_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Manager from users table
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    positions = relationship("HRPosition", back_populates="department")
    manager = relationship("User", foreign_keys=[manager_id])


class HRPosition(Base):
    """Job position/title in the organization"""
    __tablename__ = "hr_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    level = Column(Integer, default=1)  # 1=Staff, 2=Supervisor, 3=Manager, 4=Director, 5=C-Level
    base_salary = Column(Float, default=0.0)  # Default base salary for this position
    min_salary = Column(Float, nullable=True)
    max_salary = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("HRDepartment", back_populates="positions")


# ==================== EMPLOYEE ====================

class Employee(Base):
    """Enhanced Employee model with biometric and document support"""
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_code = Column(String(20), nullable=False, unique=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    nik = Column(String(20), nullable=True)  # National ID Number
    npwp = Column(String(30), nullable=True)  # Tax ID
    birth_date = Column(Date, nullable=True)
    birth_place = Column(String(100), nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    marital_status = Column(SQLEnum(MaritalStatus), nullable=True)
    religion = Column(String(50), nullable=True)
    blood_type = Column(String(5), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    
    # Photos & Biometrics
    profile_photo_url = Column(String(500), nullable=True)  # Cloudinary URL
    id_card_photo_url = Column(String(500), nullable=True)  # Cloudinary URL
    face_encoding = Column(Text, nullable=True)  # JSON encoded face embedding
    fingerprint_data = Column(Text, nullable=True)  # Encoded fingerprint template
    fingerprint_id = Column(String(100), nullable=True)  # Browser fingerprint ID for check-in
    
    # Employment
    department_id = Column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("hr_positions.id"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    hire_date = Column(Date, nullable=False, default=datetime.utcnow)
    termination_date = Column(Date, nullable=True)
    contract_type = Column(SQLEnum(ContractType), default=ContractType.PERMANENT)
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    
    # Salary & Benefits
    base_salary = Column(Float, default=0.0)
    bank_name = Column(String(100), nullable=True)
    bank_account = Column(String(50), nullable=True)
    bank_account_name = Column(String(100), nullable=True)
    
    # BPJS
    bpjs_kesehatan = Column(String(30), nullable=True)
    bpjs_ketenagakerjaan = Column(String(30), nullable=True)
    
    # Emergency Contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("HRDepartment", foreign_keys=[department_id])
    position = relationship("HRPosition")
    manager = relationship("Employee", remote_side=[id], backref="subordinates")
    documents = relationship("EmployeeDocument", back_populates="employee")
    attendances = relationship("Attendance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    payslips = relationship("Payslip", back_populates="employee")


class EmployeeDocument(Base):
    """Employee documents storage"""
    __tablename__ = "employee_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # CV, IJAZAH, KTP, KONTRAK, etc.
    document_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)  # Cloudinary URL
    expiry_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    employee = relationship("Employee", back_populates="documents")


# ==================== ATTENDANCE ====================

class Shift(Base):
    """Work shift definition"""
    __tablename__ = "hr_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    late_tolerance_minutes = Column(Integer, default=15)
    early_leave_tolerance = Column(Integer, default=15)
    is_overnight = Column(Boolean, default=False)  # For night shifts
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EmployeeSchedule(Base):
    """Employee work schedule assignment"""
    __tablename__ = "employee_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("hr_shifts.id"), nullable=False)
    date = Column(Date, nullable=False)
    is_holiday = Column(Boolean, default=False)
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee")
    shift = relationship("Shift")


class Attendance(Base):
    """Daily attendance record with biometric tracking"""
    __tablename__ = "attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("hr_shifts.id"), nullable=True)
    
    # Check In
    check_in = Column(DateTime, nullable=True)
    check_in_method = Column(SQLEnum(CheckInMethod), default=CheckInMethod.MANUAL)
    check_in_photo_url = Column(String(500), nullable=True)  # Face capture
    check_in_location = Column(String(255), nullable=True)  # Lat,Lng
    check_in_device = Column(String(100), nullable=True)
    
    # Check Out
    check_out = Column(DateTime, nullable=True)
    check_out_method = Column(SQLEnum(CheckInMethod), nullable=True)
    check_out_photo_url = Column(String(500), nullable=True)
    check_out_location = Column(String(255), nullable=True)
    check_out_device = Column(String(100), nullable=True)
    
    # Calculations
    status = Column(SQLEnum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    overtime_minutes = Column(Integer, default=0)
    work_hours = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="attendances")
    shift = relationship("Shift")


# ==================== LEAVE MANAGEMENT ====================

class LeaveType(Base):
    """Leave type definitions"""
    __tablename__ = "leave_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(10), nullable=False)
    annual_quota = Column(Integer, default=12)
    is_paid = Column(Boolean, default=True)
    requires_document = Column(Boolean, default=False)
    max_consecutive_days = Column(Integer, nullable=True)
    color = Column(String(7), default="#3B82F6")  # For calendar display
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class LeaveBalance(Base):
    """Employee leave balance per year"""
    __tablename__ = "leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    quota = Column(Integer, default=0)
    used = Column(Integer, default=0)
    carried_forward = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee")
    leave_type = relationship("LeaveType")


class LeaveRequest(Base):
    """Leave request with approval workflow"""
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    attachment_url = Column(String(500), nullable=True)
    
    status = Column(SQLEnum(LeaveStatus), default=LeaveStatus.PENDING)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="leave_requests")
    leave_type = relationship("LeaveType")


# ==================== PAYROLL ====================

class SalaryComponent(Base):
    """Salary component definitions (allowances, deductions)"""
    __tablename__ = "salary_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)
    component_type = Column(String(20), nullable=False)  # EARNING, DEDUCTION
    is_taxable = Column(Boolean, default=True)
    is_fixed = Column(Boolean, default=True)  # Fixed or variable
    default_amount = Column(Float, default=0.0)
    calculation_formula = Column(Text, nullable=True)  # For dynamic calculation
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EmployeeSalaryComponent(Base):
    """Employee-specific salary components"""
    __tablename__ = "employee_salary_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("salary_components.id"), nullable=False)
    amount = Column(Float, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PayrollPeriod(Base):
    """Payroll period (monthly cycle)"""
    __tablename__ = "payroll_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(50))  # e.g. "January 2024"
    period_month = Column(Integer, nullable=False)  # 1-12
    period_year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT)
    is_closed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("PayrollRun", back_populates="period")


class PayrollRun(Base):
    """Payroll calculation run"""
    __tablename__ = "payroll_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey("payroll_periods.id"))
    run_date = Column(DateTime, default=datetime.utcnow)
    run_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.DRAFT)
    
    total_employees = Column(Integer, default=0)
    total_gross = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    total_net = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    period = relationship("PayrollPeriod", back_populates="runs")
    payslips = relationship("Payslip", back_populates="run")


class Payslip(Base):
    """Individual employee payslip"""
    __tablename__ = "payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_runs.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    
    # Earnings
    base_salary = Column(Float, default=0.0)
    allowances = Column(Float, default=0.0)
    overtime_pay = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    gross_pay = Column(Float, default=0.0)
    
    # Deductions
    tax_deduction = Column(Float, default=0.0)
    bpjs_kes_deduction = Column(Float, default=0.0)
    bpjs_tk_deduction = Column(Float, default=0.0)
    other_deductions = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    
    net_pay = Column(Float, default=0.0)
    
    # Details (JSON for component breakdown)
    earnings_detail = Column(JSONB, nullable=True)
    deductions_detail = Column(JSONB, nullable=True)
    
    # Status
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("PayrollRun", back_populates="payslips")
    employee = relationship("Employee", back_populates="payslips")


# ==================== PERFORMANCE ====================

class KPI(Base):
    """Key Performance Indicator for employees"""
    __tablename__ = "hr_kpis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    period_year = Column(Integer, nullable=False)
    period_quarter = Column(Integer, nullable=True)  # 1-4 or null for annual
    
    metric_name = Column(String(200), nullable=False)
    metric_description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True)
    weight = Column(Float, default=1.0)  # Percentage weight
    unit = Column(String(20), nullable=True)  # %, count, currency
    
    score = Column(Float, nullable=True)  # Calculated score
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PerformanceReview(Base):
    """Employee performance review"""
    __tablename__ = "performance_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    period_year = Column(Integer, nullable=False)
    period_type = Column(String(20), nullable=False)  # MONTHLY, QUARTERLY, ANNUAL
    
    kpi_score = Column(Float, nullable=True)
    competency_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    rating = Column(String(20), nullable=True)  # A, B, C, D, E
    
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    goals_next_period = Column(Text, nullable=True)
    
    employee_feedback = Column(Text, nullable=True)
    status = Column(String(20), default="DRAFT")  # DRAFT, SUBMITTED, ACKNOWLEDGED
    
    submitted_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== CAMERA & MONITORING ====================

class OfficeCamera(Base):
    """Office camera for monitoring"""
    __tablename__ = "office_cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    camera_type = Column(SQLEnum(CameraType), default=CameraType.WEBCAM)
    stream_url = Column(String(500), nullable=True)  # RTSP/HTTP URL for IP cameras
    device_id = Column(String(100), nullable=True)  # For USB/Webcam
    is_active = Column(Boolean, default=True)
    is_ai_enabled = Column(Boolean, default=False)  # Enable activity detection
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CameraActivity(Base):
    """Activity detection from cameras"""
    __tablename__ = "camera_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("office_cameras.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    activity_type = Column(SQLEnum(ActivityType), nullable=True)
    employee_detected_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    people_count = Column(Integer, default=0)
    
    snapshot_url = Column(String(500), nullable=True)  # Cloudinary URL
    confidence_score = Column(Float, nullable=True)
    activity_metadata = Column(JSONB, nullable=True)  # Additional AI detection data
    
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("OfficeCamera")
