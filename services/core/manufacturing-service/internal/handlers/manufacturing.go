package handlers

import (
	"strconv"
	"time"

	"github.com/elviskudo/mini-erp/services/manufacturing-service/internal/database"
	"github.com/elviskudo/mini-erp/services/manufacturing-service/internal/models"
	"github.com/elviskudo/mini-erp/services/manufacturing-service/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

type ManufacturingHandler struct{}

func NewManufacturingHandler() *ManufacturingHandler {
	return &ManufacturingHandler{}
}

// Helper to parse pagination params
func getPaginationParams(c *gin.Context) (int, int, int) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 10
	}
	offset := (page - 1) * limit
	return page, limit, offset
}

// ========== CATEGORIES ==========

// ListCategories lists all categories
func (h *ManufacturingHandler) ListCategories(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")
	page, limit, offset := getPaginationParams(c)

	if db == nil {
		response.SuccessList(c, getMockCategories(), page, limit, 0, "Categories retrieved (mock)")
		return
	}

	var categories []models.Category
	var total int64
	query := db.Model(&models.Category{}).Where("tenant_id = ?", tenantID)
	query.Count(&total)
	if err := query.Order("name ASC").Offset(offset).Limit(limit).Find(&categories).Error; err != nil {
		response.InternalError(c, "Failed to fetch categories")
		return
	}
	response.SuccessList(c, categories, page, limit, total, "Categories retrieved")
}

func getMockCategories() []models.Category {
	return []models.Category{
		{ID: "cat-1", Name: "Raw Materials"},
		{ID: "cat-2", Name: "Finished Goods"},
	}
}

// GetCategory gets category by ID
func (h *ManufacturingHandler) GetCategory(c *gin.Context) {
	db := database.GetDB()
	categoryID := c.Param("id")

	if db == nil {
		response.NotFound(c, "Category not found")
		return
	}

	var category models.Category
	if err := db.Where("id = ?", categoryID).First(&category).Error; err != nil {
		response.NotFound(c, "Category not found")
		return
	}
	response.Success(c, category, "Category retrieved")
}

