"""
HR & Payroll Router
Complete API endpoints for employee management, attendance with face recognition,
payroll, leave management, camera monitoring, and performance tracking
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID
import base64
import json
import os

import database
import models
from models import models_hr
from auth import get_current_user
from schemas.schemas_hr import (
    # Department & Position
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    # Employee
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListResponse,
    EmployeeDocumentCreate, EmployeeDocumentResponse,
    FaceRegistrationRequest, FaceCheckInRequest, FaceCheckInResponse,
    # Attendance
    ShiftCreate, ShiftResponse,
    AttendanceCheckIn, AttendanceCheckOut, AttendanceResponse,
    # Leave
    LeaveTypeCreate, LeaveTypeResponse,
    LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestApproval, LeaveRequestResponse,
    LeaveBalanceResponse,
    # Payroll
    PayrollPeriodCreate, PayrollPeriodResponse,
    PayslipResponse, PayrollRunResponse,
    # Camera
    CameraCreate, CameraUpdate, CameraResponse, CameraActivityResponse,
    # KPI & Performance
    KPICreate, KPIUpdate, KPIResponse,
    PerformanceReviewCreate, PerformanceReviewResponse,
    # Dashboard
    HRDashboardStats
)

router = APIRouter(
    prefix="/hr",
    tags=["Human Resources"]
)


# ==================== DASHBOARD ====================

@router.get("/stats", response_model=HRDashboardStats)
async def get_hr_dashboard_stats(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get HR dashboard statistics"""
    tenant_id = current_user.tenant_id
    today = date.today()
    
    # Total employees
    total_employees = await db.scalar(
        select(func.count()).select_from(models_hr.Employee)
        .where(models_hr.Employee.tenant_id == tenant_id)
    ) or 0
    
    # Active employees
    active_employees = await db.scalar(
        select(func.count()).select_from(models_hr.Employee)
        .where(and_(
            models_hr.Employee.tenant_id == tenant_id,
            models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
        ))
    ) or 0
    
    # Present today
    present_today = await db.scalar(
        select(func.count()).select_from(models_hr.Attendance)
        .where(and_(
            models_hr.Attendance.tenant_id == tenant_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.check_in != None
        ))
    ) or 0
    
    # Late today
    late_today = await db.scalar(
        select(func.count()).select_from(models_hr.Attendance)
        .where(and_(
            models_hr.Attendance.tenant_id == tenant_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.status == models_hr.AttendanceStatus.LATE
        ))
    ) or 0
    
    # On leave today
    on_leave_today = await db.scalar(
        select(func.count()).select_from(models_hr.LeaveRequest)
        .where(and_(
            models_hr.LeaveRequest.tenant_id == tenant_id,
            models_hr.LeaveRequest.status == models_hr.LeaveStatus.APPROVED,
            models_hr.LeaveRequest.start_date <= today,
            models_hr.LeaveRequest.end_date >= today
        ))
    ) or 0
    
    # Pending leave requests
    pending_leave = await db.scalar(
        select(func.count()).select_from(models_hr.LeaveRequest)
        .where(and_(
            models_hr.LeaveRequest.tenant_id == tenant_id,
            models_hr.LeaveRequest.status == models_hr.LeaveStatus.PENDING
        ))
    ) or 0
    
    # Contracts expiring in 30 days
    expiring_contracts = await db.scalar(
        select(func.count()).select_from(models_hr.Employee)
        .where(and_(
            models_hr.Employee.tenant_id == tenant_id,
            models_hr.Employee.contract_end != None,
            models_hr.Employee.contract_end <= today + timedelta(days=30),
            models_hr.Employee.contract_end >= today
        ))
    ) or 0
    
    return HRDashboardStats(
        total_employees=total_employees,
        active_employees=active_employees,
        present_today=present_today,
        late_today=late_today,
        on_leave_today=on_leave_today,
        absent_today=active_employees - present_today - on_leave_today,
        pending_leave_requests=pending_leave,
        contracts_expiring_soon=expiring_contracts
    )


# ==================== MANAGERS ====================

