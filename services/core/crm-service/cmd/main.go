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
		crm.GET("/opportunities/:id", h.GetOpportunity)
		crm.PUT("/opportunities/:id", h.UpdateOpportunity)
		crm.DELETE("/opportunities/:id", h.DeleteOpportunity)
		crm.PUT("/opportunities/:id/stage", h.UpdateOpportunityStage)

		crm.GET("/activities", h.ListActivities)
		crm.POST("/activities", h.CreateActivity)
		crm.GET("/activities/:id", h.GetActivity)
		crm.PUT("/activities/:id", h.UpdateActivity)
		crm.DELETE("/activities/:id", h.DeleteActivity)
		crm.PUT("/activities/:id/complete", h.CompleteActivity)

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

		// Campaigns
		crm.GET("/campaigns", h.ListCampaigns)
		crm.POST("/campaigns", h.CreateCampaign)
		crm.GET("/campaigns/:id", h.GetCampaign)
		crm.PUT("/campaigns/:id", h.UpdateCampaign)
		crm.DELETE("/campaigns/:id", h.DeleteCampaign)

		// Web Forms
		crm.GET("/forms", h.ListWebForms)
		crm.POST("/forms", h.CreateWebForm)
		crm.GET("/forms/:id", h.GetWebForm)
		crm.PUT("/forms/:id", h.UpdateWebForm)
		crm.DELETE("/forms/:id", h.DeleteWebForm)
		crm.GET("/forms/:id/submissions", h.ListWebFormSubmissions)

		// Customer Activity - use :id consistent with other customer routes
		crm.GET("/customers/:id/emails", h.ListCustomerEmails)
		crm.POST("/customers/:id/emails", h.CreateCustomerEmail)

		crm.GET("/customers/:id/calls", h.ListCustomerCalls)
		crm.POST("/customers/:id/calls", h.CreateCustomerCall)

		crm.GET("/customers/:id/meetings", h.ListCustomerMeetings)
		crm.POST("/customers/:id/meetings", h.CreateCustomerMeeting)

		crm.GET("/customers/:id/documents", h.ListCustomerDocuments)
		crm.POST("/customers/:id/documents", h.CreateCustomerDocument)

		// Separate routes for updating/deleting by activity ID
		crm.PUT("/meetings/:id", h.UpdateCustomerMeeting)
		crm.DELETE("/documents/:id", h.DeleteCustomerDocument)

		// Promos
		crm.GET("/promos", h.ListPromos)
		crm.POST("/promos", h.CreatePromo)
		crm.GET("/promos/:id", h.GetPromo)
		crm.PUT("/promos/:id", h.UpdatePromo)
		crm.DELETE("/promos/:id", h.DeletePromo)
		crm.POST("/promos/:id/publish", h.PublishPromo)

		// Email Broadcasts
		crm.GET("/email-broadcasts", h.ListEmailBroadcasts)
		crm.POST("/email-broadcasts", h.CreateEmailBroadcast)
		crm.GET("/email-broadcasts/:id", h.GetEmailBroadcast)
		crm.PUT("/email-broadcasts/:id", h.UpdateEmailBroadcast)
		crm.DELETE("/email-broadcasts/:id", h.DeleteEmailBroadcast)
	}

	// Public endpoint for form submission (no auth required)
	r.POST("/public/forms/:slug/submit", h.SubmitWebForm)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8017"
	}

	log.Printf("👥 CRM Service starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start CRM service: %v", err)
	}
}
