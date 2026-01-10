"""
HR & Payroll Schemas
Pydantic schemas for employee management, attendance, payroll, leave, and performance
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime, time
from uuid import UUID
from enum import Enum


# ==================== ENUMS ====================

class EmployeeStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"
    PROBATION = "PROBATION"


class ContractTypeEnum(str, Enum):
    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    PROBATION = "PROBATION"
    INTERNSHIP = "INTERNSHIP"
    PART_TIME = "PART_TIME"


class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MaritalStatusEnum(str, Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"


class CheckInMethodEnum(str, Enum):
    FACE = "FACE"
    FINGERPRINT = "FINGERPRINT"
    MANUAL = "MANUAL"
    QR_CODE = "QR_CODE"
    MOBILE = "MOBILE"


class LeaveStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PayrollStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class CameraTypeEnum(str, Enum):
    WEBCAM = "WEBCAM"
    CCTV = "CCTV"
    IP_CAMERA = "IP_CAMERA"
    USB_CAMERA = "USB_CAMERA"


# ==================== DEPARTMENT ====================

class DepartmentBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    manager_id: Optional[UUID] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== POSITION ====================

class PositionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    level: int = 1
    base_salary: Optional[float] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    level: Optional[int] = None
    base_salary: Optional[float] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== EMPLOYEE ====================

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    nik: Optional[str] = None
    npwp: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    gender: Optional[GenderEnum] = None
    marital_status: Optional[MaritalStatusEnum] = None
    religion: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    hire_date: date
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    contract_type: ContractTypeEnum = ContractTypeEnum.PERMANENT
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    base_salary: float = 0.0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    bpjs_kesehatan: Optional[str] = None
    bpjs_ketenagakerjaan: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    nik: Optional[str] = None
    npwp: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    gender: Optional[GenderEnum] = None
    marital_status: Optional[MaritalStatusEnum] = None
    religion: Optional[str] = None
    blood_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    contract_type: Optional[ContractTypeEnum] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    base_salary: Optional[float] = None
    status: Optional[EmployeeStatusEnum] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    bpjs_kesehatan: Optional[str] = None
    bpjs_ketenagakerjaan: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    employee_code: str
    blood_type: Optional[str] = None
    hire_date: date
    termination_date: Optional[date] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    contract_type: Optional[ContractTypeEnum] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    base_salary: float
    status: EmployeeStatusEnum
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    bpjs_kesehatan: Optional[str] = None
    bpjs_ketenagakerjaan: Optional[str] = None
    profile_photo_url: Optional[str] = None
    id_card_photo_url: Optional[str] = None
    fingerprint_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    has_face_registered: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    id: UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department_name: Optional[str] = None
    position_name: Optional[str] = None
    status: EmployeeStatusEnum
    profile_photo_url: Optional[str] = None
    hire_date: date

    class Config:
        from_attributes = True


# ==================== FACE & BIOMETRIC ====================

class FaceRegistrationRequest(BaseModel):
    face_image_base64: str  # Base64 encoded image


class FaceCheckInRequest(BaseModel):
    face_image_base64: str
    location: Optional[str] = None  # lat,lng
    device: Optional[str] = None


class FaceCheckInResponse(BaseModel):
    success: bool
    message: str
    employee_id: Optional[UUID] = None
    employee_name: Optional[str] = None
    check_in_time: Optional[datetime] = None
    photo_url: Optional[str] = None


# ==================== DOCUMENT ====================

class EmployeeDocumentCreate(BaseModel):
    document_type: str
    document_name: str
    file_url: str
    expiry_date: Optional[date] = None
    notes: Optional[str] = None


class EmployeeDocumentResponse(BaseModel):
    id: UUID
    employee_id: UUID
    document_type: str
    document_name: str
    file_url: str
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== SHIFT ====================

class ShiftBase(BaseModel):
    name: str
    code: str
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    late_tolerance_minutes: int = 15
    is_overnight: bool = False


class ShiftCreate(ShiftBase):
    pass


class ShiftResponse(ShiftBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ATTENDANCE ====================

class AttendanceCheckIn(BaseModel):
    method: CheckInMethodEnum = CheckInMethodEnum.MANUAL
    face_image_base64: Optional[str] = None
    location: Optional[str] = None
    device: Optional[str] = None
    notes: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    method: CheckInMethodEnum = CheckInMethodEnum.MANUAL
    face_image_base64: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    check_in_method: Optional[CheckInMethodEnum] = None
    check_out_method: Optional[CheckInMethodEnum] = None
    status: str
    late_minutes: int
    overtime_minutes: int
    work_hours: float
    check_in_photo_url: Optional[str] = None
    check_out_photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceListFilter(BaseModel):
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


# ==================== LEAVE ====================

class LeaveTypeCreate(BaseModel):
    name: str
    code: str
    annual_quota: int = 12
    is_paid: bool = True
    requires_document: bool = False
    max_consecutive_days: Optional[int] = None
    color: str = "#3B82F6"


class LeaveTypeResponse(BaseModel):
    id: UUID
    name: str
    code: str
    annual_quota: int
    is_paid: bool
    requires_document: bool
    color: str
    is_active: bool

    class Config:
        from_attributes = True


class LeaveRequestCreate(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: Optional[str] = None
    attachment_url: Optional[str] = None


class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None


class LeaveRequestApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    leave_type_id: UUID
    leave_type_name: Optional[str] = None
    start_date: date
    end_date: date
    total_days: int
    reason: Optional[str] = None
    status: LeaveStatusEnum
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveBalanceResponse(BaseModel):
    leave_type_id: UUID
    leave_type_name: str
    year: int
    quota: int
    used: int
    remaining: int

    class Config:
        from_attributes = True


# ==================== PAYROLL ====================

class PayrollPeriodCreate(BaseModel):
    name: str
    period_month: int
    period_year: int
    start_date: date
    end_date: date
    payment_date: Optional[date] = None


class PayrollPeriodResponse(BaseModel):
    id: UUID
    name: str
    period_month: int
    period_year: int
    start_date: date
    end_date: date
    payment_date: Optional[date] = None
    status: PayrollStatusEnum
    is_closed: bool

    class Config:
        from_attributes = True


class PayslipResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    base_salary: float
    allowances: float
    overtime_pay: float
    bonus: float
    gross_pay: float
    tax_deduction: float
    bpjs_kes_deduction: float
    bpjs_tk_deduction: float
    other_deductions: float
    total_deductions: float
    net_pay: float
    is_paid: bool
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayrollRunResponse(BaseModel):
    id: UUID
    payroll_period_id: UUID
    run_date: datetime
    status: PayrollStatusEnum
    total_employees: int
    total_gross: float
    total_deductions: float
    total_net: float

    class Config:
        from_attributes = True


# ==================== CAMERA ====================

class CameraCreate(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    camera_type: CameraTypeEnum = CameraTypeEnum.WEBCAM
    stream_url: Optional[str] = None
    device_id: Optional[str] = None
    is_ai_enabled: bool = False


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    camera_type: Optional[CameraTypeEnum] = None
    stream_url: Optional[str] = None
    device_id: Optional[str] = None
    is_ai_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class CameraResponse(BaseModel):
    id: UUID
    name: str
    location: Optional[str] = None
    camera_type: CameraTypeEnum
    stream_url: Optional[str] = None
    device_id: Optional[str] = None
    is_active: bool
    is_ai_enabled: bool

    class Config:
        from_attributes = True


class CameraActivityResponse(BaseModel):
    id: UUID
    camera_id: UUID
    camera_name: Optional[str] = None
    timestamp: datetime
    activity_type: Optional[str] = None
    employee_detected_id: Optional[UUID] = None
    employee_name: Optional[str] = None
    people_count: int
    snapshot_url: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== KPI & PERFORMANCE ====================

class KPICreate(BaseModel):
    employee_id: UUID
    period_year: int
    period_quarter: Optional[int] = None
    metric_name: str
    metric_description: Optional[str] = None
    target_value: float
    weight: float = 1.0
    unit: Optional[str] = None


class KPIUpdate(BaseModel):
    actual_value: Optional[float] = None
    target_value: Optional[float] = None
    weight: Optional[float] = None


class KPIResponse(BaseModel):
    id: UUID
    employee_id: UUID
    period_year: int
    period_quarter: Optional[int] = None
    metric_name: str
    target_value: float
    actual_value: Optional[float] = None
    weight: float
    unit: Optional[str] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


class PerformanceReviewCreate(BaseModel):
    employee_id: UUID
    period_year: int
    period_type: str  # MONTHLY, QUARTERLY, ANNUAL
    kpi_score: Optional[float] = None
    competency_score: Optional[float] = None
    overall_score: Optional[float] = None
    rating: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    goals_next_period: Optional[str] = None


class PerformanceReviewResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    reviewer_id: UUID
    period_year: int
    period_type: str
    kpi_score: Optional[float] = None
    overall_score: Optional[float] = None
    rating: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== DASHBOARD STATS ====================

class HRDashboardStats(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    on_leave_today: int = 0
    absent_today: int = 0
    late_today: int = 0
    present_today: int = 0
    pending_leave_requests: int = 0
    contracts_expiring_soon: int = 0
    birthdays_this_month: int = 0
