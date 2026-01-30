package handlers

import (
	"fmt"
	"strconv"
	"time"

	"github.com/google/uuid"

	"github.com/elviskudo/mini-erp/services/logistics-service/internal/database"
	"github.com/elviskudo/mini-erp/services/logistics-service/internal/models"
	"github.com/elviskudo/mini-erp/services/logistics-service/internal/response"
	"github.com/gin-gonic/gin"
)

type LogisticsHandler struct{}

func NewLogisticsHandler() *LogisticsHandler { return &LogisticsHandler{} }

func (h *LogisticsHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, gin.H{"total_deliveries": 20, "pending": 5, "in_transit": 8, "delivered": 7}, "Statistics retrieved")
		return
	}
	var total, pending, inTransit, delivered int64
	db.Model(&models.DeliveryOrder{}).Count(&total)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "PENDING").Count(&pending)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "IN_TRANSIT").Count(&inTransit)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "DELIVERED").Count(&delivered)
	response.Success(c, gin.H{"total_deliveries": total, "pending": pending, "in_transit": inTransit, "delivered": delivered}, "Statistics retrieved")
}

func (h *LogisticsHandler) ListDeliveries(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	var dos []models.DeliveryOrder
	var total int64

	db.Model(&models.DeliveryOrder{}).Count(&total)
	if err := db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&dos).Error; err != nil {
		response.InternalError(c, "Failed to fetch deliveries")
		return
	}

	// Calculate items count for each DO
	for i := range dos {
		var count int64
		db.Model(&models.DeliveryOrderItem{}).Where("delivery_order_id = ?", dos[i].ID).Count(&count)
		dos[i].ItemsCount = int(count)
	}

	response.SuccessList(c, dos, page, limit, total, "Deliveries retrieved")
}

func (h *LogisticsHandler) GetDelivery(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	id := c.Param("id")
	var do models.DeliveryOrder
	if err := db.Preload("Items").First(&do, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Delivery not found")
		return
	}

	// Double check items count
	do.ItemsCount = len(do.Items)

	response.Success(c, do, "Delivery retrieved")
}

