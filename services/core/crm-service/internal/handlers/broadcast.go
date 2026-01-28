package handlers

import (
	"net/http"
	"time"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/gin-gonic/gin"
)

// ListEmailBroadcasts returns all email broadcasts
func (h *CRMHandler) ListEmailBroadcasts(c *gin.Context) {
	var broadcasts []models.EmailBroadcast
	db := database.GetDB()

	query := db
	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.Find(&broadcasts).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch broadcasts"})
		return
	}

	c.JSON(http.StatusOK, broadcasts)
}

// CreateEmailBroadcast creates a new broadcast
func (h *CRMHandler) CreateEmailBroadcast(c *gin.Context) {
	var req models.EmailBroadcast
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Set tenant ID from header
	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		req.TenantID = tenantID
	}
	if req.TenantID == "" {
		req.TenantID = "00000000-0000-0000-0000-000000000000" // Default/Fallback
	}

	req.CreatedAt = time.Now()
	req.UpdatedAt = time.Now()

	if err := database.GetDB().Create(&req).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create broadcast"})
		return
	}

	c.JSON(http.StatusCreated, req)
}

// GetEmailBroadcast returns a single broadcast
func (h *CRMHandler) GetEmailBroadcast(c *gin.Context) {
	id := c.Param("id")
	var broadcast models.EmailBroadcast

	db := database.GetDB()
	query := db.Where("id = ?", id)

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.First(&broadcast).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Broadcast not found"})
		return
	}

	c.JSON(http.StatusOK, broadcast)
}

// UpdateEmailBroadcast updates a broadcast
func (h *CRMHandler) UpdateEmailBroadcast(c *gin.Context) {
	id := c.Param("id")
	var broadcast models.EmailBroadcast

	db := database.GetDB()
	query := db.Where("id = ?", id)

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	if err := query.First(&broadcast).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Broadcast not found"})
		return
	}

	var req models.EmailBroadcast
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Prevent updating ID and TenantID
	req.ID = broadcast.ID
	req.TenantID = broadcast.TenantID
	req.CreatedAt = broadcast.CreatedAt
	req.UpdatedAt = time.Now()

	if err := db.Save(&req).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update broadcast"})
		return
	}

	c.JSON(http.StatusOK, req)
}

// DeleteEmailBroadcast deletes a broadcast
func (h *CRMHandler) DeleteEmailBroadcast(c *gin.Context) {
	id := c.Param("id")

	db := database.GetDB()
	query := db.Where("id = ?", id)

	if tenantID := c.GetHeader("X-Tenant-ID"); tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}

	result := query.Delete(&models.EmailBroadcast{})
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete broadcast"})
		return
	}
	if result.RowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Broadcast not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Broadcast deleted"})
}

// SendEmailBroadcast triggers the sending of a broadcast
// Logic placeholder: this would likely push a job to a queue
func (h *CRMHandler) SendEmailBroadcast(c *gin.Context) {
	// This could be an additional action, but standard CRUD covers the basics.
	// For now, if the user updates status to 'sending', it might trigger logic elsewhere.
	c.JSON(http.StatusNotImplemented, gin.H{"message": "Sending logic not yet implemented"})
}
