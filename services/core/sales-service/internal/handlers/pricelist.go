package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ListPriceLists lists all price lists
func (h *SalesHandler) ListPriceLists(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.PriceList
	var total int64
	db := database.GetDB().Model(&models.PriceList{})

	if search != "" {
		db = db.Where("name ILIKE ?", "%"+search+"%")
	}
	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		db = db.Where("tenant_id = ?", tenantID)
	}

	db.Count(&total)
	db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	response.SuccessList(c, items, page, limit, total, "Price lists fetched")
}

// GetPriceList gets a price list
func (h *SalesHandler) GetPriceList(c *gin.Context) {
	id := c.Param("id")
	var item models.PriceList
	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Price list not found")
		return
	}
	response.Success(c, item, "Price list fetched")
}

// CreatePriceList creates a price list
func (h *SalesHandler) CreatePriceList(c *gin.Context) {
	var body models.PriceList
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	// Set tenant ID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create price list: "+err.Error())
		return
	}
	response.Success(c, body, "Price list created")
}

// UpdatePriceList updates a price list
func (h *SalesHandler) UpdatePriceList(c *gin.Context) {
	id := c.Param("id")
	var item models.PriceList
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Price list not found")
		return
	}

	var body models.PriceList
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = item.ID
	body.TenantID = item.TenantID
	body.CreatedAt = item.CreatedAt

	if err := database.GetDB().Save(&body).Error; err != nil {
		response.Err(c, 500, "Failed to update price list: "+err.Error())
		return
	}
	response.Success(c, body, "Price list updated")
}

// DeletePriceList deletes a price list
func (h *SalesHandler) DeletePriceList(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.PriceList{}, "id = ?", id).Error; err != nil {
		response.Err(c, 500, "Failed to delete price list")
		return
	}
	response.Success(c, nil, "Price list deleted")
}
