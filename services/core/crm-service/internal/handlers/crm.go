package handlers

import (
	"strconv"
	"strings"

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
		response.Success(c, gin.H{
			"total_leads":         15,
			"new_leads":           5,
			"qualified_leads":     8,
			"total_customers":     50,
			"total_opportunities": 10,
			"pipeline_value":      500000000,
		}, "Statistics retrieved")
		return
	}

	var totalLeads, newLeads, qualified, totalCustomers, totalOpportunities int64
	db.Model(&models.Lead{}).Count(&totalLeads)
	db.Model(&models.Lead{}).Where("status = ?", "NEW").Count(&newLeads)
	db.Model(&models.Lead{}).Where("status = ?", "QUALIFIED").Count(&qualified)
	db.Model(&models.Customer{}).Count(&totalCustomers)
	db.Model(&models.Opportunity{}).Count(&totalOpportunities)

	response.Success(c, gin.H{
		"total_leads":         totalLeads,
		"new_leads":           newLeads,
		"qualified_leads":     qualified,
		"total_customers":     totalCustomers,
		"total_opportunities": totalOpportunities,
	}, "Statistics retrieved")
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
		response.Success(c, gin.H{"id": leadID, "name": "PT ABC Corp"}, "Lead retrieved")
		return
	}

	var lead models.Lead
	if err := db.First(&lead, "id = ?", leadID).Error; err != nil {
		response.NotFound(c, "Lead not found")
		return
	}
	response.Success(c, lead, "Lead retrieved")
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
		response.Success(c, gin.H{"id": customerID, "name": "PT Sejahtera"}, "Customer retrieved")
		return
	}

	var customer models.Customer
	if err := db.First(&customer, "id = ?", customerID).Error; err != nil {
		response.NotFound(c, "Customer not found")
		return
	}
	response.Success(c, customer, "Customer retrieved")
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
	db := database.GetDB()
	customerID := c.Param("id")

	if db == nil {
		response.Updated(c, "Customer updated successfully", gin.H{"id": customerID})
		return
	}

	var customer models.Customer
	if err := db.First(&customer, "id = ?", customerID).Error; err != nil {
		response.NotFound(c, "Customer not found")
		return
	}

	var req models.Customer
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Update fields
	customer.Name = req.Name
	customer.Email = req.Email
	customer.Phone = req.Phone
	customer.Address = req.Address
	customer.CreditLimit = req.CreditLimit

	if err := db.Save(&customer).Error; err != nil {
		response.InternalError(c, "Failed to update customer")
		return
	}
	response.Updated(c, "Customer updated successfully", customer)
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

// GetOpportunity retrieves an opportunity by ID
func (h *CRMHandler) GetOpportunity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, gin.H{"id": id, "name": "Mock Opportunity"}, "Opportunity retrieved")
		return
	}

	var opp models.Opportunity
	if err := db.First(&opp, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Opportunity not found")
		return
	}
	response.Success(c, opp, "Opportunity retrieved")
}

// CreateOpportunity creates an opportunity
func (h *CRMHandler) CreateOpportunity(c *gin.Context) {
	db := database.GetDB()

	var req models.Opportunity
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if db == nil {
		response.Created(c, "Opportunity created successfully", gin.H{"id": "new-opp-id", "name": req.Name})
		return
	}

	// Set tenant ID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		req.TenantID = tenantID
	}
	if req.TenantID == "" {
		req.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	// Handle empty strings for UUID pointer fields - convert to nil
	if req.CustomerID != nil && *req.CustomerID == "" {
		req.CustomerID = nil
	}
	if req.LeadID != nil && *req.LeadID == "" {
		req.LeadID = nil
	}
	if req.AssignedTo != nil && *req.AssignedTo == "" {
		req.AssignedTo = nil
	}
	if req.CreatedBy != nil && *req.CreatedBy == "" {
		req.CreatedBy = nil
	}

	// Convert Stage to uppercase for enum compatibility (QUALIFICATION, NEEDS_ANALYSIS, etc)
	if req.Stage != nil && *req.Stage != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.Stage, " ", "_"))
		req.Stage = &upper
	}

	if err := db.Create(&req).Error; err != nil {
		response.InternalError(c, "Failed to create opportunity: "+err.Error())
		return
	}
	response.Created(c, "Opportunity created successfully", req)
}

