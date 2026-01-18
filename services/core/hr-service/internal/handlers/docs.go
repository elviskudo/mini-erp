package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// ScalarDocs serves the Scalar API documentation
func ScalarDocs(c *gin.Context) {
	html := `<!DOCTYPE html>
<html>
<head>
  <title>HR Service - API Documentation</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <script id="api-reference" data-url="/openapi.json"></script>
  <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>`
	c.Header("Content-Type", "text/html")
	c.String(http.StatusOK, html)
}

// OpenAPISpec returns the OpenAPI specification for HR Service
func OpenAPISpec(c *gin.Context) {
	spec := gin.H{
		"openapi": "3.0.3",
		"info": gin.H{
			"title":       "Mini-ERP HR Service API",
			"version":     "1.0.0",
			"description": "Human Resources Management - Departments, Positions, Employees, Shifts, Attendance, Leave Management, Payroll",
		},
		"servers": []gin.H{
			{"url": "http://localhost:8012", "description": "Development server"},
			{"url": "http://localhost:8000/api/v1", "description": "Via API Gateway"},
		},
		"tags": []gin.H{
			{"name": "Dashboard", "description": "HR Dashboard Statistics"},
			{"name": "Departments", "description": "Department Management"},
			{"name": "Positions", "description": "Position/Job Title Management"},
			{"name": "Employees", "description": "Employee Master Data"},
			{"name": "Shifts", "description": "Work Shift Configuration"},
			{"name": "Attendance", "description": "Attendance Tracking & Check-in/out"},
			{"name": "Leave", "description": "Leave Types, Requests & Balance"},
			{"name": "Payroll", "description": "Payroll Processing & Payslips"},
		},
		"paths": buildHRPaths(),
		"components": gin.H{
			"schemas":         buildHRSchemas(),
			"securitySchemes": gin.H{"BearerAuth": gin.H{"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
		},
	}
	c.JSON(http.StatusOK, spec)
}

func buildHRPaths() gin.H {
	return gin.H{
		"/hr/stats":                                 gin.H{"get": endpoint("Dashboard", "Get HR dashboard statistics")},
		"/hr/managers":                              gin.H{"get": endpoint("Dashboard", "List managers for department assignment")},
		"/hr/departments":                           gin.H{"get": endpoint("Departments", "List departments"), "post": endpointWithBody("Departments", "Create department", "DepartmentCreate")},
		"/hr/departments/{dept_id}":                 gin.H{"put": endpointWithParam("Departments", "Update department", "dept_id"), "delete": endpointWithParam("Departments", "Delete department", "dept_id")},
		"/hr/positions":                             gin.H{"get": endpoint("Positions", "List positions"), "post": endpointWithBody("Positions", "Create position", "PositionCreate")},
		"/hr/positions/{pos_id}":                    gin.H{"put": endpointWithParam("Positions", "Update position", "pos_id"), "delete": endpointWithParam("Positions", "Delete position", "pos_id")},
		"/hr/employees":                             gin.H{"get": endpoint("Employees", "List employees"), "post": endpointWithBody("Employees", "Create employee", "EmployeeCreate")},
		"/hr/employees/{employee_id}":               gin.H{"get": endpointWithParam("Employees", "Get employee details", "employee_id"), "put": endpointWithParam("Employees", "Update employee", "employee_id"), "delete": endpointWithParam("Employees", "Terminate employee", "employee_id")},
		"/hr/employees/{employee_id}/documents":     gin.H{"get": endpointWithParam("Employees", "List employee documents", "employee_id"), "post": endpointWithParam("Employees", "Add employee document", "employee_id")},
		"/hr/employees/{employee_id}/register-face": gin.H{"post": endpointWithParam("Employees", "Register face for attendance", "employee_id")},
		"/hr/shifts":                                gin.H{"get": endpoint("Shifts", "List shifts"), "post": endpointWithBody("Shifts", "Create shift", "ShiftCreate")},
		"/hr/shifts/{shift_id}":                     gin.H{"put": endpointWithParam("Shifts", "Update shift", "shift_id"), "delete": endpointWithParam("Shifts", "Delete shift", "shift_id")},
		"/hr/attendance":                            gin.H{"get": endpoint("Attendance", "List attendance records")},
		"/hr/attendance/check-in":                   gin.H{"post": endpointWithBody("Attendance", "Record check-in", "AttendanceCheckIn")},
		"/hr/attendance/check-out":                  gin.H{"post": endpointWithBody("Attendance", "Record check-out", "AttendanceCheckOut")},
		"/hr/attendance/face-check-in":              gin.H{"post": endpoint("Attendance", "Check-in via face recognition")},
		"/hr/leave-types":                           gin.H{"get": endpoint("Leave", "List leave types"), "post": endpointWithBody("Leave", "Create leave type", "LeaveTypeCreate")},
		"/hr/leave-requests":                        gin.H{"get": endpoint("Leave", "List leave requests"), "post": endpointWithBody("Leave", "Submit leave request", "LeaveRequestCreate")},
		"/hr/leave-requests/{request_id}/approve":   gin.H{"post": endpointWithParam("Leave", "Approve/reject leave request", "request_id")},
		"/hr/leave-balance/{employee_id}":           gin.H{"get": endpointWithParam("Leave", "Get employee leave balance", "employee_id")},
		"/hr/payroll/periods":                       gin.H{"get": endpoint("Payroll", "List payroll periods"), "post": endpointWithBody("Payroll", "Create payroll period", "PayrollPeriodCreate")},
		"/hr/payroll/periods/{period_id}/run":       gin.H{"post": endpointWithParam("Payroll", "Run payroll calculation", "period_id")},
		"/hr/payroll/periods/{period_id}/payslips":  gin.H{"get": endpointWithParam("Payroll", "List payslips for period", "period_id")},
		"/hr/payroll/payslips/{payslip_id}":         gin.H{"get": endpointWithParam("Payroll", "Get payslip details", "payslip_id")},
	}
}

func buildHRSchemas() gin.H {
	return gin.H{
		"DepartmentCreate": gin.H{"type": "object", "required": []string{"code", "name"}, "properties": gin.H{
			"code": gin.H{"type": "string"}, "name": gin.H{"type": "string"}, "manager_id": gin.H{"type": "string"},
		}},
		"PositionCreate": gin.H{"type": "object", "required": []string{"code", "name", "department_id"}, "properties": gin.H{
			"code": gin.H{"type": "string"}, "name": gin.H{"type": "string"}, "department_id": gin.H{"type": "string"}, "level": gin.H{"type": "integer"},
		}},
		"EmployeeCreate": gin.H{"type": "object", "required": []string{"first_name", "last_name", "email", "department_id", "position_id"}, "properties": gin.H{
			"first_name": gin.H{"type": "string"}, "last_name": gin.H{"type": "string"}, "email": gin.H{"type": "string", "format": "email"},
			"phone": gin.H{"type": "string"}, "department_id": gin.H{"type": "string"}, "position_id": gin.H{"type": "string"},
			"hire_date": gin.H{"type": "string", "format": "date"}, "basic_salary": gin.H{"type": "number"},
		}},
		"ShiftCreate": gin.H{"type": "object", "required": []string{"name", "start_time", "end_time"}, "properties": gin.H{
			"name": gin.H{"type": "string"}, "start_time": gin.H{"type": "string"}, "end_time": gin.H{"type": "string"},
			"break_duration_minutes": gin.H{"type": "integer"}, "late_tolerance_minutes": gin.H{"type": "integer"},
		}},
		"AttendanceCheckIn": gin.H{"type": "object", "required": []string{"employee_id"}, "properties": gin.H{
			"employee_id": gin.H{"type": "string"}, "method": gin.H{"type": "string"}, "face_image_base64": gin.H{"type": "string"}, "location": gin.H{"type": "string"},
		}},
		"AttendanceCheckOut": gin.H{"type": "object", "required": []string{"employee_id"}, "properties": gin.H{
			"employee_id": gin.H{"type": "string"}, "method": gin.H{"type": "string"}, "location": gin.H{"type": "string"},
		}},
		"LeaveTypeCreate": gin.H{"type": "object", "required": []string{"code", "name"}, "properties": gin.H{
			"code": gin.H{"type": "string"}, "name": gin.H{"type": "string"}, "default_days": gin.H{"type": "integer"}, "is_paid": gin.H{"type": "boolean"},
		}},
		"LeaveRequestCreate": gin.H{"type": "object", "required": []string{"employee_id", "leave_type_id", "start_date", "end_date"}, "properties": gin.H{
			"employee_id": gin.H{"type": "string"}, "leave_type_id": gin.H{"type": "string"},
			"start_date": gin.H{"type": "string", "format": "date"}, "end_date": gin.H{"type": "string", "format": "date"}, "reason": gin.H{"type": "string"},
		}},
		"PayrollPeriodCreate": gin.H{"type": "object", "required": []string{"name", "start_date", "end_date"}, "properties": gin.H{
			"name": gin.H{"type": "string"}, "start_date": gin.H{"type": "string", "format": "date"}, "end_date": gin.H{"type": "string", "format": "date"},
		}},
	}
}

// Helper functions
func endpoint(tag, summary string) gin.H {
	return gin.H{"tags": []string{tag}, "summary": summary, "security": []gin.H{{"BearerAuth": []string{}}}, "responses": gin.H{"200": gin.H{"description": "Success"}}}
}

func endpointWithBody(tag, summary, schema string) gin.H {
	return gin.H{"tags": []string{tag}, "summary": summary, "security": []gin.H{{"BearerAuth": []string{}}},
		"requestBody": gin.H{"required": true, "content": gin.H{"application/json": gin.H{"schema": gin.H{"$ref": "#/components/schemas/" + schema}}}},
		"responses":   gin.H{"200": gin.H{"description": "Success"}}}
}

func endpointWithParam(tag, summary, param string) gin.H {
	return gin.H{"tags": []string{tag}, "summary": summary, "security": []gin.H{{"BearerAuth": []string{}}},
		"parameters": []gin.H{{"name": param, "in": "path", "required": true, "schema": gin.H{"type": "string"}}},
		"responses":  gin.H{"200": gin.H{"description": "Success"}}}
}
