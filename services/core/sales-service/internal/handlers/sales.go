package handlers

import (
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
	// Placeholder
	var items []models.Quotation
	// database.GetDB().Find(&items)
	response.SuccessList(c, items, 1, 10, 0, "Quotations retrieved")
}

func (h *SalesHandler) CreateQuotation(c *gin.Context) {
	response.Success(c, nil, "Quotation created")
}

func (h *SalesHandler) GetQuotation(c *gin.Context) {
	response.Success(c, nil, "Quotation detail")
}

func (h *SalesHandler) UpdateQuotation(c *gin.Context) {
	response.Success(c, nil, "Quotation updated")
}

func (h *SalesHandler) ConvertQuotation(c *gin.Context) {
	response.Success(c, nil, "Quotation converted to Order")
}

// --- Orders ---

func (h *SalesHandler) ListOrders(c *gin.Context) {
	var items []models.SalesOrder
	response.SuccessList(c, items, 1, 10, 0, "Orders retrieved")
}

func (h *SalesHandler) CreateOrder(c *gin.Context) {
	response.Success(c, nil, "Order created")
}

func (h *SalesHandler) GetOrder(c *gin.Context) {
	response.Success(c, nil, "Order detail")
}

func (h *SalesHandler) UpdateOrderStatus(c *gin.Context) {
	response.Success(c, nil, "Order status updated")
}

func (h *SalesHandler) GenerateInvoice(c *gin.Context) {
	response.Success(c, nil, "Invoice generated")
}

// --- Invoices ---

func (h *SalesHandler) ListInvoices(c *gin.Context) {
	var items []models.Invoice
	response.SuccessList(c, items, 1, 10, 0, "Invoices retrieved")
}

func (h *SalesHandler) CreateInvoice(c *gin.Context) {
	response.Success(c, nil, "Invoice created")
}

func (h *SalesHandler) GetInvoice(c *gin.Context) {
	response.Success(c, nil, "Invoice detail")
}

func (h *SalesHandler) RecordPayment(c *gin.Context) {
	response.Success(c, nil, "Payment recorded")
}