@router.get("/managers")
async def list_managers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List users with MANAGER role from same tenant for department manager selection"""
    result = await db.execute(
        select(models.User).where(
            models.User.tenant_id == current_user.tenant_id,
            models.User.role.in_([models.UserRole.MANAGER, models.UserRole.ADMIN])
        ).order_by(models.User.username)
    )
    users = result.scalars().all()
    return [{"id": str(u.id), "name": u.username, "email": u.email} for u in users]


# ==================== DEPARTMENTS ====================

@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all departments"""
    result = await db.execute(
        select(models_hr.HRDepartment)
        .where(models_hr.HRDepartment.tenant_id == current_user.tenant_id)
        .order_by(models_hr.HRDepartment.name)
    )
    return result.scalars().all()


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept: DepartmentCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new department"""
    db_dept = models_hr.HRDepartment(
        tenant_id=current_user.tenant_id,
        **dept.model_dump()
    )
    db.add(db_dept)
    await db.commit()
    await db.refresh(db_dept)
    return db_dept


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    dept_update: DepartmentUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a department"""
    result = await db.execute(
        select(models_hr.HRDepartment).where(
            models_hr.HRDepartment.id == dept_id,
            models_hr.HRDepartment.tenant_id == current_user.tenant_id
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    for key, value in dept_update.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a department (soft delete)"""
    result = await db.execute(
        select(models_hr.HRDepartment).where(
            models_hr.HRDepartment.id == dept_id,
            models_hr.HRDepartment.tenant_id == current_user.tenant_id
        )
    )
    dept = result.scalars().first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if department has employees
    emp_check = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.department_id == dept_id
        ).limit(1)
    )
    if emp_check.scalars().first():
        raise HTTPException(status_code=400, detail="Cannot delete department with employees")
    
    await db.delete(dept)
    await db.commit()
    return {"message": "Department deleted successfully"}


# ==================== POSITIONS ====================

@router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    department_id: Optional[UUID] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all positions"""
    query = select(models_hr.HRPosition).where(
        models_hr.HRPosition.tenant_id == current_user.tenant_id
    )
    if department_id:
        query = query.where(models_hr.HRPosition.department_id == department_id)
    query = query.order_by(models_hr.HRPosition.level, models_hr.HRPosition.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/positions", response_model=PositionResponse)
async def create_position(
    pos: PositionCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new position"""
    db_pos = models_hr.HRPosition(
        tenant_id=current_user.tenant_id,
        **pos.model_dump()
    )
    db.add(db_pos)
    await db.commit()
    await db.refresh(db_pos)
    return db_pos


@router.put("/positions/{pos_id}", response_model=PositionResponse)
async def update_position(
    pos_id: UUID,
    pos: PositionCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a position"""
    result = await db.execute(
        select(models_hr.HRPosition).where(
            models_hr.HRPosition.id == pos_id,
            models_hr.HRPosition.tenant_id == current_user.tenant_id
        )
    )
    db_pos = result.scalars().first()
    if not db_pos:
        raise HTTPException(status_code=404, detail="Position not found")
    
    for key, value in pos.model_dump(exclude_unset=True).items():
        setattr(db_pos, key, value)
    
    await db.commit()
    await db.refresh(db_pos)
    return db_pos


@router.delete("/positions/{pos_id}")
async def delete_position(
    pos_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a position"""
    result = await db.execute(
        select(models_hr.HRPosition).where(
            models_hr.HRPosition.id == pos_id,
            models_hr.HRPosition.tenant_id == current_user.tenant_id
        )
    )
    db_pos = result.scalars().first()
    if not db_pos:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Check if position has employees
    emp_check = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.position_id == pos_id
        ).limit(1)
    )
    if emp_check.scalars().first():
        raise HTTPException(status_code=400, detail="Cannot delete position with employees")
    
    await db.delete(db_pos)
    await db.commit()
    return {"message": "Position deleted successfully"}


# ==================== EMPLOYEES ====================

@router.get("/employees", response_model=List[EmployeeListResponse])
async def list_employees(
    department_id: Optional[UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all employees with filters"""
    query = select(models_hr.Employee).where(
        models_hr.Employee.tenant_id == current_user.tenant_id
    ).options(
        selectinload(models_hr.Employee.department),
        selectinload(models_hr.Employee.position)
    )
    
    if department_id:
        query = query.where(models_hr.Employee.department_id == department_id)
    if status:
        query = query.where(models_hr.Employee.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.where(or_(
            models_hr.Employee.first_name.ilike(search_filter),
            models_hr.Employee.last_name.ilike(search_filter),
            models_hr.Employee.email.ilike(search_filter),
            models_hr.Employee.employee_code.ilike(search_filter)
        ))
    
    query = query.order_by(models_hr.Employee.first_name)
    result = await db.execute(query)
    employees = result.scalars().all()
    
    return [
        EmployeeListResponse(
            id=emp.id,
            employee_code=emp.employee_code,
            first_name=emp.first_name,
            last_name=emp.last_name,
            email=emp.email,
            phone=emp.phone,
            department_name=emp.department.name if emp.department else None,
            position_name=emp.position.name if emp.position else None,
            status=emp.status,
            profile_photo_url=emp.profile_photo_url,
            hire_date=emp.hire_date
        )
        for emp in employees
    ]


@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new employee"""
    # Generate employee code
    count = await db.scalar(
        select(func.count()).select_from(models_hr.Employee)
        .where(models_hr.Employee.tenant_id == current_user.tenant_id)
    )
    employee_code = f"EMP-{(count or 0) + 1:05d}"
    
    db_employee = models_hr.Employee(
        tenant_id=current_user.tenant_id,
        employee_code=employee_code,
        **employee.model_dump()
    )
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get employee details"""
    result = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    response = EmployeeResponse.model_validate(employee)
    response.has_face_registered = employee.face_encoding is not None
    return response


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_update: EmployeeUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an employee"""
    result = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    for key, value in employee_update.model_dump(exclude_unset=True).items():
        setattr(employee, key, value)
    
    await db.commit()
    await db.refresh(employee)
    return employee


@router.delete("/employees/{employee_id}")
async def delete_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Soft delete employee (set to TERMINATED)"""
    result = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee.status = models_hr.EmployeeStatus.TERMINATED
    employee.termination_date = date.today()
    await db.commit()
    return {"message": "Employee terminated successfully"}


# ==================== EMPLOYEE PHOTOS & DOCUMENTS ====================

@router.post("/employees/{employee_id}/upload-photo")
async def upload_employee_photo(
    employee_id: UUID,
    photo_type: str = Form(...),  # profile or id_card
    image_base64: str = Form(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Upload employee photo (profile or ID card) to Cloudinary"""
    import cloudinary
    import cloudinary.uploader
    
    result = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            f"data:image/jpeg;base64,{image_base64}",
            folder=f"hr/employees/{employee_id}",
            public_id=f"{photo_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        photo_url = upload_result.get("secure_url")
        
        if photo_type == "profile":
            employee.profile_photo_url = photo_url
        elif photo_type == "id_card":
            employee.id_card_photo_url = photo_url
        
        await db.commit()
        return {"success": True, "url": photo_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/employees/{employee_id}/documents", response_model=List[EmployeeDocumentResponse])
async def list_employee_documents(
    employee_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List employee documents"""
    result = await db.execute(
        select(models_hr.EmployeeDocument).where(
            models_hr.EmployeeDocument.employee_id == employee_id,
            models_hr.EmployeeDocument.tenant_id == current_user.tenant_id
        ).order_by(models_hr.EmployeeDocument.created_at.desc())
    )
    return result.scalars().all()


@router.post("/employees/{employee_id}/documents", response_model=EmployeeDocumentResponse)
async def add_employee_document(
    employee_id: UUID,
    doc: EmployeeDocumentCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add employee document"""
    db_doc = models_hr.EmployeeDocument(
        tenant_id=current_user.tenant_id,
        employee_id=employee_id,
        uploaded_by=current_user.id,
        **doc.model_dump()
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    return db_doc


# ==================== FACE RECOGNITION ====================

@router.post("/employees/{employee_id}/register-face")
async def register_employee_face(
    employee_id: UUID,
    request: FaceRegistrationRequest,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Register employee face encoding for attendance"""
    try:
        import face_recognition
        import numpy as np
    except ImportError:
        # Fallback if face_recognition not installed
        result = await db.execute(
            select(models_hr.Employee).where(
                models_hr.Employee.id == employee_id,
                models_hr.Employee.tenant_id == current_user.tenant_id
            )
        )
        employee = result.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Store base64 image as placeholder face encoding
        employee.face_encoding = request.face_image_base64[:500]  # Store partial as placeholder
        await db.commit()
        return {"success": True, "message": "Face registered (simplified mode)"}
    
    result = await db.execute(
        select(models_hr.Employee).where(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.face_image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        import cv2
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_image)
        if not face_encodings:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        # Store encoding as JSON
        encoding = face_encodings[0].tolist()
        employee.face_encoding = json.dumps(encoding)
        await db.commit()
        
        return {"success": True, "message": "Face registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face registration failed: {str(e)}")


# ==================== SHIFTS ====================

@router.get("/shifts", response_model=List[ShiftResponse])
async def list_shifts(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all shifts"""
    result = await db.execute(
        select(models_hr.Shift).where(
            models_hr.Shift.tenant_id == current_user.tenant_id,
            models_hr.Shift.is_active == True
        ).order_by(models_hr.Shift.start_time)
    )
    return result.scalars().all()


@router.post("/shifts", response_model=ShiftResponse)
async def create_shift(
    shift: ShiftCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new shift"""
    db_shift = models_hr.Shift(
        tenant_id=current_user.tenant_id,
        **shift.model_dump()
    )
    db.add(db_shift)
    await db.commit()
    await db.refresh(db_shift)
    return db_shift


@router.put("/shifts/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    shift_update: ShiftCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an existing shift"""
    result = await db.execute(
        select(models_hr.Shift).where(
            models_hr.Shift.id == shift_id,
            models_hr.Shift.tenant_id == current_user.tenant_id
        )
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    for key, value in shift_update.model_dump().items():
        setattr(shift, key, value)
    
    await db.commit()
    await db.refresh(shift)
    return shift


@router.delete("/shifts/{shift_id}")
async def delete_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a shift"""
    result = await db.execute(
        select(models_hr.Shift).where(
            models_hr.Shift.id == shift_id,
            models_hr.Shift.tenant_id == current_user.tenant_id
        )
    )
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    await db.delete(shift)
    await db.commit()
    return {"message": "Shift deleted successfully"}


# ==================== ATTENDANCE ====================

@router.post("/attendance/check-in", response_model=AttendanceResponse)
async def attendance_check_in(
    employee_id: UUID,
    check_in: AttendanceCheckIn,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record employee check-in"""
    today = date.today()
    now = datetime.now()
    
    # Check if already checked in today
    existing = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        ))
    )
    attendance = existing.scalar_one_or_none()
    
    if attendance and attendance.check_in:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Get employee's scheduled shift
    schedule_result = await db.execute(
        select(models_hr.EmployeeSchedule).where(and_(
            models_hr.EmployeeSchedule.employee_id == employee_id,
            models_hr.EmployeeSchedule.date == today
        )).options(selectinload(models_hr.EmployeeSchedule.shift))
    )
    schedule = schedule_result.scalar_one_or_none()
    
    # Calculate late minutes
    late_minutes = 0
    if schedule and schedule.shift:
        shift_start = datetime.combine(today, schedule.shift.start_time)
        tolerance = schedule.shift.late_tolerance_minutes or 0
        if now > shift_start + timedelta(minutes=tolerance):
            late_minutes = int((now - shift_start).total_seconds() / 60)
    
    # Upload check-in photo if provided
    photo_url = None
    if check_in.face_image_base64:
        try:
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{check_in.face_image_base64}",
                folder=f"hr/attendance/{today.isoformat()}",
                public_id=f"checkin_{employee_id}_{now.strftime('%H%M%S')}"
            )
            photo_url = upload_result.get("secure_url")
        except:
            pass
    
    if not attendance:
        attendance = models_hr.Attendance(
            tenant_id=current_user.tenant_id,
            employee_id=employee_id,
            date=today,
            shift_id=schedule.shift_id if schedule else None
        )
        db.add(attendance)
    
    attendance.check_in = now
    attendance.check_in_method = check_in.method
    attendance.check_in_photo_url = photo_url
    attendance.check_in_location = check_in.location
    attendance.check_in_device = check_in.device
    attendance.late_minutes = late_minutes
    attendance.status = models_hr.AttendanceStatus.LATE if late_minutes > 0 else models_hr.AttendanceStatus.PRESENT
    attendance.notes = check_in.notes
    
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/attendance/check-out", response_model=AttendanceResponse)
async def attendance_check_out(
    employee_id: UUID,
    check_out: AttendanceCheckOut,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record employee check-out"""
    today = date.today()
    now = datetime.now()
    
    result = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        )).options(selectinload(models_hr.Attendance.shift))
    )
    attendance = result.scalar_one_or_none()
    
    if not attendance or not attendance.check_in:
        raise HTTPException(status_code=400, detail="Must check in first")
    
    if attendance.check_out:
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Calculate work hours and overtime
    check_in_time = attendance.check_in
    work_seconds = (now - check_in_time).total_seconds()
    work_hours = work_seconds / 3600
    
    overtime_minutes = 0
    if attendance.shift:
        shift_end = datetime.combine(today, attendance.shift.end_time)
        if now > shift_end:
            overtime_minutes = int((now - shift_end).total_seconds() / 60)
    
    # Upload check-out photo
    photo_url = None
    if check_out.face_image_base64:
        try:
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{check_out.face_image_base64}",
                folder=f"hr/attendance/{today.isoformat()}",
                public_id=f"checkout_{employee_id}_{now.strftime('%H%M%S')}"
            )
            photo_url = upload_result.get("secure_url")
        except:
            pass
    
    attendance.check_out = now
    attendance.check_out_method = check_out.method
    attendance.check_out_photo_url = photo_url
    attendance.check_out_location = check_out.location
    attendance.work_hours = round(work_hours, 2)
    attendance.overtime_minutes = overtime_minutes
    
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/attendance/face-check-in", response_model=FaceCheckInResponse)
async def face_attendance_check_in(
    request: FaceCheckInRequest,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-in using face recognition"""
    try:
        import face_recognition
        import numpy as np
    except ImportError:
        raise HTTPException(status_code=501, detail="Face recognition not available")
    
    try:
        # Decode and process image
        image_data = base64.b64decode(request.face_image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        import cv2
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get face encoding from image
        face_encodings = face_recognition.face_encodings(rgb_image)
        if not face_encodings:
            return FaceCheckInResponse(success=False, message="No face detected")
        
        unknown_encoding = face_encodings[0]
        
        # Get all employees with registered faces
        result = await db.execute(
            select(models_hr.Employee).where(and_(
                models_hr.Employee.tenant_id == current_user.tenant_id,
                models_hr.Employee.face_encoding != None,
                models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
            ))
        )
        employees = result.scalars().all()
        
        # Compare faces
        for emp in employees:
            try:
                known_encoding = np.array(json.loads(emp.face_encoding))
                match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
                if match[0]:
                    # Found match - record attendance
                    check_in_data = AttendanceCheckIn(
                        method=models_hr.CheckInMethod.FACE,
                        face_image_base64=request.face_image_base64,
                        location=request.location,
                        device=request.device
                    )
                    attendance = await attendance_check_in(emp.id, check_in_data, db, current_user)
                    
                    return FaceCheckInResponse(
                        success=True,
                        message=f"Welcome, {emp.first_name}!",
                        employee_id=emp.id,
                        employee_name=f"{emp.first_name} {emp.last_name}",
                        check_in_time=attendance.check_in,
                        photo_url=attendance.check_in_photo_url
                    )
            except:
                continue
        
        return FaceCheckInResponse(success=False, message="Face not recognized")
    except Exception as e:
        return FaceCheckInResponse(success=False, message=str(e))


@router.get("/attendance", response_model=List[AttendanceResponse])
async def list_attendance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List attendance records"""
    query = select(models_hr.Attendance).where(
        models_hr.Attendance.tenant_id == current_user.tenant_id
    ).options(selectinload(models_hr.Attendance.employee))
    
    if start_date:
        query = query.where(models_hr.Attendance.date >= start_date)
    if end_date:
        query = query.where(models_hr.Attendance.date <= end_date)
    if employee_id:
        query = query.where(models_hr.Attendance.employee_id == employee_id)
    if department_id:
        query = query.where(models_hr.Attendance.employee.has(department_id=department_id))
    
    query = query.order_by(models_hr.Attendance.date.desc(), models_hr.Attendance.check_in.desc())
    result = await db.execute(query)
    attendances = result.scalars().all()
    
    return [
        AttendanceResponse(
            id=att.id,
            employee_id=att.employee_id,
            employee_name=f"{att.employee.first_name} {att.employee.last_name}" if att.employee else None,
            date=att.date,
            check_in=att.check_in,
            check_out=att.check_out,
            check_in_method=att.check_in_method,
            check_out_method=att.check_out_method,
            status=att.status.value if att.status else None,
            late_minutes=att.late_minutes or 0,
            overtime_minutes=att.overtime_minutes or 0,
            work_hours=att.work_hours or 0,
            check_in_photo_url=att.check_in_photo_url,
            check_out_photo_url=att.check_out_photo_url
        )
        for att in attendances
    ]


@router.post("/attendance/simple-face-check-in")
async def simple_face_check_in(
    employee_id: UUID = Query(...),
    face_image_base64: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-in using face recognition matched client-side (for when face_recognition lib not available)"""
    today = date.today()
    now = datetime.now()
    
    # Verify employee exists
    result = await db.execute(
        select(models_hr.Employee).where(and_(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        ))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        return {"success": False, "message": "Employee not found"}
    
    # Check if already checked in today
    existing = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        ))
    )
    attendance = existing.scalar_one_or_none()
    if attendance and attendance.check_in:
        return {"success": False, "message": "Already checked in today"}
    
    # Upload photo if provided
    photo_url = None
    if face_image_base64:
        try:
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{face_image_base64}",
                folder=f"hr/attendance/{today.isoformat()}",
                public_id=f"checkin_{employee_id}_{now.strftime('%H%M%S')}"
            )
            photo_url = upload_result.get("secure_url")
        except:
            pass
    
    if not attendance:
        attendance = models_hr.Attendance(
            tenant_id=current_user.tenant_id,
            employee_id=employee_id,
            date=today
        )
        db.add(attendance)
    
    attendance.check_in = now
    attendance.check_in_method = models_hr.CheckInMethod.FACE
    attendance.check_in_photo_url = photo_url
    attendance.status = models_hr.AttendanceStatus.PRESENT
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Welcome, {employee.first_name}!",
        "employee": {
            "id": str(employee.id),
            "first_name": employee.first_name,
            "last_name": employee.last_name
        },
        "check_in_time": now.isoformat()
    }


@router.post("/attendance/simple-face-check-out")
async def simple_face_check_out(
    employee_id: UUID = Query(...),
    face_image_base64: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-out using face recognition matched client-side"""
    today = date.today()
    now = datetime.now()
    
    # Verify employee
    result = await db.execute(
        select(models_hr.Employee).where(and_(
            models_hr.Employee.id == employee_id,
            models_hr.Employee.tenant_id == current_user.tenant_id
        ))
    )
    employee = result.scalar_one_or_none()
    if not employee:
        return {"success": False, "message": "Employee not found"}
    
    # Get today's attendance
    existing = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee_id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        ))
    )
    attendance = existing.scalar_one_or_none()
    
    if not attendance or not attendance.check_in:
        return {"success": False, "message": "Must check in first"}
    if attendance.check_out:
        return {"success": False, "message": "Already checked out today"}
    
    # Upload photo if provided
    photo_url = None
    if face_image_base64:
        try:
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{face_image_base64}",
                folder=f"hr/attendance/{today.isoformat()}",
                public_id=f"checkout_{employee_id}_{now.strftime('%H%M%S')}"
            )
            photo_url = upload_result.get("secure_url")
        except:
            pass
    
    # Calculate work hours
    work_seconds = (now - attendance.check_in).total_seconds()
    work_hours = work_seconds / 3600
    
    attendance.check_out = now
    attendance.check_out_method = models_hr.CheckInMethod.FACE
    attendance.check_out_photo_url = photo_url
    attendance.work_hours = round(work_hours, 2)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Goodbye, {employee.first_name}!",
        "employee": {
            "id": str(employee.id),
            "first_name": employee.first_name,
            "last_name": employee.last_name
        },
        "work_hours": round(work_hours, 2)
    }


@router.post("/attendance/fingerprint-check-in")
async def fingerprint_check_in(
    fingerprint_id: str = Form(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-in using fingerprint"""
    # Find employee by fingerprint_id
    result = await db.execute(
        select(models_hr.Employee).where(and_(
            models_hr.Employee.tenant_id == current_user.tenant_id,
            models_hr.Employee.fingerprint_id == fingerprint_id,
            models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
        ))
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        return {"success": False, "message": "Fingerprint not recognized"}
    
    # Record attendance
    today = date.today()
    now = datetime.now()
    
    existing = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee.id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        ))
    )
    attendance = existing.scalar_one_or_none()
    
    if attendance and attendance.check_in:
        return {"success": False, "message": "Already checked in today"}
    
    if not attendance:
        attendance = models_hr.Attendance(
            tenant_id=current_user.tenant_id,
            employee_id=employee.id,
            date=today
        )
        db.add(attendance)
    
    attendance.check_in = now
    attendance.check_in_method = models_hr.CheckInMethod.FINGERPRINT
    attendance.status = models_hr.AttendanceStatus.PRESENT
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Welcome, {employee.first_name}!",
        "employee": {
            "id": str(employee.id),
            "first_name": employee.first_name,
            "last_name": employee.last_name
        }
    }


@router.post("/attendance/fingerprint-check-out")
async def fingerprint_check_out(
    fingerprint_id: str = Form(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-out using fingerprint"""
    result = await db.execute(
        select(models_hr.Employee).where(and_(
            models_hr.Employee.tenant_id == current_user.tenant_id,
            models_hr.Employee.fingerprint_id == fingerprint_id,
            models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
        ))
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        return {"success": False, "message": "Fingerprint not recognized"}
    
    today = date.today()
    now = datetime.now()
    
    result = await db.execute(
        select(models_hr.Attendance).where(and_(
            models_hr.Attendance.employee_id == employee.id,
            models_hr.Attendance.date == today,
            models_hr.Attendance.tenant_id == current_user.tenant_id
        ))
    )
    attendance = result.scalar_one_or_none()
    
    if not attendance or not attendance.check_in:
        return {"success": False, "message": "Must check in first"}
    
    if attendance.check_out:
        return {"success": False, "message": "Already checked out today"}
    
    # Calculate work hours
    work_seconds = (now - attendance.check_in).total_seconds()
    work_hours = work_seconds / 3600
    
    attendance.check_out = now
    attendance.check_out_method = models_hr.CheckInMethod.FINGERPRINT
    attendance.work_hours = round(work_hours, 2)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Goodbye, {employee.first_name}!",
        "employee": {
            "id": str(employee.id),
            "first_name": employee.first_name,
            "last_name": employee.last_name
        }
    }


@router.post("/attendance/face-check-out", response_model=FaceCheckInResponse)
async def face_attendance_check_out(
    request: FaceCheckInRequest,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check-out using face recognition"""
    try:
        import face_recognition
        import numpy as np
    except ImportError:
        raise HTTPException(status_code=501, detail="Face recognition not available")
    
    try:
        image_data = base64.b64decode(request.face_image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        import cv2
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        face_encodings = face_recognition.face_encodings(rgb_image)
        if not face_encodings:
            return FaceCheckInResponse(success=False, message="No face detected")
        
        unknown_encoding = face_encodings[0]
        
        result = await db.execute(
            select(models_hr.Employee).where(and_(
                models_hr.Employee.tenant_id == current_user.tenant_id,
                models_hr.Employee.face_encoding != None,
                models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
            ))
        )
        employees = result.scalars().all()
        
        for emp in employees:
            try:
                known_encoding = np.array(json.loads(emp.face_encoding))
                match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
                if match[0]:
                    check_out_data = AttendanceCheckOut(
                        method=models_hr.CheckInMethod.FACE,
                        face_image_base64=request.face_image_base64,
                        location=request.location
                    )
                    attendance = await attendance_check_out(emp.id, check_out_data, db, current_user)
                    
                    return FaceCheckInResponse(
                        success=True,
                        message=f"Goodbye, {emp.first_name}!",
                        employee_id=emp.id,
                        employee_name=f"{emp.first_name} {emp.last_name}",
                        check_in_time=attendance.check_out,
                        photo_url=attendance.check_out_photo_url
                    )
            except:
                continue
        
        return FaceCheckInResponse(success=False, message="Face not recognized")
    except Exception as e:
        return FaceCheckInResponse(success=False, message=str(e))


# ==================== LEAVE ====================

@router.get("/leave-types", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List leave types"""
    result = await db.execute(
        select(models_hr.LeaveType).where(
            models_hr.LeaveType.tenant_id == current_user.tenant_id,
            models_hr.LeaveType.is_active == True
        )
    )
    return result.scalars().all()


@router.post("/leave-types", response_model=LeaveTypeResponse)
async def create_leave_type(
    leave_type: LeaveTypeCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a leave type"""
    db_leave_type = models_hr.LeaveType(
        tenant_id=current_user.tenant_id,
        **leave_type.model_dump()
    )
    db.add(db_leave_type)
    await db.commit()
    await db.refresh(db_leave_type)
    return db_leave_type


@router.put("/leave-types/{leave_type_id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    leave_type_id: UUID,
    leave_type_update: LeaveTypeCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a leave type"""
    result = await db.execute(
        select(models_hr.LeaveType).where(
            models_hr.LeaveType.id == leave_type_id,
            models_hr.LeaveType.tenant_id == current_user.tenant_id
        )
    )
    leave_type = result.scalar_one_or_none()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    for key, value in leave_type_update.model_dump().items():
        setattr(leave_type, key, value)
    
    await db.commit()
    await db.refresh(leave_type)
    return leave_type


@router.delete("/leave-types/{leave_type_id}")
async def delete_leave_type(
    leave_type_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a leave type"""
    result = await db.execute(
        select(models_hr.LeaveType).where(
            models_hr.LeaveType.id == leave_type_id,
            models_hr.LeaveType.tenant_id == current_user.tenant_id
        )
    )
    leave_type = result.scalar_one_or_none()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    # Soft delete - just deactivate
    leave_type.is_active = False
    await db.commit()
    return {"message": "Leave type deleted successfully"}


@router.post("/leave/request", response_model=LeaveRequestResponse)
async def create_leave_request(
    employee_id: UUID,
    request: LeaveRequestCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Submit a leave request"""
    # Calculate total days
    total_days = (request.end_date - request.start_date).days + 1
    
    # Check balance
    current_year = date.today().year
    balance_result = await db.execute(
        select(models_hr.LeaveBalance).where(and_(
            models_hr.LeaveBalance.employee_id == employee_id,
            models_hr.LeaveBalance.leave_type_id == request.leave_type_id,
            models_hr.LeaveBalance.year == current_year
        ))
    )
    balance = balance_result.scalar_one_or_none()
    
    if balance:
        remaining = balance.quota + balance.carried_forward - balance.used
        if total_days > remaining:
            raise HTTPException(status_code=400, detail=f"Insufficient leave balance. Remaining: {remaining} days")
    
    db_request = models_hr.LeaveRequest(
        tenant_id=current_user.tenant_id,
        employee_id=employee_id,
        leave_type_id=request.leave_type_id,
        start_date=request.start_date,
        end_date=request.end_date,
        total_days=total_days,
        reason=request.reason,
        attachment_url=request.attachment_url,
        status=models_hr.LeaveStatus.PENDING
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request


@router.put("/leave/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: UUID,
    approval: LeaveRequestApproval,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Approve or reject a leave request"""
    result = await db.execute(
        select(models_hr.LeaveRequest).where(
            models_hr.LeaveRequest.id == request_id,
            models_hr.LeaveRequest.tenant_id == current_user.tenant_id
        )
    )
    leave_request = result.scalar_one_or_none()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status != models_hr.LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    if approval.approved:
        leave_request.status = models_hr.LeaveStatus.APPROVED
        
        # Update balance
        current_year = date.today().year
        balance_result = await db.execute(
            select(models_hr.LeaveBalance).where(and_(
                models_hr.LeaveBalance.employee_id == leave_request.employee_id,
                models_hr.LeaveBalance.leave_type_id == leave_request.leave_type_id,
                models_hr.LeaveBalance.year == current_year
            ))
        )
        balance = balance_result.scalar_one_or_none()
        if balance:
            balance.used += leave_request.total_days
    else:
        leave_request.status = models_hr.LeaveStatus.REJECTED
        leave_request.rejection_reason = approval.rejection_reason
    
    leave_request.approver_id = current_user.id
    leave_request.approved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(leave_request)
    return leave_request


@router.get("/leave/requests", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    employee_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List leave requests"""
    query = select(models_hr.LeaveRequest).where(
        models_hr.LeaveRequest.tenant_id == current_user.tenant_id
    ).options(
        selectinload(models_hr.LeaveRequest.employee),
        selectinload(models_hr.LeaveRequest.leave_type)
    )
    
    if employee_id:
        query = query.where(models_hr.LeaveRequest.employee_id == employee_id)
    if status:
        query = query.where(models_hr.LeaveRequest.status == status)
    
    query = query.order_by(models_hr.LeaveRequest.created_at.desc())
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        LeaveRequestResponse(
            id=req.id,
            employee_id=req.employee_id,
            employee_name=f"{req.employee.first_name} {req.employee.last_name}" if req.employee else None,
            leave_type_id=req.leave_type_id,
            leave_type_name=req.leave_type.name if req.leave_type else None,
            start_date=req.start_date,
            end_date=req.end_date,
            total_days=req.total_days,
            reason=req.reason,
            status=req.status,
            approver_id=req.approver_id,
            approved_at=req.approved_at,
            rejection_reason=req.rejection_reason,
            created_at=req.created_at
        )
        for req in requests
    ]


@router.get("/leave/balance/{employee_id}", response_model=List[LeaveBalanceResponse])
async def get_leave_balance(
    employee_id: UUID,
    year: Optional[int] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get employee leave balance"""
    current_year = year or date.today().year
    
    result = await db.execute(
        select(models_hr.LeaveBalance).where(and_(
            models_hr.LeaveBalance.employee_id == employee_id,
            models_hr.LeaveBalance.year == current_year,
            models_hr.LeaveBalance.tenant_id == current_user.tenant_id
        )).options(selectinload(models_hr.LeaveBalance.leave_type))
    )
    balances = result.scalars().all()
    
    return [
        LeaveBalanceResponse(
            leave_type_id=bal.leave_type_id,
            leave_type_name=bal.leave_type.name if bal.leave_type else "Unknown",
            year=bal.year,
            quota=bal.quota,
            used=bal.used,
            remaining=bal.quota + bal.carried_forward - bal.used
        )
        for bal in balances
    ]


# ==================== PAYROLL ====================

@router.get("/payroll/periods", response_model=List[PayrollPeriodResponse])
async def list_payroll_periods(
    year: Optional[int] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List payroll periods"""
    query = select(models_hr.PayrollPeriod).where(
        models_hr.PayrollPeriod.tenant_id == current_user.tenant_id
    )
    if year:
        query = query.where(models_hr.PayrollPeriod.period_year == year)
    query = query.order_by(models_hr.PayrollPeriod.start_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/payroll/periods", response_model=PayrollPeriodResponse)
async def create_payroll_period(
    period: PayrollPeriodCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a payroll period"""
    db_period = models_hr.PayrollPeriod(
        tenant_id=current_user.tenant_id,
        **period.model_dump()
    )
    db.add(db_period)
    await db.commit()
    await db.refresh(db_period)
    return db_period


@router.post("/payroll/run/{period_id}", response_model=PayrollRunResponse)
async def run_payroll(
    period_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Execute payroll calculation for a period"""
    period = await db.get(models_hr.PayrollPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    if period.is_closed:
        raise HTTPException(status_code=400, detail="Period already closed")
    
    # Create payroll run
    payroll_run = models_hr.PayrollRun(
        tenant_id=current_user.tenant_id,
        payroll_period_id=period.id,
        run_by=current_user.id,
        status=models_hr.PayrollStatus.CALCULATED
    )
    db.add(payroll_run)
    await db.flush()
    
    # Get active employees
    result = await db.execute(
        select(models_hr.Employee).where(and_(
            models_hr.Employee.tenant_id == current_user.tenant_id,
            models_hr.Employee.status == models_hr.EmployeeStatus.ACTIVE
        ))
    )
    employees = result.scalars().all()
    
    total_gross = 0.0
    total_deductions = 0.0
    total_net = 0.0
    
    for emp in employees:
        # Calculate salary components
        base_salary = emp.base_salary or 0
        
        # Calculate overtime from attendance
        overtime_result = await db.execute(
            select(func.sum(models_hr.Attendance.overtime_minutes)).where(and_(
                models_hr.Attendance.employee_id == emp.id,
                models_hr.Attendance.date >= period.start_date,
                models_hr.Attendance.date <= period.end_date
            ))
        )
        overtime_minutes = overtime_result.scalar() or 0
        hourly_rate = base_salary / 173  # Monthly hours
        overtime_pay = (overtime_minutes / 60) * hourly_rate * 1.5
        
        gross_pay = base_salary + overtime_pay
        
        # Deductions
        tax_rate = 0.05  # 5% simplified tax
        tax_deduction = gross_pay * tax_rate
        bpjs_kes = base_salary * 0.01  # 1%
        bpjs_tk = base_salary * 0.02  # 2%
        total_ded = tax_deduction + bpjs_kes + bpjs_tk
        
        net_pay = gross_pay - total_ded
        
        payslip = models_hr.Payslip(
            tenant_id=current_user.tenant_id,
            payroll_run_id=payroll_run.id,
            employee_id=emp.id,
            base_salary=base_salary,
            overtime_pay=round(overtime_pay, 2),
            gross_pay=round(gross_pay, 2),
            tax_deduction=round(tax_deduction, 2),
            bpjs_kes_deduction=round(bpjs_kes, 2),
            bpjs_tk_deduction=round(bpjs_tk, 2),
            total_deductions=round(total_ded, 2),
            net_pay=round(net_pay, 2)
        )
        db.add(payslip)
        
        total_gross += gross_pay
        total_deductions += total_ded
        total_net += net_pay
    
    payroll_run.total_employees = len(employees)
    payroll_run.total_gross = round(total_gross, 2)
    payroll_run.total_deductions = round(total_deductions, 2)
    payroll_run.total_net = round(total_net, 2)
    
    await db.commit()
    await db.refresh(payroll_run)
    return payroll_run


@router.get("/payslips/{employee_id}", response_model=List[PayslipResponse])
async def get_employee_payslips(
    employee_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get employee payslips"""
    result = await db.execute(
        select(models_hr.Payslip).where(
            models_hr.Payslip.employee_id == employee_id,
            models_hr.Payslip.tenant_id == current_user.tenant_id
        ).order_by(models_hr.Payslip.created_at.desc())
    )
    return result.scalars().all()


# ==================== CAMERAS ====================

@router.get("/cameras", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List office cameras"""
    result = await db.execute(
        select(models_hr.OfficeCamera).where(
            models_hr.OfficeCamera.tenant_id == current_user.tenant_id
        )
    )
    return result.scalars().all()


@router.post("/cameras", response_model=CameraResponse)
async def create_camera(
    camera: CameraCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a new camera"""
    db_camera = models_hr.OfficeCamera(
        tenant_id=current_user.tenant_id,
        **camera.model_dump()
    )
    db.add(db_camera)
    await db.commit()
    await db.refresh(db_camera)
    return db_camera


@router.put("/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: UUID,
    camera_update: CameraUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update camera settings"""
    result = await db.execute(
        select(models_hr.OfficeCamera).where(
            models_hr.OfficeCamera.id == camera_id,
            models_hr.OfficeCamera.tenant_id == current_user.tenant_id
        )
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    for key, value in camera_update.model_dump(exclude_unset=True).items():
        setattr(camera, key, value)
    
    await db.commit()
    await db.refresh(camera)
    return camera


@router.delete("/cameras/{camera_id}")
async def delete_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a camera"""
    result = await db.execute(
        select(models_hr.OfficeCamera).where(
            models_hr.OfficeCamera.id == camera_id,
            models_hr.OfficeCamera.tenant_id == current_user.tenant_id
        )
    )
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    await db.delete(camera)
    await db.commit()
    return {"message": "Camera deleted successfully"}


@router.get("/camera-activities", response_model=List[CameraActivityResponse])
async def list_camera_activities(
    camera_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get camera activity logs"""
    query = select(models_hr.CameraActivity).where(
        models_hr.CameraActivity.tenant_id == current_user.tenant_id
    ).options(selectinload(models_hr.CameraActivity.camera))
    
    if camera_id:
        query = query.where(models_hr.CameraActivity.camera_id == camera_id)
    if start_date:
        query = query.where(models_hr.CameraActivity.timestamp >= start_date)
    if end_date:
        query = query.where(models_hr.CameraActivity.timestamp <= end_date)
    
    query = query.order_by(models_hr.CameraActivity.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return [
        CameraActivityResponse(
            id=act.id,
            camera_id=act.camera_id,
            camera_name=act.camera.name if act.camera else None,
            timestamp=act.timestamp,
            activity_type=act.activity_type.value if act.activity_type else None,
            employee_detected_id=act.employee_detected_id,
            people_count=act.people_count or 0,
            snapshot_url=act.snapshot_url
        )
        for act in activities
    ]


# ==================== KPI & PERFORMANCE ====================

@router.get("/kpi", response_model=List[KPIResponse])
async def list_kpis(
    employee_id: Optional[UUID] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List KPIs"""
    query = select(models_hr.KPI).where(
        models_hr.KPI.tenant_id == current_user.tenant_id
    )
    if employee_id:
        query = query.where(models_hr.KPI.employee_id == employee_id)
    if year:
        query = query.where(models_hr.KPI.period_year == year)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/kpi", response_model=KPIResponse)
async def create_kpi(
    kpi: KPICreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a KPI"""
    db_kpi = models_hr.KPI(
        tenant_id=current_user.tenant_id,
        **kpi.model_dump()
    )
    db.add(db_kpi)
    await db.commit()
    await db.refresh(db_kpi)
    return db_kpi


@router.put("/kpi/{kpi_id}", response_model=KPIResponse)
async def update_kpi(
    kpi_id: UUID,
    kpi_update: KPIUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update KPI (set actual value)"""
    result = await db.execute(
        select(models_hr.KPI).where(
            models_hr.KPI.id == kpi_id,
            models_hr.KPI.tenant_id == current_user.tenant_id
        )
    )
    kpi = result.scalar_one_or_none()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    
    for key, value in kpi_update.model_dump(exclude_unset=True).items():
        setattr(kpi, key, value)
    
    # Calculate score if actual value is set
    if kpi.actual_value is not None and kpi.target_value:
        kpi.score = min((kpi.actual_value / kpi.target_value) * 100, 100)
    
    await db.commit()
    await db.refresh(kpi)
    return kpi


@router.get("/performance-reviews", response_model=List[PerformanceReviewResponse])
async def list_performance_reviews(
    employee_id: Optional[UUID] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List performance reviews"""
    query = select(models_hr.PerformanceReview).where(
        models_hr.PerformanceReview.tenant_id == current_user.tenant_id
    )
    if employee_id:
        query = query.where(models_hr.PerformanceReview.employee_id == employee_id)
    if year:
        query = query.where(models_hr.PerformanceReview.period_year == year)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/performance-reviews", response_model=PerformanceReviewResponse)
async def create_performance_review(
    review: PerformanceReviewCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a performance review"""
    db_review = models_hr.PerformanceReview(
        tenant_id=current_user.tenant_id,
        reviewer_id=current_user.id,
        **review.model_dump()
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review
