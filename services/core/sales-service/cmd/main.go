package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Connect to database
	if err := database.Connect(); err != nil {
		log.Printf("⚠️ Database connection failed: %v", err)
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
			"service":  "sales-service",
			"version":  "1.0.0",
			"database": dbStatus,
		})
	})

	// Initialize handlers
	salesHandler := handlers.NewSalesHandler()

	// Sales routes (v1 alias)
	v1 := r.Group("/sales")
	setupRoutes(v1, salesHandler)

	// API v1 routes (gateway proxy target)
	apiV1 := r.Group("/api/v1/sales")
	setupRoutes(apiV1, salesHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8023"
	}

	log.Printf("💰 Sales Service starting on port %s", port)
	log.Printf("📊 Database: %s", getDatabaseStatus())
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start sales service: %v", err)
	}
}

func setupRoutes(rg *gin.RouterGroup, h *handlers.SalesHandler) {
	// Dashboard Stats
	rg.GET("/stats", h.GetStats)

	// Quotations
	rg.GET("/quotations", h.ListQuotations)
	rg.POST("/quotations", h.CreateQuotation)
	rg.GET("/quotations/:id", h.GetQuotation)
	rg.PUT("/quotations/:id", h.UpdateQuotation)
	rg.POST("/quotations/:id/convert", h.ConvertQuotation)

	// Orders
	rg.GET("/orders", h.ListOrders)
	rg.POST("/orders", h.CreateOrder)
	rg.GET("/orders/:id", h.GetOrder)
	rg.PUT("/orders/:id", h.UpdateOrder)
	rg.POST("/orders/:id/invoice", h.GenerateInvoice)

	// Invoices
	rg.GET("/invoices", h.ListInvoices)
	rg.POST("/invoices", h.CreateInvoice)
	rg.GET("/invoices/:id", h.GetInvoice)
	rg.POST("/invoices/:id/pay", h.RecordPayment)

	// Credit Notes
	rg.GET("/credit-notes", h.ListCreditNotes)
	rg.POST("/credit-notes", h.CreateCreditNote)
	rg.GET("/credit-notes/:id", h.GetCreditNote)
	rg.PUT("/credit-notes/:id", h.UpdateCreditNote)
	rg.DELETE("/credit-notes/:id", h.DeleteCreditNote)

	// Payments
	rg.GET("/payments", h.ListPayments)
	rg.POST("/payments", h.CreatePaymentRecord)

	// Price Lists
	rg.GET("/price-lists", h.ListPriceLists)
	rg.POST("/price-lists", h.CreatePriceList)
	rg.GET("/price-lists/:id", h.GetPriceList)
	rg.PUT("/price-lists/:id", h.UpdatePriceList)

	// Discount Rules
	rg.GET("/discount-rules", h.ListDiscountRules)
	rg.POST("/discount-rules", h.CreateDiscountRule)
	rg.GET("/discount-rules/:id", h.GetDiscountRule)
	rg.PUT("/discount-rules/:id", h.UpdateDiscountRule)

	// Contracts
	rg.GET("/contracts", h.ListContracts)
	rg.POST("/contracts", h.CreateContract)
	rg.GET("/contracts/:id", h.GetContract)
	rg.PUT("/contracts/:id", h.UpdateContract)

	// Commissions
	rg.GET("/commission", h.ListCommissions)
	rg.POST("/commission", h.CreateCommission)
	rg.PUT("/commission/:id/status", h.UpdateCommissionStatus)
}

func getDatabaseStatus() string {
	if database.GetDB() != nil {
		return "Connected to Supabase"
	}
	return "Not connected (mock mode)"
}
