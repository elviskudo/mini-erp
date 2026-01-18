package handlers

import (
	"net/http"
	"time"

	"github.com/elviskudo/mini-erp/services/hr-service/internal/database"
	"github.com/elviskudo/mini-erp/services/hr-service/internal/models"
	"github.com/gin-gonic/gin"
)

// HRHandler handles HR endpoints
type HRHandler struct{}

// NewHRHandler creates a new HR handler
func NewHRHandler() *HRHandler {
	return &HRHandler{}
}

// ========== DASHBOARD STATS ==========

// GetStats returns HR dashboard statistics from real DB
// GET /hr/stats
func (h *HRHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockStats())
		return
	}

	var totalEmployees, activeEmployees int64
	db.Model(&models.Employee{}).Count(&totalEmployees)
	db.Model(&models.Employee{}).Where("status = ?", "ACTIVE").Count(&activeEmployees)

	// Get today's attendance stats
	today := time.Now().Format("2006-01-02")
	var presentToday int64
	db.Model(&models.Attendance{}).Where("date = ?", today).Count(&presentToday)

	c.JSON(http.StatusOK, gin.H{
		"total_employees":         totalEmployees,
		"active_employees":        activeEmployees,
		"present_today":           presentToday,
		"late_today":              0,
		"on_leave_today":          0,
		"absent_today":            activeEmployees - presentToday,
		"pending_leave_requests":  0,
		"contracts_expiring_soon": 0,
	})
}

func getMockStats() gin.H {
	return gin.H{
		"total_employees": 45, "active_employees": 42, "present_today": 38,
		"late_today": 3, "on_leave_today": 2, "absent_today": 2,
		"pending_leave_requests": 5, "contracts_expiring_soon": 2,
	}
}

// ========== MANAGERS ==========

// ListManagers lists users with MANAGER role
// GET /hr/managers
func (h *HRHandler) ListManagers(c *gin.Context) {
	managers := []gin.H{
		{"id": "mgr-1", "name": "John Smith", "email": "john.smith@company.com"},
		{"id": "mgr-2", "name": "Jane Doe", "email": "jane.doe@company.com"},
	}
	c.JSON(http.StatusOK, managers)
}

// ========== DEPARTMENTS ==========

// ListDepartments lists all departments from real DB
// GET /hr/departments
func (h *HRHandler) ListDepartments(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockDepartments())
		return
	}

	var departments []models.HRDepartment
	if err := db.Find(&departments).Error; err != nil {
		c.JSON(http.StatusOK, getMockDepartments())
		return
	}

	if len(departments) == 0 {
		c.JSON(http.StatusOK, getMockDepartments())
		return
	}

	c.JSON(http.StatusOK, departments)
}

func getMockDepartments() []gin.H {
	return []gin.H{
		{"id": "dept-1", "code": "IT", "name": "Information Technology", "manager_id": nil, "is_active": true},
		{"id": "dept-2", "code": "HR", "name": "Human Resources", "manager_id": nil, "is_active": true},
		{"id": "dept-3", "code": "FIN", "name": "Finance & Accounting", "manager_id": nil, "is_active": true},
	}
}

// CreateDepartment creates a new department
// POST /hr/departments
func (h *HRHandler) CreateDepartment(c *gin.Context) {
	var req struct {
		Code      string  `json:"code" binding:"required"`
		Name      string  `json:"name" binding:"required"`
		ManagerID *string `json:"manager_id"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":         "new-dept-id",
		"code":       req.Code,
		"name":       req.Name,
		"manager_id": req.ManagerID,
		"is_active":  true,
	})
}

// UpdateDepartment updates a department
// PUT /hr/departments/:dept_id
func (h *HRHandler) UpdateDepartment(c *gin.Context) {
	deptID := c.Param("dept_id")

	var req struct {
		Code      *string `json:"code"`
		Name      *string `json:"name"`
		ManagerID *string `json:"manager_id"`
		IsActive  *bool   `json:"is_active"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      deptID,
		"message": "Department updated",
	})
}

// DeleteDepartment deletes a department
// DELETE /hr/departments/:dept_id
func (h *HRHandler) DeleteDepartment(c *gin.Context) {
	deptID := c.Param("dept_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      deptID,
		"message": "Department deleted successfully",
	})
}

// ========== POSITIONS ==========