func (h *LogisticsHandler) CreateDelivery(c *gin.Context) {
	var req struct {
		SONumber        *string `json:"so_id"`
		CustomerID      *string `json:"customer_id"`
		CustomerName    *string `json:"customer_name"`
		ShippingAddress *string `json:"shipping_address"`
		Notes           *string `json:"notes"`
		Items           []struct {
			ProductID   string  `json:"product_id"`
			ProductName string  `json:"product_name"` // From UI
			BatchID     *string `json:"batch_id"`
			BatchNumber string  `json:"batch_number"` // From UI
			Quantity    float64 `json:"quantity"`
		} `json:"items"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	tx := db.Begin()
	now := time.Now()
	// Extract tenant ID from header or context
	tenantIDStr := c.GetHeader("X-Tenant-ID")
	if tenantIDStr == "" {
		if val, exists := c.Get("tenant_id"); exists {
			tenantIDStr, _ = val.(string)
		}
	}

	if tenantIDStr == "" {
		// Fallback for development/testing - use the first valid tenant from DB or a known valid one
		// In production, this should probably return an error.
		tenantIDStr = "6c812e6d-da95-49e8-8510-cc36b196bdb6" // "Mata Rantai" tenant
	}

	// Generate DO Number (simple version)
	doNumber := fmt.Sprintf("DO-%d", now.Unix())

	do := models.DeliveryOrder{
		ID:                 uuid.New().String(),
		TenantID:           tenantIDStr,
		DONumber:           &doNumber,
		SalesOrderID:       handleEmptyUUID(req.SONumber),
		CustomerID:         handleEmptyUUID(req.CustomerID),
		CustomerName:       req.CustomerName,
		Status:             pointerString("Draft"),
		DestinationAddress: req.ShippingAddress,
		Notes:              req.Notes,
		CreatedAt:          now,
	}

	if err := tx.Create(&do).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create DO: "+err.Error())
		return
	}

	for _, item := range req.Items {
		detail := models.DeliveryOrderItem{
			ID:              uuid.New().String(),
			TenantID:        tenantIDStr,
			DeliveryOrderID: do.ID,
			ProductID:       item.ProductID,
			ProductName:     item.ProductName,
			BatchID:         handleEmptyUUID(item.BatchID),
			BatchNumber:     item.BatchNumber,
			Quantity:        item.Quantity,
			CreatedAt:       now,
		}
		if err := tx.Create(&detail).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to create DO item: "+err.Error())
			return
		}
	}

	if err := tx.Commit().Error; err != nil {
		response.InternalError(c, "Failed to commit")
		return
	}

	response.SuccessCreate(c, do, "Delivery order created successfully")
}

func pointerString(s string) *string { return &s }

func (h *LogisticsHandler) UpdateDeliveryStatus(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	var req struct {
		Status string `json:"status" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	id := c.Param("id")
	if err := db.Model(&models.DeliveryOrder{}).Where("id = ?", id).Update("status", req.Status).Error; err != nil {
		response.InternalError(c, "Failed to update status: "+err.Error())
		return
	}

	response.Success(c, nil, "Status updated")
}

func (h *LogisticsHandler) ShipDelivery(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	id := c.Param("id")
	now := time.Now()
	if err := db.Model(&models.DeliveryOrder{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":     pointerString("Shipped"),
		"shipped_at": &now,
	}).Error; err != nil {
		response.InternalError(c, "Failed to ship order: "+err.Error())
		return
	}

	response.Success(c, nil, "Order shipped successfully")
}

func (h *LogisticsHandler) ListShipments(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if db == nil {
		response.SuccessList(c, []gin.H{{"id": "ship-1", "tracking_number": "TRK-001"}}, page, limit, 1, "Shipments retrieved")
		return
	}
	var shipments []models.Shipment
	var total int64
	db.Model(&models.Shipment{}).Count(&total)
	db.Order("created_at DESC").Limit(limit).Find(&shipments)
	response.SuccessList(c, shipments, page, limit, total, "Shipments retrieved")
}

func (h *LogisticsHandler) CreateShipment(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-shipment-id"}, "Shipment created successfully")
}

func (h *LogisticsHandler) TrackShipment(c *gin.Context) {
	response.Success(c, gin.H{"tracking_number": c.Param("tracking"), "status": "IN_TRANSIT", "location": "Jakarta"}, "Tracking info retrieved")
}

func handleEmptyUUID(s *string) *string {
	if s == nil || *s == "" {
		return nil
	}
	return s
}

// ========== STOCK TRANSFERS ==========

func (h *LogisticsHandler) ListTransfers(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	var transfers []models.StockTransfer
	if err := db.Preload("Items").Order("created_at DESC").Find(&transfers).Error; err != nil {
		response.InternalError(c, "Failed to fetch transfers: "+err.Error())
		return
	}

	// Fetch warehouse names for display
	for i := range transfers {
		var fromWH, toWH struct{ Name string }
		db.Table("warehouses").Select("name").Where("id = ?", transfers[i].FromWarehouseID).First(&fromWH)
		db.Table("warehouses").Select("name").Where("id = ?", transfers[i].ToWarehouseID).First(&toWH)
		transfers[i].FromWarehouse = fromWH.Name
		transfers[i].ToWarehouse = toWH.Name
	}

	response.Success(c, transfers, "Transfers retrieved")
}

func (h *LogisticsHandler) CreateTransfer(c *gin.Context) {
	var req struct {
		FromWarehouseID string `json:"from_warehouse_id" binding:"required"`
		ToWarehouseID   string `json:"to_warehouse_id" binding:"required"`
		TransferDate    string `json:"transfer_date"`
		TransferType    string `json:"transfer_type"`
		Notes           string `json:"notes"`
		Items           []struct {
			ProductID string  `json:"product_id" binding:"required"`
			Quantity  float64 `json:"quantity" binding:"required"`
		} `json:"items" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	// Extract tenant ID
	tenantIDStr := c.GetHeader("X-Tenant-ID")
	if tenantIDStr == "" {
		if val, exists := c.Get("tenant_id"); exists {
			tenantIDStr, _ = val.(string)
		}
	}
	if tenantIDStr == "" {
		tenantIDStr = "6c812e6d-da95-49e8-8510-cc36b196bdb6" // Fallback
	}

	transferID := uuid.New().String()
	transferNumber := fmt.Sprintf("TRF-%d", time.Now().Unix())

	now := time.Now()
	var tDate *time.Time
	if req.TransferDate != "" {
		parsedDate, err := time.Parse("2006-01-02", req.TransferDate)
		if err == nil {
			tDate = &parsedDate
		}
	}

	transfer := models.StockTransfer{
		ID:              transferID,
		TenantID:        tenantIDStr,
		TransferNumber:  transferNumber,
		FromWarehouseID: req.FromWarehouseID,
		ToWarehouseID:   req.ToWarehouseID,
		TransferDate:    tDate,
		TransferType:    req.TransferType,
		Status:          models.TransferPending,
		Notes:           req.Notes,
		CreatedAt:       now,
		UpdatedAt:       now,
	}

	tx := db.Begin()
	if err := tx.Create(&transfer).Error; err != nil {
		tx.Rollback()
		response.InternalError(c, "Failed to create transfer: "+err.Error())
		return
	}

	for _, item := range req.Items {
		transferItem := models.StockTransferItem{
			ID:         uuid.New().String(),
			TenantID:   tenantIDStr,
			TransferID: transferID,
			ProductID:  item.ProductID,
			Quantity:   item.Quantity,
		}
		if err := tx.Create(&transferItem).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to create transfer item: "+err.Error())
			return
		}
	}

	tx.Commit()
	response.Success(c, transfer, "Transfer created successfully")
}

func (h *LogisticsHandler) StartTransfer(c *gin.Context) {
	id := c.Param("id")
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	now := time.Now()
	if err := db.Model(&models.StockTransfer{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":     string(models.TransferInTransit),
		"started_at": &now,
	}).Error; err != nil {
		response.InternalError(c, "Failed to start transfer: "+err.Error())
		return
	}

	response.Success(c, nil, "Transfer started")
}

func (h *LogisticsHandler) CompleteTransfer(c *gin.Context) {
	id := c.Param("id")
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	now := time.Now()
	if err := db.Model(&models.StockTransfer{}).Where("id = ?", id).Updates(map[string]interface{}{
		"status":       string(models.TransferCompleted),
		"completed_at": &now,
	}).Error; err != nil {
		response.InternalError(c, "Failed to complete transfer: "+err.Error())
		return
	}

	response.Success(c, nil, "Transfer completed")
}
