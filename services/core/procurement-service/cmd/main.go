package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/procurement-service/internal/database"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	if err := database.Connect(); err != nil {
		log.Printf("⚠️ Database connection failed: %v", err)
	}
	defer database.Close()

	r := gin.Default()
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

	r.GET("/health", func(c *gin.Context) {
		dbStatus := "connected"
		if database.GetDB() == nil {
			dbStatus = "disconnected"
		}
		c.JSON(200, gin.H{"status": "healthy", "service": "procurement-service", "database": dbStatus})
	})

	h := handlers.NewProcurementHandler()

	proc := r.Group("/procurement")
	{
		proc.GET("/stats", h.GetStats)
		proc.GET("/vendors", h.ListVendors)
		proc.POST("/vendors", h.CreateVendor)
		proc.GET("/vendors/:id", h.GetVendor)
		proc.PUT("/vendors/:id", h.UpdateVendor)
		proc.GET("/purchase-requests", h.ListPurchaseRequests)
		proc.POST("/purchase-requests", h.CreatePurchaseRequest)
		proc.POST("/purchase-requests/:id/approve", h.ApprovePurchaseRequest)
		proc.POST("/purchase-requests/:id/reject", h.RejectPurchaseRequest)
		proc.GET("/purchase-orders", h.ListPurchaseOrders)
		proc.POST("/purchase-orders", h.CreatePurchaseOrder)
		proc.POST("/purchase-orders/from-pr", h.CreatePurchaseOrderFromPR)
		proc.POST("/purchase-orders/:id/approve", h.ApprovePurchaseOrder)
		proc.POST("/purchase-orders/:id/send", h.SendPurchaseOrder)
		proc.POST("/purchase-orders/:id/receive", h.ReceivePurchaseOrder)
		proc.GET("/purchase-orders/:id/pdf", h.DownloadPurchaseOrderPDF)
		proc.GET("/bills", h.ListVendorBills)
		proc.POST("/bills", h.CreateVendorBill)
		proc.GET("/rfqs", h.ListRFQs)
		proc.POST("/rfqs", h.CreateRFQ)
		proc.GET("/rfqs/:id", h.GetRFQ)
		proc.PUT("/rfqs/:id/send", h.SendRFQ)
		proc.GET("/payments", h.ListPayments)
		proc.POST("/bills/:id/payments", h.CreateBillPayment)
		proc.GET("/analytics/summary", h.GetAnalyticsSummary)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8018"
	}
	log.Printf("🛒 Procurement Service starting on port %s", port)
	r.Run(":" + port)
}
