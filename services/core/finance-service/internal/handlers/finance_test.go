package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/elviskudo/mini-erp/services/finance-service/internal/handlers"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

// FinanceTestSuite is the test suite for finance handlers
type FinanceTestSuite struct {
	suite.Suite
	router  *gin.Engine
	handler *handlers.FinanceHandler
}

// SetupSuite sets up the test suite
func (s *FinanceTestSuite) SetupSuite() {
	gin.SetMode(gin.TestMode)
	s.handler = handlers.NewFinanceHandler()
	s.router = s.setupRouter()
}

func (s *FinanceTestSuite) setupRouter() *gin.Engine {
	r := gin.Default()

	// Health
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "finance-service"})
	})

	// COA
	r.GET("/finance/coa", s.handler.ListCOA)
	r.POST("/finance/coa", s.handler.CreateCOA)
	r.PUT("/finance/coa/:account_id", s.handler.UpdateCOA)
	r.POST("/finance/coa/seed", s.handler.SeedCOA)

	// GL
	r.GET("/finance/gl", s.handler.GetGeneralLedger)
	r.POST("/finance/journal", s.handler.CreateJournalEntry)

	// Periods
	r.GET("/finance/periods", s.handler.ListPeriods)
	r.POST("/finance/periods", s.handler.CreatePeriod)
	r.POST("/finance/periods/:id/close", s.handler.ClosePeriod)

	// Assets
	r.POST("/finance/assets", s.handler.CreateAsset)
	r.POST("/finance/assets/:id/depreciate", s.handler.DepreciateAsset)

	// Reports
	r.GET("/finance/reports/trial-balance", s.handler.GetTrialBalance)
	r.GET("/finance/reports/pl", s.handler.GetProfitLoss)
	r.GET("/finance/reports/balance-sheet", s.handler.GetBalanceSheet)

	// Banking Accounts
	r.GET("/finance/banking/accounts", s.handler.ListBankAccounts)
	r.GET("/finance/banking/accounts/:account_id", s.handler.GetBankAccount)
	r.POST("/finance/banking/accounts", s.handler.CreateBankAccount)
	r.PUT("/finance/banking/accounts/:account_id", s.handler.UpdateBankAccount)
	r.DELETE("/finance/banking/accounts/:account_id", s.handler.DeleteBankAccount)

	// Banking Transactions
	r.GET("/finance/banking/transactions", s.handler.ListBankTransactions)
	r.GET("/finance/banking/transactions/:transaction_id", s.handler.GetBankTransaction)
	r.POST("/finance/banking/transactions", s.handler.CreateBankTransaction)

	// Reconciliation
	r.GET("/finance/banking/reconciliation/:account_id", s.handler.GetReconciliationData)
	r.POST("/finance/banking/reconciliation/mark", s.handler.MarkReconciled)
	r.GET("/finance/banking/reconciliations", s.handler.ListReconciliations)

	// Petty Cash
	r.GET("/finance/banking/petty-cash", s.handler.ListPettyCash)
	r.POST("/finance/banking/petty-cash/expense", s.handler.CreatePettyCashExpense)
	r.POST("/finance/banking/petty-cash/replenish", s.handler.CreatePettyCashReplenishment)

	return r
}

// ========== HEALTH CHECK ==========

func (s *FinanceTestSuite) TestHealthCheck() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	s.router.ServeHTTP(w, req)
	assert.Equal(s.T(), 200, w.Code)
}

// ========== COA TESTS ==========

func (s *FinanceTestSuite) TestListCOA() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/coa", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)

	var response []map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Greater(s.T(), len(response), 0)
}

