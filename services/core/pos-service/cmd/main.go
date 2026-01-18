package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/pos-service/internal/database"
	"github.com/elviskudo/mini-erp/services/pos-service/internal/handlers"
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
		c.JSON(200, gin.H{"status": "healthy", "service": "pos-service", "database": dbStatus})
	})

	h := handlers.NewPOSHandler()
	pos := r.Group("/pos")
	{
		pos.GET("/stats", h.GetStats)
		pos.GET("/transactions", h.ListTransactions)
		pos.POST("/transactions", h.CreateTransaction)
		pos.GET("/transactions/:id", h.GetTransaction)
		pos.POST("/transactions/:id/void", h.VoidTransaction)
		pos.GET("/promos", h.ListPromos)
		pos.POST("/promos", h.CreatePromo)
		pos.GET("/promos/validate/:code", h.ValidatePromo)
		pos.GET("/reports/daily", h.DailySalesReport)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8021"
	}
	log.Printf("🛒 POS Service starting on port %s", port)
	r.Run(":" + port)
}
