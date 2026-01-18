package handlers

import (
	"net/http"
	"time"

	"github.com/elviskudo/mini-erp/services/finance-service/internal/database"
	"github.com/elviskudo/mini-erp/services/finance-service/internal/models"
	"github.com/elviskudo/mini-erp/services/finance-service/internal/response"
	"github.com/gin-gonic/gin"
)

// FinanceHandler handles finance endpoints
type FinanceHandler struct {
	// Add repository dependencies here
}

// NewFinanceHandler creates a new finance handler
func NewFinanceHandler() *FinanceHandler {
	return &FinanceHandler{}
}

// GetStats returns finance statistics
// GET /finance/stats
func (h *FinanceHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, gin.H{
			"total_accounts":      25,
			"total_revenue":       1250000,
			"total_expenses":      820000,
			"net_income":          430000,
			"accounts_payable":    150000,
			"accounts_receivable": 280000,
			"cash_balance":        520000,
		})
		return
	}

	var accountCount int64
	db.Model(&models.ChartOfAccount{}).Count(&accountCount)

	c.JSON(http.StatusOK, gin.H{
		"total_accounts":      accountCount,
		"total_revenue":       1250000,
		"total_expenses":      820000,
		"net_income":          430000,
		"accounts_payable":    150000,
		"accounts_receivable": 280000,
		"cash_balance":        520000,
	})
}

// ========== CHART OF ACCOUNTS (COA) ==========

// ListCOA lists all chart of accounts
// GET /finance/coa
func (h *FinanceHandler) ListCOA(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		// Fallback to mock data if DB not connected
		c.JSON(http.StatusOK, getMockCOA())
		return
	}

	var accounts []models.ChartOfAccount
	tenantID := c.GetHeader("X-Tenant-ID")

	query := db.Order("code ASC")
	if tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.Find(&accounts).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch accounts", "detail": err.Error()})
		return
	}

	// Build hierarchical structure
	result := buildCOAHierarchy(accounts)
	c.JSON(http.StatusOK, result)
}

// buildCOAHierarchy builds hierarchical COA structure
func buildCOAHierarchy(accounts []models.ChartOfAccount) []gin.H {
	// Create a map for quick lookup
	accountMap := make(map[string]*gin.H)
	var roots []gin.H

	// First pass: create all nodes
	for _, acc := range accounts {
		node := gin.H{
			"id":          acc.ID,
			"code":        acc.Code,
			"name":        acc.Name,
			"type":        acc.Type,
			"parent_id":   acc.ParentID,
			"description": acc.Description,
			"is_active":   acc.IsActive,
			"children":    []gin.H{},
		}
		accountMap[acc.ID] = &node
	}

	// Second pass: build hierarchy
	for _, acc := range accounts {
		node := accountMap[acc.ID]
		if acc.ParentID == nil || *acc.ParentID == "" {
			roots = append(roots, *node)
		} else if parent, exists := accountMap[*acc.ParentID]; exists {
			children := (*parent)["children"].([]gin.H)
			(*parent)["children"] = append(children, *node)
		} else {
			roots = append(roots, *node)
		}
	}

	if len(roots) == 0 {
		return getMockCOA()
	}
	return roots
}

// getMockCOA returns mock COA data as fallback
func getMockCOA() []gin.H {
	return []gin.H{
		{"id": "1000-id", "code": "1000", "name": "ASSETS", "type": "Asset", "parent_id": nil, "children": []gin.H{
			{"id": "1100-id", "code": "1100", "name": "Current Assets", "type": "Asset", "parent_id": "1000-id", "children": []gin.H{}},
		}},
		{"id": "2000-id", "code": "2000", "name": "LIABILITIES", "type": "Liability", "parent_id": nil, "children": []gin.H{}},
		{"id": "3000-id", "code": "3000", "name": "EQUITY", "type": "Equity", "parent_id": nil, "children": []gin.H{}},
	}
}

