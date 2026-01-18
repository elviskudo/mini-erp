package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/gateway/internal/database"
	"github.com/elviskudo/mini-erp/gateway/internal/kafka"
	"github.com/elviskudo/mini-erp/gateway/internal/middleware"
	"github.com/elviskudo/mini-erp/gateway/internal/routes"
	"github.com/gin-gonic/gin"
)

// @title Mini-ERP API Gateway
// @version 1.0
// @description Enterprise Resource Planning API Gateway with Microservices Architecture
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.mini-erp.io/support
// @contact.email support@mini-erp.io

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @host localhost:8000
// @BasePath /api/v1

// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
// @description Type "Bearer" followed by a space and JWT token.

func main() {
	// Set Gin mode based on environment
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Initialize Database (optional - can fail gracefully for now)
	if err := database.Connect(); err != nil {
		log.Printf("⚠ Database connection failed (will retry): %v", err)
	} else {
		defer database.Close()
	}

	// Initialize Kafka Producer
	if err := kafka.InitProducer(); err != nil {
		log.Printf("⚠ Kafka producer initialization failed: %v", err)
	} else {
		defer kafka.CloseProducer()
	}

	// Initialize router
	r := gin.Default()

	// Add global middleware
	r.Use(middleware.CORS())
	r.Use(middleware.RateLimiter())
	r.Use(middleware.RequestLogger())

	// Health check endpoint
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":  "healthy",
			"service": "api-gateway",
			"version": "1.0.0",
		})
	})

	// Root endpoint
	r.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"message": "Welcome to Mini ERP API Gateway",
			"docs":    "/docs",
		})
	})

	// Setup all routes
	routes.SetupRoutes(r)

	// Get port from environment or default to 8000
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	log.Printf("🚀 API Gateway starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
