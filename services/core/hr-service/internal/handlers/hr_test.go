package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/elviskudo/mini-erp/services/hr-service/internal/handlers"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

type HRTestSuite struct {
	suite.Suite
	router  *gin.Engine
	handler *handlers.HRHandler
}

func (s *HRTestSuite) SetupSuite() {
	gin.SetMode(gin.TestMode)
	s.handler = handlers.NewHRHandler()
	s.router = s.setupRouter()
}

func (s *HRTestSuite) setupRouter() *gin.Engine {
	r := gin.Default()
	hr := r.Group("/hr")

	hr.GET("/stats", s.handler.GetStats)
	hr.GET("/managers", s.handler.ListManagers)
	hr.GET("/departments", s.handler.ListDepartments)
	hr.POST("/departments", s.handler.CreateDepartment)
	hr.PUT("/departments/:dept_id", s.handler.UpdateDepartment)
	hr.DELETE("/departments/:dept_id", s.handler.DeleteDepartment)
	hr.GET("/positions", s.handler.ListPositions)
	hr.POST("/positions", s.handler.CreatePosition)
	hr.PUT("/positions/:pos_id", s.handler.UpdatePosition)
	hr.DELETE("/positions/:pos_id", s.handler.DeletePosition)
	hr.GET("/employees", s.handler.ListEmployees)
	hr.POST("/employees", s.handler.CreateEmployee)
	hr.GET("/employees/:employee_id", s.handler.GetEmployee)
	hr.PUT("/employees/:employee_id", s.handler.UpdateEmployee)
	hr.DELETE("/employees/:employee_id", s.handler.DeleteEmployee)
	hr.GET("/employees/:employee_id/documents", s.handler.ListEmployeeDocuments)
	hr.POST("/employees/:employee_id/documents", s.handler.AddEmployeeDocument)
	hr.POST("/employees/:employee_id/register-face", s.handler.RegisterFace)
	hr.GET("/shifts", s.handler.ListShifts)
	hr.POST("/shifts", s.handler.CreateShift)
	hr.PUT("/shifts/:shift_id", s.handler.UpdateShift)
	hr.DELETE("/shifts/:shift_id", s.handler.DeleteShift)
	hr.GET("/attendance", s.handler.ListAttendance)
	hr.POST("/attendance/check-in", s.handler.CheckIn)
	hr.POST("/attendance/check-out", s.handler.CheckOut)
	hr.POST("/attendance/face-check-in", s.handler.FaceCheckIn)
	hr.GET("/leave-types", s.handler.ListLeaveTypes)
	hr.POST("/leave-types", s.handler.CreateLeaveType)
	hr.GET("/leave-requests", s.handler.ListLeaveRequests)
	hr.POST("/leave-requests", s.handler.CreateLeaveRequest)
	hr.POST("/leave-requests/:request_id/approve", s.handler.ApproveLeaveRequest)
	hr.GET("/leave-balance/:employee_id", s.handler.GetLeaveBalance)
	hr.GET("/payroll/periods", s.handler.ListPayrollPeriods)
	hr.POST("/payroll/periods", s.handler.CreatePayrollPeriod)
	hr.POST("/payroll/periods/:period_id/run", s.handler.RunPayroll)
	hr.GET("/payroll/periods/:period_id/payslips", s.handler.ListPayslips)
	hr.GET("/payroll/payslips/:payslip_id", s.handler.GetPayslip)

	return r
}

// ========== DASHBOARD ==========

func (s *HRTestSuite) TestGetStats() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/stats", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestListManagers() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/managers", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== DEPARTMENTS ==========

func (s *HRTestSuite) TestListDepartments() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/departments", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateDepartment() {
	body, _ := json.Marshal(map[string]interface{}{"code": "MKT", "name": "Marketing"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/departments", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateDepartmentMissingCode() {
	body, _ := json.Marshal(map[string]interface{}{"name": "Marketing"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/departments", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 400, w.Code)
}

func (s *HRTestSuite) TestUpdateDepartment() {
	body, _ := json.Marshal(map[string]interface{}{"name": "Updated"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", "/hr/departments/dept-1", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestDeleteDepartment() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/hr/departments/dept-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== POSITIONS ==========

func (s *HRTestSuite) TestListPositions() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/positions", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreatePosition() {
	body, _ := json.Marshal(map[string]interface{}{"code": "SR-DEV", "name": "Senior Developer", "department_id": "dept-1"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/positions", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestDeletePosition() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/hr/positions/pos-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== EMPLOYEES ==========

func (s *HRTestSuite) TestListEmployees() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/employees", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateEmployee() {
	body, _ := json.Marshal(map[string]interface{}{
		"first_name": "Test", "last_name": "User", "email": "test@company.com",
		"department_id": "dept-1", "position_id": "pos-1",
	})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/employees", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateEmployeeMissingEmail() {
	body, _ := json.Marshal(map[string]interface{}{"first_name": "Test", "last_name": "User", "department_id": "dept-1", "position_id": "pos-1"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/employees", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 400, w.Code)
}

func (s *HRTestSuite) TestGetEmployee() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/employees/emp-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestDeleteEmployee() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/hr/employees/emp-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestListEmployeeDocuments() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/employees/emp-1/documents", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestRegisterFace() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/employees/emp-1/register-face", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== SHIFTS ==========

func (s *HRTestSuite) TestListShifts() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/shifts", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateShift() {
	body, _ := json.Marshal(map[string]interface{}{"name": "Flexible", "start_time": "09:00", "end_time": "18:00"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/shifts", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestDeleteShift() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/hr/shifts/shift-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== ATTENDANCE ==========

func (s *HRTestSuite) TestListAttendance() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/attendance", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCheckIn() {
	body, _ := json.Marshal(map[string]interface{}{"employee_id": "emp-1", "method": "FACE"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/attendance/check-in", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCheckInMissingEmployee() {
	body, _ := json.Marshal(map[string]interface{}{"method": "FACE"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/attendance/check-in", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 400, w.Code)
}

func (s *HRTestSuite) TestCheckOut() {
	body, _ := json.Marshal(map[string]interface{}{"employee_id": "emp-1"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/attendance/check-out", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestFaceCheckIn() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/attendance/face-check-in", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== LEAVE ==========

func (s *HRTestSuite) TestListLeaveTypes() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/leave-types", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateLeaveType() {
	body, _ := json.Marshal(map[string]interface{}{"code": "PL", "name": "Personal Leave", "default_days": 3})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/leave-types", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestListLeaveRequests() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/leave-requests", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreateLeaveRequest() {
	body, _ := json.Marshal(map[string]interface{}{
		"employee_id": "emp-1", "leave_type_id": "lt-1",
		"start_date": "2024-03-01", "end_date": "2024-03-03",
	})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/leave-requests", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestApproveLeaveRequest() {
	body, _ := json.Marshal(map[string]interface{}{"approved": true})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/leave-requests/lr-1/approve", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestGetLeaveBalance() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/leave-balance/emp-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== PAYROLL ==========

func (s *HRTestSuite) TestListPayrollPeriods() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/payroll/periods", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestCreatePayrollPeriod() {
	body, _ := json.Marshal(map[string]interface{}{"name": "March 2024", "start_date": "2024-03-01", "end_date": "2024-03-31"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/payroll/periods", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestRunPayroll() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/hr/payroll/periods/pp-1/run", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestListPayslips() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/payroll/periods/pp-1/payslips", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func (s *HRTestSuite) TestGetPayslip() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/hr/payroll/payslips/ps-1", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

func TestHRTestSuite(t *testing.T) {
	suite.Run(t, new(HRTestSuite))
}
