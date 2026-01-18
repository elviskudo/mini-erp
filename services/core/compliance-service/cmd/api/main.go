package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/compliance-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

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
		c.JSON(200, gin.H{"status": "healthy", "service": "compliance-service"})
	})

	h := handlers.NewComplianceHandler()

	// Compliance routes
	compliance := r.Group("/compliance")
	{
		compliance.GET("/reports", h.GetReports)
		compliance.GET("/audit", h.GetAuditTrails)
		compliance.GET("/iso", h.GetISOTools)
		compliance.GET("/risk", h.GetRiskManagement)
		compliance.GET("/privacy", h.GetDataPrivacy)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8022"
	}

	log.Printf("🛡️ Compliance Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start compliance service: %v", err)
	}
}
