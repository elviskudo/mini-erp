package routes

import (
	"strings"

	"github.com/elviskudo/mini-erp/gateway/internal/handlers"
	"github.com/elviskudo/mini-erp/gateway/internal/middleware"
	"github.com/elviskudo/mini-erp/gateway/internal/proxy"
	"github.com/gin-gonic/gin"
)

// SetupRoutes configures all API routes
func SetupRoutes(r *gin.Engine) {
	// Scalar API Documentation (modern alternative to Swagger)
	r.GET("/docs", handlers.ScalarDocs)
	r.GET("/docs/*any", handlers.ScalarDocs)
	r.GET("/openapi.json", handlers.OpenAPISpec)

	// API v1 group
	v1 := r.Group("/api/v1")

	// Public routes (no auth required)
	setupPublicRoutes(v1)

	// Protected routes (auth required)
	protected := v1.Group("")
	protected.Use(middleware.JWTAuth())
	protected.Use(middleware.TenantExtractor())
	setupProtectedRoutes(protected)
}

func setupPublicRoutes(rg *gin.RouterGroup) {
	// ========== AUTH SERVICE (proxied to auth-service:8010) ==========
	auth := rg.Group("/auth")
	{
		// All auth public routes proxy to auth-service
		auth.POST("/login", proxyToAuth)
		auth.POST("/register", proxyToAuth)
		auth.POST("/refresh", proxyToAuth)
		auth.POST("/token", proxyToAuth)      // OAuth2 token endpoint
		auth.POST("/send-otp", proxyToAuth)   // Send OTP
		auth.POST("/verify-otp", proxyToAuth) // Verify OTP
		auth.POST("/forgot-password", proxyToAuth)
	}
}

