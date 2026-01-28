package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// Price Lists, Discount Rules, and Contracts have been moved to their own handler files.

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

	// Handle empty UUID strings
	if body.OrderID != nil && *body.OrderID == "" {
		body.OrderID = nil
	}
	if body.InvoiceID != nil && *body.InvoiceID == "" {
		body.InvoiceID = nil
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
