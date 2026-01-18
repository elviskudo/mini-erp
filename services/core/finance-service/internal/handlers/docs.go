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
  <title>Finance Service - API Documentation</title>
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

// OpenAPISpec returns the OpenAPI specification for Finance Service
func OpenAPISpec(c *gin.Context) {
	spec := gin.H{
		"openapi": "3.0.3",
		"info": gin.H{
			"title":       "Mini-ERP Finance Service API",
			"version":     "1.0.0",
			"description": "Financial Management Service - Chart of Accounts, General Ledger, Journal Entries, Fiscal Periods, Fixed Assets, Reports, Banking, Reconciliation, Petty Cash",
		},
		"servers": []gin.H{
			{"url": "http://localhost:8011", "description": "Development server"},
			{"url": "http://localhost:8000/api/v1", "description": "Via API Gateway"},
		},
		"tags": []gin.H{
			{"name": "COA", "description": "Chart of Accounts Management"},
			{"name": "General Ledger", "description": "GL Queries & Journal Entries"},
			{"name": "Periods", "description": "Fiscal Period Management"},
			{"name": "Assets", "description": "Fixed Asset Management & Depreciation"},
			{"name": "Reports", "description": "Financial Reports"},
			{"name": "Banking", "description": "Bank Account & Transaction Management"},
			{"name": "Reconciliation", "description": "Bank Reconciliation"},
			{"name": "Petty Cash", "description": "Petty Cash Management"},
		},
		"paths": buildPaths(),
		"components": gin.H{
			"schemas":         buildSchemas(),
			"securitySchemes": buildSecuritySchemes(),
		},
	}
	c.JSON(http.StatusOK, spec)
}

