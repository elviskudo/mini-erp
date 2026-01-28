package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ListDiscountRules lists all discount rules
func (h *SalesHandler) ListDiscountRules(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)

	var items []models.DiscountRule
	var total int64
	db := database.GetDB().Model(&models.DiscountRule{})

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		db = db.Where("tenant_id = ?", tenantID)
	}

	db.Count(&total)
	db.Limit(limit).Offset(offset).Order("priority desc, created_at desc").Find(&items)

	response.SuccessList(c, items, page, limit, total, "Discount rules fetched")
}

// GetDiscountRule gets a discount rule
func (h *SalesHandler) GetDiscountRule(c *gin.Context) {
	id := c.Param("id")
	var item models.DiscountRule
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Discount rule not found")
		return
	}
	response.Success(c, item, "Discount rule fetched")
}

// CreateDiscountRule creates a discount rule
func (h *SalesHandler) CreateDiscountRule(c *gin.Context) {
	var body models.DiscountRule
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

	// Handle empty UUID strings
	if body.ProductID != nil && *body.ProductID == "" {
		body.ProductID = nil
	}
	if body.CategoryID != nil && *body.CategoryID == "" {
		body.CategoryID = nil
	}
	if body.CustomerID != nil && *body.CustomerID == "" {
		body.CustomerID = nil
	}
	if body.PromoCode != nil && *body.PromoCode == "" {
		body.PromoCode = nil
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create discount rule: "+err.Error())
		return
	}
	response.Success(c, body, "Discount rule created")
}

// UpdateDiscountRule updates a discount rule
func (h *SalesHandler) UpdateDiscountRule(c *gin.Context) {
	id := c.Param("id")
	var item models.DiscountRule
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Discount rule not found")
		return
	}

	var body models.DiscountRule
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = item.ID
	body.TenantID = item.TenantID
	body.CreatedAt = item.CreatedAt

	// Handle empty UUID strings
	if body.ProductID != nil && *body.ProductID == "" {
		body.ProductID = nil
	}
	if body.CategoryID != nil && *body.CategoryID == "" {
		body.CategoryID = nil
	}
	if body.CustomerID != nil && *body.CustomerID == "" {
		body.CustomerID = nil
	}
	if body.PromoCode != nil && *body.PromoCode == "" {
		body.PromoCode = nil
	}

	if err := database.GetDB().Save(&body).Error; err != nil {
		response.Err(c, 500, "Failed to update discount rule: "+err.Error())
		return
	}
	response.Success(c, body, "Discount rule updated")
}

// DeleteDiscountRule deletes a discount rule
func (h *SalesHandler) DeleteDiscountRule(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.DiscountRule{}, "id = ?", id).Error; err != nil {
		response.Err(c, 500, "Failed to delete discount rule")
		return
	}
	response.Success(c, nil, "Discount rule deleted")
}
