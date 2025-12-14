from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import date, datetime

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    base_salary: float = 0.0
    status: str = "Active"

class EmployeeCreate(EmployeeBase):
    hire_date: date

class EmployeeResponse(EmployeeBase):
    id: uuid.UUID
    hire_date: date
    class Config:
        from_attributes = True

class PayrollPeriodCreate(BaseModel):
    name: str
    start_date: date
    end_date: date

class PayrollPeriodResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    is_closed: bool
    class Config:
        from_attributes = True

class PayslipResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    gross_pay: float
    tax_deduction: float
    net_pay: float
    is_paid: bool
    class Config:
        from_attributes = True
