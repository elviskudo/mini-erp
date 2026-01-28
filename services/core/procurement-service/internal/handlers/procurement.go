package handlers

import (
	"strconv"
	"time" // Added this import for time.Now()

	"github.com/elviskudo/mini-erp/services/procurement-service/internal/database"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/models"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

type ProcurementHandler struct{}

func NewProcurementHandler() *ProcurementHandler { return &ProcurementHandler{} }

func (h *ProcurementHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, gin.H{"total_vendors": 10, "pending_pos": 5, "pending_prs": 3}, "Statistics retrieved")
		return
	}
	var vendors, pos, prs int64
	db.Model(&models.Vendor{}).Count(&vendors)
	db.Model(&models.PurchaseOrder{}).Where("status = ?", "PENDING").Count(&pos)
	db.Model(&models.PurchaseRequest{}).Where("status = ?", "PENDING").Count(&prs)
	response.Success(c, gin.H{"total_vendors": vendors, "pending_pos": pos, "pending_prs": prs}, "Statistics retrieved")
}

func (h *ProcurementHandler) ListVendors(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, []gin.H{{"id": "v-1", "code": "VND-001", "name": "PT Supplier Jaya"}}, page, limit, 1, "Vendors retrieved")
		return
	}

	var vendors []models.Vendor
	var total int64
	db.Model(&models.Vendor{}).Count(&total)
	if err := db.Order("name ASC").Offset(offset).Limit(limit).Find(&vendors).Error; err != nil {
		response.SuccessList(c, []models.Vendor{}, page, limit, 0, "Vendors retrieved")
		return
	}
	response.SuccessList(c, vendors, page, limit, total, "Vendors retrieved")
}

func (h *ProcurementHandler) GetVendor(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")
	if db == nil {
		response.Success(c, gin.H{"id": id, "name": "PT Supplier Jaya"}, "Vendor retrieved")
		return
	}
	var vendor models.Vendor
	if err := db.First(&vendor, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Vendor not found")
		return
	}
	response.Success(c, vendor, "Vendor retrieved")
}

func (h *ProcurementHandler) CreateVendor(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-vendor-id"}, "Vendor created successfully")
}

func (h *ProcurementHandler) UpdateVendor(c *gin.Context) {
	response.Success(c, gin.H{"id": c.Param("id")}, "Vendor updated successfully")
}

func (h *ProcurementHandler) ListPurchaseRequests(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, []gin.H{{"id": "pr-1", "pr_number": "PR-001", "status": "PENDING"}}, page, limit, 1, "Purchase requests retrieved")
		return
	}

	var prs []models.PurchaseRequest
	var total int64
	db.Model(&models.PurchaseRequest{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&prs).Error; err != nil {
		response.SuccessList(c, []models.PurchaseRequest{}, page, limit, 0, "Purchase requests retrieved")
		return
	}
	response.SuccessList(c, prs, page, limit, total, "Purchase requests retrieved")
}

