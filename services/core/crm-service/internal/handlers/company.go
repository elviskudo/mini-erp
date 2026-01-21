package handlers

import (
	"strconv"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ========== COMPANIES ==========

// ListCompanies lists companies with pagination
func (h *CRMHandler) ListCompanies(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	search := c.Query("search")

	var companies []models.Company
	var total int64

	query := db.Model(&models.Company{})
	if search != "" {
		query = query.Where("name ILIKE ?", "%"+search+"%")
	}

	query.Count(&total)
	if err := query.Order("name ASC").Offset(offset).Limit(limit).Find(&companies).Error; err != nil {
		response.InternalError(c, "Failed to fetch companies")
		return
	}

	response.SuccessList(c, companies, page, limit, int64(total), "Companies retrieved")
}

// CreateCompany creates a new company
func (h *CRMHandler) CreateCompany(c *gin.Context) {
	var company models.Company
	if err := c.ShouldBindJSON(&company); err != nil {
		response.BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	// Extract tenant_id from header
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		company.TenantID = tenantID
	}
	if company.TenantID == "" {
		company.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	db := database.GetDB()
	if err := db.Create(&company).Error; err != nil {
		response.InternalError(c, "Failed to create company: "+err.Error())
		return
	}

	response.Success(c, company, "Company created")
}

// GetCompany gets a single company by ID
func (h *CRMHandler) GetCompany(c *gin.Context) {
	id := c.Param("id")

	var company models.Company
	db := database.GetDB()
	if err := db.Preload("Contacts").First(&company, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Company not found")
		return
	}

	response.Success(c, company, "Company retrieved")
}

// UpdateCompany updates a company
func (h *CRMHandler) UpdateCompany(c *gin.Context) {
	id := c.Param("id")

	var existing models.Company
	db := database.GetDB()
	if err := db.First(&existing, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Company not found")
		return
	}

	var company models.Company
	if err := c.ShouldBindJSON(&company); err != nil {
		response.BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	company.ID = id
	company.TenantID = existing.TenantID
	company.CreatedAt = existing.CreatedAt

	if err := db.Save(&company).Error; err != nil {
		response.InternalError(c, "Failed to update company: "+err.Error())
		return
	}

	response.Success(c, company, "Company updated")
}

// DeleteCompany deletes a company
func (h *CRMHandler) DeleteCompany(c *gin.Context) {
	id := c.Param("id")

	db := database.GetDB()
	if err := db.Delete(&models.Company{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete company")
		return
	}

	response.Success(c, nil, "Company deleted")
}

// ========== CONTACTS ==========

// ListContacts lists contacts with pagination
func (h *CRMHandler) ListContacts(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	search := c.Query("search")
	companyID := c.Query("company_id")

	var contacts []models.Contact
	var total int64

	query := db.Model(&models.Contact{})
	if search != "" {
		query = query.Where("first_name ILIKE ? OR last_name ILIKE ? OR email ILIKE ?", "%"+search+"%", "%"+search+"%", "%"+search+"%")
	}
	if companyID != "" {
		query = query.Where("company_id = ?", companyID)
	}

	query.Count(&total)
	if err := query.Order("first_name ASC").Offset(offset).Limit(limit).Find(&contacts).Error; err != nil {
		response.InternalError(c, "Failed to fetch contacts")
		return
	}

	response.SuccessList(c, contacts, page, limit, int64(total), "Contacts retrieved")
}

// CreateContact creates a new contact
func (h *CRMHandler) CreateContact(c *gin.Context) {
	var contact models.Contact
	if err := c.ShouldBindJSON(&contact); err != nil {
		response.BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	// Extract tenant_id from header
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		contact.TenantID = tenantID
	}
	if contact.TenantID == "" {
		contact.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	db := database.GetDB()
	if err := db.Create(&contact).Error; err != nil {
		response.InternalError(c, "Failed to create contact: "+err.Error())
		return
	}

	response.Success(c, contact, "Contact created")
}

// GetContact gets a single contact by ID
func (h *CRMHandler) GetContact(c *gin.Context) {
	id := c.Param("id")

	var contact models.Contact
	db := database.GetDB()
	if err := db.First(&contact, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Contact not found")
		return
	}

	response.Success(c, contact, "Contact retrieved")
}

// UpdateContact updates a contact
func (h *CRMHandler) UpdateContact(c *gin.Context) {
	id := c.Param("id")

	var existing models.Contact
	db := database.GetDB()
	if err := db.First(&existing, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Contact not found")
		return
	}

	var contact models.Contact
	if err := c.ShouldBindJSON(&contact); err != nil {
		response.BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	contact.ID = id
	contact.TenantID = existing.TenantID
	contact.CreatedAt = existing.CreatedAt

	if err := db.Save(&contact).Error; err != nil {
		response.InternalError(c, "Failed to update contact: "+err.Error())
		return
	}

	response.Success(c, contact, "Contact updated")
}

// DeleteContact deletes a contact
func (h *CRMHandler) DeleteContact(c *gin.Context) {
	id := c.Param("id")

	db := database.GetDB()
	if err := db.Delete(&models.Contact{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete contact")
		return
	}

	response.Success(c, nil, "Contact deleted")
}