// CreateCOA creates a new account
// POST /finance/coa
func (h *FinanceHandler) CreateCOA(c *gin.Context) {
	var req struct {
		Code        string  `json:"code" binding:"required"`
		Name        string  `json:"name" binding:"required"`
		Type        string  `json:"type" binding:"required"`
		ParentID    *string `json:"parent_id"`
		Description *string `json:"description"`
		IsActive    *bool   `json:"is_active"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Check duplicate code in database
	// TODO: Save to database

	c.JSON(http.StatusOK, gin.H{
		"id":          "new-account-id",
		"code":        req.Code,
		"name":        req.Name,
		"type":        req.Type,
		"parent_id":   req.ParentID,
		"description": req.Description,
		"is_active":   true,
	})
}

// UpdateCOA updates an account
// PUT /finance/coa/:account_id
func (h *FinanceHandler) UpdateCOA(c *gin.Context) {
	accountID := c.Param("account_id")

	var req struct {
		Code        string  `json:"code" binding:"required"`
		Name        string  `json:"name" binding:"required"`
		Type        string  `json:"type" binding:"required"`
		ParentID    *string `json:"parent_id"`
		Description *string `json:"description"`
		IsActive    *bool   `json:"is_active"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Fetch and update in database

	c.JSON(http.StatusOK, gin.H{
		"id":          accountID,
		"code":        req.Code,
		"name":        req.Name,
		"type":        req.Type,
		"parent_id":   req.ParentID,
		"description": req.Description,
		"is_active":   req.IsActive,
	})
}

// SeedCOA seeds the chart of accounts with standard template
// POST /finance/coa/seed
func (h *FinanceHandler) SeedCOA(c *gin.Context) {
	// TODO: Create standard COA hierarchy in database
	c.JSON(http.StatusOK, gin.H{"status": "Seeded"})
}

// ========== GENERAL LEDGER ==========

// GetGeneralLedger gets journal entries for a specific account with running balance
// GET /finance/gl?account_id=xxx&date_from=xxx&date_to=xxx
func (h *FinanceHandler) GetGeneralLedger(c *gin.Context) {
	accountID := c.Query("account_id")
	if accountID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "account_id is required"})
		return
	}

	dateFrom := c.Query("date_from")
	dateTo := c.Query("date_to")
	_ = dateFrom
	_ = dateTo

	// Mock data matching backend_api response
	entries := []gin.H{
		{
			"date":           "2024-01-15",
			"journal_number": "JE-00000001",
			"description":    "Opening Balance",
			"debit":          10000000.0,
			"credit":         0.0,
			"balance":        10000000.0,
		},
		{
			"date":           "2024-01-20",
			"journal_number": "JE-00000002",
			"description":    "Sales Payment",
			"debit":          5000000.0,
			"credit":         0.0,
			"balance":        15000000.0,
		},
	}

	c.JSON(http.StatusOK, gin.H{
		"account_id":      accountID,
		"account_code":    "1110",
		"account_name":    "Cash & Bank",
		"opening_balance": 0.0,
		"entries":         entries,
	})
}