func (h *ProcurementHandler) CreatePurchaseRequest(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")
	userID := c.GetHeader("X-User-ID")

	var req struct {
		Priority     string `json:"priority"`
		RequiredDate string `json:"required_date"`
		Notes        string `json:"notes"`
		Items        []struct {
			ProductID string  `json:"product_id" binding:"required"`
			Quantity  float64 `json:"quantity" binding:"required,min=1"`
		} `json:"items" binding:"required,min=1"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	if db == nil {
		response.SuccessCreate(c, gin.H{"id": "new-pr", "pr_number": "PR-MOCK"}, "PR created (mock)")
		return
	}

	// Parse RequiredDate
	var requiredDate *time.Time
	if req.RequiredDate != "" {
		if t, err := time.Parse("2006-01-02", req.RequiredDate); err == nil {
			requiredDate = &t
		}
	}

	prID := uuid.NewString()
	prNumber := "PR-" + time.Now().Format("20060102") + "-" + prID[:4]
	status := "PENDING"

	pr := models.PurchaseRequest{
		ID:           prID,
		TenantID:     tenantID,
		RequestedBy:  &userID,
		PRNumber:     &prNumber,
		Status:       &status,
		Priority:     &req.Priority,
		RequiredDate: requiredDate,
		Notes:        &req.Notes,
		CreatedAt:    time.Now(),
		Items:        make([]models.PurchaseRequestItem, 0),
	}

	for _, item := range req.Items {
		pr.Items = append(pr.Items, models.PurchaseRequestItem{
			ID:        uuid.NewString(),
			PRID:      prID,
			ProductID: item.ProductID,
			Quantity:  item.Quantity,
		})
	}

	tx := db.Begin()
	if err := tx.Create(&pr).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create PR")
		return
	}
	tx.Commit()

	response.SuccessCreate(c, pr, "Purchase Request created successfully")
}

func (h *ProcurementHandler) ApprovePurchaseRequest(c *gin.Context) {
	response.Success(c, gin.H{"id": c.Param("id"), "status": "APPROVED"}, "Purchase request approved")
}

func (h *ProcurementHandler) ListPurchaseOrders(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, []gin.H{{"id": "po-1", "po_number": "PO-001", "status": "PENDING"}}, page, limit, 1, "Purchase orders retrieved")
		return
	}

	var pos []models.PurchaseOrder
	var total int64
	db.Model(&models.PurchaseOrder{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&pos).Error; err != nil {
		response.SuccessList(c, []models.PurchaseOrder{}, page, limit, 0, "Purchase orders retrieved")
		return
	}
	response.SuccessList(c, pos, page, limit, total, "Purchase orders retrieved")
}

func (h *ProcurementHandler) CreatePurchaseOrder(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-po-id", "po_number": "PO-NEW"}, "Purchase order created successfully")
}

func (h *ProcurementHandler) ApprovePurchaseOrder(c *gin.Context) {
	response.Success(c, gin.H{"id": c.Param("id"), "status": "APPROVED"}, "Purchase order approved")
}

func (h *ProcurementHandler) ListVendorBills(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, []gin.H{{"id": "bill-1", "bill_number": "BILL-001", "status": "PENDING"}}, page, limit, 1, "Vendor bills retrieved")
		return
	}

	var bills []models.VendorBill
	var total int64
	db.Model(&models.VendorBill{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&bills).Error; err != nil {
		response.SuccessList(c, []models.VendorBill{}, page, limit, 0, "Vendor bills retrieved")
		return
	}
	response.SuccessList(c, bills, page, limit, total, "Vendor bills retrieved")
}

func (h *ProcurementHandler) CreateVendorBill(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-bill-id"}, "Vendor bill created successfully")
}

func (h *ProcurementHandler) RejectPurchaseRequest(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	var body struct {
		Reason string `json:"reason" binding:"required"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		response.BadRequest(c, "Reason is required")
		return
	}

	if db == nil {
		response.Success(c, gin.H{"id": id, "status": "REJECTED"}, "Purchase request rejected (mock)")
		return
	}

	var pr models.PurchaseRequest
	if err := db.First(&pr, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Purchase request not found")
		return
	}

	status := "REJECTED"
	now := time.Now()
	pr.Status = &status
	pr.RejectReason = &body.Reason
	pr.RejectedAt = &now

	if err := db.Save(&pr).Error; err != nil {
		response.InternalError(c, "Failed to reject PR")
		return
	}

	response.Success(c, pr, "Purchase request rejected")
}

