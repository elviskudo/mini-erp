package handlers

import (
	"strconv"
	"time"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ========== CUSTOMER EMAILS ==========

func (h *CRMHandler) ListCustomerEmails(c *gin.Context) {
	customerID := c.Param("id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var items []models.CustomerEmail
	var total int64

	db := database.GetDB()
	query := db.Model(&models.CustomerEmail{}).Where("customer_id = ?", customerID)
	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&items).Error; err != nil {
		response.InternalError(c, "Failed to fetch emails")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Emails retrieved")
}

func (h *CRMHandler) CreateCustomerEmail(c *gin.Context) {
	customerID := c.Param("id")

	var email models.CustomerEmail
	if err := c.ShouldBindJSON(&email); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	email.CustomerID = customerID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		email.TenantID = tenantID
	}
	if email.TenantID == "" {
		email.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	now := time.Now()
	email.SentAt = &now

	if err := database.GetDB().Create(&email).Error; err != nil {
		response.InternalError(c, "Failed to create email: "+err.Error())
		return
	}

	response.Success(c, email, "Email created")
}

// ========== CUSTOMER CALLS ==========

func (h *CRMHandler) ListCustomerCalls(c *gin.Context) {
	customerID := c.Param("id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var items []models.CustomerCall
	var total int64

	db := database.GetDB()
	query := db.Model(&models.CustomerCall{}).Where("customer_id = ?", customerID)
	query.Count(&total)
	if err := query.Order("call_time DESC").Offset(offset).Limit(limit).Find(&items).Error; err != nil {
		response.InternalError(c, "Failed to fetch calls")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Calls retrieved")
}

func (h *CRMHandler) CreateCustomerCall(c *gin.Context) {
	customerID := c.Param("id")

	var call models.CustomerCall
	if err := c.ShouldBindJSON(&call); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	call.CustomerID = customerID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		call.TenantID = tenantID
	}
	if call.TenantID == "" {
		call.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if call.CallTime.IsZero() {
		call.CallTime = time.Now()
	}

	if err := database.GetDB().Create(&call).Error; err != nil {
		response.InternalError(c, "Failed to create call: "+err.Error())
		return
	}

	response.Success(c, call, "Call logged")
}

// ========== CUSTOMER MEETINGS ==========

func (h *CRMHandler) ListCustomerMeetings(c *gin.Context) {
	customerID := c.Param("id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var items []models.CustomerMeeting
	var total int64

	db := database.GetDB()
	query := db.Model(&models.CustomerMeeting{}).Where("customer_id = ?", customerID)
	query.Count(&total)
	if err := query.Order("start_time DESC").Offset(offset).Limit(limit).Find(&items).Error; err != nil {
		response.InternalError(c, "Failed to fetch meetings")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Meetings retrieved")
}

func (h *CRMHandler) CreateCustomerMeeting(c *gin.Context) {
	customerID := c.Param("id")

	var meeting models.CustomerMeeting
	if err := c.ShouldBindJSON(&meeting); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	meeting.CustomerID = customerID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		meeting.TenantID = tenantID
	}
	if meeting.TenantID == "" {
		meeting.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&meeting).Error; err != nil {
		response.InternalError(c, "Failed to create meeting: "+err.Error())
		return
	}

	response.Success(c, meeting, "Meeting created")
}

func (h *CRMHandler) UpdateCustomerMeeting(c *gin.Context) {
	id := c.Param("id")

	var existing models.CustomerMeeting
	db := database.GetDB()
	if err := db.First(&existing, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Meeting not found")
		return
	}

	var meeting models.CustomerMeeting
	if err := c.ShouldBindJSON(&meeting); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	meeting.ID = id
	meeting.CustomerID = existing.CustomerID
	meeting.TenantID = existing.TenantID
	meeting.CreatedAt = existing.CreatedAt

	if err := db.Save(&meeting).Error; err != nil {
		response.InternalError(c, "Failed to update meeting: "+err.Error())
		return
	}

	response.Success(c, meeting, "Meeting updated")
}

// ========== CUSTOMER DOCUMENTS ==========

func (h *CRMHandler) ListCustomerDocuments(c *gin.Context) {
	customerID := c.Param("id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var items []models.CustomerDocument
	var total int64

	db := database.GetDB()
	query := db.Model(&models.CustomerDocument{}).Where("customer_id = ?", customerID)
	if category := c.Query("category"); category != "" {
		query = query.Where("category = ?", category)
	}
	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&items).Error; err != nil {
		response.InternalError(c, "Failed to fetch documents")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Documents retrieved")
}

func (h *CRMHandler) CreateCustomerDocument(c *gin.Context) {
	customerID := c.Param("id")

	var doc models.CustomerDocument
	if err := c.ShouldBindJSON(&doc); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	doc.CustomerID = customerID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		doc.TenantID = tenantID
	}
	if doc.TenantID == "" {
		doc.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&doc).Error; err != nil {
		response.InternalError(c, "Failed to create document: "+err.Error())
		return
	}

	response.Success(c, doc, "Document created")
}

func (h *CRMHandler) DeleteCustomerDocument(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.CustomerDocument{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete document")
		return
	}
	response.Success(c, nil, "Document deleted")
}
