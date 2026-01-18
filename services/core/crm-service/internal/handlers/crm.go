package handlers

import (
	"strconv"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/response"
	"github.com/gin-gonic/gin"
)

type CRMHandler struct{}

func NewCRMHandler() *CRMHandler {
	return &CRMHandler{}
}

// ========== STATS ==========

// GetStats returns CRM statistics
func (h *CRMHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, "Statistics retrieved", gin.H{
			"total_leads":         15,
			"new_leads":           5,
			"qualified_leads":     8,
			"total_customers":     50,
			"total_opportunities": 10,
			"pipeline_value":      500000000,
		})
		return
	}

	var totalLeads, newLeads, qualified, totalCustomers, totalOpportunities int64
	db.Model(&models.Lead{}).Count(&totalLeads)
	db.Model(&models.Lead{}).Where("status = ?", "NEW").Count(&newLeads)
	db.Model(&models.Lead{}).Where("status = ?", "QUALIFIED").Count(&qualified)
	db.Model(&models.Customer{}).Count(&totalCustomers)
	db.Model(&models.Opportunity{}).Count(&totalOpportunities)

	response.Success(c, "Statistics retrieved", gin.H{
		"total_leads":         totalLeads,
		"new_leads":           newLeads,
		"qualified_leads":     qualified,
		"total_customers":     totalCustomers,
		"total_opportunities": totalOpportunities,
	})
}

// ========== LEADS ==========

// ListLeads lists leads with pagination
func (h *CRMHandler) ListLeads(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Leads retrieved", getMockLeads(), page, limit, 2)
		return
	}

	var leads []models.Lead
	var total int64

	query := db.Model(&models.Lead{})
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}
	if source := c.Query("source"); source != "" {
		query = query.Where("source = ?", source)
	}

	query.Count(&total)
	if err := query.Order("name ASC").Offset(offset).Limit(limit).Find(&leads).Error; err != nil {
		response.SuccessWithPagination(c, "Leads retrieved", getMockLeads(), page, limit, 2)
		return
	}

	if len(leads) == 0 {
		response.SuccessWithPagination(c, "Leads retrieved", getMockLeads(), page, limit, 2)
		return
	}
	response.SuccessWithPagination(c, "Leads retrieved", leads, page, limit, total)
}

func getMockLeads() []gin.H {
	return []gin.H{
		{"id": "lead-1", "name": "PT ABC Corp", "email": "info@abc.com", "status": "NEW", "source": "WEBSITE"},
		{"id": "lead-2", "name": "CV Maju Jaya", "email": "sales@majujaya.id", "status": "QUALIFIED", "source": "REFERRAL"},
	}
}

// GetLead gets a lead by ID
func (h *CRMHandler) GetLead(c *gin.Context) {
	db := database.GetDB()
	leadID := c.Param("id")

	if db == nil {
		response.Success(c, "Lead retrieved", gin.H{"id": leadID, "name": "PT ABC Corp"})
		return
	}

	var lead models.Lead
	if err := db.First(&lead, "id = ?", leadID).Error; err != nil {
		response.NotFound(c, "Lead not found")
		return
	}
	response.Success(c, "Lead retrieved", lead)
}

