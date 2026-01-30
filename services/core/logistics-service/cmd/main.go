package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/logistics-service/internal/database"
	"github.com/elviskudo/mini-erp/services/logistics-service/internal/handlers"
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

		if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
			c.Set("tenant_id", tenantID)
		}

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
		c.JSON(200, gin.H{"status": "healthy", "service": "logistics-service", "database": dbStatus})
	})

	h := handlers.NewLogisticsHandler()
	logis := r.Group("/logistics")
	{
		logis.GET("/stats", h.GetStats)
		logis.GET("/deliveries", h.ListDeliveries)
		logis.POST("/deliveries", h.CreateDelivery)
		logis.POST("/deliveries/create", h.CreateDelivery) // Alias for frontend
		logis.GET("/track/:tracking", h.TrackShipment)

		// Stock Transfers
		logis.GET("/transfers", h.ListTransfers)
		logis.POST("/transfers", h.CreateTransfer)
		logis.PUT("/transfers/:id/start", h.StartTransfer)
		logis.PUT("/transfers/:id/complete", h.CompleteTransfer)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8019"
	}
	log.Printf("🚚 Logistics Service starting on port %s", port)
	r.Run(":" + port)
}
