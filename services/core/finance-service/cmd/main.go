package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/finance-service/internal/database"
	"github.com/elviskudo/mini-erp/services/finance-service/internal/handlers"
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
			"service":  "finance-service",
			"version":  "1.0.0",
			"database": dbStatus,
		})
	})

	// Scalar API Documentation
	r.GET("/docs", handlers.ScalarDocs)
	r.GET("/docs/*any", handlers.ScalarDocs)
	r.GET("/openapi.json", handlers.OpenAPISpec)

	// Initialize handlers
	financeHandler := handlers.NewFinanceHandler()

	// API routes - matching backend/routers/finance.py exactly
	finance := r.Group("/finance")
	{
		// Stats
		finance.GET("/stats", financeHandler.GetStats)

		// ========== CHART OF ACCOUNTS ==========
		finance.GET("/coa", financeHandler.ListCOA)
		finance.POST("/coa", financeHandler.CreateCOA)
		finance.PUT("/coa/:account_id", financeHandler.UpdateCOA)
		finance.POST("/coa/seed", financeHandler.SeedCOA)

		// ========== GENERAL LEDGER ==========
		finance.GET("/gl", financeHandler.GetGeneralLedger)
		finance.POST("/journal", financeHandler.CreateJournalEntry)

		// ========== FISCAL PERIODS ==========
		finance.GET("/periods", financeHandler.ListPeriods)
		finance.POST("/periods", financeHandler.CreatePeriod)
		finance.POST("/periods/:id/close", financeHandler.ClosePeriod)

		// ========== FIXED ASSETS ==========
		finance.POST("/assets", financeHandler.CreateAsset)
		finance.POST("/assets/:id/depreciate", financeHandler.DepreciateAsset)

		// ========== REPORTS ==========
		finance.GET("/reports/trial-balance", financeHandler.GetTrialBalance)
		finance.GET("/reports/pl", financeHandler.GetProfitLoss)
		finance.GET("/reports/balance-sheet", financeHandler.GetBalanceSheet)

		// ========== BANKING - ACCOUNTS ==========
		finance.GET("/banking/accounts", financeHandler.ListBankAccounts)
		finance.GET("/banking/accounts/:account_id", financeHandler.GetBankAccount)
		finance.POST("/banking/accounts", financeHandler.CreateBankAccount)
		finance.PUT("/banking/accounts/:account_id", financeHandler.UpdateBankAccount)
		finance.DELETE("/banking/accounts/:account_id", financeHandler.DeleteBankAccount)

		// ========== BANKING - TRANSACTIONS ==========
		finance.GET("/banking/transactions", financeHandler.ListBankTransactions)
		finance.GET("/banking/transactions/:transaction_id", financeHandler.GetBankTransaction)
		finance.POST("/banking/transactions", financeHandler.CreateBankTransaction)

		// ========== BANKING - RECONCILIATION ==========
		finance.GET("/banking/reconciliation/:account_id", financeHandler.GetReconciliationData)
		finance.POST("/banking/reconciliation/mark", financeHandler.MarkReconciled)
		finance.GET("/banking/reconciliations", financeHandler.ListReconciliations)

		// ========== PETTY CASH ==========
		finance.GET("/banking/petty-cash", financeHandler.ListPettyCash)
		finance.POST("/banking/petty-cash/expense", financeHandler.CreatePettyCashExpense)
		finance.POST("/banking/petty-cash/replenish", financeHandler.CreatePettyCashReplenishment)

		// ========== LOYALTY (Merged from loyalty-service) ==========
		loyalty := finance.Group("/loyalty")
		{
			loyalty.POST("/topup", financeHandler.TopUpLoyalty)
			loyalty.GET("/rules", financeHandler.GetLoyaltyRules)
			loyalty.GET("/balance", financeHandler.GetLoyaltyBalance)
			loyalty.GET("/analytics", financeHandler.GetLoyaltyAnalytics)
		}
	}

	// Also mount at /api/v1/finance for gateway compatibility
	apiV1 := r.Group("/api/v1/finance")
	{
		// ========== CHART OF ACCOUNTS ==========
		apiV1.GET("/coa", financeHandler.ListCOA)
		apiV1.POST("/coa", financeHandler.CreateCOA)
		apiV1.PUT("/coa/:account_id", financeHandler.UpdateCOA)
		apiV1.POST("/coa/seed", financeHandler.SeedCOA)

		// ========== GENERAL LEDGER ==========
		apiV1.GET("/gl", financeHandler.GetGeneralLedger)
		apiV1.POST("/journal", financeHandler.CreateJournalEntry)

		// ========== FISCAL PERIODS ==========
		apiV1.GET("/periods", financeHandler.ListPeriods)
		apiV1.POST("/periods", financeHandler.CreatePeriod)
		apiV1.POST("/periods/:id/close", financeHandler.ClosePeriod)

		// ========== FIXED ASSETS ==========
		apiV1.POST("/assets", financeHandler.CreateAsset)
		apiV1.POST("/assets/:id/depreciate", financeHandler.DepreciateAsset)

		// ========== REPORTS ==========
		apiV1.GET("/reports/trial-balance", financeHandler.GetTrialBalance)
		apiV1.GET("/reports/pl", financeHandler.GetProfitLoss)
		apiV1.GET("/reports/balance-sheet", financeHandler.GetBalanceSheet)

		// ========== BANKING - ACCOUNTS ==========
		apiV1.GET("/banking/accounts", financeHandler.ListBankAccounts)
		apiV1.GET("/banking/accounts/:account_id", financeHandler.GetBankAccount)
		apiV1.POST("/banking/accounts", financeHandler.CreateBankAccount)
		apiV1.PUT("/banking/accounts/:account_id", financeHandler.UpdateBankAccount)
		apiV1.DELETE("/banking/accounts/:account_id", financeHandler.DeleteBankAccount)

		// ========== BANKING - TRANSACTIONS ==========
		apiV1.GET("/banking/transactions", financeHandler.ListBankTransactions)
		apiV1.GET("/banking/transactions/:transaction_id", financeHandler.GetBankTransaction)
		apiV1.POST("/banking/transactions", financeHandler.CreateBankTransaction)

		// ========== BANKING - RECONCILIATION ==========
		apiV1.GET("/banking/reconciliation/:account_id", financeHandler.GetReconciliationData)
		apiV1.POST("/banking/reconciliation/mark", financeHandler.MarkReconciled)
		apiV1.GET("/banking/reconciliations", financeHandler.ListReconciliations)

		// ========== PETTY CASH ==========
		apiV1.GET("/banking/petty-cash", financeHandler.ListPettyCash)
		apiV1.POST("/banking/petty-cash/expense", financeHandler.CreatePettyCashExpense)
		apiV1.POST("/banking/petty-cash/replenish", financeHandler.CreatePettyCashReplenishment)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8011"
	}

	log.Printf("💰 Finance Service starting on port %s", port)
	log.Printf("📊 Routes: COA, GL, Periods, Assets, Reports, Banking, Petty Cash")
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start finance service: %v", err)
	}
}
