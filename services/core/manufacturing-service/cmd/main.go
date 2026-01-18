package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/manufacturing-service/internal/database"
	"github.com/elviskudo/mini-erp/services/manufacturing-service/internal/handlers"
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
		c.JSON(200, gin.H{"status": "healthy", "service": "manufacturing-service", "database": dbStatus})
	})

	h := handlers.NewManufacturingHandler()

	// Manufacturing routes
	mfg := r.Group("/manufacturing")
	{
		mfg.GET("/stats", h.GetStats)

		mfg.GET("/work-centers", h.ListWorkCenters)
		mfg.POST("/work-centers", h.CreateWorkCenter)
		mfg.GET("/work-centers/:id", h.GetWorkCenter)
		mfg.PUT("/work-centers/:id", h.UpdateWorkCenter)
		mfg.DELETE("/work-centers/:id", h.DeleteWorkCenter)

		// Categories
		mfg.GET("/categories", h.ListCategories)
		mfg.POST("/categories", h.CreateCategory)
		mfg.GET("/categories/:id", h.GetCategory)
		mfg.PUT("/categories/:id", h.UpdateCategory)
		mfg.DELETE("/categories/:id", h.DeleteCategory)

		mfg.GET("/production-orders", h.ListProductionOrders)
		mfg.POST("/production-orders", h.CreateProductionOrder)
		mfg.GET("/production-orders/:id", h.GetProductionOrder)
		mfg.PUT("/production-orders/:id", h.UpdateProductionOrder)
		mfg.DELETE("/production-orders/:id", h.DeleteProductionOrder)
		mfg.PUT("/production-orders/:id/status", h.UpdateProductionOrderStatus)

		// Alias /orders -> /production-orders
		mfg.GET("/orders", h.ListProductionOrders)
		mfg.POST("/orders", h.CreateProductionOrder)
		mfg.GET("/orders/:id", h.GetProductionOrder)
		mfg.PUT("/orders/:id", h.UpdateProductionOrder)
		mfg.DELETE("/orders/:id", h.DeleteProductionOrder)

		mfg.GET("/bom", h.ListBOMItems)
		mfg.GET("/bom-items", h.ListBOMItems) // Alias for frontend compatibility
		mfg.POST("/bom", h.CreateBOM)
		mfg.GET("/bom/:id", h.GetBOM)
		mfg.PUT("/bom/:id", h.UpdateBOM)
		mfg.DELETE("/bom/:id", h.DeleteBOM)

		mfg.GET("/qc-results", h.ListQCResults)
		mfg.POST("/qc-results", h.CreateQCResult)

		// Alias /quality-checks -> /qc-results
		mfg.GET("/quality-checks", h.ListQCResults)
		mfg.POST("/quality-checks", h.CreateQCResult)
		mfg.GET("/quality-checks/:id", h.GetQCResult)
		mfg.PUT("/quality-checks/:id", h.UpdateQCResult)
		mfg.DELETE("/quality-checks/:id", h.DeleteQCResult)

		// Work Orders
		mfg.GET("/work-orders", h.ListWorkOrders)
		mfg.POST("/work-orders", h.CreateWorkOrder)
		mfg.GET("/work-orders/:id", h.GetWorkOrder)
		mfg.PUT("/work-orders/:id", h.UpdateWorkOrder)
		mfg.DELETE("/work-orders/:id", h.DeleteWorkOrder)
		mfg.PUT("/work-orders/:id/status", h.UpdateWorkOrderStatus)

		// Routings
		mfg.GET("/routings", h.ListRoutings)
		mfg.POST("/routings", h.CreateRouting)
		mfg.GET("/routings/:id", h.GetRouting)
		mfg.PUT("/routings/:id", h.UpdateRouting)
		mfg.DELETE("/routings/:id", h.DeleteRouting)

		// MRP (New)
		mrp := mfg.Group("/mrp")
		{
			mrp.GET("/run", h.RunMRP)
			mrp.GET("/mps", h.GetMPS)
			mrp.GET("/forecast", h.GetDemandForecast)
			mrp.GET("/requirements", h.GetNetRequirements)
			mrp.GET("/exceptions", h.GetMRPExceptions)
			mrp.GET("/analytics", h.GetMRPAnalytics)
		}
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8014"
	}

	log.Printf("🏭 Manufacturing Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start manufacturing service: %v", err)
	}
}