// CreateJournalEntry creates a journal entry
// POST /finance/journal
func (h *FinanceHandler) CreateJournalEntry(c *gin.Context) {
	var req struct {
		Date        string `json:"date" binding:"required"`
		Description string `json:"description" binding:"required"`
		Details     []struct {
			AccountID   string  `json:"account_id" binding:"required"`
			Description string  `json:"description"`
			Debit       float64 `json:"debit"`
			Credit      float64 `json:"credit"`
		} `json:"details" binding:"required,min=2"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate balanced entry
	var totalDebit, totalCredit float64
	for _, d := range req.Details {
		totalDebit += d.Debit
		totalCredit += d.Credit
	}

	if totalDebit != totalCredit {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":        "Journal entry must be balanced",
			"total_debit":  totalDebit,
			"total_credit": totalCredit,
		})
		return
	}

	// TODO: Save to database and update account balances

	c.JSON(http.StatusOK, gin.H{
		"id":           "new-journal-id",
		"entry_number": "JE-" + time.Now().Format("20060102150405"),
		"date":         req.Date,
		"description":  req.Description,
		"total_debit":  totalDebit,
		"total_credit": totalCredit,
		"status":       "posted",
		"message":      "Journal entry posted successfully",
	})
}

// ========== FISCAL PERIODS ==========

// ListPeriods lists all fiscal periods
// GET /finance/periods
func (h *FinanceHandler) ListPeriods(c *gin.Context) {
	periods := []gin.H{
		{
			"id":         "period-2024-01",
			"name":       "January 2024",
			"start_date": "2024-01-01T00:00:00Z",
			"end_date":   "2024-01-31T23:59:59Z",
			"is_closed":  true,
		},
		{
			"id":         "period-2024-02",
			"name":       "February 2024",
			"start_date": "2024-02-01T00:00:00Z",
			"end_date":   "2024-02-29T23:59:59Z",
			"is_closed":  false,
		},
	}

	c.JSON(http.StatusOK, periods)
}

// CreatePeriod creates a fiscal period
// POST /finance/periods
func (h *FinanceHandler) CreatePeriod(c *gin.Context) {
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
		"id":         "new-period-id",
		"name":       req.Name,
		"start_date": req.StartDate,
		"end_date":   req.EndDate,
		"is_closed":  false,
	})
}

// ClosePeriod closes a fiscal period
// POST /finance/periods/:id/close
func (h *FinanceHandler) ClosePeriod(c *gin.Context) {
	periodID := c.Param("id")

	// TODO: Update in database and lock all entries in this period

	c.JSON(http.StatusOK, gin.H{
		"id":      periodID,
		"status":  "Closed",
		"message": "Period closed successfully",
	})
}

// ========== FIXED ASSETS ==========

// CreateAsset creates a fixed asset
// POST /finance/assets
func (h *FinanceHandler) CreateAsset(c *gin.Context) {
	var req struct {
		Name               string  `json:"name" binding:"required"`
		Code               string  `json:"code" binding:"required"`
		Category           string  `json:"category"`
		AcquisitionDate    string  `json:"acquisition_date" binding:"required"`
		AcquisitionCost    float64 `json:"acquisition_cost" binding:"required"`
		UsefulLifeMonths   int     `json:"useful_life_months" binding:"required"`
		SalvageValue       float64 `json:"salvage_value"`
		DepreciationMethod string  `json:"depreciation_method"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":                       "new-asset-id",
		"name":                     req.Name,
		"code":                     req.Code,
		"category":                 req.Category,
		"acquisition_date":         req.AcquisitionDate,
		"acquisition_cost":         req.AcquisitionCost,
		"book_value":               req.AcquisitionCost,
		"accumulated_depreciation": 0,
		"useful_life_months":       req.UsefulLifeMonths,
		"salvage_value":            req.SalvageValue,
		"depreciation_method":      req.DepreciationMethod,
	})
}

// DepreciateAsset runs depreciation for an asset
// POST /finance/assets/:id/depreciate
func (h *FinanceHandler) DepreciateAsset(c *gin.Context) {
	assetID := c.Param("id")

	// Mock depreciation calculation
	depreciationAmount := 500000.0 // Monthly depreciation

	c.JSON(http.StatusOK, gin.H{
		"asset_id":                     assetID,
		"depreciation_amount":          depreciationAmount,
		"new_accumulated_depreciation": depreciationAmount,
		"new_book_value":               9500000.0,
		"journal_entry_id":             "je-depreciation-id",
		"message":                      "Depreciation posted successfully",
	})
}

// ========== REPORTS ==========