func buildPaths() gin.H {
	return gin.H{
		// ========== COA ==========
		"/finance/coa": gin.H{
			"get": gin.H{
				"tags":        []string{"COA"},
				"summary":     "List Chart of Accounts (hierarchical)",
				"description": "Returns hierarchical COA structure with parent-child relationships",
				"responses":   successResponse("List of accounts"),
			},
			"post": gin.H{
				"tags":        []string{"COA"},
				"summary":     "Create account",
				"requestBody": jsonBody("AccountCreate"),
				"responses":   successResponse("Account created"),
			},
		},
		"/finance/coa/{account_id}": gin.H{
			"put": gin.H{
				"tags":        []string{"COA"},
				"summary":     "Update account",
				"parameters":  []gin.H{pathParam("account_id", "Account ID")},
				"requestBody": jsonBody("AccountCreate"),
				"responses":   successResponse("Account updated"),
			},
		},
		"/finance/coa/seed": gin.H{
			"post": gin.H{
				"tags":      []string{"COA"},
				"summary":   "Seed standard COA template",
				"responses": successResponse("COA seeded"),
			},
		},
		// ========== GENERAL LEDGER ==========
		"/finance/gl": gin.H{
			"get": gin.H{
				"tags":    []string{"General Ledger"},
				"summary": "Get General Ledger for account",
				"parameters": []gin.H{
					queryParam("account_id", "Account ID", true),
					queryParam("date_from", "Start date", false),
					queryParam("date_to", "End date", false),
				},
				"responses": successResponse("GL entries with running balance"),
			},
		},
		"/finance/journal": gin.H{
			"post": gin.H{
				"tags":        []string{"General Ledger"},
				"summary":     "Create journal entry",
				"description": "Creates a balanced journal entry (debit = credit)",
				"requestBody": jsonBody("JournalEntryCreate"),
				"responses":   successResponse("Journal entry created"),
			},
		},
		// ========== FISCAL PERIODS ==========
		"/finance/periods": gin.H{
			"get": gin.H{
				"tags":      []string{"Periods"},
				"summary":   "List fiscal periods",
				"responses": successResponse("List of periods"),
			},
			"post": gin.H{
				"tags":        []string{"Periods"},
				"summary":     "Create fiscal period",
				"requestBody": jsonBody("PeriodCreate"),
				"responses":   successResponse("Period created"),
			},
		},
		"/finance/periods/{id}/close": gin.H{
			"post": gin.H{
				"tags":       []string{"Periods"},
				"summary":    "Close fiscal period",
				"parameters": []gin.H{pathParam("id", "Period ID")},
				"responses":  successResponse("Period closed"),
			},
		},
		// ========== FIXED ASSETS ==========
		"/finance/assets": gin.H{
			"post": gin.H{
				"tags":        []string{"Assets"},
				"summary":     "Create fixed asset",
				"requestBody": jsonBody("AssetCreate"),
				"responses":   successResponse("Asset created"),
			},
		},
		"/finance/assets/{id}/depreciate": gin.H{
			"post": gin.H{
				"tags":       []string{"Assets"},
				"summary":    "Run depreciation for asset",
				"parameters": []gin.H{pathParam("id", "Asset ID")},
				"responses":  successResponse("Depreciation posted"),
			},
		},
		// ========== REPORTS ==========
		"/finance/reports/trial-balance": gin.H{
			"get": gin.H{
				"tags":      []string{"Reports"},
				"summary":   "Get Trial Balance",
				"responses": successResponse("Trial balance report"),
			},
		},
		"/finance/reports/pl": gin.H{
			"get": gin.H{
				"tags":    []string{"Reports"},
				"summary": "Get Profit & Loss Statement",
				"parameters": []gin.H{
					queryParam("start_date", "Start date (YYYY-MM-DD)", true),
					queryParam("end_date", "End date (YYYY-MM-DD)", true),
				},
				"responses": successResponse("P&L report"),
			},
		},
		"/finance/reports/balance-sheet": gin.H{
			"get": gin.H{
				"tags":    []string{"Reports"},
				"summary": "Get Balance Sheet",
				"parameters": []gin.H{
					queryParam("date", "As of date (YYYY-MM-DD)", false),
				},
				"responses": successResponse("Balance sheet report"),
			},
		},
		// ========== BANKING ACCOUNTS ==========
		"/finance/banking/accounts": gin.H{
			"get": gin.H{
				"tags":      []string{"Banking"},
				"summary":   "List bank accounts",
				"responses": successResponse("List of bank accounts"),
			},
			"post": gin.H{
				"tags":        []string{"Banking"},
				"summary":     "Create bank account",
				"requestBody": jsonBody("BankAccountCreate"),
				"responses":   successResponse("Bank account created"),
			},
		},
		"/finance/banking/accounts/{account_id}": gin.H{
			"get": gin.H{
				"tags":       []string{"Banking"},
				"summary":    "Get bank account",
				"parameters": []gin.H{pathParam("account_id", "Bank Account ID")},
				"responses":  successResponse("Bank account details"),
			},
			"put": gin.H{
				"tags":        []string{"Banking"},
				"summary":     "Update bank account",
				"parameters":  []gin.H{pathParam("account_id", "Bank Account ID")},
				"requestBody": jsonBody("BankAccountUpdate"),
				"responses":   successResponse("Bank account updated"),
			},
			"delete": gin.H{
				"tags":       []string{"Banking"},
				"summary":    "Deactivate bank account",
				"parameters": []gin.H{pathParam("account_id", "Bank Account ID")},
				"responses":  successResponse("Bank account deactivated"),
			},
		},
		// ========== BANKING TRANSACTIONS ==========
		"/finance/banking/transactions": gin.H{
			"get": gin.H{
				"tags":    []string{"Banking"},
				"summary": "List bank transactions",
				"parameters": []gin.H{
					queryParam("bank_account_id", "Filter by account", false),
					queryParam("transaction_type", "Filter by type", false),
					queryParam("date_from", "Start date", false),
					queryParam("date_to", "End date", false),
				},
				"responses": successResponse("List of transactions"),
			},
			"post": gin.H{
				"tags":        []string{"Banking"},
				"summary":     "Create bank transaction",
				"requestBody": jsonBody("BankTransactionCreate"),
				"responses":   successResponse("Transaction created"),
			},
		},
		"/finance/banking/transactions/{transaction_id}": gin.H{
			"get": gin.H{
				"tags":       []string{"Banking"},
				"summary":    "Get bank transaction",
				"parameters": []gin.H{pathParam("transaction_id", "Transaction ID")},
				"responses":  successResponse("Transaction details"),
			},
		},
		// ========== RECONCILIATION ==========
		"/finance/banking/reconciliation/{account_id}": gin.H{
			"get": gin.H{
				"tags":        []string{"Reconciliation"},
				"summary":     "Get unreconciled transactions",
				"description": "Returns transactions pending reconciliation for a bank account",
				"parameters":  []gin.H{pathParam("account_id", "Bank Account ID")},
				"responses":   successResponse("Unreconciled transactions"),
			},
		},
		"/finance/banking/reconciliation/mark": gin.H{
			"post": gin.H{
				"tags":        []string{"Reconciliation"},
				"summary":     "Mark transactions as reconciled",
				"requestBody": jsonBody("ReconciliationMark"),
				"responses":   successResponse("Transactions marked"),
			},
		},
		"/finance/banking/reconciliations": gin.H{
			"get": gin.H{
				"tags":    []string{"Reconciliation"},
				"summary": "List reconciliation records",
				"parameters": []gin.H{
					queryParam("bank_account_id", "Filter by account", false),
				},
				"responses": successResponse("List of reconciliations"),
			},
		},
		// ========== PETTY CASH ==========
		"/finance/banking/petty-cash": gin.H{
			"get": gin.H{
				"tags":      []string{"Petty Cash"},
				"summary":   "List petty cash transactions with balance",
				"responses": successResponse("Petty cash transactions and balance"),
			},
		},
		"/finance/banking/petty-cash/expense": gin.H{
			"post": gin.H{
				"tags":        []string{"Petty Cash"},
				"summary":     "Record petty cash expense",
				"requestBody": jsonBody("PettyCashExpense"),
				"responses":   successResponse("Expense recorded"),
			},
		},
		"/finance/banking/petty-cash/replenish": gin.H{
			"post": gin.H{
				"tags":        []string{"Petty Cash"},
				"summary":     "Replenish petty cash",
				"requestBody": jsonBody("PettyCashReplenish"),
				"responses":   successResponse("Replenishment recorded"),
			},
		},
	}
}