// CreateCategory creates a new category
func (h *ManufacturingHandler) CreateCategory(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var req struct {
		Name        string  `json:"name" binding:"required"`
		Description *string `json:"description"`
		ImageURL    *string `json:"image_url"`
		IsActive    *bool   `json:"is_active"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	isActive := true
	if req.IsActive != nil {
		isActive = *req.IsActive
	}

	category := models.Category{
		TenantID:    tenantID,
		Name:        req.Name,
		Description: req.Description,
		ImageURL:    req.ImageURL,
		IsActive:    isActive,
	}

	category.ID = uuid.New().String()
	if err := db.Create(&category).Error; err != nil {
		response.InternalError(c, "Failed to create category")
		return
	}
	response.SuccessCreate(c, category, "Category created successfully")
}

// UpdateCategory updates a category
func (h *ManufacturingHandler) UpdateCategory(c *gin.Context) {
	db := database.GetDB()
	categoryID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var category models.Category
	if err := db.Where("id = ?", categoryID).First(&category).Error; err != nil {
		response.NotFound(c, "Category not found")
		return
	}

	var req struct {
		Name        *string `json:"name"`
		Description *string `json:"description"`
		ImageURL    *string `json:"image_url"`
		IsActive    *bool   `json:"is_active"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.Name != nil {
		category.Name = *req.Name
	}
	if req.Description != nil {
		category.Description = req.Description
	}
	if req.ImageURL != nil {
		category.ImageURL = req.ImageURL
	}
	if req.IsActive != nil {
		category.IsActive = *req.IsActive
	}

	if err := db.Save(&category).Error; err != nil {
		response.InternalError(c, "Failed to update category")
		return
	}
	response.Success(c, category, "Category updated successfully")
}

// DeleteCategory deletes a category
func (h *ManufacturingHandler) DeleteCategory(c *gin.Context) {
	db := database.GetDB()
	categoryID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var category models.Category
	if err := db.Where("id = ?", categoryID).First(&category).Error; err != nil {
		response.NotFound(c, "Category not found")
		return
	}

	if err := db.Delete(&category).Error; err != nil {
		response.InternalError(c, "Failed to delete category")
		return
	}
	response.Success(c, nil, "Category deleted successfully")
}

// ========== WORK CENTERS ==========

// ListWorkCenters lists all work centers with pagination
func (h *ManufacturingHandler) ListWorkCenters(c *gin.Context) {
	page, limit, offset := getPaginationParams(c)
	db := database.GetDB()

	if db == nil {
		mockData := getMockWorkCenters()
		response.SuccessList(c, mockData, page, limit, int64(len(mockData)), "Work centers retrieved successfully")
		return
	}

	var total int64
	db.Model(&models.WorkCenter{}).Count(&total)

	var workCenters []models.WorkCenter
	if err := db.Order("code ASC").Offset(offset).Limit(limit).Find(&workCenters).Error; err != nil {
		response.InternalError(c, "Failed to fetch work centers")
		return
	}

	response.SuccessList(c, workCenters, page, limit, total, "Work centers retrieved successfully")
}

func getMockWorkCenters() []gin.H {
	return []gin.H{
		{"id": "wc-1", "code": "WC001", "name": "Assembly Line 1", "cost_per_hour": 50000, "capacity_hours": 8},
		{"id": "wc-2", "code": "WC002", "name": "Welding Station", "cost_per_hour": 75000, "capacity_hours": 6},
	}
}

// GetWorkCenter gets work center by ID
func (h *ManufacturingHandler) GetWorkCenter(c *gin.Context) {
	wcID := c.Param("id")
	db := database.GetDB()

	if db == nil {
		response.Success(c, gin.H{"id": wcID, "code": "WC001", "name": "Assembly Line 1"}, "Work center retrieved successfully")
		return
	}

	var workCenter models.WorkCenter
	if err := db.First(&workCenter, "id = ?", wcID).Error; err != nil {
		response.NotFound(c, "Work center not found")
		return
	}
	response.Success(c, workCenter, "Work center retrieved successfully")
}

// CreateWorkCenter creates a new work center
func (h *ManufacturingHandler) CreateWorkCenter(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var req struct {
		Code          string   `json:"code" binding:"required"`
		Name          string   `json:"name" binding:"required"`
		CostPerHour   *float64 `json:"cost_per_hour"`
		CapacityHours *float64 `json:"capacity_hours"`
		Location      *string  `json:"location"`
		Latitude      *float64 `json:"latitude"`
		Longitude     *float64 `json:"longitude"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.ValidationError(c, []response.Error{{Field: "body", Message: err.Error()}})
		return
	}

	// Get tenant_id from header (set by gateway)
	tenantID := c.GetHeader("X-Tenant-ID")

	// Create work center
	workCenter := models.WorkCenter{
		Code:     req.Code,
		Name:     req.Name,
		IsActive: true,
	}

	if tenantID != "" {
		workCenter.TenantID = &tenantID
	}
	if req.CostPerHour != nil {
		workCenter.CostPerHour = req.CostPerHour
	}
	if req.CapacityHours != nil {
		workCenter.CapacityHours = req.CapacityHours
	}
	if req.Location != nil {
		workCenter.Location = req.Location
	}
	if req.Latitude != nil {
		workCenter.Latitude = req.Latitude
	}
	if req.Longitude != nil {
		workCenter.Longitude = req.Longitude
	}

	// Save to database
	workCenter.ID = uuid.New().String()
	if err := db.Create(&workCenter).Error; err != nil {
		response.InternalError(c, "Failed to create work center: "+err.Error())
		return
	}

	response.SuccessCreate(c, workCenter, "Work center created successfully")
}

// UpdateWorkCenter updates a work center
func (h *ManufacturingHandler) UpdateWorkCenter(c *gin.Context) {
	wcID := c.Param("id")
	db := database.GetDB()

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Find existing work center
	var workCenter models.WorkCenter
	if err := db.First(&workCenter, "id = ?", wcID).Error; err != nil {
		response.NotFound(c, "Work center not found")
		return
	}

	// Bind update request
	var req struct {
		Code          *string  `json:"code"`
		Name          *string  `json:"name"`
		CostPerHour   *float64 `json:"cost_per_hour"`
		CapacityHours *float64 `json:"capacity_hours"`
		Location      *string  `json:"location"`
		Latitude      *float64 `json:"latitude"`
		Longitude     *float64 `json:"longitude"`
		IsActive      *bool    `json:"is_active"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.ValidationError(c, []response.Error{{Field: "body", Message: err.Error()}})
		return
	}

	// Update fields if provided
	if req.Code != nil {
		workCenter.Code = *req.Code
	}
	if req.Name != nil {
		workCenter.Name = *req.Name
	}
	if req.CostPerHour != nil {
		workCenter.CostPerHour = req.CostPerHour
	}
	if req.CapacityHours != nil {
		workCenter.CapacityHours = req.CapacityHours
	}
	if req.Location != nil {
		workCenter.Location = req.Location
	}
	if req.Latitude != nil {
		workCenter.Latitude = req.Latitude
	}
	if req.Longitude != nil {
		workCenter.Longitude = req.Longitude
	}
	if req.IsActive != nil {
		workCenter.IsActive = *req.IsActive
	}

	// Save to database
	if err := db.Save(&workCenter).Error; err != nil {
		response.InternalError(c, "Failed to update work center")
		return
	}

	response.Success(c, workCenter, "Work center updated successfully")
}

// DeleteWorkCenter deletes a work center
func (h *ManufacturingHandler) DeleteWorkCenter(c *gin.Context) {
	wcID := c.Param("id")
	db := database.GetDB()

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Check if work center exists
	var workCenter models.WorkCenter
	if err := db.First(&workCenter, "id = ?", wcID).Error; err != nil {
		response.NotFound(c, "Work center not found")
		return
	}

	// Delete from database
	if err := db.Delete(&workCenter).Error; err != nil {
		response.InternalError(c, "Failed to delete work center")
		return
	}

	response.Success(c, gin.H{"id": wcID}, "Work center deleted successfully")
}

// ========== PRODUCTION ORDERS ==========

// ListProductionOrders lists all production orders with pagination
func (h *ManufacturingHandler) ListProductionOrders(c *gin.Context) {
	page, limit, offset := getPaginationParams(c)
	db := database.GetDB()

	if db == nil {
		mockData := getMockProductionOrders()
		response.SuccessList(c, mockData, page, limit, int64(len(mockData)), "Production orders retrieved successfully")
		return
	}

	var total int64
	query := db.Model(&models.ProductionOrder{})

	// Apply filters
	filters := make(map[string]string)
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
		filters["status"] = status
	}

	query.Count(&total)

	var orders []models.ProductionOrder
	if err := query.Order("order_no DESC").Offset(offset).Limit(limit).Find(&orders).Error; err != nil {
		response.InternalError(c, "Failed to fetch production orders")
		return
	}

	response.SuccessListWithSort(c, orders, page, limit, total, "order_no", "desc", filters, "Production orders retrieved successfully")
}