// GetTrialBalance gets trial balance report
// GET /finance/reports/trial-balance
func (h *FinanceHandler) GetTrialBalance(c *gin.Context) {
	accounts := []gin.H{
		{"code": "1110", "name": "Cash & Bank", "debit": 15000000.0, "credit": 0.0},
		{"code": "1120", "name": "Accounts Receivable", "debit": 5000000.0, "credit": 0.0},
		{"code": "2100", "name": "Accounts Payable", "debit": 0.0, "credit": 3000000.0},
		{"code": "3100", "name": "Capital", "debit": 0.0, "credit": 10000000.0},
		{"code": "4100", "name": "Sales Revenue", "debit": 0.0, "credit": 12000000.0},
		{"code": "5100", "name": "COGS", "debit": 5000000.0, "credit": 0.0},
	}

	var totalDebit, totalCredit float64
	for _, acc := range accounts {
		totalDebit += acc["debit"].(float64)
		totalCredit += acc["credit"].(float64)
	}

	c.JSON(http.StatusOK, gin.H{
		"title":        "Trial Balance",
		"date":         time.Now().Format("2006-01-02"),
		"accounts":     accounts,
		"total_debit":  totalDebit,
		"total_credit": totalCredit,
		"balanced":     totalDebit == totalCredit,
	})
}

// GetProfitLoss gets P&L report
// GET /finance/reports/pl?start_date=xxx&end_date=xxx
func (h *FinanceHandler) GetProfitLoss(c *gin.Context) {
	startDate := c.Query("start_date")
	endDate := c.Query("end_date")

	if startDate == "" || endDate == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "start_date and end_date are required"})
		return
	}

	revenue := []gin.H{
		{"code": "4100", "name": "Sales Revenue", "amount": 12000000.0},
	}
	expenses := []gin.H{
		{"code": "5100", "name": "COGS", "amount": 5000000.0},
		{"code": "5200", "name": "Operating Expenses", "amount": 2000000.0},
	}

	totalRevenue := 12000000.0
	totalExpenses := 7000000.0
	netIncome := totalRevenue - totalExpenses

	c.JSON(http.StatusOK, gin.H{
		"title":          "Profit & Loss Statement",
		"start_date":     startDate,
		"end_date":       endDate,
		"revenue":        revenue,
		"total_revenue":  totalRevenue,
		"expenses":       expenses,
		"total_expenses": totalExpenses,
		"net_income":     netIncome,
	})
}

// GetBalanceSheet gets balance sheet report
// GET /finance/reports/balance-sheet?date=xxx
func (h *FinanceHandler) GetBalanceSheet(c *gin.Context) {
	date := c.Query("date")
	if date == "" {
		date = time.Now().Format("2006-01-02")
	}

	assets := []gin.H{
		{"code": "1110", "name": "Cash & Bank", "amount": 15000000.0},
		{"code": "1120", "name": "Accounts Receivable", "amount": 5000000.0},
	}
	liabilities := []gin.H{
		{"code": "2100", "name": "Accounts Payable", "amount": 3000000.0},
	}
	equity := []gin.H{
		{"code": "3100", "name": "Capital", "amount": 10000000.0},
		{"code": "3200", "name": "Retained Earnings", "amount": 7000000.0},
	}

	totalAssets := 20000000.0
	totalLiabilities := 3000000.0
	totalEquity := 17000000.0

	c.JSON(http.StatusOK, gin.H{
		"title":             "Balance Sheet",
		"date":              date,
		"assets":            assets,
		"total_assets":      totalAssets,
		"liabilities":       liabilities,
		"total_liabilities": totalLiabilities,
		"equity":            equity,
		"total_equity":      totalEquity,
		"balanced":          totalAssets == (totalLiabilities + totalEquity),
	})
}

// ========== BANKING - ACCOUNTS ==========

// ListBankAccounts lists all bank accounts
// GET /finance/banking/accounts
func (h *FinanceHandler) ListBankAccounts(c *gin.Context) {
	accounts := []gin.H{
		{
			"id":              "bank-1",
			"code":            "BANK-001",
			"name":            "BCA Operating",
			"bank_name":       "BCA",
			"account_number":  "1234567890",
			"account_holder":  "PT. Company",
			"account_type":    "Checking",
			"currency_code":   "IDR",
			"opening_balance": 100000000.0,
			"current_balance": 150000000.0,
			"is_active":       true,
		},
		{
			"id":              "bank-2",
			"code":            "BANK-002",
			"name":            "Mandiri Savings",
			"bank_name":       "Mandiri",
			"account_number":  "0987654321",
			"account_holder":  "PT. Company",
			"account_type":    "Savings",
			"currency_code":   "IDR",
			"opening_balance": 50000000.0,
			"current_balance": 55000000.0,
			"is_active":       true,
		},
	}

	c.JSON(http.StatusOK, accounts)
}