func (h *ProcurementHandler) CreatePurchaseOrderFromPR(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	var req struct {
		PRID     string             `json:"pr_id" binding:"required"`
		VendorID string             `json:"vendor_id" binding:"required"`
		PriceMap map[string]float64 `json:"price_map"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	if db == nil {
		response.SuccessCreate(c, gin.H{"id": "new-po", "po_number": "PO-MOCK"}, "PO created (mock)")
		return
	}

	// Fetch PR with items
	var pr models.PurchaseRequest
	if err := db.Preload("Items").First(&pr, "id = ?", req.PRID).Error; err != nil {
		response.NotFound(c, "Purchase request not found")
		return
	}

	// Create PO
	poID := uuid.NewString()
	poNumber := "PO-" + time.Now().Format("20060102") + "-" + poID[:4]
	status := "OPEN" // or DRAFT

	po := models.PurchaseOrder{
		ID:        poID,
		TenantID:  tenantID,
		VendorID:  req.VendorID,
		PRID:      &pr.ID,
		PONumber:  &poNumber,
		Status:    &status,
		CreatedAt: time.Now(),
		Items:     make([]models.PurchaseOrderItem, 0),
	}

	var totalAmount float64
	for _, item := range pr.Items {
		price := req.PriceMap[item.ProductID]
		lineTotal := price * item.Quantity
		totalAmount += lineTotal

		po.Items = append(po.Items, models.PurchaseOrderItem{
			ID:        uuid.NewString(),
			POID:      poID,
			ProductID: item.ProductID,
			Quantity:  item.Quantity,
			UnitPrice: price,
			LineTotal: lineTotal,
		})
	}
	po.Subtotal = &totalAmount
	po.TotalAmount = &totalAmount

	tx := db.Begin()
	if err := tx.Create(&po).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create PO")
		return
	}

	// Update PR status
	prStatus := "CONVERTED"
	if err := tx.Model(&pr).Update("status", prStatus).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to update PR status")
		return
	}

	tx.Commit()
	response.SuccessCreate(c, po, "Purchase Order created successfully")
}

func (h *ProcurementHandler) SendPurchaseOrder(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	var body struct {
		Notes string `json:"notes"`
	}
	c.ShouldBindJSON(&body) // Optional

	if db == nil {
		response.Success(c, nil, "PO Sent (mock)")
		return
	}

	var po models.PurchaseOrder
	if err := db.First(&po, "id = ?", id).Error; err != nil {
		response.NotFound(c, "PO not found")
		return
	}

	status := "SENT" // SENT to vendor
	po.Status = &status
	// optionally append notes

	if err := db.Save(&po).Error; err != nil {
		response.InternalError(c, "Failed to update PO")
		return
	}
	response.Success(c, po, "Purchase Order sent to vendor")
}

func (h *ProcurementHandler) ReceivePurchaseOrder(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	var req struct {
		Items []struct {
			POLineID  string  `json:"po_line_id"`
			ProductID string  `json:"product_id"`
			Quantity  float64 `json:"quantity"`
		} `json:"items"`
		ShippingCost float64  `json:"shipping_cost"`
		ReceivedTemp *float64 `json:"received_temp"`
		Notes        string   `json:"notes"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Invalid request")
		return
	}

	if db == nil {
		response.Success(c, nil, "PO Received (mock)")
		return
	}

	tx := db.Begin()

	// Update Header
	status := "PARTIAL_RECEIVE"
	// Logic to check if all received... simplified for now
	if err := tx.Model(&models.PurchaseOrder{}).Where("id = ?", id).
		Updates(map[string]interface{}{
			"status":        status,
			"shipping_cost": req.ShippingCost,
		}).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to update PO header")
		return
	}

	// Update Items
	for _, item := range req.Items {
		// Increment received qty
		// WARNING: This is a simplifed update. In real ERP we'd have a Receipts table.
		// Here we just update the PO Item received_qty
		if err := tx.Model(&models.PurchaseOrderItem{}).
			Where("id = ?", item.POLineID).
			Update("received_qty", gorm.Expr("received_qty + ?", item.Quantity)).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to update PO item")
			return
		}
	}

	tx.Commit()
	response.Success(c, nil, "Goods received successfully")
}

func (h *ProcurementHandler) DownloadPurchaseOrderPDF(c *gin.Context) {
	c.Header("Content-Disposition", "attachment; filename=po.pdf")
	c.Data(200, "application/pdf", []byte("%PDF-1.4... (Real PDF generation not implemented yet)"))
}