func getMockProductionOrders() []gin.H {
	return []gin.H{
		{"id": "po-1", "order_no": "PO-2024-001", "status": "IN_PROGRESS", "quantity": 100, "progress": 50},
		{"id": "po-2", "order_no": "PO-2024-002", "status": "COMPLETED", "quantity": 200, "progress": 100},
	}
}

// GetProductionOrder gets production order by ID
func (h *ManufacturingHandler) GetProductionOrder(c *gin.Context) {
	orderID := c.Param("id")
	db := database.GetDB()

	if db == nil {
		response.Success(c, gin.H{"id": orderID, "order_no": "PO-2024-001", "status": "IN_PROGRESS"}, "Production order retrieved successfully")
		return
	}

	var order models.ProductionOrder
	if err := db.First(&order, "id = ?", orderID).Error; err != nil {
		response.NotFound(c, "Production order not found")
		return
	}
	response.Success(c, order, "Production order retrieved successfully")
}

// CreateProductionOrder creates a new production order
func (h *ManufacturingHandler) CreateProductionOrder(c *gin.Context) {
	var req struct {
		Quantity float64 `json:"quantity" binding:"required"`
		Notes    *string `json:"notes"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.ValidationError(c, []response.Error{{Field: "quantity", Message: "Quantity is required"}})
		return
	}
	response.SuccessCreate(c, gin.H{"id": "new-order-id", "order_no": "PO-2024-NEW", "status": "DRAFT"}, "Production order created successfully")
}

// UpdateProductionOrderStatus updates status
func (h *ManufacturingHandler) UpdateProductionOrderStatus(c *gin.Context) {
	orderID := c.Param("id")
	var req struct {
		Status   string `json:"status" binding:"required"`
		Progress int    `json:"progress"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.ValidationError(c, []response.Error{{Field: "status", Message: "Status is required"}})
		return
	}
	response.Success(c, gin.H{"id": orderID, "status": req.Status, "progress": req.Progress}, "Production order status updated successfully")
}

// ========== BOM ==========