// GetBankAccount gets a bank account by ID
// GET /finance/banking/accounts/:account_id
func (h *FinanceHandler) GetBankAccount(c *gin.Context) {
	accountID := c.Param("account_id")

	c.JSON(http.StatusOK, gin.H{
		"id":              accountID,
		"code":            "BANK-001",
		"name":            "BCA Operating",
		"bank_name":       "BCA",
		"account_number":  "1234567890",
		"account_holder":  "PT. Company",
		"account_type":    "Checking",
		"currency_code":   "IDR",
		"opening_balance": 100000000.0,
		"current_balance": 150000000.0,
		"is_active":       true,
	})
}

// CreateBankAccount creates a bank account
// POST /finance/banking/accounts
func (h *FinanceHandler) CreateBankAccount(c *gin.Context) {
	var req struct {
		Code           string  `json:"code" binding:"required"`
		Name           string  `json:"name" binding:"required"`
		BankName       string  `json:"bank_name"`
		AccountNumber  string  `json:"account_number"`
		AccountHolder  string  `json:"account_holder"`
		AccountType    string  `json:"account_type"`
		CurrencyCode   string  `json:"currency_code"`
		OpeningBalance float64 `json:"opening_balance"`
		GLAccountID    *string `json:"gl_account_id"`
		Notes          string  `json:"notes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      "new-bank-id",
		"code":    req.Code,
		"name":    req.Name,
		"message": "Bank account created successfully",
	})
}

// UpdateBankAccount updates a bank account
// PUT /finance/banking/accounts/:account_id
func (h *FinanceHandler) UpdateBankAccount(c *gin.Context) {
	accountID := c.Param("account_id")

	var req struct {
		Code          *string `json:"code"`
		Name          *string `json:"name"`
		BankName      *string `json:"bank_name"`
		AccountNumber *string `json:"account_number"`
		AccountHolder *string `json:"account_holder"`
		AccountType   *string `json:"account_type"`
		CurrencyCode  *string `json:"currency_code"`
		IsActive      *bool   `json:"is_active"`
		Notes         *string `json:"notes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":      accountID,
		"message": "Bank account updated",
	})
}

// DeleteBankAccount deactivates a bank account
// DELETE /finance/banking/accounts/:account_id
func (h *FinanceHandler) DeleteBankAccount(c *gin.Context) {
	accountID := c.Param("account_id")

	c.JSON(http.StatusOK, gin.H{
		"id":      accountID,
		"message": "Bank account deactivated",
	})
}

// ========== BANKING - TRANSACTIONS ==========

// ListBankTransactions lists bank transactions
// GET /finance/banking/transactions?bank_account_id=xxx&transaction_type=xxx&date_from=xxx&date_to=xxx
func (h *FinanceHandler) ListBankTransactions(c *gin.Context) {
	bankAccountID := c.Query("bank_account_id")
	_ = bankAccountID

	transactions := []gin.H{
		{
			"id":                 "tx-1",
			"bank_account_id":    "bank-1",
			"transaction_number": "TXN-20240115001",
			"transaction_date":   "2024-01-15T10:30:00Z",
			"value_date":         "2024-01-15T10:30:00Z",
			"transaction_type":   "Deposit",
			"amount":             10000000.0,
			"running_balance":    110000000.0,
			"counterparty_name":  "Customer A",
			"description":        "Payment for Invoice INV-001",
			"is_reconciled":      true,
		},
		{
			"id":                 "tx-2",
			"bank_account_id":    "bank-1",
			"transaction_number": "TXN-20240116001",
			"transaction_date":   "2024-01-16T14:00:00Z",
			"value_date":         "2024-01-16T14:00:00Z",
			"transaction_type":   "Withdrawal",
			"amount":             5000000.0,
			"running_balance":    105000000.0,
			"counterparty_name":  "Vendor B",
			"description":        "Payment for Bill BILL-001",
			"is_reconciled":      false,
		},
	}

	c.JSON(http.StatusOK, transactions)
}

