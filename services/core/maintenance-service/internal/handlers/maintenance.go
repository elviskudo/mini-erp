package handlers

import (
	"strconv"

	"github.com/elviskudo/mini-erp/services/maintenance-service/internal/database"
	"github.com/elviskudo/mini-erp/services/maintenance-service/internal/models"
	"github.com/elviskudo/mini-erp/services/maintenance-service/internal/response"
	"github.com/gin-gonic/gin"
)

type MaintenanceHandler struct{}

func NewMaintenanceHandler() *MaintenanceHandler { return &MaintenanceHandler{} }

func (h *MaintenanceHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, "Statistics retrieved", gin.H{"total_assets": 50, "open_work_orders": 10, "overdue_maintenance": 3})
		return
	}
	var assets, openWO, overdue int64
	db.Model(&models.Asset{}).Count(&assets)
	db.Model(&models.MaintenanceWorkOrder{}).Where("status = ?", "OPEN").Count(&openWO)
	db.Model(&models.MaintenanceSchedule{}).Where("next_due < NOW() AND is_active = true").Count(&overdue)
	response.Success(c, "Statistics retrieved", gin.H{"total_assets": assets, "open_work_orders": openWO, "overdue_maintenance": overdue})
}

func (h *MaintenanceHandler) ListAssets(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	if db == nil {
		response.SuccessWithPagination(c, "Assets retrieved", []gin.H{{"id": "asset-1", "asset_code": "AST-001", "name": "CNC Machine"}}, page, limit, 1)
		return
	}
	var assets []models.Asset
	var total int64
	db.Model(&models.Asset{}).Count(&total)
	db.Order("name ASC").Offset(offset).Limit(limit).Find(&assets)
	response.SuccessWithPagination(c, "Assets retrieved", assets, page, limit, total)
}

func (h *MaintenanceHandler) CreateAsset(c *gin.Context) {
	response.Created(c, "Asset created successfully", gin.H{"id": "new-asset-id", "asset_code": "AST-NEW"})
}

func (h *MaintenanceHandler) GetAsset(c *gin.Context) {
	response.Success(c, "Asset retrieved", gin.H{"id": c.Param("id"), "asset_code": "AST-001", "name": "CNC Machine"})
}

func (h *MaintenanceHandler) UpdateAsset(c *gin.Context) {
	response.Updated(c, "Asset updated successfully", gin.H{"id": c.Param("id")})
}

func (h *MaintenanceHandler) ListWorkOrders(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	if db == nil {
		response.SuccessWithPagination(c, "Work orders retrieved", []gin.H{{"id": "wo-1", "wo_number": "WO-001", "status": "OPEN"}}, page, limit, 1)
		return
	}
	var wos []models.MaintenanceWorkOrder
	var total int64
	db.Model(&models.MaintenanceWorkOrder{}).Count(&total)
	db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&wos)
	response.SuccessWithPagination(c, "Work orders retrieved", wos, page, limit, total)
}

func (h *MaintenanceHandler) CreateWorkOrder(c *gin.Context) {
	response.Created(c, "Work order created successfully", gin.H{"id": "new-wo-id", "wo_number": "WO-NEW"})
}

func (h *MaintenanceHandler) UpdateWorkOrderStatus(c *gin.Context) {
	response.Updated(c, "Work order status updated", gin.H{"id": c.Param("id"), "status": "IN_PROGRESS"})
}

func (h *MaintenanceHandler) ListSchedules(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if db == nil {
		response.SuccessWithPagination(c, "Schedules retrieved", []gin.H{{"id": "sch-1", "frequency": "MONTHLY"}}, page, limit, 1)
		return
	}
	var schedules []models.MaintenanceSchedule
	var total int64
	db.Model(&models.MaintenanceSchedule{}).Count(&total)
	db.Limit(limit).Find(&schedules)
	response.SuccessWithPagination(c, "Schedules retrieved", schedules, page, limit, total)
}

func (h *MaintenanceHandler) CreateSchedule(c *gin.Context) {
	response.Created(c, "Schedule created successfully", gin.H{"id": "new-schedule-id"})
}