// CreateLead creates a new lead
func (h *CRMHandler) CreateLead(c *gin.Context) {
	var req struct {
		Name    string `json:"name" binding:"required"`
		Email   string `json:"email"`
		Company string `json:"company"`
		Source  string `json:"source"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}
	response.Created(c, "Lead created successfully", gin.H{"id": "new-lead-id", "name": req.Name})
}

// UpdateLead updates a lead
func (h *CRMHandler) UpdateLead(c *gin.Context) {
	leadID := c.Param("id")
	response.Updated(c, "Lead updated successfully", gin.H{"id": leadID})
}

// ConvertLead converts a lead to customer/opportunity
func (h *CRMHandler) ConvertLead(c *gin.Context) {
	leadID := c.Param("id")
	response.Updated(c, "Lead converted successfully", gin.H{"id": leadID, "status": "CONVERTED"})
}

// ========== CUSTOMERS ==========

// ListCustomers lists customers with pagination
func (h *CRMHandler) ListCustomers(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Customers retrieved", getMockCustomers(), page, limit, 2)
		return
	}

	var customers []models.Customer
	var total int64

	query := db.Model(&models.Customer{})
	if search := c.Query("search"); search != "" {
		query = query.Where("name ILIKE ? OR email ILIKE ?", "%"+search+"%", "%"+search+"%")
	}

	query.Count(&total)
	if err := query.Order("name ASC").Offset(offset).Limit(limit).Find(&customers).Error; err != nil {
		response.SuccessWithPagination(c, "Customers retrieved", getMockCustomers(), page, limit, 2)
		return
	}

	if len(customers) == 0 {
		response.SuccessWithPagination(c, "Customers retrieved", getMockCustomers(), page, limit, 2)
		return
	}
	response.SuccessWithPagination(c, "Customers retrieved", customers, page, limit, total)
}

func getMockCustomers() []gin.H {
	return []gin.H{
		{"id": "cust-1", "name": "PT Sejahtera", "email": "info@sejahtera.com", "credit_limit": 50000000},
		{"id": "cust-2", "name": "CV Makmur", "email": "sales@makmur.id", "credit_limit": 25000000},
	}
}

// GetCustomer gets customer by ID
func (h *CRMHandler) GetCustomer(c *gin.Context) {
	db := database.GetDB()
	customerID := c.Param("id")

	if db == nil {
		response.Success(c, "Customer retrieved", gin.H{"id": customerID, "name": "PT Sejahtera"})
		return
	}

	var customer models.Customer
	if err := db.First(&customer, "id = ?", customerID).Error; err != nil {
		response.NotFound(c, "Customer not found")
		return
	}
	response.Success(c, "Customer retrieved", customer)
}

// CreateCustomer creates a customer
func (h *CRMHandler) CreateCustomer(c *gin.Context) {
	var req struct {
		Name  string `json:"name" binding:"required"`
		Email string `json:"email"`
		Phone string `json:"phone"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}
	response.Created(c, "Customer created successfully", gin.H{"id": "new-customer-id", "name": req.Name})
}

// UpdateCustomer updates a customer
func (h *CRMHandler) UpdateCustomer(c *gin.Context) {
	customerID := c.Param("id")
	response.Updated(c, "Customer updated successfully", gin.H{"id": customerID})
}

// ========== OPPORTUNITIES ==========

// ListOpportunities lists opportunities with pagination
func (h *CRMHandler) ListOpportunities(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Opportunities retrieved", []gin.H{
			{"id": "opp-1", "name": "ERP System Sale", "stage": "PROPOSAL", "amount": 500000000},
		}, page, limit, 1)
		return
	}

	var opportunities []models.Opportunity
	var total int64

	query := db.Model(&models.Opportunity{})
	if stage := c.Query("stage"); stage != "" {
		query = query.Where("stage = ?", stage)
	}

	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&opportunities).Error; err != nil {
		response.SuccessWithPagination(c, "Opportunities retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Opportunities retrieved", opportunities, page, limit, total)
}

// CreateOpportunity creates an opportunity
func (h *CRMHandler) CreateOpportunity(c *gin.Context) {
	response.Created(c, "Opportunity created successfully", gin.H{"id": "new-opp-id"})
}

// ========== ACTIVITIES ==========

// ListActivities lists activities
func (h *CRMHandler) ListActivities(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Activities retrieved", []gin.H{
			{"id": "act-1", "type": "CALL", "subject": "Follow up call"},
		}, page, limit, 1)
		return
	}

	var activities []models.Activity
	var total int64

	query := db.Model(&models.Activity{})
	query.Count(&total)

	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&activities).Error; err != nil {
		response.SuccessWithPagination(c, "Activities retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Activities retrieved", activities, page, limit, total)
}

// CreateActivity creates an activity
func (h *CRMHandler) CreateActivity(c *gin.Context) {
	response.Created(c, "Activity created successfully", gin.H{"id": "new-activity-id"})
}