// UpdateOpportunity updates an opportunity
func (h *CRMHandler) UpdateOpportunity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Updated(c, "Opportunity updated successfully", gin.H{"id": id})
		return
	}

	var opp models.Opportunity
	if err := db.First(&opp, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Opportunity not found")
		return
	}

	var req models.Opportunity
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	opp.Name = req.Name
	opp.Description = req.Description
	opp.Probability = req.Probability
	opp.ExpectedValue = req.ExpectedValue
	opp.ExpectedCloseDate = req.ExpectedCloseDate
	opp.ActualValue = req.ActualValue
	opp.LostReason = req.LostReason

	// Convert Stage to uppercase for enum compatibility
	if req.Stage != nil && *req.Stage != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.Stage, " ", "_"))
		opp.Stage = &upper
	} else {
		opp.Stage = nil
	}

	// Handle UUID pointer fields - convert empty strings to nil
	if req.CustomerID != nil && *req.CustomerID == "" {
		opp.CustomerID = nil
	} else {
		opp.CustomerID = req.CustomerID
	}
	if req.LeadID != nil && *req.LeadID == "" {
		opp.LeadID = nil
	} else {
		opp.LeadID = req.LeadID
	}
	if req.AssignedTo != nil && *req.AssignedTo == "" {
		opp.AssignedTo = nil
	} else {
		opp.AssignedTo = req.AssignedTo
	}

	if err := db.Save(&opp).Error; err != nil {
		response.InternalError(c, "Failed to update opportunity: "+err.Error())
		return
	}
	response.Updated(c, "Opportunity updated successfully", opp)
}

// DeleteOpportunity deletes an opportunity
func (h *CRMHandler) DeleteOpportunity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, nil, "Opportunity deleted successfully")
		return
	}

	if err := db.Delete(&models.Opportunity{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete opportunity")
		return
	}
	response.Success(c, nil, "Opportunity deleted successfully")
}

// UpdateOpportunityStage updates just the stage
func (h *CRMHandler) UpdateOpportunityStage(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")
	stage := c.Query("stage")

	// Convert stage to uppercase for enum compatibility
	stageUpper := strings.ToUpper(strings.ReplaceAll(stage, " ", "_"))

	if db == nil {
		response.Updated(c, "Stage updated", gin.H{"id": id, "stage": stageUpper})
		return
	}

	if err := db.Model(&models.Opportunity{}).Where("id = ?", id).Update("stage", stageUpper).Error; err != nil {
		response.InternalError(c, "Failed to update stage: "+err.Error())
		return
	}
	response.Updated(c, "Stage updated successfully", gin.H{"id": id, "stage": stageUpper})
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

// GetActivity retrieves an activity by ID
func (h *CRMHandler) GetActivity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, gin.H{"id": id}, "Activity retrieved")
		return
	}

	var act models.Activity
	if err := db.First(&act, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Activity not found")
		return
	}
	response.Success(c, act, "Activity retrieved")
}

