package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/auth-service/internal/database"
	"github.com/elviskudo/mini-erp/services/auth-service/internal/handlers"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Connect to database
	if err := database.Connect(); err != nil {
		log.Printf("⚠️ Database connection failed: %v (running with limited functionality)", err)
	} else {
		// Seed menus if connected
		if err := database.SeedMenus(); err != nil {
			log.Printf("⚠️ Menu seeding failed: %v", err)
		}
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
			"service":  "auth-service",
			"version":  "1.0.0",
			"database": dbStatus,
		})
	})

	// Scalar API Documentation
	r.GET("/docs", handlers.ScalarDocs)
	r.GET("/docs/*any", handlers.ScalarDocs)
	r.GET("/openapi.json", handlers.OpenAPISpec)

	// Initialize handlers
	authHandler := handlers.NewAuthHandler()

	// Auth routes
	setupRoutes(r.Group("/auth"), authHandler)
	setupRoutes(r.Group("/api/v1/auth"), authHandler)

	// Menu routes (separate from auth prefix)
	setupMenuRoutes(r, authHandler)

	// Tenant routes
	setupTenantRoutes(r, authHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8010"
	}

	log.Printf("🔐 Auth Service starting on port %s", port)
	log.Printf("📊 Database: %s", getDatabaseStatus())
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start auth service: %v", err)
	}
}

func setupRoutes(auth *gin.RouterGroup, h *handlers.AuthHandler) {
	// Public routes (no auth required)
	auth.POST("/login", h.Login)
	auth.POST("/token", h.Login) // OAuth2 compatible
	auth.POST("/register", h.Register)
	auth.POST("/refresh", h.RefreshToken)
	auth.POST("/send-otp", h.SendOTP)
	auth.POST("/verify-otp", h.VerifyOTP)
	auth.POST("/forgot-password", h.ForgotPassword)

	// Protected routes (need JWT middleware in gateway)
	auth.GET("/me", h.GetProfile)
	auth.POST("/logout", h.Logout)
	auth.GET("/user-tenants", h.GetUserTenants) // Get tenants for current user
	auth.POST("/switch-tenant", h.SwitchTenant) // Switch to different tenant
	auth.GET("/users", h.ListUsers)             // List users
}

// setupMenuRoutes sets up menu routes (separate from auth group)
func setupMenuRoutes(r *gin.Engine, h *handlers.AuthHandler) {
	// Menus endpoint - accessible at /menus (protected by gateway JWT)
	r.GET("/menus", h.GetMenus)
	r.GET("/api/v1/menus", h.GetMenus)
}

// setupTenantRoutes sets up tenant routes
func setupTenantRoutes(r *gin.Engine, h *handlers.AuthHandler) {
	// Tenants endpoints
	r.GET("/tenants", h.GetTenants)
	r.GET("/tenants/:id", h.GetTenant)
	r.GET("/api/v1/tenants", h.GetTenants)
	r.GET("/api/v1/tenants/:id", h.GetTenant)
}

func getDatabaseStatus() string {
	if database.GetDB() != nil {
		return "Connected to Supabase"
	}
	return "Not connected (mock mode)"
}
