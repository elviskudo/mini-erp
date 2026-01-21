package handlers

import (
	"github.com/elviskudo/mini-erp/services/sales-service/internal/database"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"github.com/elviskudo/mini-erp/services/sales-service/internal/response"
	"github.com/gin-gonic/gin"
)

type SalesHandler struct{}

func NewSalesHandler() *SalesHandler {
	return &SalesHandler{}
}

// --- Dashboard ---

func (h *SalesHandler) GetStats(c *gin.Context) {
	// Mock stats for now or query DB
	response.Success(c, gin.H{
		"revenue_monthly": 150000000,
		"active_orders":   25,
		"conversion_rate": 15.5,
		"pipeline_value":  500000000,
	}, "Dashboard stats retrieved")
}

// --- Quotations ---

func (h *SalesHandler) ListQuotations(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.Quotation
	var total int64

	db := database.GetDB().Model(&models.Quotation{}).Preload("Items")

	if search != "" {
		db = db.Where("quotation_number ILIKE ?", "%"+search+"%")
	}

	db.Count(&total)
	result := db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	if result.Error != nil {
		response.Err(c, 500, "Failed to fetch quotations")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Quotations retrieved")
}

func (h *SalesHandler) CreateQuotation(c *gin.Context) {
	var body models.Quotation
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
		response.Err(c, 500, "Failed to create quotation: "+err.Error())
		return
	}

	response.Success(c, body, "Quotation created")
}

func (h *SalesHandler) GetQuotation(c *gin.Context) {
	id := c.Param("id")
	var item models.Quotation

	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Quotation not found")
		return
	}

	response.Success(c, item, "Quotation detail")
}

func (h *SalesHandler) UpdateQuotation(c *gin.Context) {
	id := c.Param("id")
	var body models.Quotation
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body")
		return
	}

	var existing models.Quotation
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Quotation not found")
		return
	}

	// Update fields
	existing.QuotationNumber = body.QuotationNumber
	existing.CustomerID = body.CustomerID
	existing.Date = body.Date
	existing.ValidUntil = body.ValidUntil
	existing.Status = body.Status
	existing.Subtotal = body.Subtotal
	existing.TaxAmount = body.TaxAmount
	existing.DiscountAmount = body.DiscountAmount
	existing.TotalAmount = body.TotalAmount
	existing.Notes = body.Notes
	existing.TermsConditions = body.TermsConditions

	// Transaction for items update
	tx := database.GetDB().Begin()

	// Delete existing items
	if err := tx.Where("quotation_id = ?", id).Delete(&models.QuotationItem{}).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update quotation items")
		return
	}

	// Re-add items
	if len(body.Items) > 0 {
		for i := range body.Items {
			body.Items[i].QuotationID = id
			// Ensure ID is generated or empty
			body.Items[i].ID = ""
		}
		if err := tx.Create(&body.Items).Error; err != nil {
			tx.Rollback()
			response.Err(c, 500, "Failed to save new items: "+err.Error())
			return
		}
	}

	if err := tx.Save(&existing).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update quotation")
		return
	}

	tx.Commit()
	response.Success(c, existing, "Quotation updated")
}

func (h *SalesHandler) ConvertQuotation(c *gin.Context) {
	id := c.Param("id")
	// Logic to convert to Sales Order would go here
	// For now just update status
	if err := database.GetDB().Model(&models.Quotation{}).Where("id = ?", id).Update("status", "accepted").Error; err != nil {
		response.Err(c, 500, "Failed to convert quotation")
		return
	}
	response.Success(c, nil, "Quotation converted to Order")
}

// --- Orders ---

func (h *SalesHandler) ListOrders(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.SalesOrder
	var total int64

	db := database.GetDB().Model(&models.SalesOrder{}).Preload("Items")

	if search != "" {
		db = db.Where("order_number ILIKE ?", "%"+search+"%")
	}

	db.Count(&total)
	result := db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	if result.Error != nil {
		response.Err(c, 500, "Failed to fetch orders")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Orders retrieved")
}

func (h *SalesHandler) CreateOrder(c *gin.Context) {
	var body models.SalesOrder
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body: "+err.Error())
		return
	}

	// Extract tenant_id from header (like manufacturing does)
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID != "" {
		body.TenantID = tenantID
	}

	// Set a default tenant if not provided (for testing)
	if body.TenantID == "" {
		body.TenantID = "00000000-0000-0000-0000-000000000000"
	}

	if err := database.GetDB().Create(&body).Error; err != nil {
		response.Err(c, 500, "Failed to create order: "+err.Error())
		return
	}

	response.Success(c, body, "Order created")
}