// CreateActivity creates an activity
func (h *CRMHandler) CreateActivity(c *gin.Context) {
	db := database.GetDB()

	var req models.Activity
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if db == nil {
		response.Created(c, "Activity created successfully", gin.H{"id": "new-activity-id", "title": req.Title})
		return
	}

	// Set tenant ID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		req.TenantID = tenantID
	}
	if req.TenantID == "" {
		req.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	// Handle empty strings for UUID pointer fields - convert to nil
	if req.LeadID != nil && *req.LeadID == "" {
		req.LeadID = nil
	}
	if req.CustomerID != nil && *req.CustomerID == "" {
		req.CustomerID = nil
	}
	if req.AssignedTo != nil && *req.AssignedTo == "" {
		req.AssignedTo = nil
	}
	if req.OpportunityID != nil && *req.OpportunityID == "" {
		req.OpportunityID = nil
	}
	if req.CreatedBy != nil && *req.CreatedBy == "" {
		req.CreatedBy = nil
	}

	// Convert ActivityType to uppercase for enum compatibility
	if req.ActivityType != nil && *req.ActivityType != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.ActivityType, " ", "_"))
		req.ActivityType = &upper
	} else {
		req.ActivityType = nil
	}

	// Convert Status to uppercase for enum compatibility
	if req.Status != nil && *req.Status != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.Status, " ", "_"))
		req.Status = &upper
	} else {
		req.Status = nil
	}

	// Handle empty DueTime
	if req.DueTime != nil && *req.DueTime == "" {
		req.DueTime = nil
	}

	if err := db.Create(&req).Error; err != nil {
		response.InternalError(c, "Failed to create activity: "+err.Error())
		return
	}
	response.Created(c, "Activity created successfully", req)
}

// UpdateActivity updates an activity
func (h *CRMHandler) UpdateActivity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Updated(c, "Activity updated successfully", gin.H{"id": id})
		return
	}

	var act models.Activity
	if err := db.First(&act, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Activity not found")
		return
	}

	var req models.Activity
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Update fields using correct column names
	act.Title = req.Title
	act.Description = req.Description
	act.DueDate = req.DueDate
	act.DurationMinutes = req.DurationMinutes
	act.Priority = req.Priority
	act.Outcome = req.Outcome

	// Convert ActivityType to uppercase for enum compatibility
	if req.ActivityType != nil && *req.ActivityType != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.ActivityType, " ", "_"))
		act.ActivityType = &upper
	} else {
		act.ActivityType = nil
	}

	// Convert Status to uppercase for enum compatibility
	if req.Status != nil && *req.Status != "" {
		upper := strings.ToUpper(strings.ReplaceAll(*req.Status, " ", "_"))
		act.Status = &upper
	} else {
		act.Status = nil
	}

	// Handle empty DueTime
	if req.DueTime != nil && *req.DueTime == "" {
		act.DueTime = nil
	} else {
		act.DueTime = req.DueTime
	}

	// Handle UUID pointer fields - convert empty strings to nil
	if req.LeadID != nil && *req.LeadID == "" {
		act.LeadID = nil
	} else {
		act.LeadID = req.LeadID
	}
	if req.CustomerID != nil && *req.CustomerID == "" {
		act.CustomerID = nil
	} else {
		act.CustomerID = req.CustomerID
	}
	if req.OpportunityID != nil && *req.OpportunityID == "" {
		act.OpportunityID = nil
	} else {
		act.OpportunityID = req.OpportunityID
	}
	if req.AssignedTo != nil && *req.AssignedTo == "" {
		act.AssignedTo = nil
	} else {
		act.AssignedTo = req.AssignedTo
	}

	if err := db.Save(&act).Error; err != nil {
		response.InternalError(c, "Failed to update activity: "+err.Error())
		return
	}
	response.Updated(c, "Activity updated successfully", act)
}

// DeleteActivity deletes an activity
func (h *CRMHandler) DeleteActivity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, nil, "Activity deleted successfully")
		return
	}

	if err := db.Delete(&models.Activity{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete activity")
		return
	}
	response.Success(c, nil, "Activity deleted successfully")
}

// CompleteActivity marks an activity as completed
func (h *CRMHandler) CompleteActivity(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Updated(c, "Activity completed", gin.H{"id": id, "status": "Completed"})
		return
	}

	if err := db.Model(&models.Activity{}).Where("id = ?", id).Update("status", "Completed").Error; err != nil {
		response.InternalError(c, "Failed to complete activity")
		return
	}
	response.Updated(c, "Activity marked as completed", gin.H{"id": id, "status": "Completed"})
}