func buildSchemas() gin.H {
	return gin.H{
		"AccountCreate": gin.H{
			"type":     "object",
			"required": []string{"code", "name", "type"},
			"properties": gin.H{
				"code":        gin.H{"type": "string", "example": "1150"},
				"name":        gin.H{"type": "string", "example": "Prepaid Expenses"},
				"type":        gin.H{"type": "string", "enum": []string{"Asset", "Liability", "Equity", "Income", "Expense"}},
				"parent_id":   gin.H{"type": "string", "format": "uuid"},
				"description": gin.H{"type": "string"},
			},
		},
		"JournalEntryCreate": gin.H{
			"type":     "object",
			"required": []string{"date", "description", "details"},
			"properties": gin.H{
				"date":        gin.H{"type": "string", "format": "date"},
				"description": gin.H{"type": "string"},
				"details": gin.H{
					"type": "array",
					"items": gin.H{
						"type": "object",
						"properties": gin.H{
							"account_id": gin.H{"type": "string"},
							"debit":      gin.H{"type": "number"},
							"credit":     gin.H{"type": "number"},
						},
					},
				},
			},
		},
		"PeriodCreate": gin.H{
			"type":     "object",
			"required": []string{"name", "start_date", "end_date"},
			"properties": gin.H{
				"name":       gin.H{"type": "string"},
				"start_date": gin.H{"type": "string", "format": "date"},
				"end_date":   gin.H{"type": "string", "format": "date"},
			},
		},
		"AssetCreate": gin.H{
			"type":     "object",
			"required": []string{"name", "code", "acquisition_date", "acquisition_cost", "useful_life_months"},
			"properties": gin.H{
				"name":               gin.H{"type": "string"},
				"code":               gin.H{"type": "string"},
				"category":           gin.H{"type": "string"},
				"acquisition_date":   gin.H{"type": "string", "format": "date"},
				"acquisition_cost":   gin.H{"type": "number"},
				"useful_life_months": gin.H{"type": "integer"},
				"salvage_value":      gin.H{"type": "number"},
			},
		},
		"BankAccountCreate": gin.H{
			"type":     "object",
			"required": []string{"code", "name"},
			"properties": gin.H{
				"code":            gin.H{"type": "string"},
				"name":            gin.H{"type": "string"},
				"bank_name":       gin.H{"type": "string"},
				"account_number":  gin.H{"type": "string"},
				"account_holder":  gin.H{"type": "string"},
				"account_type":    gin.H{"type": "string", "enum": []string{"Checking", "Savings", "Credit", "Cash"}},
				"currency_code":   gin.H{"type": "string", "default": "IDR"},
				"opening_balance": gin.H{"type": "number"},
			},
		},
		"BankTransactionCreate": gin.H{
			"type":     "object",
			"required": []string{"bank_account_id", "amount"},
			"properties": gin.H{
				"bank_account_id":   gin.H{"type": "string"},
				"transaction_date":  gin.H{"type": "string", "format": "date-time"},
				"transaction_type":  gin.H{"type": "string", "enum": []string{"Deposit", "Withdrawal", "Transfer In", "Transfer Out"}},
				"amount":            gin.H{"type": "number"},
				"counterparty_name": gin.H{"type": "string"},
				"description":       gin.H{"type": "string"},
			},
		},
		"ReconciliationMark": gin.H{
			"type":     "object",
			"required": []string{"transaction_ids"},
			"properties": gin.H{
				"transaction_ids": gin.H{"type": "array", "items": gin.H{"type": "string"}},
				"statement_date":  gin.H{"type": "string", "format": "date"},
			},
		},
		"PettyCashExpense": gin.H{
			"type":     "object",
			"required": []string{"amount"},
			"properties": gin.H{
				"date":         gin.H{"type": "string", "format": "date"},
				"amount":       gin.H{"type": "number"},
				"category":     gin.H{"type": "string"},
				"description":  gin.H{"type": "string"},
				"requested_by": gin.H{"type": "string"},
			},
		},
		"PettyCashReplenish": gin.H{
			"type":     "object",
			"required": []string{"amount"},
			"properties": gin.H{
				"date":              gin.H{"type": "string", "format": "date"},
				"amount":            gin.H{"type": "number"},
				"source_account_id": gin.H{"type": "string"},
				"description":       gin.H{"type": "string"},
			},
		},
	}
}

func buildSecuritySchemes() gin.H {
	return gin.H{
		"BearerAuth": gin.H{
			"type":         "http",
			"scheme":       "bearer",
			"bearerFormat": "JWT",
		},
	}
}

// Helper functions
func successResponse(desc string) gin.H {
	return gin.H{"200": gin.H{"description": desc}}
}

func pathParam(name, desc string) gin.H {
	return gin.H{"name": name, "in": "path", "required": true, "schema": gin.H{"type": "string"}, "description": desc}
}

func queryParam(name, desc string, required bool) gin.H {
	return gin.H{"name": name, "in": "query", "required": required, "schema": gin.H{"type": "string"}, "description": desc}
}

func jsonBody(schemaRef string) gin.H {
	return gin.H{
		"required": true,
		"content": gin.H{
			"application/json": gin.H{
				"schema": gin.H{"$ref": "#/components/schemas/" + schemaRef},
			},
		},
	}
}
