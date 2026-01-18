package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/projects-service/internal/database"
	"github.com/elviskudo/mini-erp/services/projects-service/internal/handlers"
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
		c.JSON(200, gin.H{"status": "healthy", "service": "projects-service", "database": dbStatus})
	})

	h := handlers.NewProjectsHandler()

	// Projects routes
	proj := r.Group("/projects")
	{
		proj.GET("/stats", h.GetStats)

		proj.GET("", h.ListProjects)
		proj.POST("", h.CreateProject)
		proj.GET("/:id", h.GetProject)
		proj.PUT("/:id", h.UpdateProject)
		proj.DELETE("/:id", h.DeleteProject)

		proj.GET("/tasks", h.ListTasks)
		proj.POST("/tasks", h.CreateTask)
		proj.PUT("/tasks/:id/status", h.UpdateTaskStatus)

		proj.GET("/members", h.ListMembers)

		proj.GET("/expenses", h.ListExpenses)
		proj.POST("/expenses", h.CreateExpense)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8016"
	}

	log.Printf("📋 Projects Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start projects service: %v", err)
	}
}