func (s *FinanceTestSuite) TestCreateCOASuccess() {
	body, _ := json.Marshal(map[string]interface{}{
		"code": "1150",
		"name": "Prepaid Expenses",
		"type": "Asset",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/coa", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "1150", response["code"])
}

func (s *FinanceTestSuite) TestCreateCOAMissingCode() {
	body, _ := json.Marshal(map[string]interface{}{
		"name": "Test Account",
		"type": "Asset",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/coa", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

func (s *FinanceTestSuite) TestUpdateCOA() {
	body, _ := json.Marshal(map[string]interface{}{
		"code": "1150",
		"name": "Updated Prepaid",
		"type": "Asset",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", "/finance/coa/test-id", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestSeedCOA() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/coa/seed", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== GL TESTS ==========

func (s *FinanceTestSuite) TestGetGLWithAccountID() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/gl?account_id=test-id", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "test-id", response["account_id"])
}

func (s *FinanceTestSuite) TestGetGLMissingAccountID() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/gl", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

func (s *FinanceTestSuite) TestCreateJournalBalanced() {
	body, _ := json.Marshal(map[string]interface{}{
		"date":        "2024-01-15",
		"description": "Test Entry",
		"details": []map[string]interface{}{
			{"account_id": "1110", "debit": 1000000, "credit": 0},
			{"account_id": "4100", "debit": 0, "credit": 1000000},
		},
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/journal", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreateJournalUnbalanced() {
	body, _ := json.Marshal(map[string]interface{}{
		"date":        "2024-01-15",
		"description": "Unbalanced Entry",
		"details": []map[string]interface{}{
			{"account_id": "1110", "debit": 1000000, "credit": 0},
			{"account_id": "4100", "debit": 0, "credit": 500000},
		},
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/journal", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

// ========== PERIODS TESTS ==========

func (s *FinanceTestSuite) TestListPeriods() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/periods", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreatePeriod() {
	body, _ := json.Marshal(map[string]interface{}{
		"name":       "March 2024",
		"start_date": "2024-03-01",
		"end_date":   "2024-03-31",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/periods", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestClosePeriod() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/periods/test-period/close", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== ASSETS TESTS ==========

func (s *FinanceTestSuite) TestCreateAsset() {
	body, _ := json.Marshal(map[string]interface{}{
		"name":               "Computer",
		"code":               "FA-001",
		"acquisition_date":   "2024-01-01",
		"acquisition_cost":   10000000,
		"useful_life_months": 36,
		"salvage_value":      1000000,
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/assets", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestDepreciateAsset() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/assets/test-asset/depreciate", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== REPORTS TESTS ==========

func (s *FinanceTestSuite) TestTrialBalance() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/reports/trial-balance", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "Trial Balance", response["title"])
}

func (s *FinanceTestSuite) TestProfitLoss() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/reports/pl?start_date=2024-01-01&end_date=2024-01-31", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestProfitLossMissingDates() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/reports/pl", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

func (s *FinanceTestSuite) TestBalanceSheet() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/reports/balance-sheet?date=2024-01-31", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== BANKING ACCOUNTS TESTS ==========

func (s *FinanceTestSuite) TestListBankAccounts() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/accounts", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestGetBankAccount() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/accounts/bank-1", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreateBankAccount() {
	body, _ := json.Marshal(map[string]interface{}{
		"code":           "BANK-003",
		"name":           "BNI Account",
		"bank_name":      "BNI",
		"account_number": "1234567890",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/accounts", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestUpdateBankAccount() {
	body, _ := json.Marshal(map[string]interface{}{
		"name": "Updated BCA",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", "/finance/banking/accounts/bank-1", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestDeleteBankAccount() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/finance/banking/accounts/bank-1", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== BANKING TRANSACTIONS TESTS ==========

func (s *FinanceTestSuite) TestListBankTransactions() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/transactions", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestGetBankTransaction() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/transactions/tx-1", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreateBankTransaction() {
	body, _ := json.Marshal(map[string]interface{}{
		"bank_account_id":  "bank-1",
		"transaction_type": "Deposit",
		"amount":           5000000,
		"description":      "Customer payment",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/transactions", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreateBankTransactionInvalidAmount() {
	body, _ := json.Marshal(map[string]interface{}{
		"bank_account_id": "bank-1",
		"amount":          -100,
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/transactions", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

// ========== RECONCILIATION TESTS ==========

func (s *FinanceTestSuite) TestGetReconciliationData() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/reconciliation/bank-1", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestMarkReconciled() {
	body, _ := json.Marshal(map[string]interface{}{
		"transaction_ids": []string{"tx-1", "tx-2"},
		"statement_date":  "2024-01-31",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/reconciliation/mark", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestMarkReconciledEmpty() {
	body, _ := json.Marshal(map[string]interface{}{
		"transaction_ids": []string{},
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/reconciliation/mark", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

func (s *FinanceTestSuite) TestListReconciliations() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/reconciliations", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// ========== PETTY CASH TESTS ==========

func (s *FinanceTestSuite) TestListPettyCash() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/finance/banking/petty-cash", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.NotNil(s.T(), response["balance"])
}

func (s *FinanceTestSuite) TestCreatePettyCashExpense() {
	body, _ := json.Marshal(map[string]interface{}{
		"amount":       150000,
		"category":     "Office Supplies",
		"description":  "Paper and pens",
		"requested_by": "John",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/petty-cash/expense", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

func (s *FinanceTestSuite) TestCreatePettyCashExpenseInvalidAmount() {
	body, _ := json.Marshal(map[string]interface{}{
		"amount": -100,
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/petty-cash/expense", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 400, w.Code)
}

func (s *FinanceTestSuite) TestCreatePettyCashReplenishment() {
	body, _ := json.Marshal(map[string]interface{}{
		"amount":            5000000,
		"source_account_id": "bank-1",
		"description":       "Monthly replenishment",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/finance/banking/petty-cash/replenish", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), 200, w.Code)
}

// Run the test suite
func TestFinanceTestSuite(t *testing.T) {
	suite.Run(t, new(FinanceTestSuite))
}
