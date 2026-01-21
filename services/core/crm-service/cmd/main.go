package main

import (
	"log"
	"os"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/handlers"
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
		c.JSON(200, gin.H{"status": "healthy", "service": "crm-service", "database": dbStatus})
	})

	h := handlers.NewCRMHandler()

	// CRM routes
	crm := r.Group("/crm")
	{
		crm.GET("/stats", h.GetStats)

		crm.GET("/leads", h.ListLeads)
		crm.POST("/leads", h.CreateLead)
		crm.GET("/leads/:id", h.GetLead)
		crm.PUT("/leads/:id", h.UpdateLead)
		crm.POST("/leads/:id/convert", h.ConvertLead)

		crm.GET("/customers", h.ListCustomers)
		crm.POST("/customers", h.CreateCustomer)
		crm.GET("/customers/:id", h.GetCustomer)
		crm.PUT("/customers/:id", h.UpdateCustomer)

		crm.GET("/opportunities", h.ListOpportunities)
		crm.POST("/opportunities", h.CreateOpportunity)

		crm.GET("/activities", h.ListActivities)
		crm.POST("/activities", h.CreateActivity)

		// Companies (B2B)
		crm.GET("/companies", h.ListCompanies)
		crm.POST("/companies", h.CreateCompany)
		crm.GET("/companies/:id", h.GetCompany)
		crm.PUT("/companies/:id", h.UpdateCompany)
		crm.DELETE("/companies/:id", h.DeleteCompany)

		// Contacts
		crm.GET("/contacts", h.ListContacts)
		crm.POST("/contacts", h.CreateContact)
		crm.GET("/contacts/:id", h.GetContact)
		crm.PUT("/contacts/:id", h.UpdateContact)
		crm.DELETE("/contacts/:id", h.DeleteContact)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8017"
	}

	log.Printf("👥 CRM Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start CRM service: %v", err)
	}
}