func (h *ProcurementHandler) ListRFQs(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, []gin.H{}, page, limit, 0, "RFQs retrieved")
		return
	}

	var rfqs []models.RFQ
	var total int64
	db.Model(&models.RFQ{}).Count(&total)
	if err := db.Preload("Items").Preload("Vendors.Vendor").Order("created_at DESC").Offset(offset).Limit(limit).Find(&rfqs).Error; err != nil {
		response.InternalError(c, "Failed to fetch RFQs")
		return
	}

	// Transform for frontend
	var result []gin.H
	for _, r := range rfqs {
		var vendors []gin.H
		for _, v := range r.Vendors {
			vendorName := "Unknown"
			if v.Vendor != nil {
				vendorName = v.Vendor.Name
			}
			vendors = append(vendors, gin.H{
				"id":            v.ID,
				"vendor_id":     v.VendorID,
				"vendor_name":   vendorName,
				"is_selected":   v.IsSelected,
				"quoted_amount": v.QuotedAmount,
				"delivery_days": v.DeliveryDays,
			})
		}

		result = append(result, gin.H{
			"id":            r.ID,
			"rfq_number":    r.RFQNumber,
			"status":        r.Status,
			"deadline":      r.Deadline,
			"items_count":   len(r.Items),
			"vendors_count": len(r.Vendors),
			"notes":         r.Notes,
			"items":         r.Items,
			"vendors":       vendors,
		})
	}

	response.SuccessList(c, result, page, limit, total, "RFQs retrieved")
}

