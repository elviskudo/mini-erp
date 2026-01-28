package handlers

import (
	"net/http"
	"time"

	"github.com/elviskudo/mini-erp/services/pos-service/internal/database"
	"github.com/elviskudo/mini-erp/services/pos-service/internal/models"
	"github.com/gin-gonic/gin"
)

type PromoHandler struct{}

func NewPromoHandler() *PromoHandler {
	return &PromoHandler{}
}

// ListPromos lists available promos for cashier
func (h *PromoHandler) ListPromos(c *gin.Context) {
	var promos []models.Promo
	db := database.GetDB()

	query := db.Where("is_active = ?", true).
		Where("start_date <= ?", time.Now()).
		Where("end_date >= ?", time.Now())

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.Find(&promos).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch promos"})
		return
	}

	c.JSON(http.StatusOK, promos)
}

// GetPromoByCode looks up a promo by code (for scanning/typing)
func (h *PromoHandler) GetPromoByCode(c *gin.Context) {
	code := c.Param("code")
	var promo models.Promo
	db := database.GetDB()

	query := db.Where("code = ?", code).
		Where("is_active = ?", true)

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.First(&promo).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Invalid or expired promo code"})
		return
	}

	// Additional validation
	now := time.Now()
	if promo.StartDate != nil && now.Before(*promo.StartDate) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Promo has not started yet"})
		return
	}
	if promo.EndDate != nil && now.After(*promo.EndDate) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Promo has expired"})
		return
	}
	if promo.UsageLimit != nil && *promo.UsageLimit > 0 && *promo.UsageCount >= *promo.UsageLimit {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Promo usage limit reached"})
		return
	}

	c.JSON(http.StatusOK, promo)
}

// ApplyPromo applies a promo to a cart (mock logic for now)
func (h *PromoHandler) ApplyPromo(c *gin.Context) {
	// This would calculate the discount based on cart items
	c.JSON(http.StatusOK, gin.H{"message": "Promo applied successfully"})
}
