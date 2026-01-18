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
  <title>Mini-ERP API Documentation</title>
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

// OpenAPISpec returns the comprehensive OpenAPI specification for ALL services
func OpenAPISpec(c *gin.Context) {
	spec := map[string]interface{}{
		"openapi": "3.0.3",
		"info": map[string]interface{}{
			"title":       "Mini-ERP API Gateway",
			"version":     "1.0.0",
			"description": "Enterprise Resource Planning API with Microservices Architecture. This is the centralized API documentation for all Mini-ERP services.",
			"contact": map[string]string{
				"name":  "API Support",
				"email": "support@mini-erp.io",
			},
		},
		"servers": []map[string]string{
			{"url": "http://localhost:8000", "description": "Development - API Gateway"},
		},
		"tags": []map[string]string{
			{"name": "Auth", "description": "Authentication & Authorization"},
			{"name": "Users", "description": "User Management"},
			{"name": "Finance", "description": "Financial Management (GL, AR, AP, Banking)"},
			{"name": "HR", "description": "Human Resources (Employees, Attendance, Payroll)"},
			{"name": "Inventory", "description": "Inventory Management (Products, Stock, Opname)"},
			{"name": "CRM", "description": "Customer Relationship Management"},
			{"name": "Procurement", "description": "Procurement (PR, PO, Vendors)"},
			{"name": "Manufacturing", "description": "Manufacturing (Production, BOM)"},
			{"name": "Fleet", "description": "Fleet Management (Vehicles, Bookings)"},
			{"name": "Projects", "description": "Project Management"},
			{"name": "Maintenance", "description": "Asset Maintenance"},
			{"name": "POS", "description": "Point of Sale"},
			{"name": "Marketplace", "description": "E-commerce Integration"},
			{"name": "Clinic", "description": "Clinic Management"},
			{"name": "Travel", "description": "Travel & Booking"},
			{"name": "Sports", "description": "Sports Training Management"},
		},
		"paths": buildAllPaths(),
		"components": map[string]interface{}{
			"schemas":         buildSchemas(),
			"securitySchemes": buildSecuritySchemes(),
		},
	}
	c.JSON(http.StatusOK, spec)
}

func buildSecuritySchemes() map[string]interface{} {
	return map[string]interface{}{
		"BearerAuth": map[string]interface{}{
			"type":         "http",
			"scheme":       "bearer",
			"bearerFormat": "JWT",
			"description":  "Enter your JWT token",
		},
	}
}