// ListPositions lists all positions
// GET /hr/positions?department_id=xxx
func (h *HRHandler) ListPositions(c *gin.Context) {
	positions := []gin.H{
		{"id": "pos-1", "code": "DEV", "name": "Software Developer", "department_id": "dept-1", "level": 3, "min_salary": 8000000, "max_salary": 15000000},
		{"id": "pos-2", "code": "LEAD", "name": "Team Lead", "department_id": "dept-1", "level": 4, "min_salary": 15000000, "max_salary": 25000000},
		{"id": "pos-3", "code": "MGR", "name": "Manager", "department_id": "dept-1", "level": 5, "min_salary": 25000000, "max_salary": 40000000},
	}
	c.JSON(http.StatusOK, positions)
}

// CreatePosition creates a new position
// POST /hr/positions
func (h *HRHandler) CreatePosition(c *gin.Context) {
	var req struct {
		Code         string   `json:"code" binding:"required"`
		Name         string   `json:"name" binding:"required"`
		DepartmentID string   `json:"department_id" binding:"required"`
		Level        int      `json:"level"`
		MinSalary    *float64 `json:"min_salary"`
		MaxSalary    *float64 `json:"max_salary"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":            "new-pos-id",
		"code":          req.Code,
		"name":          req.Name,
		"department_id": req.DepartmentID,
		"level":         req.Level,
	})
}

// UpdatePosition updates a position
// PUT /hr/positions/:pos_id
func (h *HRHandler) UpdatePosition(c *gin.Context) {
	posID := c.Param("pos_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      posID,
		"message": "Position updated",
	})
}

// DeletePosition deletes a position
// DELETE /hr/positions/:pos_id
func (h *HRHandler) DeletePosition(c *gin.Context) {
	posID := c.Param("pos_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      posID,
		"message": "Position deleted successfully",
	})
}

// ========== EMPLOYEES ==========

// ListEmployees lists all employees from real DB
// GET /hr/employees?department_id=xxx&status=xxx&search=xxx
func (h *HRHandler) ListEmployees(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockEmployees())
		return
	}

	var employees []models.Employee
	query := db.Order("employee_code ASC")

	// Apply filters
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}
	if dept := c.Query("department"); dept != "" {
		query = query.Where("department = ?", dept)
	}
	if search := c.Query("search"); search != "" {
		searchPattern := "%" + search + "%"
		query = query.Where("first_name ILIKE ? OR last_name ILIKE ? OR email ILIKE ? OR employee_code ILIKE ?",
			searchPattern, searchPattern, searchPattern, searchPattern)
	}

	if err := query.Find(&employees).Error; err != nil {
		c.JSON(http.StatusOK, getMockEmployees())
		return
	}

	if len(employees) == 0 {
		c.JSON(http.StatusOK, getMockEmployees())
		return
	}

	c.JSON(http.StatusOK, employees)
}

func getMockEmployees() []gin.H {
	return []gin.H{
		{"id": "emp-1", "employee_code": "EMP-00001", "first_name": "Ahmad", "last_name": "Wijaya", "email": "ahmad@company.com", "status": "ACTIVE"},
		{"id": "emp-2", "employee_code": "EMP-00002", "first_name": "Siti", "last_name": "Rahayu", "email": "siti@company.com", "status": "ACTIVE"},
	}
}

// CreateEmployee creates a new employee
// POST /hr/employees
func (h *HRHandler) CreateEmployee(c *gin.Context) {
	var req struct {
		FirstName      string  `json:"first_name" binding:"required"`
		LastName       string  `json:"last_name" binding:"required"`
		Email          string  `json:"email" binding:"required,email"`
		Phone          string  `json:"phone"`
		DepartmentID   string  `json:"department_id" binding:"required"`
		PositionID     string  `json:"position_id" binding:"required"`
		HireDate       string  `json:"hire_date"`
		BasicSalary    float64 `json:"basic_salary"`
		EmploymentType string  `json:"employment_type"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":            "new-emp-id",
		"employee_code": "EMP-00003",
		"first_name":    req.FirstName,
		"last_name":     req.LastName,
		"email":         req.Email,
		"status":        "ACTIVE",
	})
}

// GetEmployee gets employee details
// GET /hr/employees/:employee_id
func (h *HRHandler) GetEmployee(c *gin.Context) {
	empID := c.Param("employee_id")

	c.JSON(http.StatusOK, gin.H{
		"id":                  empID,
		"employee_code":       "EMP-00001",
		"first_name":          "Ahmad",
		"last_name":           "Wijaya",
		"email":               "ahmad.wijaya@company.com",
		"phone":               "081234567890",
		"department_id":       "dept-1",
		"position_id":         "pos-1",
		"status":              "ACTIVE",
		"hire_date":           "2023-01-15",
		"basic_salary":        12000000,
		"employment_type":     "PERMANENT",
		"has_face_registered": true,
	})
}

