package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

// === Credit Notes ===

func (h *SalesHandler) ListCreditNotes(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.CreditNote
	var total int64

	db := database.GetDB().Model(&models.CreditNote{}).Preload("Items")

	if search != "" {
		db = db.Where("credit_note_number ILIKE ?", "%"+search+"%")
	}

	db.Count(&total)
	result := db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	if result.Error != nil {
		response.Err(c, 500, result.Error.Error())
		return
	}

	response.SuccessList(c, items, page, limit, total, "Credit notes fetched")
}

func (h *SalesHandler) CreateCreditNote(c *gin.Context) {
	var body models.CreditNote
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	// Extract tenant_id from header
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create credit note: "+err.Error())
		return
	}

	response.Success(c, body, "Credit note created")
}

func (h *SalesHandler) GetCreditNote(c *gin.Context) {
	id := c.Param("id")

	var item models.CreditNote
	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Credit note not found")
		return
	}

	response.Success(c, item, "Credit note fetched")
}

func (h *SalesHandler) UpdateCreditNote(c *gin.Context) {
	id := c.Param("id")

	var existing models.CreditNote
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Credit note not found")
		return
	}

	var body models.CreditNote
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	body.ID = id
	body.TenantID = existing.TenantID
	body.CreatedAt = existing.CreatedAt

	// Delete old items and create new ones
	tx := database.GetDB().Begin()
	tx.Where("credit_note_id = ?", id).Delete(&models.CreditNoteItem{})

	if err := tx.Save(&body).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update credit note: "+err.Error())
		return
	}
	tx.Commit()

	response.Success(c, body, "Credit note updated")
}

// === Payment Records ===

func (h *SalesHandler) ListPayments(c *gin.Context) {
	invoiceID := c.Query("invoice_id")

	var items []models.PaymentRecord
	db := database.GetDB().Model(&models.PaymentRecord{})

	if invoiceID != "" {
		db = db.Where("invoice_id = ?", invoiceID)
	}

	result := db.Order("date desc").Find(&items)
	if result.Error != nil {
		response.Err(c, 500, result.Error.Error())
		return
	}

	response.Success(c, items, "Payments fetched")
}

func (h *SalesHandler) CreatePaymentRecord(c *gin.Context) {
	var body models.PaymentRecord
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	// Extract tenant_id from header
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	// Create payment record
	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create payment: "+err.Error())
		return
	}

	// Update invoice paid_amount
	var invoice models.Invoice
	if err := database.GetDB().First(&invoice, "id = ?", body.InvoiceID).Error; err == nil {
		invoice.PaidAmount += body.Amount
		if invoice.PaidAmount >= invoice.TotalAmount {
			invoice.Status = "Paid"
		} else if invoice.PaidAmount > 0 {
			invoice.Status = "Partial"
		}
		database.GetDB().Save(&invoice)
	}

	response.Success(c, body, "Payment recorded")
}
