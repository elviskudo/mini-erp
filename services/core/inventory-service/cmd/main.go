package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/inventory-service/internal/database"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/handlers"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/response"
	"github.com/gin-gonic/gin"
)

func main() {
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Connect to database
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
		response.Success(c, gin.H{
			"status":   "healthy",
			"service":  "inventory-service",
			"version":  "1.0.0",
			"database": dbStatus,
		}, "Service is healthy")
	})

	// Scalar API Documentation
	r.GET("/docs", handlers.ScalarDocs)
	r.GET("/docs/*any", handlers.ScalarDocs)
	r.GET("/openapi.json", handlers.OpenAPISpec)

	// Initialize handlers
	invHandler := handlers.NewInventoryHandler()

	// Inventory routes
	inv := r.Group("/inventory")
	{
		// Stats
		inv.GET("/stats", invHandler.GetStats)

		// Products
		inv.GET("/products", invHandler.ListProducts)
		inv.GET("/products/:id", invHandler.GetProduct)
		inv.POST("/products", invHandler.CreateProduct)
		inv.PUT("/products/:id", invHandler.UpdateProduct)
		inv.DELETE("/products/:id", invHandler.DeleteProduct)

		// Warehouses
		inv.GET("/warehouses", invHandler.ListWarehouses)
		inv.GET("/warehouses/:id", invHandler.GetWarehouse)
		inv.POST("/warehouses", invHandler.CreateWarehouse)
		inv.PUT("/warehouses/:id", invHandler.UpdateWarehouse)

		// Stock
		inv.GET("/stock", invHandler.ListStock)

		// Movements
		inv.GET("/movements", invHandler.ListMovements)

		// Opname
		inv.GET("/opnames", invHandler.ListOpnames)
		inv.GET("/opnames/:id", invHandler.GetOpname)
		inv.POST("/opnames", invHandler.CreateOpname)

		// Opname Extended (New Menu)
		opname := inv.Group("/opname")
		{
			opname.GET("/schedule", invHandler.ListOpnameSchedules)
			opname.GET("/schedules", invHandler.ListOpnameSchedules) // Alias for plural
			opname.POST("/schedule", invHandler.CreateOpnameSchedule)
			opname.POST("/schedule/:id/assign", invHandler.AddTeamMember)
			opname.POST("/assign-team", invHandler.AssignTeam)
			opname.GET("/print-list/:warehouse_id", invHandler.PrintOpnameList)
			opname.GET("/list", invHandler.ListOpnames) // Dashboard list
			opname.GET("/counting", invHandler.ListOpnameCounting)
			opname.POST("/counting", invHandler.SubmitOpnameCount)
			opname.GET("/matching", invHandler.ListOpnameMatching)
			opname.POST("/matching", invHandler.SubmitOpnameMatch)
			opname.GET("/adjustment", invHandler.ListOpnameAdjustments)
			opname.POST("/adjustment", invHandler.SubmitOpnameAdjustment)
		}

		// Locations
		inv.GET("/locations", invHandler.GetLocationsHierarchy)
		inv.GET("/locations-for-move", invHandler.GetLocationsForMove)
		inv.GET("/storage-zones", invHandler.ListStorageZones)
		inv.POST("/storage-zones", invHandler.CreateStorageZone)
		inv.GET("/storage-zones/:id", invHandler.GetStorageZone)
		inv.PUT("/storage-zones/:id", invHandler.UpdateStorageZone)
		inv.DELETE("/storage-zones/:id", invHandler.DeleteStorageZone)

		// Categories
		inv.GET("/categories", invHandler.ListCategories)
	}

	// Also mount at /api/v1/inventory
	apiV1 := r.Group("/api/v1/inventory")
	{
		apiV1.GET("/stats", invHandler.GetStats)
		apiV1.GET("/products", invHandler.ListProducts)
		apiV1.GET("/products/:id", invHandler.GetProduct)
		apiV1.POST("/products", invHandler.CreateProduct)
		apiV1.PUT("/products/:id", invHandler.UpdateProduct)
		apiV1.DELETE("/products/:id", invHandler.DeleteProduct)
		apiV1.GET("/warehouses", invHandler.ListWarehouses)
		apiV1.GET("/warehouses/:id", invHandler.GetWarehouse)
		apiV1.POST("/warehouses", invHandler.CreateWarehouse)
		apiV1.PUT("/warehouses/:id", invHandler.UpdateWarehouse)
		apiV1.GET("/stock", invHandler.ListStock)
		apiV1.GET("/movements", invHandler.ListMovements)
		apiV1.GET("/opnames", invHandler.ListOpnames)
		apiV1.GET("/opnames/:id", invHandler.GetOpname)
		apiV1.POST("/opnames", invHandler.CreateOpname)
		apiV1.GET("/locations", invHandler.GetLocationsHierarchy)
		apiV1.GET("/locations-for-move", invHandler.GetLocationsForMove)
		apiV1.GET("/storage-zones", invHandler.ListStorageZones)
		apiV1.POST("/storage-zones", invHandler.CreateStorageZone)
		apiV1.GET("/storage-zones/:id", invHandler.GetStorageZone)
		apiV1.PUT("/storage-zones/:id", invHandler.UpdateStorageZone)
		apiV1.DELETE("/storage-zones/:id", invHandler.DeleteStorageZone)
		apiV1.GET("/categories", invHandler.ListCategories)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8013"
	}

	log.Printf("📦 Inventory Service starting on port %s", port)
	log.Printf("📊 Database: %s", getDatabaseStatus())
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start inventory service: %v", err)
	}
}

func getDatabaseStatus() string {
	if database.GetDB() != nil {
		return "Connected to Supabase"
	}
	return "Not connected (mock mode)"
}
