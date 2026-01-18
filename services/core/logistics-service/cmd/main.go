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
		logis.GET("/deliveries/:id", h.GetDelivery)
		logis.PUT("/deliveries/:id/status", h.UpdateDeliveryStatus)
		logis.GET("/shipments", h.ListShipments)
		logis.POST("/shipments", h.CreateShipment)
		logis.GET("/track/:tracking", h.TrackShipment)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8019"
	}
	log.Printf("🚚 Logistics Service starting on port %s", port)
	r.Run(":" + port)
}
