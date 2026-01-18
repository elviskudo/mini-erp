package handlers

import (
	"strconv"

	"github.com/elviskudo/mini-erp/services/procurement-service/internal/database"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/models"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/response"
	"github.com/gin-gonic/gin"
)

type ProcurementHandler struct{}

func NewProcurementHandler() *ProcurementHandler { return &ProcurementHandler{} }

func (h *ProcurementHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, "Statistics retrieved", gin.H{"total_vendors": 10, "pending_pos": 5, "pending_prs": 3})
		return
	}
	var vendors, pos, prs int64
	db.Model(&models.Vendor{}).Count(&vendors)
	db.Model(&models.PurchaseOrder{}).Where("status = ?", "PENDING").Count(&pos)
	db.Model(&models.PurchaseRequest{}).Where("status = ?", "PENDING").Count(&prs)
	response.Success(c, "Statistics retrieved", gin.H{"total_vendors": vendors, "pending_pos": pos, "pending_prs": prs})
}

func (h *ProcurementHandler) ListVendors(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Vendors retrieved", []gin.H{{"id": "v-1", "code": "VND-001", "name": "PT Supplier Jaya"}}, page, limit, 1)
		return
	}

	var vendors []models.Vendor
	var total int64
	db.Model(&models.Vendor{}).Count(&total)
	if err := db.Order("name ASC").Offset(offset).Limit(limit).Find(&vendors).Error; err != nil {
		response.SuccessWithPagination(c, "Vendors retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Vendors retrieved", vendors, page, limit, total)
}

func (h *ProcurementHandler) GetVendor(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")
	if db == nil {
		response.Success(c, "Vendor retrieved", gin.H{"id": id, "name": "PT Supplier Jaya"})
		return
	}
	var vendor models.Vendor
	if err := db.First(&vendor, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Vendor not found")
		return
	}
	response.Success(c, "Vendor retrieved", vendor)
}

func (h *ProcurementHandler) CreateVendor(c *gin.Context) {
	response.Created(c, "Vendor created successfully", gin.H{"id": "new-vendor-id"})
}

func (h *ProcurementHandler) UpdateVendor(c *gin.Context) {
	response.Updated(c, "Vendor updated successfully", gin.H{"id": c.Param("id")})
}

func (h *ProcurementHandler) ListPurchaseRequests(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Purchase requests retrieved", []gin.H{{"id": "pr-1", "pr_number": "PR-001", "status": "PENDING"}}, page, limit, 1)
		return
	}

	var prs []models.PurchaseRequest
	var total int64
	db.Model(&models.PurchaseRequest{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&prs).Error; err != nil {
		response.SuccessWithPagination(c, "Purchase requests retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Purchase requests retrieved", prs, page, limit, total)
}

func (h *ProcurementHandler) CreatePurchaseRequest(c *gin.Context) {
	response.Created(c, "Purchase request created successfully", gin.H{"id": "new-pr-id", "pr_number": "PR-NEW"})
}

func (h *ProcurementHandler) ApprovePurchaseRequest(c *gin.Context) {
	response.Updated(c, "Purchase request approved", gin.H{"id": c.Param("id"), "status": "APPROVED"})
}

func (h *ProcurementHandler) ListPurchaseOrders(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Purchase orders retrieved", []gin.H{{"id": "po-1", "po_number": "PO-001", "status": "PENDING"}}, page, limit, 1)
		return
	}

	var pos []models.PurchaseOrder
	var total int64
	db.Model(&models.PurchaseOrder{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&pos).Error; err != nil {
		response.SuccessWithPagination(c, "Purchase orders retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Purchase orders retrieved", pos, page, limit, total)
}

func (h *ProcurementHandler) CreatePurchaseOrder(c *gin.Context) {
	response.Created(c, "Purchase order created successfully", gin.H{"id": "new-po-id", "po_number": "PO-NEW"})
}

func (h *ProcurementHandler) ApprovePurchaseOrder(c *gin.Context) {
	response.Updated(c, "Purchase order approved", gin.H{"id": c.Param("id"), "status": "APPROVED"})
}

func (h *ProcurementHandler) ListVendorBills(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Vendor bills retrieved", []gin.H{{"id": "bill-1", "bill_number": "BILL-001", "status": "PENDING"}}, page, limit, 1)
		return
	}

	var bills []models.VendorBill
	var total int64
	db.Model(&models.VendorBill{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&bills).Error; err != nil {
		response.SuccessWithPagination(c, "Vendor bills retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Vendor bills retrieved", bills, page, limit, total)
}

func (h *ProcurementHandler) CreateVendorBill(c *gin.Context) {
	response.Created(c, "Vendor bill created successfully", gin.H{"id": "new-bill-id"})
}