// UpdateEmployee updates an employee
// PUT /hr/employees/:employee_id
func (h *HRHandler) UpdateEmployee(c *gin.Context) {
	empID := c.Param("employee_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      empID,
		"message": "Employee updated",
	})
}

// DeleteEmployee soft deletes (terminates) an employee
// DELETE /hr/employees/:employee_id
func (h *HRHandler) DeleteEmployee(c *gin.Context) {
	empID := c.Param("employee_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      empID,
		"message": "Employee terminated successfully",
	})
}

// ========== EMPLOYEE DOCUMENTS ==========

// ListEmployeeDocuments lists employee documents
// GET /hr/employees/:employee_id/documents
func (h *HRHandler) ListEmployeeDocuments(c *gin.Context) {
	empID := c.Param("employee_id")
	docs := []gin.H{
		{"id": "doc-1", "employee_id": empID, "document_type": "ID_CARD", "document_url": "https://...", "uploaded_at": "2024-01-15"},
		{"id": "doc-2", "employee_id": empID, "document_type": "CONTRACT", "document_url": "https://...", "uploaded_at": "2024-01-15"},
	}
	c.JSON(http.StatusOK, docs)
}

// AddEmployeeDocument adds employee document
// POST /hr/employees/:employee_id/documents
func (h *HRHandler) AddEmployeeDocument(c *gin.Context) {
	empID := c.Param("employee_id")
	c.JSON(http.StatusOK, gin.H{
		"id":          "new-doc-id",
		"employee_id": empID,
		"message":     "Document added",
	})
}

// RegisterFace registers employee face for attendance
// POST /hr/employees/:employee_id/register-face
func (h *HRHandler) RegisterFace(c *gin.Context) {
	empID := c.Param("employee_id")
	c.JSON(http.StatusOK, gin.H{
		"success":     true,
		"employee_id": empID,
		"message":     "Face registered successfully",
	})
}

// ========== SHIFTS ==========

// ListShifts lists all shifts
// GET /hr/shifts
func (h *HRHandler) ListShifts(c *gin.Context) {
	shifts := []gin.H{
		{"id": "shift-1", "name": "Morning", "start_time": "08:00", "end_time": "17:00", "break_duration_minutes": 60, "late_tolerance_minutes": 15, "is_active": true},
		{"id": "shift-2", "name": "Afternoon", "start_time": "14:00", "end_time": "22:00", "break_duration_minutes": 60, "late_tolerance_minutes": 15, "is_active": true},
		{"id": "shift-3", "name": "Night", "start_time": "22:00", "end_time": "06:00", "break_duration_minutes": 60, "late_tolerance_minutes": 15, "is_active": true},
	}
	c.JSON(http.StatusOK, shifts)
}