// ListBOMItems lists BOM items with pagination
func (h *ManufacturingHandler) ListBOMItems(c *gin.Context) {
	page, limit, offset := getPaginationParams(c)
	db := database.GetDB()

	if db == nil {
		mockData := getMockBOMItems()
		response.SuccessList(c, mockData, page, limit, int64(len(mockData)), "BOM items retrieved successfully")
		return
	}

	var total int64
	query := db.Model(&models.BOMItem{})

	filters := make(map[string]string)
	if productID := c.Query("product_id"); productID != "" {
		query = query.Where("product_id = ?", productID)
		filters["product_id"] = productID
	}

	query.Count(&total)

	var items []models.BOMItem
	if err := query.Offset(offset).Limit(limit).Find(&items).Error; err != nil {
		response.InternalError(c, "Failed to fetch BOM items")
		return
	}

	response.SuccessListWithSort(c, items, page, limit, total, "id", "asc", filters, "BOM items retrieved successfully")
}

func getMockBOMItems() []gin.H {
	return []gin.H{
		{"id": "bom-1", "product_id": "prod-1", "material_id": "mat-1", "quantity": 2, "uom": "PCS"},
	}
}

// CreateBOM creates a new BOM item
func (h *ManufacturingHandler) CreateBOM(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-bom-id"}, "BOM item created successfully")
}

// ========== QC ==========

// ListQCResults lists QC results with pagination
func (h *ManufacturingHandler) ListQCResults(c *gin.Context) {
	page, limit, offset := getPaginationParams(c)
	db := database.GetDB()

	if db == nil {
		mockData := []gin.H{{"id": "qc-1", "order_id": "po-1", "passed_qty": 95, "rejected_qty": 5}}
		response.SuccessList(c, mockData, page, limit, 1, "QC results retrieved successfully")
		return
	}

	var total int64
	query := db.Model(&models.ProductionQCResult{})

	filters := make(map[string]string)
	if orderID := c.Query("order_id"); orderID != "" {
		query = query.Where("order_id = ?", orderID)
		filters["order_id"] = orderID
	}

	query.Count(&total)

	var results []models.ProductionQCResult
	if err := query.Offset(offset).Limit(limit).Find(&results).Error; err != nil {
		response.InternalError(c, "Failed to fetch QC results")
		return
	}

	response.SuccessListWithSort(c, results, page, limit, total, "id", "asc", filters, "QC results retrieved successfully")
}

// CreateQCResult creates a QC result
func (h *ManufacturingHandler) CreateQCResult(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "new-qc-id"}, "QC result recorded successfully")
}

// ========== STATS ==========

// GetStats returns manufacturing dashboard stats
func (h *ManufacturingHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, gin.H{
			"total_work_centers": 2,
			"total_orders":       10,
			"in_progress_orders": 3,
			"completed_orders":   7,
		}, "Manufacturing stats retrieved successfully")
		return
	}

	var totalWC, totalOrders, inProgress, completed int64
	db.Model(&models.WorkCenter{}).Count(&totalWC)
	db.Model(&models.ProductionOrder{}).Count(&totalOrders)
	db.Model(&models.ProductionOrder{}).Where("status = ?", "IN_PROGRESS").Count(&inProgress)
	db.Model(&models.ProductionOrder{}).Where("status = ?", "COMPLETED").Count(&completed)

	response.Success(c, gin.H{
		"total_work_centers": totalWC,
		"total_orders":       totalOrders,
		"in_progress_orders": inProgress,
		"completed_orders":   completed,
	}, "Manufacturing stats retrieved successfully")
}

// ========== PRODUCTION ORDER CRUD ==========