// GetBankTransaction gets a bank transaction by ID
// GET /finance/banking/transactions/:transaction_id
func (h *FinanceHandler) GetBankTransaction(c *gin.Context) {
	txID := c.Param("transaction_id")

	c.JSON(http.StatusOK, gin.H{
		"id":                 txID,
		"bank_account_id":    "bank-1",
		"transaction_number": "TXN-20240115001",
		"transaction_date":   "2024-01-15T10:30:00Z",
		"transaction_type":   "Deposit",
		"amount":             10000000.0,
		"running_balance":    110000000.0,
		"counterparty_name":  "Customer A",
		"description":        "Payment for Invoice INV-001",
		"is_reconciled":      true,
	})
}

// CreateBankTransaction creates a bank transaction
// POST /finance/banking/transactions
func (h *FinanceHandler) CreateBankTransaction(c *gin.Context) {
	var req struct {
		BankAccountID       string  `json:"bank_account_id" binding:"required"`
		TransactionDate     string  `json:"transaction_date"`
		TransactionType     string  `json:"transaction_type"`
		Amount              float64 `json:"amount" binding:"required,gt=0"`
		CounterpartyName    string  `json:"counterparty_name"`
		CounterpartyAccount string  `json:"counterparty_account"`
		ReferenceType       string  `json:"reference_type"`
		ReferenceNumber     string  `json:"reference_number"`
		Description         string  `json:"description"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	txNumber := "TXN-" + time.Now().Format("20060102150405")

	c.JSON(http.StatusOK, gin.H{
		"id":                 "new-tx-id",
		"transaction_number": txNumber,
		"amount":             req.Amount,
		"running_balance":    160000000.0, // Mock
		"message":            "Transaction created successfully",
	})
}

// ========== BANKING - RECONCILIATION ==========

// GetReconciliationData gets unreconciled transactions for an account
// GET /finance/banking/reconciliation/:account_id
func (h *FinanceHandler) GetReconciliationData(c *gin.Context) {
	accountID := c.Param("account_id")

	transactions := []gin.H{
		{
			"id":               "tx-2",
			"transaction_date": "2024-01-16",
			"reference_number": "TXN-20240116001",
			"description":      "Payment for Bill BILL-001",
			"amount":           5000000.0,
			"transaction_type": "Withdrawal",
		},
		{
			"id":               "tx-3",
			"transaction_date": "2024-01-17",
			"reference_number": "TXN-20240117001",
			"description":      "Utility Payment",
			"amount":           500000.0,
			"transaction_type": "Withdrawal",
		},
	}

	c.JSON(http.StatusOK, gin.H{
		"bank_account_id":   accountID,
		"bank_account_name": "BCA Operating",
		"book_balance":      150000000.0,
		"transactions":      transactions,
	})
}

// MarkReconciled marks transactions as reconciled
// POST /finance/banking/reconciliation/mark
func (h *FinanceHandler) MarkReconciled(c *gin.Context) {
	var req struct {
		TransactionIDs []string `json:"transaction_ids" binding:"required"`
		StatementDate  string   `json:"statement_date"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.TransactionIDs) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "No transactions provided"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":          "Marked " + string(rune(len(req.TransactionIDs))) + " transactions as reconciled",
		"reconciled_count": len(req.TransactionIDs),
	})
}

// ListReconciliations lists reconciliation records
// GET /finance/banking/reconciliations
func (h *FinanceHandler) ListReconciliations(c *gin.Context) {
	reconciliations := []gin.H{
		{
			"id":                       "recon-1",
			"bank_account_id":          "bank-1",
			"statement_date":           "2024-01-31",
			"statement_ending_balance": 150000000.0,
			"book_balance":             150000000.0,
			"status":                   "completed",
		},
	}

	c.JSON(http.StatusOK, reconciliations)
}