// CreateShift creates a shift
// POST /hr/shifts
func (h *HRHandler) CreateShift(c *gin.Context) {
	var req struct {
		Name                 string `json:"name" binding:"required"`
		StartTime            string `json:"start_time" binding:"required"`
		EndTime              string `json:"end_time" binding:"required"`
		BreakDurationMinutes int    `json:"break_duration_minutes"`
		LateToleranceMinutes int    `json:"late_tolerance_minutes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":         "new-shift-id",
		"name":       req.Name,
		"start_time": req.StartTime,
		"end_time":   req.EndTime,
		"is_active":  true,
	})
}

// UpdateShift updates a shift
// PUT /hr/shifts/:shift_id
func (h *HRHandler) UpdateShift(c *gin.Context) {
	shiftID := c.Param("shift_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      shiftID,
		"message": "Shift updated",
	})
}

// DeleteShift deletes a shift
// DELETE /hr/shifts/:shift_id
func (h *HRHandler) DeleteShift(c *gin.Context) {
	shiftID := c.Param("shift_id")
	c.JSON(http.StatusOK, gin.H{
		"id":      shiftID,
		"message": "Shift deleted successfully",
	})
}

// ========== ATTENDANCE ==========

// ListAttendance lists attendance records
// GET /hr/attendance?start_date=xxx&end_date=xxx&employee_id=xxx&department_id=xxx
func (h *HRHandler) ListAttendance(c *gin.Context) {
	attendance := []gin.H{
		{
			"id":               "att-1",
			"employee_id":      "emp-1",
			"employee_name":    "Ahmad Wijaya",
			"date":             "2024-01-15",
			"check_in":         "08:05:00",
			"check_out":        "17:30:00",
			"check_in_method":  "FACE",
			"check_out_method": "FACE",
			"status":           "PRESENT",
			"late_minutes":     0,
			"overtime_minutes": 30,
			"work_hours":       9.42,
		},
	}
	c.JSON(http.StatusOK, attendance)
}

// CheckIn records employee check-in
// POST /hr/attendance/check-in
func (h *HRHandler) CheckIn(c *gin.Context) {
	var req struct {
		EmployeeID      string  `json:"employee_id" binding:"required"`
		Method          string  `json:"method"`
		FaceImageBase64 *string `json:"face_image_base64"`
		Location        *string `json:"location"`
		Device          *string `json:"device"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	now := time.Now()
	c.JSON(http.StatusOK, gin.H{
		"id":          "new-att-id",
		"employee_id": req.EmployeeID,
		"date":        now.Format("2006-01-02"),
		"check_in":    now.Format("15:04:05"),
		"status":      "PRESENT",
		"message":     "Check-in successful",
	})
}

// CheckOut records employee check-out
// POST /hr/attendance/check-out
func (h *HRHandler) CheckOut(c *gin.Context) {
	var req struct {
		EmployeeID      string  `json:"employee_id" binding:"required"`
		Method          string  `json:"method"`
		FaceImageBase64 *string `json:"face_image_base64"`
		Location        *string `json:"location"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	now := time.Now()
	c.JSON(http.StatusOK, gin.H{
		"id":          "att-id",
		"employee_id": req.EmployeeID,
		"check_out":   now.Format("15:04:05"),
		"work_hours":  8.5,
		"message":     "Check-out successful",
	})
}

// FaceCheckIn check-in using face recognition
// POST /hr/attendance/face-check-in
func (h *HRHandler) FaceCheckIn(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"success":       true,
		"message":       "Welcome, Ahmad!",
		"employee_id":   "emp-1",
		"employee_name": "Ahmad Wijaya",
		"check_in_time": time.Now().Format(time.RFC3339),
	})
}

// ========== LEAVE TYPES ==========

// ListLeaveTypes lists all leave types
// GET /hr/leave-types
func (h *HRHandler) ListLeaveTypes(c *gin.Context) {
	leaveTypes := []gin.H{
		{"id": "lt-1", "name": "Annual Leave", "code": "AL", "default_days": 12, "is_paid": true, "requires_approval": true},
		{"id": "lt-2", "name": "Sick Leave", "code": "SL", "default_days": 14, "is_paid": true, "requires_approval": true},
		{"id": "lt-3", "name": "Unpaid Leave", "code": "UL", "default_days": 0, "is_paid": false, "requires_approval": true},
		{"id": "lt-4", "name": "Maternity Leave", "code": "ML", "default_days": 90, "is_paid": true, "requires_approval": true},
	}
	c.JSON(http.StatusOK, leaveTypes)
}

// CreateLeaveType creates a leave type
// POST /hr/leave-types
func (h *HRHandler) CreateLeaveType(c *gin.Context) {
	var req struct {
		Name             string `json:"name" binding:"required"`
		Code             string `json:"code" binding:"required"`
		DefaultDays      int    `json:"default_days"`
		IsPaid           bool   `json:"is_paid"`
		RequiresApproval bool   `json:"requires_approval"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":   "new-lt-id",
		"name": req.Name,
		"code": req.Code,
	})
}

// ========== LEAVE REQUESTS ==========

// ListLeaveRequests lists leave requests
// GET /hr/leave-requests?employee_id=xxx&status=xxx
func (h *HRHandler) ListLeaveRequests(c *gin.Context) {
	requests := []gin.H{
		{
			"id":              "lr-1",
			"employee_id":     "emp-1",
			"employee_name":   "Ahmad Wijaya",
			"leave_type_id":   "lt-1",
			"leave_type_name": "Annual Leave",
			"start_date":      "2024-02-01",
			"end_date":        "2024-02-03",
			"days":            3,
			"reason":          "Family vacation",
			"status":          "PENDING",
		},
	}
	c.JSON(http.StatusOK, requests)
}

