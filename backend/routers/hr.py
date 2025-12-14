from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid
import database
from models import models_hr
import models
import schemas
from datetime import datetime

router = APIRouter(
    prefix="/hr",
    tags=["Human Resources"]
)

@router.post("/employees", response_model=schemas.EmployeeResponse)
async def create_employee(employee: schemas.EmployeeCreate, db: AsyncSession = Depends(database.get_db)):
    db_employee = models_hr.Employee(**employee.dict())
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee

@router.get("/employees", response_model=List[schemas.EmployeeResponse])
async def list_employees(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models_hr.Employee))
    return result.scalars().all()

@router.get("/employees/{id}", response_model=schemas.EmployeeResponse)
async def get_employee(id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    employee = await db.get(models_hr.Employee, id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.post("/payroll/periods", response_model=schemas.PayrollPeriodResponse)
async def create_payroll_period(period: schemas.PayrollPeriodCreate, db: AsyncSession = Depends(database.get_db)):
    new_period = models_hr.PayrollPeriod(**period.dict())
    db.add(new_period)
    await db.commit()
    await db.refresh(new_period)
    return new_period

@router.get("/payroll/periods", response_model=List[schemas.PayrollPeriodResponse])
async def list_payroll_periods(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models_hr.PayrollPeriod).order_by(models_hr.PayrollPeriod.start_date.desc()))
    return result.scalars().all()

from services import gl_engine

@router.post("/payroll/run/{period_id}", response_model=schemas.PayrollPeriodResponse) # Return updated period or run status
async def run_payroll(period_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    # 1. Fetch Period
    period = await db.get(models_hr.PayrollPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    if period.is_closed:
        raise HTTPException(status_code=400, detail="Period already closed")

    # 2. Check for existing run (Allow re-run? For MVP, assume one run per period or block)
    # Let's create a new Run
    payroll_run = models_hr.PayrollRun(
        payroll_period_id=period.id,
        status="Completed"
    )
    db.add(payroll_run)
    await db.flush()

    # 3. Fetch Active Employees
    result = await db.execute(select(models_hr.Employee).where(models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE))
    employees = result.scalars().all()
    
    total_gross = 0.0
    total_tax = 0.0
    total_net = 0.0
    
    for emp in employees:
        gross = emp.base_salary
        tax_rate = 0.1 # Flat 10% simplified
        tax = gross * tax_rate
        net = gross - tax
        
        payslip = models_hr.Payslip(
            payroll_run_id=payroll_run.id,
            employee_id=emp.id,
            gross_pay=gross,
            tax_deduction=tax,
            net_pay=net,
            is_paid=True # Assume instant payment logic
        )
        db.add(payslip)
        
        total_gross += gross
        total_tax += tax
        total_net += net
        
    # 4. GL Posting (Finance Integration)
    # Dr Salaries Expense (5000 range - 5200 Operating Exp?)
    # Cr Cash/Bank (1110)
    # Cr Tax Payable? (2000 range) - For simplicity, assume Tax is withheld/paid later or just net out cash.
    # Standard: Dr Salary Exp (Gross), Cr Tax Payable (Tax), Cr Cash (Net).
    
    # Needs Account lookup. Hardcoding or looking up by code.
    # Let's assume seeded codes: 5200 (Exp), 1110 (Cash), 2100 (AP? Use generic liability for Tax, or just AP for simplicity)
    
    if employees:
         # Find Accounts
        acc_exp_res = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == "5200"))
        acc_cash_res = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == "1110")) 
        acc_liab_res = await db.execute(select(models.ChartOfAccount).where(models.ChartOfAccount.code == "2100")) # Using AP as proxy for Tax Payable
        
        acc_exp = acc_exp_res.scalar_one_or_none()
        acc_cash = acc_cash_res.scalar_one_or_none()
        acc_liab = acc_liab_res.scalar_one_or_none()
        
        if acc_exp and acc_cash and acc_liab:
            journal_entry = schemas.JournalEntryCreate(
                date=datetime.now(),
                description=f"Payroll Run - {period.name}",
                details=[
                    # Dr Expense (Gross)
                    schemas.JournalDetailCreate(account_id=acc_exp.id, debit=total_gross, credit=0),
                    # Cr Cash (Net)
                    schemas.JournalDetailCreate(account_id=acc_cash.id, debit=0, credit=total_net),
                    # Cr Tax Payable (Tax)
                    schemas.JournalDetailCreate(account_id=acc_liab.id, debit=0, credit=total_tax)
                ]
            )
            await gl_engine.post_journal_entry(db, journal_entry)

    period.is_closed = True
    await db.commit()
    return period

@router.get("/payslips/{employee_id}", response_model=List[schemas.PayslipResponse])
async def get_payslips(employee_id: uuid.UUID, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models_hr.Payslip).where(models_hr.Payslip.employee_id == employee_id))
    return result.scalars().all()