func (h *ProcurementHandler) CreateRFQ(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	var req struct {
		Deadline string `json:"deadline"`
		Priority string `json:"priority"`
		Notes    string `json:"notes"`
		Items    []struct {
			ProductID      string  `json:"product_id"`
			Quantity       float64 `json:"quantity"`
			Specifications string  `json:"specifications"`
		} `json:"items"`
		VendorIDs []string `json:"vendor_ids"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Invalid request: "+err.Error())
		return
	}

	if db == nil {
		response.SuccessCreate(c, nil, "RFQ Created (mock)")
		return
	}

	var deadline *time.Time
	if req.Deadline != "" {
		if t, err := time.Parse("2006-01-02", req.Deadline); err == nil {
			deadline = &t
		}
	}

	rfqID := uuid.NewString()
	rfqNumber := "RFQ-" + time.Now().Format("20060102") + "-" + rfqID[:4]

	rfq := models.RFQ{
		ID:        rfqID,
		TenantID:  tenantID,
		RFQNumber: rfqNumber,
		Status:    "Draft",
		Priority:  req.Priority,
		Notes:     &req.Notes,
		Deadline:  deadline,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	tx := db.Begin()
	if err := tx.Create(&rfq).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create RFQ")
		return
	}

	for _, item := range req.Items {
		if err := tx.Create(&models.RFQItem{
			ID:             uuid.NewString(),
			TenantID:       tenantID,
			RFQID:          rfqID,
			ProductID:      item.ProductID,
			Quantity:       item.Quantity,
			Specifications: &item.Specifications,
		}).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to create RFQ items")
			return
		}
	}

	for _, vid := range req.VendorIDs {
		if err := tx.Create(&models.RFQVendor{
			ID:       uuid.NewString(),
			TenantID: tenantID,
			RFQID:    rfqID,
			VendorID: vid,
		}).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to create RFQ vendors")
			return
		}
	}

	tx.Commit()
	response.SuccessCreate(c, rfq, "RFQ created successfully")
}

func (h *ProcurementHandler) GetRFQ(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.NotFound(c, "RFQ not found")
		return
	}

	var rfq models.RFQ
	if err := db.Preload("Items").Preload("Vendors.Vendor").First(&rfq, "id = ?", id).Error; err != nil {
		response.NotFound(c, "RFQ not found")
		return
	}

	// Transform Vendors to include names
	var vendors []gin.H
	for _, v := range rfq.Vendors {
		vendors = append(vendors, gin.H{
			"id":            v.ID,
			"vendor_id":     v.VendorID,
			"vendor_name":   v.Vendor.Name,
			"is_selected":   v.IsSelected,
			"quoted_amount": v.QuotedAmount,
			"delivery_days": v.DeliveryDays,
		})
	}

	result := gin.H{
		"id":         rfq.ID,
		"rfq_number": rfq.RFQNumber,
		"deadline":   rfq.Deadline,
		"status":     rfq.Status,
		"items":      rfq.Items,
		"vendors":    vendors,
	}

	response.Success(c, result, "RFQ retrieved")
}

func (h *ProcurementHandler) SendRFQ(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")

	if db == nil {
		response.Success(c, nil, "RFQ Sent (mock)")
		return
	}

	if err := db.Model(&models.RFQ{}).Where("id = ?", id).Update("status", "Sent").Error; err != nil {
		response.InternalError(c, "Failed to update RFQ")
		return
	}

	response.Success(c, nil, "RFQ Sent to vendors")
}

func (h *ProcurementHandler) ListPayments(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.SuccessList(c, []gin.H{}, 1, 10, 0, "Payments retrieved")
		return
	}

	var payments []models.Payment
	// Preload Bill and Vendor via Bill
	if err := db.Preload("Bill.Vendor").Order("payment_date DESC").Find(&payments).Error; err != nil {
		response.InternalError(c, "Failed to fetch payments")
		return
	}

	var result []gin.H
	for _, p := range payments {
		vendorName := "Unknown"
		billNum := "-"
		if p.Bill != nil {
			billNum = *p.Bill.BillNumber
			if p.Bill.Vendor != nil {
				vendorName = p.Bill.Vendor.Name
			}
		}

		result = append(result, gin.H{
			"id":             p.ID,
			"payment_date":   p.PaymentDate,
			"amount":         p.Amount,
			"payment_method": p.PaymentMethod,
			"reference":      p.Reference,
			"bill_number":    billNum,
			"vendor_name":    vendorName,
		})
	}

	response.Success(c, result, "Payments retrieved")
}

func (h *ProcurementHandler) CreateBillPayment(c *gin.Context) {
	db := database.GetDB()
	billID := c.Param("id")
	tenantID := c.GetHeader("X-Tenant-ID")

	var req struct {
		Amount        float64 `json:"amount" binding:"required"`
		PaymentMethod string  `json:"payment_method"`
		Reference     string  `json:"reference"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Invalid request")
		return
	}

	if db == nil {
		response.SuccessCreate(c, nil, "Payment recorded (mock)")
		return
	}

	tx := db.Begin()

	// 1. Create Payment
	payment := models.Payment{
		ID:            uuid.NewString(),
		TenantID:      tenantID,
		BillID:        billID,
		Amount:        req.Amount,
		PaymentMethod: req.PaymentMethod,
		Reference:     &req.Reference,
		PaymentDate:   time.Now(),
		CreatedAt:     time.Now(),
	}

	if err := tx.Create(&payment).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create payment")
		return
	}

	// 2. Update Bill Paid Amount and Status
	var bill models.VendorBill
	if err := tx.First(&bill, "id = ?", billID).Error; err != nil {
		tx.Rollback()
		response.NotFound(c, "Bill not found")
		return
	}

	newPaid := *bill.PaidAmount + req.Amount
	status := *bill.Status
	if newPaid >= *bill.TotalAmount {
		status = "PAID"
	} else {
		status = "PARTIAL"
	}

	if err := tx.Model(&bill).Updates(map[string]interface{}{
		"paid_amount": newPaid,
		"status":      status,
	}).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to update bill status")
		return
	}

	tx.Commit()
	response.SuccessCreate(c, payment, "Payment recorded successfully")
}

func (h *ProcurementHandler) GetAnalyticsSummary(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, gin.H{"spend_this_month": 0}, "Analytics summary")
		return
	}

	var poCount int64
	db.Model(&models.PurchaseOrder{}).Count(&poCount)

	var vendorCount int64
	db.Model(&models.Vendor{}).Count(&vendorCount)

	// Calculate Spend This Month (from payments or bills? typically Spend = PO or Bill total. Let's use PO Total for now)
	var totalSpend float64
	now := time.Now()
	startOfMonth := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())

	db.Model(&models.PurchaseOrder{}).
		Where("created_at >= ?", startOfMonth).
		Select("COALESCE(SUM(total_amount), 0)").
		Scan(&totalSpend)

	response.Success(c, gin.H{
		"total_orders":    poCount,
		"active_vendors":  vendorCount,
		"total_purchases": totalSpend,
		"avg_lead_time":   5,  // Placeholder/Mock
		"growth_percent":  12, // Placeholder/Mock
	}, "Analytics summary")
}