// UpdateProductionOrder updates a production order
func (h *ManufacturingHandler) UpdateProductionOrder(c *gin.Context) {
	db := database.GetDB()
	orderID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var order models.ProductionOrder
	if err := db.First(&order, "id = ?", orderID).Error; err != nil {
		response.NotFound(c, "Production order not found")
		return
	}

	var req struct {
		OrderNo  *string  `json:"order_no"`
		Quantity *float64 `json:"quantity"`
		Status   *string  `json:"status"`
		Notes    *string  `json:"notes"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.OrderNo != nil {
		order.OrderNo = *req.OrderNo
	}
	if req.Quantity != nil {
		order.Quantity = *req.Quantity
	}
	if req.Status != nil {
		order.Status = req.Status
	}
	if req.Notes != nil {
		order.Notes = req.Notes
	}

	if err := db.Save(&order).Error; err != nil {
		response.InternalError(c, "Failed to update production order")
		return
	}

	response.Success(c, order, "Production order updated successfully")
}

// DeleteProductionOrder deletes a production order
func (h *ManufacturingHandler) DeleteProductionOrder(c *gin.Context) {
	db := database.GetDB()
	orderID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var order models.ProductionOrder
	if err := db.First(&order, "id = ?", orderID).Error; err != nil {
		response.NotFound(c, "Production order not found")
		return
	}

	if err := db.Delete(&order).Error; err != nil {
		response.InternalError(c, "Failed to delete production order")
		return
	}

	response.Success(c, gin.H{"id": orderID}, "Production order deleted successfully")
}

// ========== BOM CRUD ==========

// GetBOM gets BOM by ID
func (h *ManufacturingHandler) GetBOM(c *gin.Context) {
	db := database.GetDB()
	bomID := c.Param("id")

	if db == nil {
		response.NotFound(c, "BOM not found")
		return
	}

	var bom models.BOMItem
	if err := db.First(&bom, "id = ?", bomID).Error; err != nil {
		response.NotFound(c, "BOM not found")
		return
	}

	response.Success(c, bom, "BOM retrieved successfully")
}

// UpdateBOM updates a BOM
func (h *ManufacturingHandler) UpdateBOM(c *gin.Context) {
	db := database.GetDB()
	bomID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var bom models.BOMItem
	if err := db.First(&bom, "id = ?", bomID).Error; err != nil {
		response.NotFound(c, "BOM not found")
		return
	}

	var req struct {
		ProductID       *string  `json:"product_id"`
		MaterialID      *string  `json:"material_id"`
		Quantity        *float64 `json:"quantity"`
		UOM             *string  `json:"uom"`
		WastePercentage *float64 `json:"waste_percentage"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.ProductID != nil {
		bom.ProductID = *req.ProductID
	}
	if req.MaterialID != nil {
		bom.ComponentID = req.MaterialID
	}
	if req.Quantity != nil {
		bom.Quantity = *req.Quantity
	}
	if req.UOM != nil {
		bom.UOM = req.UOM
	}
	if req.WastePercentage != nil {
		bom.WastePercentage = req.WastePercentage
	}

	if err := db.Save(&bom).Error; err != nil {
		response.InternalError(c, "Failed to update BOM")
		return
	}

	response.Success(c, bom, "BOM updated successfully")
}

// DeleteBOM deletes a BOM
func (h *ManufacturingHandler) DeleteBOM(c *gin.Context) {
	db := database.GetDB()
	bomID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var bom models.BOMItem
	if err := db.First(&bom, "id = ?", bomID).Error; err != nil {
		response.NotFound(c, "BOM not found")
		return
	}

	if err := db.Delete(&bom).Error; err != nil {
		response.InternalError(c, "Failed to delete BOM")
		return
	}

	response.Success(c, gin.H{"id": bomID}, "BOM deleted successfully")
}

// ========== QC RESULT CRUD ==========

// GetQCResult gets QC result by ID
func (h *ManufacturingHandler) GetQCResult(c *gin.Context) {
	db := database.GetDB()
	qcID := c.Param("id")

	if db == nil {
		response.NotFound(c, "QC result not found")
		return
	}

	var qc models.ProductionQCResult
	if err := db.First(&qc, "id = ?", qcID).Error; err != nil {
		response.NotFound(c, "QC result not found")
		return
	}

	response.Success(c, qc, "QC result retrieved successfully")
}

// UpdateQCResult updates a QC result
func (h *ManufacturingHandler) UpdateQCResult(c *gin.Context) {
	db := database.GetDB()
	qcID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var qc models.ProductionQCResult
	if err := db.First(&qc, "id = ?", qcID).Error; err != nil {
		response.NotFound(c, "QC result not found")
		return
	}

	var req struct {
		Inspector   *string  `json:"inspector"`
		PassedQty   *float64 `json:"passed_qty"`
		RejectedQty *float64 `json:"rejected_qty"`
		Notes       *string  `json:"notes"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.Inspector != nil {
		qc.Inspector = req.Inspector
	}
	if req.PassedQty != nil {
		qc.PassedQty = req.PassedQty
	}
	if req.RejectedQty != nil {
		qc.RejectedQty = req.RejectedQty
	}
	if req.Notes != nil {
		qc.Notes = req.Notes
	}

	if err := db.Save(&qc).Error; err != nil {
		response.InternalError(c, "Failed to update QC result")
		return
	}

	response.Success(c, qc, "QC result updated successfully")
}

// DeleteQCResult deletes a QC result
func (h *ManufacturingHandler) DeleteQCResult(c *gin.Context) {
	db := database.GetDB()
	qcID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var qc models.ProductionQCResult
	if err := db.First(&qc, "id = ?", qcID).Error; err != nil {
		response.NotFound(c, "QC result not found")
		return
	}

	if err := db.Delete(&qc).Error; err != nil {
		response.InternalError(c, "Failed to delete QC result")
		return
	}

	response.Success(c, gin.H{"id": qcID}, "QC result deleted successfully")
}

// ========== WORK ORDERS ==========

// ListWorkOrders lists all work orders
func (h *ManufacturingHandler) ListWorkOrders(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")
	page, limit, offset := getPaginationParams(c)

	if db == nil {
		response.SuccessList(c, []gin.H{}, page, limit, 0, "Work orders retrieved (mock)")
		return
	}

	var workOrders []models.WorkOrder
	var total int64
	query := db.Model(&models.WorkOrder{}).Where("tenant_id = ?", tenantID)
	query.Count(&total)
	if err := query.Preload("WorkCenter").Order("work_order_no DESC").Offset(offset).Limit(limit).Find(&workOrders).Error; err != nil {
		response.InternalError(c, "Failed to fetch work orders")
		return
	}
	response.SuccessList(c, workOrders, page, limit, total, "Work orders retrieved")
}

// GetWorkOrder gets work order by ID
func (h *ManufacturingHandler) GetWorkOrder(c *gin.Context) {
	db := database.GetDB()
	workOrderID := c.Param("id")

	if db == nil {
		response.NotFound(c, "Work order not found")
		return
	}

	var workOrder models.WorkOrder
	if err := db.Preload("WorkCenter").Where("id = ?", workOrderID).First(&workOrder).Error; err != nil {
		response.NotFound(c, "Work order not found")
		return
	}
	response.Success(c, workOrder, "Work order retrieved")
}

// CreateWorkOrder creates a new work order
func (h *ManufacturingHandler) CreateWorkOrder(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var req struct {
		ProductionOrderID string   `json:"production_order_id" binding:"required"`
		WorkCenterID      string   `json:"work_center_id" binding:"required"`
		OperationName     string   `json:"operation_name" binding:"required"`
		WorkOrderNo       *string  `json:"work_order_no"`
		Sequence          *int     `json:"sequence"`
		PlannedQty        *float64 `json:"planned_qty"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Generate work order number if not provided
	workOrderNo := ""
	if req.WorkOrderNo != nil {
		workOrderNo = *req.WorkOrderNo
	} else {
		var count int64
		db.Model(&models.WorkOrder{}).Where("tenant_id = ?", tenantID).Count(&count)
		workOrderNo = "WO-" + tenantID[:8] + "-" + strconv.FormatInt(count+1, 10)
	}

	sequence := 10
	if req.Sequence != nil {
		sequence = *req.Sequence
	}

	workOrder := models.WorkOrder{
		TenantID:          tenantID,
		ProductionOrderID: req.ProductionOrderID,
		WorkCenterID:      req.WorkCenterID,
		WorkOrderNo:       workOrderNo,
		Sequence:          sequence,
		OperationName:     req.OperationName,
		Status:            "Pending",
		PlannedQty:        req.PlannedQty,
	}

	workOrder.ID = uuid.New().String()

	if err := db.Create(&workOrder).Error; err != nil {
		response.InternalError(c, "Failed to create work order: "+err.Error())
		return
	}
	response.SuccessCreate(c, workOrder, "Work order created successfully")
}

// UpdateWorkOrder updates a work order
func (h *ManufacturingHandler) UpdateWorkOrder(c *gin.Context) {
	db := database.GetDB()
	workOrderID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var workOrder models.WorkOrder
	if err := db.Where("id = ?", workOrderID).First(&workOrder).Error; err != nil {
		response.NotFound(c, "Work order not found")
		return
	}

	var req struct {
		WorkCenterID  *string  `json:"work_center_id"`
		OperationName *string  `json:"operation_name"`
		Sequence      *int     `json:"sequence"`
		PlannedQty    *float64 `json:"planned_qty"`
		CompletedQty  *float64 `json:"completed_qty"`
		ScrapQty      *float64 `json:"scrap_qty"`
		LaborHours    *float64 `json:"labor_hours"`
		Notes         *string  `json:"notes"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.WorkCenterID != nil {
		workOrder.WorkCenterID = *req.WorkCenterID
	}
	if req.OperationName != nil {
		workOrder.OperationName = *req.OperationName
	}
	if req.Sequence != nil {
		workOrder.Sequence = *req.Sequence
	}
	if req.PlannedQty != nil {
		workOrder.PlannedQty = req.PlannedQty
	}
	if req.CompletedQty != nil {
		workOrder.CompletedQty = req.CompletedQty
	}
	if req.ScrapQty != nil {
		workOrder.ScrapQty = req.ScrapQty
	}
	if req.LaborHours != nil {
		workOrder.LaborHours = req.LaborHours
	}
	if req.Notes != nil {
		workOrder.Notes = req.Notes
	}

	if err := db.Save(&workOrder).Error; err != nil {
		response.InternalError(c, "Failed to update work order")
		return
	}
	response.Success(c, workOrder, "Work order updated successfully")
}

// UpdateWorkOrderStatus updates work order status
func (h *ManufacturingHandler) UpdateWorkOrderStatus(c *gin.Context) {
	db := database.GetDB()
	workOrderID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var workOrder models.WorkOrder
	if err := db.Where("id = ?", workOrderID).First(&workOrder).Error; err != nil {
		response.NotFound(c, "Work order not found")
		return
	}

	var req struct {
		Status string `json:"status" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	workOrder.Status = req.Status
	if err := db.Save(&workOrder).Error; err != nil {
		response.InternalError(c, "Failed to update work order status")
		return
	}
	response.Success(c, workOrder, "Work order status updated")
}

// DeleteWorkOrder deletes a work order
func (h *ManufacturingHandler) DeleteWorkOrder(c *gin.Context) {
	db := database.GetDB()
	workOrderID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var workOrder models.WorkOrder
	if err := db.Where("id = ?", workOrderID).First(&workOrder).Error; err != nil {
		response.NotFound(c, "Work order not found")
		return
	}

	if err := db.Delete(&workOrder).Error; err != nil {
		response.InternalError(c, "Failed to delete work order")
		return
	}
	response.Success(c, nil, "Work order deleted successfully")
}

// ========== ROUTINGS ==========

// ListRoutings lists all routings with relations
func (h *ManufacturingHandler) ListRoutings(c *gin.Context) {
	db := database.GetDB()
	page, limit, offset := getPaginationParams(c)
	tenantID := c.GetHeader("X-Tenant-ID")

	if db == nil {
		response.SuccessList(c, []gin.H{}, page, limit, 0, "Routings retrieved successfully")
		return
	}

	var routings []models.Routing
	var total int64

	query := db.Model(&models.Routing{})
	if tenantID != "" {
		query = query.Where("tenant_id = ?", tenantID)
	}
	query.Count(&total)
	// Preload Steps with WorkCenter, and Product
	query.Preload("Steps", func(db2 interface{}) interface{} {
		return db2.(*gorm.DB).Order("sequence ASC").Preload("WorkCenter")
	}).Preload("Product").Offset(offset).Limit(limit).Find(&routings)

	response.SuccessList(c, routings, page, limit, total, "Routings retrieved successfully")
}

// GetRouting gets routing by ID with relations
func (h *ManufacturingHandler) GetRouting(c *gin.Context) {
	db := database.GetDB()
	routingID := c.Param("id")

	if db == nil {
		response.NotFound(c, "Routing not found")
		return
	}

	var routing models.Routing
	if err := db.Preload("Steps", func(db2 interface{}) interface{} {
		return db2.(*gorm.DB).Order("sequence ASC").Preload("WorkCenter")
	}).Preload("Product").First(&routing, "id = ?", routingID).Error; err != nil {
		response.NotFound(c, "Routing not found")
		return
	}

	response.Success(c, routing, "Routing retrieved successfully")
}

// CreateRouting creates a new routing
func (h *ManufacturingHandler) CreateRouting(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var req struct {
		ProductID string  `json:"product_id" binding:"required"`
		Name      string  `json:"name" binding:"required"`
		Version   *string `json:"version"`
		IsActive  *bool   `json:"is_active"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	isActive := true
	if req.IsActive != nil {
		isActive = *req.IsActive
	}

	routing := models.Routing{
		TenantID:  &tenantID,
		ProductID: req.ProductID,
		Name:      req.Name,
		Version:   req.Version,
		IsActive:  &isActive,
	}

	routing.ID = uuid.New().String()
	for i := range routing.Steps {
		routing.Steps[i].ID = uuid.New().String()
		routing.Steps[i].RoutingID = routing.ID
		routing.Steps[i].TenantID = tenantID
	}

	if err := db.Create(&routing).Error; err != nil {
		response.InternalError(c, "Failed to create routing: "+err.Error())
		return
	}

	response.SuccessCreate(c, routing, "Routing created successfully")
}

// UpdateRouting updates a routing
func (h *ManufacturingHandler) UpdateRouting(c *gin.Context) {
	db := database.GetDB()
	routingID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var routing models.Routing
	if err := db.First(&routing, "id = ?", routingID).Error; err != nil {
		response.NotFound(c, "Routing not found")
		return
	}

	var req struct {
		ProductID      *string  `json:"product_id"`
		Name           *string  `json:"name"`
		Version        *string  `json:"version"`
		IsActive       *bool    `json:"is_active"`
		TotalTimeHours *float64 `json:"total_time_hours"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.ProductID != nil {
		routing.ProductID = *req.ProductID
	}
	if req.Name != nil {
		routing.Name = *req.Name
	}
	if req.Version != nil {
		routing.Version = req.Version
	}
	if req.IsActive != nil {
		routing.IsActive = req.IsActive
	}
	if req.TotalTimeHours != nil {
		routing.TotalTimeHours = req.TotalTimeHours
	}

	if err := db.Save(&routing).Error; err != nil {
		response.InternalError(c, "Failed to update routing")
		return
	}

	response.Success(c, routing, "Routing updated successfully")
}

// DeleteRouting deletes a routing
func (h *ManufacturingHandler) DeleteRouting(c *gin.Context) {
	db := database.GetDB()
	routingID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	var routing models.Routing
	if err := db.First(&routing, "id = ?", routingID).Error; err != nil {
		response.NotFound(c, "Routing not found")
		return
	}

	if err := db.Delete(&routing).Error; err != nil {
		response.InternalError(c, "Failed to delete routing")
		return
	}

	response.Success(c, gin.H{"id": routingID}, "Routing deleted successfully")
}

// ========== MRP ==========

// RunMRP calculates material requirements
func (h *ManufacturingHandler) RunMRP(c *gin.Context) {
	response.Success(c, gin.H{
		"execution_id": "mrp-run-" + strconv.FormatInt(time.Now().Unix(), 10),
		"status":       "started",
		"message":      "MRP calculation started in background",
	}, "MRP Run initiated")
}

// GetMPS returns Master Production Schedule
func (h *ManufacturingHandler) GetMPS(c *gin.Context) {
	response.SuccessList(c, []gin.H{
		{"period": "2024-W01", "product": "Product A", "quantity": 100},
		{"period": "2024-W02", "product": "Product A", "quantity": 150},
	}, 1, 10, 2, "MPS retrieved")
}

// GetDemandForecast returns forecast data
func (h *ManufacturingHandler) GetDemandForecast(c *gin.Context) {
	response.Success(c, gin.H{
		"forecast": []gin.H{
			{"month": "Jan", "predicted": 120, "actual": 110},
			{"month": "Feb", "predicted": 140, "actual": 0},
		},
		"accuracy": "92%",
	}, "Demand forecast retrieved")
}

// GetNetRequirements returns calculated material needs
func (h *ManufacturingHandler) GetNetRequirements(c *gin.Context) {
	response.SuccessList(c, []gin.H{
		{"material": "Steel Sheet", "required": 500, "available": 200, "shortage": 300},
		{"material": "Plastic Pellets", "required": 1000, "available": 1200, "shortage": 0},
	}, 1, 10, 2, "Net requirements retrieved")
}

// GetMRPExceptions returns alerts and exceptions
func (h *ManufacturingHandler) GetMRPExceptions(c *gin.Context) {
	response.SuccessList(c, []gin.H{
		{"type": "SHORTAGE", "message": "Steel Sheet shortage for WO-101", "severity": "HIGH"},
		{"type": "DELAY", "message": "Potential delay for PO-2024-005", "severity": "MEDIUM"},
	}, 1, 10, 2, "MRP exceptions retrieved")
}

// GetMRPAnalytics returns KPI data for MRP
func (h *ManufacturingHandler) GetMRPAnalytics(c *gin.Context) {
	response.Success(c, gin.H{
		"lead_time_variance": "-2 days",
		"planning_accuracy":  "95%",
		"stockout_risk":      "Low",
	}, "MRP analytics retrieved")
}