func (h *SalesHandler) GetOrder(c *gin.Context) {
	id := c.Param("id")
	var item models.SalesOrder

	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Order not found")
		return
	}

	response.Success(c, item, "Order detail")
}

// Rename UpdateOrderStatus to UpdateOrder to be generic, or add new handler?
// Assuming route is PUT /sales/orders/:id -> UpdateOrder
func (h *SalesHandler) UpdateOrder(c *gin.Context) {
	id := c.Param("id")
	var body models.SalesOrder
	if err := c.ShouldBindJSON(&body); err != nil {
		response.Err(c, 400, "Invalid request body")
		return
	}

	var existing models.SalesOrder
	if err := database.GetDB().First(&existing, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Order not found")
		return
	}

	existing.OrderNumber = body.OrderNumber
	existing.CustomerID = body.CustomerID
	existing.Date = body.Date
	existing.Status = body.Status
	existing.Subtotal = body.Subtotal
	existing.TaxAmount = body.TaxAmount
	existing.DiscountAmount = body.DiscountAmount
	existing.TotalAmount = body.TotalAmount
	existing.PaymentStatus = body.PaymentStatus
	existing.Notes = body.Notes

	tx := database.GetDB().Begin()

	// Delete existing items
	if err := tx.Where("sales_order_id = ?", id).Delete(&models.SalesOrderItem{}).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update order items")
		return
	}

	// Re-add items
	if len(body.Items) > 0 {
		for i := range body.Items {
			body.Items[i].SalesOrderID = id
			body.Items[i].ID = ""
		}
		if err := tx.Create(&body.Items).Error; err != nil {
			tx.Rollback()
			response.Err(c, 500, "Failed to save new items")
			return
		}
	}

	if err := tx.Save(&existing).Error; err != nil {
		tx.Rollback()
		response.Err(c, 500, "Failed to update order")
		return
	}

	tx.Commit()
	response.Success(c, existing, "Order updated")
}

func (h *SalesHandler) GenerateInvoice(c *gin.Context) {
	response.Success(c, nil, "Invoice generated")
}

// --- Invoices ---

func (h *SalesHandler) ListInvoices(c *gin.Context) {
	page, limit, offset := response.GetPagination(c)
	search := c.Query("search")

	var items []models.Invoice
	var total int64

	db := database.GetDB().Model(&models.Invoice{}).Preload("Items")

	if search != "" {
		db = db.Where("invoice_number ILIKE ?", "%"+search+"%")
	}

	db.Count(&total)
	result := db.Limit(limit).Offset(offset).Order("created_at desc").Find(&items)

	if result.Error != nil {
		response.Err(c, 500, "Failed to fetch invoices")
		return
	}

	response.SuccessList(c, items, page, limit, total, "Invoices retrieved")
}

func (h *SalesHandler) CreateInvoice(c *gin.Context) {
	var body models.Invoice
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
		response.Err(c, 500, "Failed to create invoice: "+err.Error())
		return
	}

	response.Success(c, body, "Invoice created")
}

func (h *SalesHandler) GetInvoice(c *gin.Context) {
	id := c.Param("id")
	var item models.Invoice

	if err := database.GetDB().Preload("Items").First(&item, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Invoice not found")
		return
	}

	response.Success(c, item, "Invoice detail")
}

func (h *SalesHandler) RecordPayment(c *gin.Context) {
	id := c.Param("id")

	// Check invoice exists
	var invoice models.Invoice
	if err := database.GetDB().First(&invoice, "id = ?", id).Error; err != nil {
		response.Err(c, 404, "Invoice not found")
		return
	}

	// Update status to Paid (basic implementation)
	invoice.Status = "Paid"
	invoice.PaidAmount = invoice.TotalAmount

	if err := database.GetDB().Save(&invoice).Error; err != nil {
		response.Err(c, 500, "Failed to record payment")
		return
	}

	response.Success(c, invoice, "Payment recorded")
}
