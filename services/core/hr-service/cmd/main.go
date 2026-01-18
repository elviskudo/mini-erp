package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/hr-service/internal/database"
	"github.com/elviskudo/mini-erp/services/hr-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Connect to database
	if err := database.Connect(); err != nil {
		log.Printf("⚠️ Database connection failed: %v (running with mock data)", err)
	}
	defer database.Close()

	r := gin.Default()

	// CORS
	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-ID")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Health check
	r.GET("/health", func(c *gin.Context) {
		dbStatus := "connected"
		if database.GetDB() == nil {
			dbStatus = "disconnected"
		}
		c.JSON(200, gin.H{
			"status":   "healthy",
			"service":  "hr-service",
			"version":  "1.0.0",
			"database": dbStatus,
		})
	})

	// Scalar API Documentation
	r.GET("/docs", handlers.ScalarDocs)
	r.GET("/docs/*any", handlers.ScalarDocs)
	r.GET("/openapi.json", handlers.OpenAPISpec)

	// Initialize handlers
	hrHandler := handlers.NewHRHandler()

	// Mount at both paths for gateway compatibility
	setupRoutes(r.Group("/hr"), hrHandler)
	setupRoutes(r.Group("/api/v1/hr"), hrHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8012"
	}

	log.Printf("👥 HR Service starting on port %s", port)
	log.Printf("📊 Routes: Departments, Positions, Employees, Shifts, Attendance, Leave, Payroll")
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start hr service: %v", err)
	}
}

func setupRoutes(hr *gin.RouterGroup, h *handlers.HRHandler) {
	// Dashboard
	hr.GET("/stats", h.GetStats)
	hr.GET("/managers", h.ListManagers)

	// Departments
	hr.GET("/departments", h.ListDepartments)
	hr.POST("/departments", h.CreateDepartment)
	hr.PUT("/departments/:dept_id", h.UpdateDepartment)
	hr.DELETE("/departments/:dept_id", h.DeleteDepartment)

	// Positions
	hr.GET("/positions", h.ListPositions)
	hr.POST("/positions", h.CreatePosition)
	hr.PUT("/positions/:pos_id", h.UpdatePosition)
	hr.DELETE("/positions/:pos_id", h.DeletePosition)

	// Employees
	hr.GET("/employees", h.ListEmployees)
	hr.POST("/employees", h.CreateEmployee)
	hr.GET("/employees/:employee_id", h.GetEmployee)
	hr.PUT("/employees/:employee_id", h.UpdateEmployee)
	hr.DELETE("/employees/:employee_id", h.DeleteEmployee)

	// Employee Documents
	hr.GET("/employees/:employee_id/documents", h.ListEmployeeDocuments)
	hr.POST("/employees/:employee_id/documents", h.AddEmployeeDocument)
	hr.POST("/employees/:employee_id/register-face", h.RegisterFace)

	// Shifts
	hr.GET("/shifts", h.ListShifts)
	hr.POST("/shifts", h.CreateShift)
	hr.PUT("/shifts/:shift_id", h.UpdateShift)
	hr.DELETE("/shifts/:shift_id", h.DeleteShift)

	// Attendance
	hr.GET("/attendance", h.ListAttendance)
	hr.POST("/attendance/check-in", h.CheckIn)
	hr.POST("/attendance/check-out", h.CheckOut)
	hr.POST("/attendance/face-check-in", h.FaceCheckIn)

	// Leave Types
	hr.GET("/leave-types", h.ListLeaveTypes)
	hr.POST("/leave-types", h.CreateLeaveType)

	// Leave Requests
	hr.GET("/leave-requests", h.ListLeaveRequests)
	hr.POST("/leave-requests", h.CreateLeaveRequest)
	hr.POST("/leave-requests/:request_id/approve", h.ApproveLeaveRequest)
	hr.GET("/leave-balance/:employee_id", h.GetLeaveBalance)

	// Payroll
	hr.GET("/payroll/periods", h.ListPayrollPeriods)
	hr.POST("/payroll/periods", h.CreatePayrollPeriod)
	hr.POST("/payroll/periods/:period_id/run", h.RunPayroll)
	hr.GET("/payroll/periods/:period_id/payslips", h.ListPayslips)
	hr.GET("/payroll/payslips/:payslip_id", h.GetPayslip)
}