// ========== LOYALTY (Merged from loyalty-service) ==========

// TopUpLoyalty handles coin topup
// POST /finance/loyalty/topup
func (h *FinanceHandler) TopUpLoyalty(c *gin.Context) {
	response.Success(c, gin.H{"amount": 100}, "Coin Top-Up Successful (Mock)")
}

// GetLoyaltyRules returns redemption rules
// GET /finance/loyalty/rules
func (h *FinanceHandler) GetLoyaltyRules(c *gin.Context) {
	data := []gin.H{
		{"id": 1, "points": 100, "reward": "Rp 10.000 Discount"},
		{"id": 2, "points": 500, "reward": "Premium Membership"},
	}
	response.SuccessList(c, data, 1, 10, 2, "Loyalty rules retrieved")
}

// GetLoyaltyBalance returns user coin balance
// GET /finance/loyalty/balance
func (h *FinanceHandler) GetLoyaltyBalance(c *gin.Context) {
	response.Success(c, gin.H{
		"balance": 1500,
		"currency": "Coins",
	}, "Balance retrieved")
}

// GetLoyaltyAnalytics returns loyalty stats
// GET /finance/loyalty/analytics
func (h *FinanceHandler) GetLoyaltyAnalytics(c *gin.Context) {
	response.Success(c, gin.H{
		"churn_rate": "2.5%",
		"active_users": 15000,
	}, "Analytics data retrieved")
}
			"completed_at":             "2024-02-01T10:00:00Z",
		},
	}

	c.JSON(http.StatusOK, reconciliations)
}

// ========== PETTY CASH ==========

// ListPettyCash lists petty cash transactions
// GET /finance/banking/petty-cash
func (h *FinanceHandler) ListPettyCash(c *gin.Context) {
	transactions := []gin.H{
		{
			"id":                 "pc-1",
			"date":               "2024-01-15",
			"type":               "replenishment",
			"category":           "Replenishment",
			"description":        "Initial petty cash fund",
			"amount":             5000000.0,
			"requested_by":       "",
			"transaction_number": "PC-REP-001",
		},
		{
			"id":                 "pc-2",
			"date":               "2024-01-16",
			"type":               "expense",
			"category":           "Office Supplies",
			"description":        "Purchase paper and pens",
			"amount":             150000.0,
			"requested_by":       "John",
			"transaction_number": "PC-EXP-001",
		},
	}

	// Calculate balance
	balance := 5000000.0 - 150000.0

	c.JSON(http.StatusOK, gin.H{
		"balance":      balance,
		"transactions": transactions,
	})
}

// CreatePettyCashExpense records a petty cash expense
// POST /finance/banking/petty-cash/expense
func (h *FinanceHandler) CreatePettyCashExpense(c *gin.Context) {
	var req struct {
		Date        string  `json:"date"`
		Amount      float64 `json:"amount" binding:"required,gt=0"`
		Category    string  `json:"category"`
		Description string  `json:"description"`
		RequestedBy string  `json:"requested_by"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	txNumber := "PC-EXP-" + time.Now().Format("20060102150405")

	c.JSON(http.StatusOK, gin.H{
		"id":                 "new-pc-expense-id",
		"transaction_number": txNumber,
		"amount":             req.Amount,
		"type":               "expense",
		"message":            "Expense recorded successfully",
	})
}

// CreatePettyCashReplenishment records a petty cash replenishment
// POST /finance/banking/petty-cash/replenish
func (h *FinanceHandler) CreatePettyCashReplenishment(c *gin.Context) {
	var req struct {
		Date            string  `json:"date"`
		Amount          float64 `json:"amount" binding:"required,gt=0"`
		SourceAccountID string  `json:"source_account_id"`
		Description     string  `json:"description"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	txNumber := "PC-REP-" + time.Now().Format("20060102150405")

	c.JSON(http.StatusOK, gin.H{
		"id":                 "new-pc-replenish-id",
		"transaction_number": txNumber,
		"amount":             req.Amount,
		"type":               "replenishment",
		"message":            "Replenishment recorded successfully",
	})
}