func buildSchemas() map[string]interface{} {
	return map[string]interface{}{
		// Auth Schemas
		"LoginRequest": map[string]interface{}{
			"type":     "object",
			"required": []string{"email", "password"},
			"properties": map[string]interface{}{
				"email":    map[string]interface{}{"type": "string", "format": "email", "example": "user@example.com"},
				"password": map[string]interface{}{"type": "string", "minLength": 6, "example": "password123"},
			},
		},
		"RegisterRequest": map[string]interface{}{
			"type":     "object",
			"required": []string{"email", "password", "first_name"},
			"properties": map[string]interface{}{
				"email":      map[string]interface{}{"type": "string", "format": "email"},
				"password":   map[string]interface{}{"type": "string", "minLength": 6},
				"first_name": map[string]interface{}{"type": "string"},
				"last_name":  map[string]interface{}{"type": "string"},
				"tenant_id":  map[string]interface{}{"type": "string", "format": "uuid"},
			},
		},
		"TokenResponse": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"access_token":  map[string]interface{}{"type": "string"},
				"refresh_token": map[string]interface{}{"type": "string"},
				"token_type":    map[string]interface{}{"type": "string", "example": "Bearer"},
				"expires_in":    map[string]interface{}{"type": "integer", "example": 86400},
			},
		},
		"UserResponse": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"id":         map[string]interface{}{"type": "string", "format": "uuid"},
				"email":      map[string]interface{}{"type": "string", "format": "email"},
				"first_name": map[string]interface{}{"type": "string"},
				"last_name":  map[string]interface{}{"type": "string"},
				"tenant_id":  map[string]interface{}{"type": "string", "format": "uuid"},
				"is_admin":   map[string]interface{}{"type": "boolean"},
			},
		},
		// Generic Schemas
		"PaginatedResponse": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"data":  map[string]interface{}{"type": "array", "items": map[string]interface{}{}},
				"total": map[string]interface{}{"type": "integer"},
				"page":  map[string]interface{}{"type": "integer"},
				"limit": map[string]interface{}{"type": "integer"},
			},
		},
		"ErrorResponse": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"error":   map[string]interface{}{"type": "string"},
				"message": map[string]interface{}{"type": "string"},
			},
		},
		// Finance Schemas
		"ChartOfAccount": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"id":           map[string]interface{}{"type": "string", "format": "uuid"},
				"code":         map[string]interface{}{"type": "string"},
				"name":         map[string]interface{}{"type": "string"},
				"account_type": map[string]interface{}{"type": "string", "enum": []string{"asset", "liability", "equity", "revenue", "expense"}},
				"balance":      map[string]interface{}{"type": "number"},
			},
		},
		// HR Schemas
		"Employee": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"id":            map[string]interface{}{"type": "string", "format": "uuid"},
				"employee_code": map[string]interface{}{"type": "string"},
				"first_name":    map[string]interface{}{"type": "string"},
				"last_name":     map[string]interface{}{"type": "string"},
				"email":         map[string]interface{}{"type": "string", "format": "email"},
				"department_id": map[string]interface{}{"type": "string", "format": "uuid"},
				"position_id":   map[string]interface{}{"type": "string", "format": "uuid"},
				"status":        map[string]interface{}{"type": "string"},
			},
		},
		// Inventory Schemas
		"Product": map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"id":            map[string]interface{}{"type": "string", "format": "uuid"},
				"sku":           map[string]interface{}{"type": "string"},
				"name":          map[string]interface{}{"type": "string"},
				"category_id":   map[string]interface{}{"type": "string", "format": "uuid"},
				"cost_price":    map[string]interface{}{"type": "number"},
				"selling_price": map[string]interface{}{"type": "number"},
			},
		},
	}
}

