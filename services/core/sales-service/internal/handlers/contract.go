package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ListContracts lists all contracts
func (h *SalesHandler) ListContracts(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.SalesContract
	var total int64
	db := database.GetDB().Model(&models.SalesContract{})

	if search != "" {
		db = db.Where("contract_number ILIKE ?", "%"+search+"%")
	}
	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		db = db.Where("tenant_id = ?", tenantID)
	}

	db.Count(&total)
	db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	response.SuccessList(c, items, page, limit, total, "Contracts fetched")
}

// GetContract gets a contract
func (h *SalesHandler) GetContract(c *gin.Context) {
	id := c.Param("id")
	var item models.SalesContract
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Contract not found")
		return
	}
	response.Success(c, item, "Contract fetched")
}

// CreateContract creates a contract
func (h *SalesHandler) CreateContract(c *gin.Context) {
	var body models.SalesContract
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create contract: "+err.Error())
		return
	}
	response.Success(c, body, "Contract created")
}

// UpdateContract updates a contract
func (h *SalesHandler) UpdateContract(c *gin.Context) {
	id := c.Param("id")
	var item models.SalesContract
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Contract not found")
		return
	}

	var body models.SalesContract
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = item.ID
	body.TenantID = item.TenantID
	body.CreatedAt = item.CreatedAt

	if err := database.GetDB().Save(&body).Error; err != nil {
		response.Err(c, 500, "Failed to update contract: "+err.Error())
		return
	}
	response.Success(c, body, "Contract updated")
}

// DeleteContract deletes a contract
func (h *SalesHandler) DeleteContract(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.SalesContract{}, "id = ?", id).Error; err != nil {
		response.Err(c, 500, "Failed to delete contract")
		return
	}
	response.Success(c, nil, "Contract deleted")
}
