package handlers

import (
	"strconv"
	"strings"
	"time"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ========== PROMOS ==========

// ListPromos lists all promos
func (h *CRMHandler) ListPromos(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Promos retrieved", []gin.H{
			{"id": "promo-1", "code": "PROMO10", "name": "10% Off", "promo_type": "PERCENTAGE", "value": 10},
		}, page, limit, 1)
		return
	}

	var promos []models.Promo
	var total int64
	tenantID := c.GetHeader("X-Tenant-ID")

	query := db.Model(&models.Promo{})
	if tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}
	query.Count(&total)
	query.Offset(offset).Limit(limit).Order("created_at DESC").Find(&promos)

	response.SuccessWithPagination(c, "Promos retrieved successfully", promos, page, limit, total)
}

// GetPromo gets a promo by ID
func (h *CRMHandler) GetPromo(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, gin.H{"id": id, "code": "PROMO10", "name": "Sample Promo"}, "Promo retrieved")
		return
	}

	var promo models.Promo
	if err := db.First(&promo, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Promo not found")
		return
	}
	response.Success(c, promo, "Promo retrieved successfully")
}

// CreatePromo creates a promo
func (h *CRMHandler) CreatePromo(c *gin.Context) {
	db := database.GetDB()

	var req models.Promo
	if err := c.ShouldBindJSON(&req); err != nil {
		// Log the error to stdout for docker logs visibility
		println("❌ CreatePromo Bind Error:", err.Error())
		response.BadRequest(c, "Invalid request body: "+err.Error())
		return
	}

	if db == nil {
		response.Created(c, "Promo created successfully", gin.H{"id": "new-promo-id", "code": req.Code})
		return
	}

	// Set tenant ID
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		req.TenantID = &tenantID
	}

	// Convert PromoType to uppercase
	if req.PromoType != nil && *req.PromoType != "" {
		upper := strings.ToUpper(*req.PromoType)
		req.PromoType = &upper
	}

	// Handle empty UUID strings
	if req.CreatedBy != nil && *req.CreatedBy == "" {
		req.CreatedBy = nil
	}

	req.CreatedAt = time.Now()
	req.UpdatedAt = time.Now()

	if err := db.Create(&req).Error; err != nil {
		response.InternalError(c, "Failed to create promo: "+err.Error())
		return
	}
	response.Created(c, "Promo created successfully", req)
}

// UpdatePromo updates a promo
func (h *CRMHandler) UpdatePromo(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Updated(c, "Promo updated successfully", gin.H{"id": id})
		return
	}

	var promo models.Promo
	if err := db.First(&promo, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Promo not found")
		return
	}

	var req models.Promo
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	promo.Code = req.Code
	promo.Name = req.Name
	promo.Description = req.Description
	promo.Value = req.Value
	promo.MinOrder = req.MinOrder
	promo.MaxDiscount = req.MaxDiscount
	promo.StartDate = req.StartDate
	promo.EndDate = req.EndDate
	promo.IsActive = req.IsActive
	promo.UsageLimit = req.UsageLimit
	promo.PerCustomerLimit = req.PerCustomerLimit

	// Convert PromoType to uppercase
	if req.PromoType != nil && *req.PromoType != "" {
		upper := strings.ToUpper(*req.PromoType)
		promo.PromoType = &upper
	}

	promo.UpdatedAt = time.Now()

	if err := db.Save(&promo).Error; err != nil {
		response.InternalError(c, "Failed to update promo: "+err.Error())
		return
	}
	response.Updated(c, "Promo updated successfully", promo)
}

// DeletePromo deletes a promo
func (h *CRMHandler) DeletePromo(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, nil, "Promo deleted successfully")
		return
	}

	if err := db.Delete(&models.Promo{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete promo")
		return
	}
	response.Success(c, nil, "Promo deleted successfully")
}

// PublishPromo synchronizes a promo to the POS service/tables
func (h *CRMHandler) PublishPromo(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	var promo models.Promo
	if err := db.First(&promo, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Promo not found")
		return
	}

	if promo.IsActive == nil || !*promo.IsActive {
		response.BadRequest(c, "Cannot publish inactive promo")
		return
	}

	// Direct sync to POS Promos table (Shared Database Pattern)
	// We map crm_promos -> pos_promos
	posPromo := map[string]interface{}{
		"id":           promo.ID,
		"tenant_id":    promo.TenantID,
		"code":         promo.Code,
		"name":         promo.Name,
		"type":         promo.PromoType, // Column mapping: promo_type -> type
		"value":        promo.Value,
		"min_purchase": promo.MinOrder, // Column mapping: min_order -> min_purchase
		"start_date":   promo.StartDate,
		"end_date":     promo.EndDate,
		"is_active":    promo.IsActive,
		"created_at":   promo.CreatedAt,
		// "updated_at":      time.Now(), // DB handles this or we set it
	}

	// Use raw SQL or map to a struct. Using map with Table() is cleaner.
	// NOTE: We assume "pos_promos" table exists in the same DB.
	// If it doesn't exist yet (e.g. running in independent DBs), this will fail.
	// Given docker-compose uses single Postgres for all services (anti-pattern but practical here), this works.

	// Check if exists in pos_promos
	var count int64
	db.Table("pos_promos").Where("id = ?", promo.ID).Count(&count)

	var err error
	if count > 0 {
		err = db.Table("pos_promos").Where("id = ?", promo.ID).Updates(posPromo).Error
	} else {
		err = db.Table("pos_promos").Create(posPromo).Error
	}

	if err != nil {
		response.InternalError(c, "Failed to publish promo to POS: "+err.Error())
		return
	}

	response.Success(c, nil, "Promo published to POS successfully")
}

// Email Broadcasts have been moved to internal/handlers/broadcast.go
