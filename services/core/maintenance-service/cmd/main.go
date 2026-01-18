package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/maintenance-service/internal/database"
	"github.com/elviskudo/mini-erp/services/maintenance-service/internal/handlers"
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
		c.JSON(200, gin.H{"status": "healthy", "service": "maintenance-service", "database": dbStatus})
	})

	h := handlers.NewMaintenanceHandler()
	maint := r.Group("/maintenance")
	{
		maint.GET("/stats", h.GetStats)
		maint.GET("/assets", h.ListAssets)
		maint.POST("/assets", h.CreateAsset)
		maint.GET("/assets/:id", h.GetAsset)
		maint.PUT("/assets/:id", h.UpdateAsset)
		maint.GET("/work-orders", h.ListWorkOrders)
		maint.POST("/work-orders", h.CreateWorkOrder)
		maint.PUT("/work-orders/:id/status", h.UpdateWorkOrderStatus)
		maint.GET("/schedules", h.ListSchedules)
		maint.POST("/schedules", h.CreateSchedule)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8020"
	}
	log.Printf("🔧 Maintenance Service starting on port %s", port)
	r.Run(":" + port)
}
