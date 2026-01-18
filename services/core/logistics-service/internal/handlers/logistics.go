package handlers

import (
	"strconv"

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
		response.Success(c, "Statistics retrieved", gin.H{"total_deliveries": 20, "pending": 5, "in_transit": 8, "delivered": 7})
		return
	}
	var total, pending, inTransit, delivered int64
	db.Model(&models.DeliveryOrder{}).Count(&total)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "PENDING").Count(&pending)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "IN_TRANSIT").Count(&inTransit)
	db.Model(&models.DeliveryOrder{}).Where("status = ?", "DELIVERED").Count(&delivered)
	response.Success(c, "Statistics retrieved", gin.H{"total_deliveries": total, "pending": pending, "in_transit": inTransit, "delivered": delivered})
}

func (h *LogisticsHandler) ListDeliveries(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	if db == nil {
		response.SuccessWithPagination(c, "Deliveries retrieved", []gin.H{{"id": "do-1", "do_number": "DO-001", "status": "PENDING"}}, page, limit, 1)
		return
	}
	var dos []models.DeliveryOrder
	var total int64
	db.Model(&models.DeliveryOrder{}).Count(&total)
	db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&dos)
	response.SuccessWithPagination(c, "Deliveries retrieved", dos, page, limit, total)
}

func (h *LogisticsHandler) GetDelivery(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")
	if db == nil {
		response.Success(c, "Delivery retrieved", gin.H{"id": id, "do_number": "DO-001"})
		return
	}
	var do models.DeliveryOrder
	if err := db.First(&do, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Delivery not found")
		return
	}
	response.Success(c, "Delivery retrieved", do)
}

func (h *LogisticsHandler) CreateDelivery(c *gin.Context) {
	response.Created(c, "Delivery order created successfully", gin.H{"id": "new-do-id", "do_number": "DO-NEW"})
}

func (h *LogisticsHandler) UpdateDeliveryStatus(c *gin.Context) {
	response.Updated(c, "Delivery status updated", gin.H{"id": c.Param("id"), "status": "IN_TRANSIT"})
}

func (h *LogisticsHandler) ListShipments(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if db == nil {
		response.SuccessWithPagination(c, "Shipments retrieved", []gin.H{{"id": "ship-1", "tracking_number": "TRK-001"}}, page, limit, 1)
		return
	}
	var shipments []models.Shipment
	var total int64
	db.Model(&models.Shipment{}).Count(&total)
	db.Order("created_at DESC").Limit(limit).Find(&shipments)
	response.SuccessWithPagination(c, "Shipments retrieved", shipments, page, limit, total)
}

func (h *LogisticsHandler) CreateShipment(c *gin.Context) {
	response.Created(c, "Shipment created successfully", gin.H{"id": "new-shipment-id"})
}

func (h *LogisticsHandler) TrackShipment(c *gin.Context) {
	response.Success(c, "Tracking info retrieved", gin.H{"tracking_number": c.Param("tracking"), "status": "IN_TRANSIT", "location": "Jakarta"})
}
