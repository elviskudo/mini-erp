from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base
from datetime import datetime

class EmployeeStatus:
    ACTIVE = "Active"
    TERMINATED = "Terminated"
    ON_LEAVE = "On Leave"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    hire_date = Column(Date, default=datetime.utcnow)
    base_salary = Column(Float, default=0.0) # Monthly
    status = Column(String, default=EmployeeStatus.ACTIVE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String) # e.g. "January 2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False)
    
    runs = relationship("PayrollRun", back_populates="period")

class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey("payroll_periods.id"))
    run_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # Draft, Approved, Paid
    
    period = relationship("PayrollPeriod", back_populates="runs")
    payslips = relationship("Payslip", back_populates="run")

class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_runs.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    
    gross_pay = Column(Float, default=0.0)
    tax_deduction = Column(Float, default=0.0)
    other_deductions = Column(Float, default=0.0)
    net_pay = Column(Float, default=0.0)
    
    is_paid = Column(Boolean, default=False)
    
    run = relationship("PayrollRun", back_populates="payslips")
    employee = relationship("Employee")
