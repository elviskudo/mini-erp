package handlers

import (
	"net/http"

	"github.com/elviskudo/mini-erp/services/auth-service/internal/database"
	"github.com/elviskudo/mini-erp/services/auth-service/internal/models"
	"github.com/gin-gonic/gin"
)

// GetTenant returns tenant details by ID
// GET /tenants/:id
func (h *AuthHandler) GetTenant(c *gin.Context) {
	id := c.Param("id")

	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not connected"})
		return
	}

	var tenant models.Tenant
	if result := db.First(&tenant, "id = ?", id); result.Error != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Tenant not found"})
		return
	}

	c.JSON(http.StatusOK, tenant)
}

// GetTenants returns all tenants (admin only)
// GET /tenants
func (h *AuthHandler) GetTenants(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not connected"})
		return
	}

	var tenants []models.Tenant
	if result := db.Order("name").Find(&tenants); result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch tenants"})
		return
	}

	c.JSON(http.StatusOK, tenants)
}
