package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ========== PRICE LISTS ==========

func (h *SalesHandler) ListPriceLists(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	var items []models.PriceList
	var total int64

	db := database.GetDB().Model(&models.PriceList{})
	db.Count(&total)
	if err := db.Preload("Items").Limit(limit).Offset(offset).Order("name ASC").Find(&items).Error; err != nil {
		response.Err(c, 500, err.Error())
		return
	}

	response.SuccessList(c, items, page, limit, total, "Price lists fetched")
}

func (h *SalesHandler) CreatePriceList(c *gin.Context) {
	var body models.PriceList
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create: "+err.Error())
		return
	}

	response.Success(c, body, "Price list created")
}

func (h *SalesHandler) GetPriceList(c *gin.Context) {
	id := c.Param("id")
	var item models.PriceList
	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}
	response.Success(c, item, "Price list fetched")
}

func (h *SalesHandler) UpdatePriceList(c *gin.Context) {
	id := c.Param("id")
	var existing models.PriceList
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}

	var body models.PriceList
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = id
	body.TenantID = existing.TenantID
	body.CreatedAt = existing.CreatedAt

	tx := database.GetDB().Begin()
	tx.Where("price_list_id = ?", id).Delete(&models.PriceListItem{})
	if err := tx.Save(&body).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update: "+err.Error())
		return
	}
	tx.Commit()

	response.Success(c, body, "Price list updated")
}

// ========== DISCOUNT RULES ==========

func (h *SalesHandler) ListDiscountRules(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	var items []models.DiscountRule
	var total int64

	db := database.GetDB().Model(&models.DiscountRule{})
	db.Count(&total)
	if err := db.Limit(limit).Offset(offset).Order("priority DESC, name ASC").Find(&items).Error; err != nil {
		response.Err(c, 500, err.Error())
		return
	}

	response.SuccessList(c, items, page, limit, total, "Discount rules fetched")
}

func (h *SalesHandler) CreateDiscountRule(c *gin.Context) {
	var body models.DiscountRule
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create: "+err.Error())
		return
	}

	response.Success(c, body, "Discount rule created")
}

func (h *SalesHandler) GetDiscountRule(c *gin.Context) {
	id := c.Param("id")
	var item models.DiscountRule
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}
	response.Success(c, item, "Discount rule fetched")
}

func (h *SalesHandler) UpdateDiscountRule(c *gin.Context) {
	id := c.Param("id")
	var existing models.DiscountRule
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}

	var body models.DiscountRule
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = id
	body.TenantID = existing.TenantID
	body.CreatedAt = existing.CreatedAt

	if err := database.GetDB().Save(&body).Error; err != nil {
		response.Err(c, 500, "Failed to update: "+err.Error())
		return
	}

	response.Success(c, body, "Discount rule updated")
}

// ========== SALES CONTRACTS ==========

func (h *SalesHandler) ListContracts(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	var items []models.SalesContract
	var total int64

	db := database.GetDB().Model(&models.SalesContract{})
	db.Count(&total)
	if err := db.Limit(limit).Offset(offset).Order("created_at DESC").Find(&items).Error; err != nil {
		response.Err(c, 500, err.Error())
		return
	}

	response.SuccessList(c, items, page, limit, total, "Contracts fetched")
}

func (h *SalesHandler) CreateContract(c *gin.Context) {
	var body models.SalesContract
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create: "+err.Error())
		return
	}

	response.Success(c, body, "Contract created")
}

func (h *SalesHandler) GetContract(c *gin.Context) {
	id := c.Param("id")
	var item models.SalesContract
	if err := database.GetDB().First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}
	response.Success(c, item, "Contract fetched")
}

func (h *SalesHandler) UpdateContract(c *gin.Context) {
	id := c.Param("id")
	var existing models.SalesContract
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}

	var body models.SalesContract
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	body.ID = id
	body.TenantID = existing.TenantID
	body.CreatedAt = existing.CreatedAt

	if err := database.GetDB().Save(&body).Error; err != nil {
		response.Err(c, 500, "Failed to update: "+err.Error())
		return
	}

	response.Success(c, body, "Contract updated")
}

// ========== COMMISSIONS ==========

func (h *SalesHandler) ListCommissions(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	var items []models.Commission
	var total int64

	db := database.GetDB().Model(&models.Commission{})

	if status := c.Query("status"); status != "" {
		db = db.Where("status = ?", status)
	}
	if salespersonID := c.Query("salesperson_id"); salespersonID != "" {
		db = db.Where("salesperson_id = ?", salespersonID)
	}

	db.Count(&total)
	if err := db.Limit(limit).Offset(offset).Order("created_at DESC").Find(&items).Error; err != nil {
		response.Err(c, 500, err.Error())
		return
	}

	response.SuccessList(c, items, page, limit, total, "Commissions fetched")
}

func (h *SalesHandler) CreateCommission(c *gin.Context) {
	var body models.Commission
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	// Calculate commission amount if not provided
	if body.Amount == 0 && body.OrderAmount > 0 && body.Rate > 0 {
		body.Amount = body.OrderAmount * body.Rate / 100
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create: "+err.Error())
		return
	}

	response.Success(c, body, "Commission created")
}

func (h *SalesHandler) UpdateCommissionStatus(c *gin.Context) {
	id := c.Param("id")
	var existing models.Commission
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Not found")
		return
	}

	var body struct {
		Status string `json:"status"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request")
		return
	}

	existing.Status = body.Status
	if err := database.GetDB().Save(&existing).Error; err != nil {
		response.Err(c, 500, "Failed to update: "+err.Error())
		return
	}

	response.Success(c, existing, "Commission status updated")
}