func setupProtectedRoutes(rg *gin.RouterGroup) {
	// ========== AUTH SERVICE (protected routes) ==========
	rg.GET("/menus", proxyToAuth) // Menus endpoint

	auth := rg.Group("/auth")
	{
		auth.GET("/me", proxyToAuth)
		auth.POST("/logout", proxyToAuth)
		auth.PUT("/profile", proxyToAuth)
		auth.GET("/user-tenants", proxyToAuth)   // Get user's available tenants
		auth.POST("/switch-tenant", proxyToAuth) // Switch to different tenant
	}

	// ========== FINANCE SERVICE (proxied to finance-service:8011) ==========
	// Routes match backend/routers/finance.py exactly
	proxyToFinance := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "finance", path)
	}

	finance := rg.Group("/finance")
	{
		// Stats
		finance.GET("/stats", proxyToFinance)

		// Chart of Accounts
		finance.GET("/coa", proxyToFinance)
		finance.POST("/coa", proxyToFinance)
		finance.PUT("/coa/:account_id", proxyToFinance)
		finance.POST("/coa/seed", proxyToFinance)

		// General Ledger
		finance.GET("/gl", proxyToFinance) // GL query with account_id param
		finance.POST("/journal", proxyToFinance)

		// Fiscal Periods
		finance.GET("/periods", proxyToFinance)
		finance.POST("/periods", proxyToFinance)
		finance.POST("/periods/:id/close", proxyToFinance)

		// Fixed Assets
		finance.POST("/assets", proxyToFinance)
		finance.POST("/assets/:id/depreciate", proxyToFinance)

		// Reports
		finance.GET("/reports/trial-balance", proxyToFinance)
		finance.GET("/reports/pl", proxyToFinance)
		finance.GET("/reports/balance-sheet", proxyToFinance)

		// Banking - Accounts
		finance.GET("/banking/accounts", proxyToFinance)
		finance.GET("/banking/accounts/:account_id", proxyToFinance)
		finance.POST("/banking/accounts", proxyToFinance)
		finance.PUT("/banking/accounts/:account_id", proxyToFinance)
		finance.DELETE("/banking/accounts/:account_id", proxyToFinance)

		// Banking - Transactions
		finance.GET("/banking/transactions", proxyToFinance)
		finance.GET("/banking/transactions/:transaction_id", proxyToFinance)
		finance.POST("/banking/transactions", proxyToFinance)

		// Banking - Reconciliation
		finance.GET("/banking/reconciliation/:account_id", proxyToFinance)
		finance.POST("/banking/reconciliation/mark", proxyToFinance)
		finance.GET("/banking/reconciliations", proxyToFinance)

		// Banking - Petty Cash
		finance.GET("/banking/petty-cash", proxyToFinance)
		finance.POST("/banking/petty-cash/expense", proxyToFinance)
		finance.POST("/banking/petty-cash/replenish", proxyToFinance)
	}

	// ========== HR SERVICE (proxied to hr-service:8012) ==========
	proxyToHR := func(c *gin.Context) {
		path := c.Request.URL.Path
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "hr", path)
	}

	hr := rg.Group("/hr")
	{
		// Dashboard
		hr.GET("/stats", proxyToHR)
		hr.GET("/managers", proxyToHR)

		// Departments
		hr.GET("/departments", proxyToHR)
		hr.POST("/departments", proxyToHR)
		hr.PUT("/departments/:dept_id", proxyToHR)
		hr.DELETE("/departments/:dept_id", proxyToHR)

		// Positions
		hr.GET("/positions", proxyToHR)
		hr.POST("/positions", proxyToHR)
		hr.PUT("/positions/:pos_id", proxyToHR)
		hr.DELETE("/positions/:pos_id", proxyToHR)

		// Employees
		hr.GET("/employees", proxyToHR)
		hr.POST("/employees", proxyToHR)
		hr.GET("/employees/:employee_id", proxyToHR)
		hr.PUT("/employees/:employee_id", proxyToHR)
		hr.DELETE("/employees/:employee_id", proxyToHR)

		// Employee Documents & Face
		hr.GET("/employees/:employee_id/documents", proxyToHR)
		hr.POST("/employees/:employee_id/documents", proxyToHR)
		hr.POST("/employees/:employee_id/register-face", proxyToHR)

		// Shifts
		hr.GET("/shifts", proxyToHR)
		hr.POST("/shifts", proxyToHR)
		hr.PUT("/shifts/:shift_id", proxyToHR)
		hr.DELETE("/shifts/:shift_id", proxyToHR)

		// Attendance
		hr.GET("/attendance", proxyToHR)
		hr.POST("/attendance/check-in", proxyToHR)
		hr.POST("/attendance/check-out", proxyToHR)
		hr.POST("/attendance/face-check-in", proxyToHR)

		// Leave Types
		hr.GET("/leave-types", proxyToHR)
		hr.POST("/leave-types", proxyToHR)

		// Leave Requests
		hr.GET("/leave-requests", proxyToHR)
		hr.POST("/leave-requests", proxyToHR)
		hr.POST("/leave-requests/:request_id/approve", proxyToHR)
		hr.GET("/leave-balance/:employee_id", proxyToHR)

		// Payroll
		hr.GET("/payroll/periods", proxyToHR)
		hr.POST("/payroll/periods", proxyToHR)
		hr.POST("/payroll/periods/:period_id/run", proxyToHR)
		hr.GET("/payroll/periods/:period_id/payslips", proxyToHR)
		hr.GET("/payroll/payslips/:payslip_id", proxyToHR)
	}

	// ========== INVENTORY SERVICE (proxied to inventory-service:8013) ==========
	proxyToInventory := func(c *gin.Context) {
		path := c.Request.URL.Path
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "inventory", path)
	}

	inventory := rg.Group("/inventory")
	{
		// Stats
		inventory.GET("/stats", proxyToInventory)

		// Products
		inventory.GET("/products", proxyToInventory)
		inventory.POST("/products", proxyToInventory)
		inventory.GET("/products/:id", proxyToInventory)
		inventory.PUT("/products/:id", proxyToInventory)
		inventory.DELETE("/products/:id", proxyToInventory)

		// Warehouses
		inventory.GET("/warehouses", proxyToInventory)
		inventory.POST("/warehouses", proxyToInventory)
		inventory.GET("/warehouses/:id", proxyToInventory)
		inventory.PUT("/warehouses/:id", proxyToInventory)
		inventory.DELETE("/warehouses/:id", proxyToInventory)

		// Stock
		inventory.GET("/stock", proxyToInventory)

		// Movements
		inventory.GET("/movements", proxyToInventory)

		// Opname
		inventory.GET("/opnames", proxyToInventory)
		inventory.POST("/opnames", proxyToInventory)
		inventory.GET("/opnames/:id", proxyToInventory)

		// Locations
		inventory.GET("/locations", proxyToInventory)
	}

	// ========== MANUFACTURING SERVICE (proxied to manufacturing-service:8014) ==========
	// Roles: PRODUCTION, STAFF, LAB_TECH
	proxyToManufacturing := func(c *gin.Context) {
		// Transform /api/v1/manufacturing/... to /manufacturing/...
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "manufacturing", path)
	}

	mfg := rg.Group("/manufacturing")
	{
		mfg.GET("/stats", proxyToManufacturing)
		mfg.GET("/work-centers", proxyToManufacturing)
		mfg.POST("/work-centers", proxyToManufacturing)
		mfg.GET("/work-centers/:id", proxyToManufacturing)
		mfg.PUT("/work-centers/:id", proxyToManufacturing)
		mfg.DELETE("/work-centers/:id", proxyToManufacturing)

		// Production Orders - full CRUD
		mfg.GET("/production-orders", proxyToManufacturing)
		mfg.POST("/production-orders", proxyToManufacturing)
		mfg.GET("/production-orders/:id", proxyToManufacturing)
		mfg.PUT("/production-orders/:id", proxyToManufacturing)
		mfg.DELETE("/production-orders/:id", proxyToManufacturing)
		mfg.PUT("/production-orders/:id/status", proxyToManufacturing)

		// Orders - alias for production-orders
		mfg.GET("/orders", proxyToManufacturing)
		mfg.POST("/orders", proxyToManufacturing)
		mfg.GET("/orders/:id", proxyToManufacturing)
		mfg.PUT("/orders/:id", proxyToManufacturing)
		mfg.DELETE("/orders/:id", proxyToManufacturing)

		// BOM - full CRUD
		mfg.GET("/bom", proxyToManufacturing)
		mfg.GET("/bom-items", proxyToManufacturing) // Alias for frontend compatibility
		mfg.POST("/bom", proxyToManufacturing)
		mfg.GET("/bom/:id", proxyToManufacturing)
		mfg.PUT("/bom/:id", proxyToManufacturing)
		mfg.DELETE("/bom/:id", proxyToManufacturing)

		// QC Results - full CRUD
		mfg.GET("/qc-results", proxyToManufacturing)
		mfg.POST("/qc-results", proxyToManufacturing)
		mfg.GET("/qc-results/:id", proxyToManufacturing)
		mfg.PUT("/qc-results/:id", proxyToManufacturing)
		mfg.DELETE("/qc-results/:id", proxyToManufacturing)

		// Quality Checks - alias for qc-results
		mfg.GET("/quality-checks", proxyToManufacturing)
		mfg.POST("/quality-checks", proxyToManufacturing)
		mfg.GET("/quality-checks/:id", proxyToManufacturing)
		mfg.PUT("/quality-checks/:id", proxyToManufacturing)
		mfg.DELETE("/quality-checks/:id", proxyToManufacturing)

		// Routings - full CRUD
		mfg.GET("/routings", proxyToManufacturing)
		mfg.POST("/routings", proxyToManufacturing)
		mfg.GET("/routings/:id", proxyToManufacturing)
		mfg.PUT("/routings/:id", proxyToManufacturing)
		mfg.DELETE("/routings/:id", proxyToManufacturing)

		// Products - proxy to inventory service with path rewrite
		proxyProductsToInventory := func(c *gin.Context) {
			// Rewrite /api/v1/manufacturing/products... to /api/v1/inventory/products...
			path := strings.Replace(c.Request.URL.Path, "/manufacturing/", "/inventory/", 1)
			if query := c.Request.URL.RawQuery; query != "" {
				path += "?" + query
			}
			proxy.ProxyRequest(c, "inventory", path)
		}
		mfg.GET("/products", proxyProductsToInventory)
		mfg.POST("/products", proxyProductsToInventory)
		mfg.GET("/products/:id", proxyProductsToInventory)
		mfg.PUT("/products/:id", proxyProductsToInventory)
		mfg.DELETE("/products/:id", proxyProductsToInventory)

		// Categories - proxy to manufacturing service
		mfg.GET("/categories", proxyToManufacturing)
		mfg.POST("/categories", proxyToManufacturing)
		mfg.GET("/categories/:id", proxyToManufacturing)
		mfg.PUT("/categories/:id", proxyToManufacturing)
		mfg.DELETE("/categories/:id", proxyToManufacturing)

		// Work Orders
		mfg.GET("/work-orders", proxyToManufacturing)
		mfg.POST("/work-orders", proxyToManufacturing)
		mfg.GET("/work-orders/:id", proxyToManufacturing)
		mfg.PUT("/work-orders/:id", proxyToManufacturing)
		mfg.DELETE("/work-orders/:id", proxyToManufacturing)
		mfg.PUT("/work-orders/:id/status", proxyToManufacturing)
	}

	// ========== FLEET SERVICE (proxied to fleet-service:8015) ==========
	proxyToFleet := func(c *gin.Context) {
		// Transform /api/v1/fleet/... to /fleet/...
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "fleet", path)
	}

	fleet := rg.Group("/fleet")
	fleet.Use(middleware.RoleMiddleware("LOGISTICS", "MANAGER"))
	{
		fleet.GET("/stats", proxyToFleet)
		fleet.GET("/vehicles", proxyToFleet)
		fleet.POST("/vehicles", proxyToFleet)
		fleet.GET("/vehicles/:id", proxyToFleet)
		fleet.PUT("/vehicles/:id", proxyToFleet)
		fleet.DELETE("/vehicles/:id", proxyToFleet)
		fleet.GET("/bookings", proxyToFleet)
		fleet.POST("/bookings", proxyToFleet)
		fleet.POST("/bookings/:id/approve", proxyToFleet)
		fleet.GET("/drivers", proxyToFleet)
		fleet.POST("/drivers", proxyToFleet)
		fleet.GET("/fuel-logs", proxyToFleet)
		fleet.POST("/fuel-logs", proxyToFleet)
		fleet.GET("/maintenance-logs", proxyToFleet)
		fleet.POST("/maintenance-logs", proxyToFleet)
	}

	// ========== PROJECTS SERVICE (proxied to projects-service:8016) ==========
	proxyToProjects := func(c *gin.Context) {
		// Transform /api/v1/projects/... to /projects/...
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "projects", path)
	}

	proj := rg.Group("/projects")
	{
		proj.GET("/stats", proxyToProjects)
		proj.GET("", proxyToProjects)
		proj.POST("", proxyToProjects)
		proj.GET("/:id", proxyToProjects)
		proj.PUT("/:id", proxyToProjects)
		proj.DELETE("/:id", proxyToProjects)
		proj.GET("/tasks", proxyToProjects)
		proj.POST("/tasks", proxyToProjects)
		proj.PUT("/tasks/:id/status", proxyToProjects)
		proj.GET("/members", proxyToProjects)
		proj.GET("/expenses", proxyToProjects)
		proj.POST("/expenses", proxyToProjects)
	}

	// ========== CRM SERVICE (proxied to crm-service:8017) ==========
	proxyToCRM := func(c *gin.Context) {
		// Transform /api/v1/crm/... to /crm/...
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "crm", path)
	}

	crm := rg.Group("/crm")
	{
		crm.GET("/stats", proxyToCRM)
		crm.GET("/leads", proxyToCRM)
		crm.POST("/leads", proxyToCRM)
		crm.GET("/leads/:id", proxyToCRM)
		crm.PUT("/leads/:id", proxyToCRM)
		crm.POST("/leads/:id/convert", proxyToCRM)
		crm.GET("/customers", proxyToCRM)
		crm.POST("/customers", proxyToCRM)
		crm.GET("/customers/:id", proxyToCRM)
		crm.PUT("/customers/:id", proxyToCRM)
		crm.GET("/opportunities", proxyToCRM)
		crm.POST("/opportunities", proxyToCRM)
		crm.GET("/activities", proxyToCRM)
		crm.POST("/activities", proxyToCRM)
	}

	// ========== PROCUREMENT SERVICE (proxied to procurement-service:8018) ==========
	proxyToProcurement := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "procurement", path)
	}

	proc := rg.Group("/procurement")
	{
		proc.GET("/stats", proxyToProcurement)
		proc.GET("/vendors", proxyToProcurement)
		proc.POST("/vendors", proxyToProcurement)
		proc.GET("/vendors/:id", proxyToProcurement)
		proc.PUT("/vendors/:id", proxyToProcurement)
		proc.GET("/purchase-requests", proxyToProcurement)
		proc.POST("/purchase-requests", proxyToProcurement)
		proc.POST("/purchase-requests/:id/approve", proxyToProcurement)
		proc.GET("/purchase-orders", proxyToProcurement)
		proc.POST("/purchase-orders", proxyToProcurement)
		proc.POST("/purchase-orders/:id/approve", proxyToProcurement)
		proc.GET("/bills", proxyToProcurement)
		proc.POST("/bills", proxyToProcurement)
	}

	// ========== LOGISTICS SERVICE (proxied to logistics-service:8019) ==========
	proxyToLogistics := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "logistics", path)
	}

	logis := rg.Group("/logistics")
	{
		logis.GET("/stats", proxyToLogistics)
		logis.GET("/deliveries", proxyToLogistics)
		logis.POST("/deliveries", proxyToLogistics)
		logis.GET("/deliveries/:id", proxyToLogistics)
		logis.PUT("/deliveries/:id/status", proxyToLogistics)
		logis.GET("/shipments", proxyToLogistics)
		logis.POST("/shipments", proxyToLogistics)
		logis.GET("/track/:tracking", proxyToLogistics)
	}

	rg.Any("/delivery/*any", proxyToLegacy("delivery"))

	// Production
	rg.Any("/mrp/*any", proxyToLegacy("mrp"))
	rg.Any("/qc/*any", proxyToLegacy("qc"))
	rg.Any("/iot/*any", proxyToLegacy("iot"))

	// Stock Operations
	rg.Any("/opname/*any", proxyToLegacy("opname"))

	// ========== SALES SERVICE (proxied to sales-service:8023) ==========
	proxyToSales := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "sales", path)
	}

	sales := rg.Group("/sales")
	{
		sales.GET("/stats", proxyToSales)
		// Quotations
		sales.GET("/quotations", proxyToSales)
		sales.POST("/quotations", proxyToSales)
		sales.GET("/quotations/:id", proxyToSales)
		sales.PUT("/quotations/:id", proxyToSales)
		sales.POST("/quotations/:id/convert", proxyToSales)
		// Orders
		sales.GET("/orders", proxyToSales)
		sales.POST("/orders", proxyToSales)
		sales.GET("/orders/:id", proxyToSales)
		sales.PUT("/orders/:id/status", proxyToSales)
		sales.POST("/orders/:id/invoice", proxyToSales)
		// Invoices
		sales.GET("/invoices", proxyToSales)
		sales.POST("/invoices", proxyToSales)
		sales.GET("/invoices/:id", proxyToSales)
		sales.POST("/invoices/:id/pay", proxyToSales)
	}

	// Finance legacy (AP/AR/Sales)
	rg.Any("/ap/*any", proxyToLegacy("ap"))
	rg.Any("/ar/*any", proxyToLegacy("ar"))
	// rg.Any("/sales/*any", proxyToLegacy("sales")) // Replaced by new service

	// ========== MAINTENANCE SERVICE (proxied to maintenance-service:8020) ==========
	proxyToMaintenance := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "maintenance", path)
	}

	maint := rg.Group("/maintenance")
	{
		maint.GET("/stats", proxyToMaintenance)
		maint.GET("/assets", proxyToMaintenance)
		maint.POST("/assets", proxyToMaintenance)
		maint.GET("/assets/:id", proxyToMaintenance)
		maint.PUT("/assets/:id", proxyToMaintenance)
		maint.GET("/work-orders", proxyToMaintenance)
		maint.POST("/work-orders", proxyToMaintenance)
		maint.PUT("/work-orders/:id/status", proxyToMaintenance)
		maint.GET("/schedules", proxyToMaintenance)
		maint.POST("/schedules", proxyToMaintenance)
	}

	// ========== POS SERVICE (proxied to pos-service:8021) ==========
	proxyToPOS := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "pos", path)
	}

	pos := rg.Group("/pos")
	pos.Use(middleware.RoleMiddleware("POS_OFFICER", "MANAGER"))
	{
		pos.GET("/stats", proxyToPOS)
		// ... existing routes
	}

	// ========== COMPLIANCE SERVICE (proxied to compliance-service:8022) ==========
	proxyToCompliance := func(c *gin.Context) {
		path := c.Request.URL.Path
		path = strings.TrimPrefix(path, "/api/v1")
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "compliance", path)
	}

	comp := rg.Group("/compliance")
	comp.Use(middleware.RoleMiddleware("COMPLIANCE_OFFICER", "MANAGER"))
	{
		comp.GET("/reports", proxyToCompliance)
		// ... existing routes
	}

	// ========== LOYALTY SERVICE (merged into finance-service) ==========
	proxyToLoyalty := func(c *gin.Context) {
		// Rewrite /api/v1/loyalty... to /finance/loyalty...
		path := strings.Replace(c.Request.URL.Path, "/api/v1/loyalty", "/finance/loyalty", 1)
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, "finance", path)
	}

	loyl := rg.Group("/loyalty")
	loyl.Use(middleware.RoleMiddleware("FINANCE", "MANAGER"))
	{
		loyl.POST("/topup", proxyToLoyalty)
		// ... existing routes
	}

	// Verticals (future Nuxt.js apps - currently return not implemented)
	rg.Any("/clinic/*any", notImplemented)
	rg.Any("/travel/*any", notImplemented)
	rg.Any("/sports/*any", notImplemented)
}

// ========== PROXY HELPERS ==========

// proxyToAuth forwards request to auth-service
func proxyToAuth(c *gin.Context) {
	path := c.Request.URL.Path
	if query := c.Request.URL.RawQuery; query != "" {
		path += "?" + query
	}
	proxy.ProxyRequest(c, "auth", path)
}

// proxyToFinance forwards request to finance-service
func proxyToFinance(c *gin.Context) {
	path := c.Request.URL.Path
	if query := c.Request.URL.RawQuery; query != "" {
		path += "?" + query
	}
	proxy.ProxyRequest(c, "finance", path)
}

// proxyToLegacy creates a handler that forwards to legacy backend
func proxyToLegacy(serviceName string) gin.HandlerFunc {
	return func(c *gin.Context) {
		path := c.Request.URL.Path
		if query := c.Request.URL.RawQuery; query != "" {
			path += "?" + query
		}
		proxy.ProxyRequest(c, serviceName, path)
	}
}

// notImplemented returns 501 for services not yet implemented
func notImplemented(c *gin.Context) {
	c.JSON(501, gin.H{
		"error":   "not_implemented",
		"message": "This service is not yet implemented. Coming soon!",
	})
}