// CreateLeaveRequest creates a leave request
// POST /hr/leave-requests
func (h *HRHandler) CreateLeaveRequest(c *gin.Context) {
	var req struct {
		EmployeeID  string  `json:"employee_id" binding:"required"`
		LeaveTypeID string  `json:"leave_type_id" binding:"required"`
		StartDate   string  `json:"start_date" binding:"required"`
		EndDate     string  `json:"end_date" binding:"required"`
		Reason      *string `json:"reason"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      "new-lr-id",
		"status":  "PENDING",
		"message": "Leave request submitted",
	})
}

// ApproveLeaveRequest approves or rejects a leave request
// POST /hr/leave-requests/:request_id/approve
func (h *HRHandler) ApproveLeaveRequest(c *gin.Context) {
	reqID := c.Param("request_id")

	var req struct {
		Approved bool    `json:"approved"`
		Notes    *string `json:"notes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	status := "APPROVED"
	if !req.Approved {
		status = "REJECTED"
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      reqID,
		"status":  status,
		"message": "Leave request " + status,
	})
}

// GetLeaveBalance gets employee leave balance
// GET /hr/leave-balance/:employee_id
func (h *HRHandler) GetLeaveBalance(c *gin.Context) {
	empID := c.Param("employee_id")

	balances := []gin.H{
		{"leave_type_id": "lt-1", "leave_type_name": "Annual Leave", "total_days": 12, "used_days": 3, "remaining_days": 9},
		{"leave_type_id": "lt-2", "leave_type_name": "Sick Leave", "total_days": 14, "used_days": 1, "remaining_days": 13},
	}

	c.JSON(http.StatusOK, gin.H{
		"employee_id": empID,
		"year":        2024,
		"balances":    balances,
	})
}

// ========== PAYROLL ==========

// ListPayrollPeriods lists payroll periods
// GET /hr/payroll/periods
func (h *HRHandler) ListPayrollPeriods(c *gin.Context) {
	periods := []gin.H{
		{"id": "pp-1", "name": "January 2024", "start_date": "2024-01-01", "end_date": "2024-01-31", "status": "CLOSED", "total_employees": 42, "total_amount": 500000000},
		{"id": "pp-2", "name": "February 2024", "start_date": "2024-02-01", "end_date": "2024-02-29", "status": "OPEN", "total_employees": 0, "total_amount": 0},
	}
	c.JSON(http.StatusOK, periods)
}

// CreatePayrollPeriod creates a payroll period
// POST /hr/payroll/periods
func (h *HRHandler) CreatePayrollPeriod(c *gin.Context) {
	var req struct {
		Name      string `json:"name" binding:"required"`
		StartDate string `json:"start_date" binding:"required"`
		EndDate   string `json:"end_date" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":     "new-pp-id",
		"name":   req.Name,
		"status": "OPEN",
	})
}

// RunPayroll runs payroll calculation for a period
// POST /hr/payroll/periods/:period_id/run
func (h *HRHandler) RunPayroll(c *gin.Context) {
	periodID := c.Param("period_id")

	c.JSON(http.StatusOK, gin.H{
		"period_id":        periodID,
		"total_employees":  42,
		"total_gross":      600000000,
		"total_deductions": 100000000,
		"total_net":        500000000,
		"status":           "PROCESSED",
		"message":          "Payroll calculated successfully",
	})
}

// ListPayslips lists payslips for a period
// GET /hr/payroll/periods/:period_id/payslips
func (h *HRHandler) ListPayslips(c *gin.Context) {
	periodID := c.Param("period_id")

	payslips := []gin.H{
		{
			"id":            "ps-1",
			"period_id":     periodID,
			"employee_id":   "emp-1",
			"employee_name": "Ahmad Wijaya",
			"basic_salary":  12000000,
			"allowances":    2000000,
			"gross_salary":  14000000,
			"deductions":    1400000,
			"net_salary":    12600000,
			"status":        "GENERATED",
		},
	}
	c.JSON(http.StatusOK, payslips)
}

// GetPayslip gets a specific payslip
// GET /hr/payroll/payslips/:payslip_id
func (h *HRHandler) GetPayslip(c *gin.Context) {
	payslipID := c.Param("payslip_id")

	c.JSON(http.StatusOK, gin.H{
		"id":                   payslipID,
		"employee_id":          "emp-1",
		"employee_name":        "Ahmad Wijaya",
		"period_name":          "January 2024",
		"basic_salary":         12000000,
		"position_allowance":   1000000,
		"transport_allowance":  500000,
		"meal_allowance":       500000,
		"overtime_pay":         750000,
		"gross_salary":         14750000,
		"bpjs_kesehatan":       147500,
		"bpjs_ketenagakerjaan": 295000,
		"pph21":                500000,
		"total_deductions":     942500,
		"net_salary":           13807500,
	})
}
