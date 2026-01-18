package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/fleet-service/internal/database"
	"github.com/elviskudo/mini-erp/services/fleet-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

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
		c.JSON(200, gin.H{"status": "healthy", "service": "fleet-service", "database": dbStatus})
	})

	h := handlers.NewFleetHandler()

	// Fleet routes
	fleet := r.Group("/fleet")
	{
		fleet.GET("/stats", h.GetStats)

		fleet.GET("/vehicles", h.ListVehicles)
		fleet.POST("/vehicles", h.CreateVehicle)
		fleet.GET("/vehicles/:id", h.GetVehicle)
		fleet.PUT("/vehicles/:id", h.UpdateVehicle)
		fleet.DELETE("/vehicles/:id", h.DeleteVehicle)

		fleet.GET("/bookings", h.ListBookings)
		fleet.POST("/bookings", h.CreateBooking)
		fleet.POST("/bookings/:id/approve", h.ApproveBooking)

		fleet.GET("/drivers", h.ListDrivers)
		fleet.POST("/drivers", h.CreateDriver)

		fleet.GET("/fuel-logs", h.ListFuelLogs)
		fleet.POST("/fuel-logs", h.CreateFuelLog)

		fleet.GET("/maintenance-logs", h.ListMaintenanceLogs)
		fleet.POST("/maintenance-logs", h.CreateMaintenanceLog)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8015"
	}

	log.Printf("🚗 Fleet Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start fleet service: %v", err)
	}
}
