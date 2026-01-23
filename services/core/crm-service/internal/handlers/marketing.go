package handlers

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/database"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"github.com/elviskudo/mini-erp/services/crm-service/internal/response"
	"github.com/gin-gonic/gin"
)

// ========== CAMPAIGNS ==========

func (h *CRMHandler) ListCampaigns(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var campaigns []models.Campaign
	var total int64

	query := db.Model(&models.Campaign{})
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}
	if cType := c.Query("type"); cType != "" {
		query = query.Where("type = ?", cType)
	}

	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&campaigns).Error; err != nil {
		response.InternalError(c, "Failed to fetch campaigns")
		return
	}

	response.SuccessList(c, campaigns, page, limit, total, "Campaigns retrieved")
}

func (h *CRMHandler) CreateCampaign(c *gin.Context) {
	var campaign models.Campaign
	if err := c.ShouldBindJSON(&campaign); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		campaign.TenantID = tenantID
	}
	if campaign.TenantID == "" {
		campaign.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	db := database.GetDB()
	if err := db.Create(&campaign).Error; err != nil {
		response.InternalError(c, "Failed to create campaign: "+err.Error())
		return
	}

	response.Success(c, campaign, "Campaign created")
}

func (h *CRMHandler) GetCampaign(c *gin.Context) {
	id := c.Param("id")
	var campaign models.Campaign
	if err := database.GetDB().First(&campaign, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Campaign not found")
		return
	}
	response.Success(c, campaign, "Campaign retrieved")
}

func (h *CRMHandler) UpdateCampaign(c *gin.Context) {
	id := c.Param("id")
	var existing models.Campaign
	db := database.GetDB()
	if err := db.First(&existing, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Campaign not found")
		return
	}

	var campaign models.Campaign
	if err := c.ShouldBindJSON(&campaign); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	campaign.ID = id
	campaign.TenantID = existing.TenantID
	campaign.CreatedAt = existing.CreatedAt

	if err := db.Save(&campaign).Error; err != nil {
		response.InternalError(c, "Failed to update campaign: "+err.Error())
		return
	}

	response.Success(c, campaign, "Campaign updated")
}

func (h *CRMHandler) DeleteCampaign(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.Campaign{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete campaign")
		return
	}
	response.Success(c, nil, "Campaign deleted")
}

// ========== WEB FORMS ==========

func (h *CRMHandler) ListWebForms(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var forms []models.WebForm
	var total int64

	query := db.Model(&models.WebForm{})
	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&forms).Error; err != nil {
		response.InternalError(c, "Failed to fetch web forms")
		return
	}

	response.SuccessList(c, forms, page, limit, total, "Web forms retrieved")
}

func (h *CRMHandler) CreateWebForm(c *gin.Context) {
	var form models.WebForm
	if err := c.ShouldBindJSON(&form); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		form.TenantID = tenantID
	}
	if form.TenantID == "" {
		form.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	// Generate slug if not provided
	if form.Slug == "" {
		form.Slug = generateSlug(form.Name)
	}

	// Handle empty strings for UUID fields - convert to nil
	if form.CampaignID != nil && *form.CampaignID == "" {
		form.CampaignID = nil
	}
	if form.RedirectURL != nil && *form.RedirectURL == "" {
		form.RedirectURL = nil
	}
	if form.CreatedBy != nil && *form.CreatedBy == "" {
		form.CreatedBy = nil
	}

	db := database.GetDB()
	if err := db.Create(&form).Error; err != nil {
		response.InternalError(c, "Failed to create web form: "+err.Error())
		return
	}

	response.Success(c, form, "Web form created")
}

func (h *CRMHandler) GetWebForm(c *gin.Context) {
	id := c.Param("id")
	var form models.WebForm
	if err := database.GetDB().First(&form, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Web form not found")
		return
	}
	response.Success(c, form, "Web form retrieved")
}

func (h *CRMHandler) UpdateWebForm(c *gin.Context) {
	id := c.Param("id")
	var existing models.WebForm
	db := database.GetDB()
	if err := db.First(&existing, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Web form not found")
		return
	}

	var form models.WebForm
	if err := c.ShouldBindJSON(&form); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	form.ID = id
	form.TenantID = existing.TenantID
	form.CreatedAt = existing.CreatedAt
	form.Submissions = existing.Submissions

	// Handle empty strings for UUID fields - convert to nil
	if form.CampaignID != nil && *form.CampaignID == "" {
		form.CampaignID = nil
	}
	if form.RedirectURL != nil && *form.RedirectURL == "" {
		form.RedirectURL = nil
	}
	if form.CreatedBy != nil && *form.CreatedBy == "" {
		form.CreatedBy = nil
	}

	if err := db.Save(&form).Error; err != nil {
		response.InternalError(c, "Failed to update web form: "+err.Error())
		return
	}

	response.Success(c, form, "Web form updated")
}

func (h *CRMHandler) DeleteWebForm(c *gin.Context) {
	id := c.Param("id")
	if err := database.GetDB().Delete(&models.WebForm{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete web form")
		return
	}
	response.Success(c, nil, "Web form deleted")
}

// Public endpoint - submit form
func (h *CRMHandler) SubmitWebForm(c *gin.Context) {
	slug := c.Param("slug")

	var form models.WebForm
	db := database.GetDB()
	if err := db.First(&form, "slug = ? AND status = ?", slug, "active").Error; err != nil {
		response.NotFound(c, "Form not found or inactive")
		return
	}

	var data map[string]interface{}
	if err := c.ShouldBindJSON(&data); err != nil {
		response.BadRequest(c, "Invalid submission data")
		return
	}

	// Create submission
	submission := models.WebFormSubmission{
		FormID: form.ID,
		Data:   fmt.Sprintf("%v", data), // Convert to JSON string
	}

	ipAddr := c.ClientIP()
	userAgent := c.GetHeader("User-Agent")
	submission.IPAddress = &ipAddr
	submission.UserAgent = &userAgent

	if err := db.Create(&submission).Error; err != nil {
		response.InternalError(c, "Failed to save submission")
		return
	}

	// Update submission count
	db.Model(&form).Update("submissions", form.Submissions+1)

	response.Success(c, gin.H{
		"message":      form.SuccessMessage,
		"redirect_url": form.RedirectURL,
	}, "Form submitted successfully")
}

func (h *CRMHandler) ListWebFormSubmissions(c *gin.Context) {
	formID := c.Param("id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var submissions []models.WebFormSubmission
	var total int64

	db := database.GetDB()
	query := db.Model(&models.WebFormSubmission{}).Where("form_id = ?", formID)
	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&submissions).Error; err != nil {
		response.InternalError(c, "Failed to fetch submissions")
		return
	}

	response.SuccessList(c, submissions, page, limit, total, "Submissions retrieved")
}

func generateSlug(name string) string {
	slug := strings.ToLower(name)
	slug = strings.ReplaceAll(slug, " ", "-")
	slug = strings.ReplaceAll(slug, "_", "-")
	return slug + "-" + fmt.Sprintf("%d", time.Now().UnixNano()%10000)
}