func buildAllPaths() map[string]interface{} {
	paths := make(map[string]interface{})

	// ========== HEALTH ==========
	paths["/health"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":    []string{"Health"},
			"summary": "Health check",
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Service is healthy"},
			},
		},
	}

	// ========== AUTH ENDPOINTS ==========
	paths["/api/v1/auth/login"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":        []string{"Auth"},
			"summary":     "User login",
			"description": "Authenticate user and return JWT tokens",
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{"$ref": "#/components/schemas/LoginRequest"},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{
					"description": "Successful login",
					"content": map[string]interface{}{
						"application/json": map[string]interface{}{
							"schema": map[string]interface{}{"$ref": "#/components/schemas/TokenResponse"},
						},
					},
				},
				"401": map[string]interface{}{"description": "Invalid credentials"},
			},
		},
	}

	paths["/api/v1/auth/register"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":        []string{"Auth"},
			"summary":     "User registration",
			"description": "Register a new user account",
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{"$ref": "#/components/schemas/RegisterRequest"},
					},
				},
			},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "User created successfully"},
				"400": map[string]interface{}{"description": "Invalid request data"},
				"409": map[string]interface{}{"description": "Email already exists"},
			},
		},
	}

	paths["/api/v1/auth/refresh"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":    []string{"Auth"},
			"summary": "Refresh access token",
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"refresh_token"},
							"properties": map[string]interface{}{
								"refresh_token": map[string]interface{}{"type": "string"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Token refreshed"},
				"401": map[string]interface{}{"description": "Invalid refresh token"},
			},
		},
	}

	paths["/api/v1/auth/me"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Auth"},
			"summary":  "Get current user",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{
					"description": "User profile",
					"content": map[string]interface{}{
						"application/json": map[string]interface{}{
							"schema": map[string]interface{}{"$ref": "#/components/schemas/UserResponse"},
						},
					},
				},
				"401": map[string]interface{}{"description": "Unauthorized"},
			},
		},
	}

	paths["/api/v1/auth/logout"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Auth"},
			"summary":  "User logout",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Logged out successfully"},
			},
		},
	}

	paths["/api/v1/auth/forgot-password"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":    []string{"Auth"},
			"summary": "Forgot password",
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":       "object",
							"required":   []string{"email"},
							"properties": map[string]interface{}{"email": map[string]interface{}{"type": "string", "format": "email"}},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Reset email sent if account exists"},
			},
		},
	}

	paths["/api/v1/auth/verify-otp"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":    []string{"Auth"},
			"summary": "Verify OTP",
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"email", "otp"},
							"properties": map[string]interface{}{
								"email": map[string]interface{}{"type": "string", "format": "email"},
								"otp":   map[string]interface{}{"type": "string"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "OTP verified"},
				"400": map[string]interface{}{"description": "Invalid OTP"},
			},
		},
	}

	// ========== USERS ==========
	paths["/api/v1/users"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Users"},
			"summary":  "List users",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "page", "in": "query", "schema": map[string]interface{}{"type": "integer", "default": 1}},
				{"name": "limit", "in": "query", "schema": map[string]interface{}{"type": "integer", "default": 10}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of users"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Users"},
			"summary":  "Create user",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "User created"},
			},
		},
	}

	// ========== FINANCE: COA ==========
	paths["/api/v1/finance/coa"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":        []string{"Finance"},
			"summary":     "List Chart of Accounts (hierarchical)",
			"description": "Returns hierarchical COA structure with parent-child relationships",
			"security":    []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Hierarchical list of accounts"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Create account",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"code", "name", "type"},
							"properties": map[string]interface{}{
								"code":      map[string]interface{}{"type": "string", "example": "1150"},
								"name":      map[string]interface{}{"type": "string", "example": "Prepaid Expenses"},
								"type":      map[string]interface{}{"type": "string", "enum": []string{"Asset", "Liability", "Equity", "Income", "Expense"}},
								"parent_id": map[string]interface{}{"type": "string", "format": "uuid"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Account created"},
			},
		},
	}

	paths["/api/v1/finance/coa/{account_id}"] = map[string]interface{}{
		"put": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Update account",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Account updated"},
			},
		},
	}

	paths["/api/v1/finance/coa/seed"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Seed standard COA template",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "COA seeded with standard template"},
			},
		},
	}

	// ========== FINANCE: GENERAL LEDGER ==========
	paths["/api/v1/finance/gl"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":        []string{"Finance"},
			"summary":     "Get General Ledger for account",
			"description": "Returns journal entries for an account with running balance",
			"security":    []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "query", "required": true, "schema": map[string]interface{}{"type": "string"}},
				{"name": "date_from", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
				{"name": "date_to", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "GL entries with running balance"},
			},
		},
	}

	paths["/api/v1/finance/journal"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":        []string{"Finance"},
			"summary":     "Create journal entry",
			"description": "Creates a balanced journal entry (total debit = total credit)",
			"security":    []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"date", "description", "details"},
							"properties": map[string]interface{}{
								"date":        map[string]interface{}{"type": "string", "format": "date"},
								"description": map[string]interface{}{"type": "string"},
								"details": map[string]interface{}{
									"type": "array",
									"items": map[string]interface{}{
										"type": "object",
										"properties": map[string]interface{}{
											"account_id": map[string]interface{}{"type": "string"},
											"debit":      map[string]interface{}{"type": "number"},
											"credit":     map[string]interface{}{"type": "number"},
										},
									},
								},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Journal entry created and posted"},
				"400": map[string]interface{}{"description": "Journal entry not balanced"},
			},
		},
	}

	// ========== FINANCE: FISCAL PERIODS ==========
	paths["/api/v1/finance/periods"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "List fiscal periods",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of fiscal periods"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Create fiscal period",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"name", "start_date", "end_date"},
							"properties": map[string]interface{}{
								"name":       map[string]interface{}{"type": "string"},
								"start_date": map[string]interface{}{"type": "string", "format": "date"},
								"end_date":   map[string]interface{}{"type": "string", "format": "date"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Period created"},
			},
		},
	}

	paths["/api/v1/finance/periods/{id}/close"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Close fiscal period",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Period closed"},
			},
		},
	}

	// ========== FINANCE: FIXED ASSETS ==========
	paths["/api/v1/finance/assets"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Create fixed asset",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"name", "code", "acquisition_date", "acquisition_cost", "useful_life_months"},
							"properties": map[string]interface{}{
								"name":               map[string]interface{}{"type": "string"},
								"code":               map[string]interface{}{"type": "string"},
								"category":           map[string]interface{}{"type": "string"},
								"acquisition_date":   map[string]interface{}{"type": "string", "format": "date"},
								"acquisition_cost":   map[string]interface{}{"type": "number"},
								"useful_life_months": map[string]interface{}{"type": "integer"},
								"salvage_value":      map[string]interface{}{"type": "number"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Asset created"},
			},
		},
	}

	paths["/api/v1/finance/assets/{id}/depreciate"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Run depreciation for asset",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Depreciation posted"},
			},
		},
	}

	// ========== FINANCE: REPORTS ==========
	paths["/api/v1/finance/reports/trial-balance"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Get Trial Balance report",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Trial balance with debit/credit totals"},
			},
		},
	}

	paths["/api/v1/finance/reports/pl"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Get Profit & Loss statement",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "start_date", "in": "query", "required": true, "schema": map[string]interface{}{"type": "string", "format": "date"}},
				{"name": "end_date", "in": "query", "required": true, "schema": map[string]interface{}{"type": "string", "format": "date"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "P&L report with revenue, expenses, net income"},
			},
		},
	}

	paths["/api/v1/finance/reports/balance-sheet"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Get Balance Sheet report",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "date", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Balance sheet with assets, liabilities, equity"},
			},
		},
	}

	// ========== FINANCE: BANKING ACCOUNTS ==========
	paths["/api/v1/finance/banking/accounts"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "List bank accounts",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of bank accounts"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Create bank account",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"code", "name"},
							"properties": map[string]interface{}{
								"code":            map[string]interface{}{"type": "string"},
								"name":            map[string]interface{}{"type": "string"},
								"bank_name":       map[string]interface{}{"type": "string"},
								"account_number":  map[string]interface{}{"type": "string"},
								"account_holder":  map[string]interface{}{"type": "string"},
								"account_type":    map[string]interface{}{"type": "string", "enum": []string{"Checking", "Savings", "Credit", "Cash"}},
								"currency_code":   map[string]interface{}{"type": "string", "default": "IDR"},
								"opening_balance": map[string]interface{}{"type": "number"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Bank account created"},
			},
		},
	}

	paths["/api/v1/finance/banking/accounts/{account_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Get bank account details",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Bank account details"},
			},
		},
		"put": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Update bank account",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Bank account updated"},
			},
		},
		"delete": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Deactivate bank account",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Bank account deactivated"},
			},
		},
	}

	// ========== FINANCE: BANKING TRANSACTIONS ==========
	paths["/api/v1/finance/banking/transactions"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "List bank transactions",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "bank_account_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "transaction_type", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "date_from", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
				{"name": "date_to", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of bank transactions"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Create bank transaction",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"bank_account_id", "amount"},
							"properties": map[string]interface{}{
								"bank_account_id":   map[string]interface{}{"type": "string"},
								"transaction_date":  map[string]interface{}{"type": "string", "format": "date-time"},
								"transaction_type":  map[string]interface{}{"type": "string", "enum": []string{"Deposit", "Withdrawal", "Transfer In", "Transfer Out"}},
								"amount":            map[string]interface{}{"type": "number"},
								"counterparty_name": map[string]interface{}{"type": "string"},
								"description":       map[string]interface{}{"type": "string"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Transaction created"},
			},
		},
	}

	paths["/api/v1/finance/banking/transactions/{transaction_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Get bank transaction details",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "transaction_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Transaction details"},
			},
		},
	}

	// ========== FINANCE: RECONCILIATION ==========
	paths["/api/v1/finance/banking/reconciliation/{account_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":        []string{"Finance"},
			"summary":     "Get unreconciled transactions",
			"description": "Returns transactions pending reconciliation for a bank account",
			"security":    []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "account_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Unreconciled transactions and book balance"},
			},
		},
	}

	paths["/api/v1/finance/banking/reconciliation/mark"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Mark transactions as reconciled",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"transaction_ids"},
							"properties": map[string]interface{}{
								"transaction_ids": map[string]interface{}{"type": "array", "items": map[string]interface{}{"type": "string"}},
								"statement_date":  map[string]interface{}{"type": "string", "format": "date"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Transactions marked as reconciled"},
			},
		},
	}

	paths["/api/v1/finance/banking/reconciliations"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "List reconciliation records",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "bank_account_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of reconciliation records"},
			},
		},
	}

	// ========== FINANCE: PETTY CASH ==========
	paths["/api/v1/finance/banking/petty-cash"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "List petty cash transactions with current balance",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Petty cash balance and transactions"},
			},
		},
	}

	paths["/api/v1/finance/banking/petty-cash/expense"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Record petty cash expense",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"amount"},
							"properties": map[string]interface{}{
								"date":         map[string]interface{}{"type": "string", "format": "date"},
								"amount":       map[string]interface{}{"type": "number"},
								"category":     map[string]interface{}{"type": "string"},
								"description":  map[string]interface{}{"type": "string"},
								"requested_by": map[string]interface{}{"type": "string"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Expense recorded"},
			},
		},
	}

	paths["/api/v1/finance/banking/petty-cash/replenish"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"Finance"},
			"summary":  "Replenish petty cash",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"requestBody": map[string]interface{}{
				"required": true,
				"content": map[string]interface{}{
					"application/json": map[string]interface{}{
						"schema": map[string]interface{}{
							"type":     "object",
							"required": []string{"amount"},
							"properties": map[string]interface{}{
								"date":              map[string]interface{}{"type": "string", "format": "date"},
								"amount":            map[string]interface{}{"type": "number"},
								"source_account_id": map[string]interface{}{"type": "string"},
								"description":       map[string]interface{}{"type": "string"},
							},
						},
					},
				},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Petty cash replenished"},
			},
		},
	}

	// ========== HR: DASHBOARD ==========
	paths["/api/v1/hr/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Get HR dashboard statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Dashboard stats including employee counts, attendance, leave"},
			},
		},
	}

	paths["/api/v1/hr/managers"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "List managers for department assignment",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of managers"},
			},
		},
	}

	// ========== HR: DEPARTMENTS ==========
	paths["/api/v1/hr/departments"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "List departments",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of departments"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Create department",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Department created"},
			},
		},
	}

	paths["/api/v1/hr/departments/{dept_id}"] = map[string]interface{}{
		"put": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Update department",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "dept_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Updated"}},
		},
		"delete": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Delete department",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "dept_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Deleted"}},
		},
	}

	// ========== HR: POSITIONS ==========
	paths["/api/v1/hr/positions"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "List positions",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of positions"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Create position",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Position created"},
			},
		},
	}

	paths["/api/v1/hr/positions/{pos_id}"] = map[string]interface{}{
		"put": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Update position",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "pos_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Updated"}},
		},
		"delete": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Delete position",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "pos_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Deleted"}},
		},
	}

	// ========== HR: EMPLOYEES ==========
	paths["/api/v1/hr/employees"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "List employees",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "department_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "search", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of employees"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Create employee",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Employee created with auto-generated code"},
			},
		},
	}

	paths["/api/v1/hr/employees/{employee_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Get employee details",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Employee details"}},
		},
		"put": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Update employee",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Updated"}},
		},
		"delete": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Terminate employee",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Terminated"}},
		},
	}

	paths["/api/v1/hr/employees/{employee_id}/documents"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "List employee documents",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Documents list"}},
		},
		"post": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Add employee document",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Document added"}},
		},
	}

	paths["/api/v1/hr/employees/{employee_id}/register-face"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Register face for attendance",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Face registered"}},
		},
	}

	// ========== HR: SHIFTS ==========
	paths["/api/v1/hr/shifts"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "List shifts",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "List of shifts"}},
		},
		"post": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "Create shift",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Shift created"}},
		},
	}

	paths["/api/v1/hr/shifts/{shift_id}"] = map[string]interface{}{
		"put": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Update shift",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "shift_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Updated"}},
		},
		"delete": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Delete shift",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "shift_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Deleted"}},
		},
	}

	// ========== HR: ATTENDANCE ==========
	paths["/api/v1/hr/attendance"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "List attendance records",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "start_date", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
				{"name": "end_date", "in": "query", "schema": map[string]interface{}{"type": "string", "format": "date"}},
				{"name": "employee_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Attendance records with work hours"},
			},
		},
	}

	paths["/api/v1/hr/attendance/check-in"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Employee check-in",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Checked in successfully"},
			},
		},
	}

	paths["/api/v1/hr/attendance/check-out"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Employee check-out",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Checked out with work hours calculated"},
			},
		},
	}

	paths["/api/v1/hr/attendance/face-check-in"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":     []string{"HR"},
			"summary":  "Face recognition check-in",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Face matched and checked in"},
			},
		},
	}

	// ========== HR: LEAVE ==========
	paths["/api/v1/hr/leave-types"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "List leave types",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Leave types"}},
		},
		"post": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "Create leave type",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Leave type created"}},
		},
	}

	paths["/api/v1/hr/leave-requests"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "List leave requests",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Leave requests"}},
		},
		"post": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "Submit leave request",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Request submitted"}},
		},
	}

	paths["/api/v1/hr/leave-requests/{request_id}/approve"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Approve/reject leave request",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "request_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Request approved/rejected"}},
		},
	}

	paths["/api/v1/hr/leave-balance/{employee_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Get employee leave balance",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "employee_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Leave balances by type"}},
		},
	}

	// ========== HR: PAYROLL ==========
	paths["/api/v1/hr/payroll/periods"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "List payroll periods",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Payroll periods"}},
		},
		"post": map[string]interface{}{
			"tags":      []string{"HR"},
			"summary":   "Create payroll period",
			"security":  []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{"200": map[string]interface{}{"description": "Period created"}},
		},
	}

	paths["/api/v1/hr/payroll/periods/{period_id}/run"] = map[string]interface{}{
		"post": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Run payroll calculation",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "period_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Payroll calculated"}},
		},
	}

	paths["/api/v1/hr/payroll/periods/{period_id}/payslips"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "List payslips for period",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "period_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Payslips list"}},
		},
	}

	paths["/api/v1/hr/payroll/payslips/{payslip_id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":       []string{"HR"},
			"summary":    "Get payslip details",
			"security":   []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{{"name": "payslip_id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}}},
			"responses":  map[string]interface{}{"200": map[string]interface{}{"description": "Detailed payslip"}},
		},
	}

	// ========== INVENTORY ==========
	paths["/api/v1/inventory/products"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "List products",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "category_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "search", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "type", "in": "query", "schema": map[string]interface{}{"type": "string"}, "description": "Filter by type: RAW_MATERIAL, FINISHED_GOOD"},
				{"name": "is_active", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of products"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Create product",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Product created"},
			},
		},
	}

	paths["/api/v1/inventory/products/{id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Get product by ID",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Product details"},
			},
		},
		"put": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Update product",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Product updated"},
			},
		},
		"delete": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Delete product",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Product deleted"},
			},
		},
	}

	paths["/api/v1/inventory/warehouses"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "List warehouses",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of warehouses"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Create warehouse",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Warehouse created"},
			},
		},
	}

	paths["/api/v1/inventory/warehouses/{id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Get warehouse by ID",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Warehouse details"},
			},
		},
		"put": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Update warehouse",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Warehouse updated"},
			},
		},
	}

	paths["/api/v1/inventory/stock"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Get stock levels",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "warehouse_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "product_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Stock levels"},
			},
		},
	}

	paths["/api/v1/inventory/movements"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "List stock movements",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "movement_type", "in": "query", "schema": map[string]interface{}{"type": "string"}, "description": "IN, OUT, TRANSFER, ADJUSTMENT"},
				{"name": "warehouse_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of stock movements"},
			},
		},
	}

	paths["/api/v1/inventory/opnames"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "List stock opnames",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}, "description": "DRAFT, IN_PROGRESS, COMPLETED"},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of stock opnames"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Create stock opname",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Stock opname created"},
			},
		},
	}

	paths["/api/v1/inventory/opnames/{id}"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Get opname by ID",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "id", "in": "path", "required": true, "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Opname details"},
			},
		},
	}

	paths["/api/v1/inventory/locations"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Inventory"},
			"summary":  "Get locations hierarchy (Warehouses -> Floors -> Rooms)",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Locations hierarchy"},
			},
		},
	}

	// ========== CRM ==========
	paths["/api/v1/crm/customers"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List customers",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of customers"},
			},
		},
	}

	paths["/api/v1/crm/leads"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List leads",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of leads"},
			},
		},
	}

	// ========== MANUFACTURING ==========
	paths["/api/v1/manufacturing/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "Get manufacturing statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Manufacturing stats"},
			},
		},
	}

	paths["/api/v1/manufacturing/work-centers"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "List work centers",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of work centers"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "Create work center",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Work center created"},
			},
		},
	}

	paths["/api/v1/manufacturing/production-orders"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "List production orders",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}, "description": "DRAFT, IN_PROGRESS, COMPLETED"},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of production orders"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "Create production order",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Production order created"},
			},
		},
	}

	paths["/api/v1/manufacturing/bom"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Manufacturing"},
			"summary":  "List BOM items",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of BOM items"},
			},
		},
	}

	// ========== FLEET ==========
	paths["/api/v1/fleet/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "Get fleet statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Fleet stats"},
			},
		},
	}

	paths["/api/v1/fleet/vehicles"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "List vehicles",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}, "description": "AVAILABLE, BOOKED, MAINTENANCE"},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of vehicles"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "Create vehicle",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Vehicle created"},
			},
		},
	}

	paths["/api/v1/fleet/bookings"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "List vehicle bookings",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of bookings"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "Create booking",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Booking created"},
			},
		},
	}

	paths["/api/v1/fleet/drivers"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "List drivers",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of drivers"},
			},
		},
	}

	paths["/api/v1/fleet/fuel-logs"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "List fuel logs",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of fuel logs"},
			},
		},
	}

	paths["/api/v1/fleet/maintenance-logs"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Fleet"},
			"summary":  "List maintenance logs",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of maintenance logs"},
			},
		},
	}

	// ========== PROJECTS ==========
	paths["/api/v1/projects/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "Get project statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Project stats with standardized response"},
			},
		},
	}

	paths["/api/v1/projects"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "List projects with pagination",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "page", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "limit", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of projects with pagination"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "Create project",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Project created"},
			},
		},
	}

	paths["/api/v1/projects/tasks"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "List project tasks",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "project_id", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of tasks"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "Create task",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Task created"},
			},
		},
	}

	paths["/api/v1/projects/members"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "List project members",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of members"},
			},
		},
	}

	paths["/api/v1/projects/expenses"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "List project expenses",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of expenses"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Projects"},
			"summary":  "Create expense",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Expense created"},
			},
		},
	}

	// ========== CRM ==========
	paths["/api/v1/crm/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "Get CRM statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "CRM stats"},
			},
		},
	}

	paths["/api/v1/crm/leads"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List leads with pagination",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "page", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "limit", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "status", "in": "query", "schema": map[string]interface{}{"type": "string"}},
				{"name": "source", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of leads"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "Create lead",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Lead created"},
			},
		},
	}

	paths["/api/v1/crm/customers"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List customers with pagination",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "page", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "limit", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "search", "in": "query", "schema": map[string]interface{}{"type": "string"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of customers"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "Create customer",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Customer created"},
			},
		},
	}

	paths["/api/v1/crm/opportunities"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List opportunities",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of opportunities"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "Create opportunity",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Opportunity created"},
			},
		},
	}

	paths["/api/v1/crm/activities"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "List activities",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of activities"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"CRM"},
			"summary":  "Create activity",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Activity created"},
			},
		},
	}

	// ========== PROCUREMENT ==========
	paths["/api/v1/procurement/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "Get procurement statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Procurement stats"},
			},
		},
	}

	paths["/api/v1/procurement/vendors"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "List vendors with pagination",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"parameters": []map[string]interface{}{
				{"name": "page", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
				{"name": "limit", "in": "query", "schema": map[string]interface{}{"type": "integer"}},
			},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of vendors"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "Create vendor",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Vendor created"},
			},
		},
	}

	paths["/api/v1/procurement/purchase-requests"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "List purchase requests",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of PRs"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "Create purchase request",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "PR created"},
			},
		},
	}

	paths["/api/v1/procurement/purchase-orders"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "List purchase orders",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of POs"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "Create purchase order",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "PO created"},
			},
		},
	}

	paths["/api/v1/procurement/bills"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Procurement"},
			"summary":  "List vendor bills",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of bills"},
			},
		},
	}

	// ========== LOGISTICS ==========
	paths["/api/v1/logistics/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Logistics"},
			"summary":  "Get logistics statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Logistics stats"},
			},
		},
	}

	paths["/api/v1/logistics/deliveries"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Logistics"},
			"summary":  "List delivery orders",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of deliveries"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Logistics"},
			"summary":  "Create delivery order",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Delivery created"},
			},
		},
	}

	paths["/api/v1/logistics/shipments"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Logistics"},
			"summary":  "List shipments",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of shipments"},
			},
		},
	}

	// ========== MAINTENANCE ==========
	paths["/api/v1/maintenance/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "Get maintenance statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Maintenance stats"},
			},
		},
	}

	paths["/api/v1/maintenance/assets"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "List assets",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of assets"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "Create asset",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Asset created"},
			},
		},
	}

	paths["/api/v1/maintenance/work-orders"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "List work orders",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of work orders"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "Create work order",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Work order created"},
			},
		},
	}

	paths["/api/v1/maintenance/schedules"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Maintenance"},
			"summary":  "List maintenance schedules",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of schedules"},
			},
		},
	}

	// ========== POS ==========
	paths["/api/v1/pos/stats"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"POS"},
			"summary":  "Get POS statistics",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "POS stats"},
			},
		},
	}

	paths["/api/v1/pos/transactions"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"POS"},
			"summary":  "List POS transactions",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of transactions"},
			},
		},
		"post": map[string]interface{}{
			"tags":     []string{"POS"},
			"summary":  "Create POS transaction",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"201": map[string]interface{}{"description": "Transaction created"},
			},
		},
	}

	paths["/api/v1/pos/promos"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"POS"},
			"summary":  "List promos",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of promos"},
			},
		},
	}

	paths["/api/v1/pos/reports/daily"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"POS"},
			"summary":  "Daily sales report",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "Daily report"},
			},
		},
	}

	// ========== CLINIC ==========
	paths["/api/v1/clinic/appointments"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Clinic"},
			"summary":  "List appointments",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of appointments"},
			},
		},
	}

	paths["/api/v1/clinic/doctors"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Clinic"},
			"summary":  "List doctors",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of doctors"},
			},
		},
	}

	paths["/api/v1/clinic/patients"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Clinic"},
			"summary":  "List patients",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of patients"},
			},
		},
	}

	// ========== TRAVEL ==========
	paths["/api/v1/travel/tickets"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Travel"},
			"summary":  "List tickets",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of tickets"},
			},
		},
	}

	// ========== SPORTS ==========
	paths["/api/v1/sports/training-programs"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Sports"},
			"summary":  "List training programs",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of programs"},
			},
		},
	}

	paths["/api/v1/sports/athletes"] = map[string]interface{}{
		"get": map[string]interface{}{
			"tags":     []string{"Sports"},
			"summary":  "List athletes",
			"security": []map[string]interface{}{{"BearerAuth": []string{}}},
			"responses": map[string]interface{}{
				"200": map[string]interface{}{"description": "List of athletes"},
			},
		},
	}

	return paths
}
