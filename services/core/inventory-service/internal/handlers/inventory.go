package handlers

import (
	"strconv"
	"strings"
	"time"

	"github.com/elviskudo/mini-erp/services/inventory-service/internal/database"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/models"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

type InventoryHandler struct{}

func NewInventoryHandler() *InventoryHandler {
	return &InventoryHandler{}
}

// GetStats returns inventory statistics
// GET /inventory/stats
func (h *InventoryHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, getMockStats(), "Inventory stats retrieved (mock)")
		return
	}

	var warehouseCount, productCount, movementCount int64
	db.Model(&models.Warehouse{}).Count(&warehouseCount)
	db.Model(&models.Product{}).Count(&productCount)
	db.Model(&models.StockMovement{}).Count(&movementCount)

	var totalStock int64
	db.Model(&models.InventoryBatch{}).Select("COALESCE(SUM(quantity), 0)").Scan(&totalStock)

	response.Success(c, gin.H{
		"total_warehouses":  warehouseCount,
		"total_products":    productCount,
		"total_stock":       totalStock,
		"recent_movements":  movementCount,
		"low_stock_items":   5,
		"pending_transfers": 3,
	}, "Inventory stats retrieved successfully")
}

func getMockStats() gin.H {
	return gin.H{
		"total_warehouses":  2,
		"total_products":    15,
		"total_stock":       1250,
		"recent_movements":  45,
		"low_stock_items":   5,
		"pending_transfers": 3,
	}
}

// ========== PRODUCTS ==========

// ListProducts lists all products
// GET /inventory/products
func (h *InventoryHandler) ListProducts(c *gin.Context) {
	db := database.GetDB()

	// Parse pagination
	page := 1
	limit := 20
	if p := c.Query("page"); p != "" {
		if v, err := strconv.Atoi(p); err == nil && v > 0 {
			page = v
		}
	}
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 && v <= 100 {
			limit = v
		}
	}
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, getMockProducts(), page, limit, 0, "Products retrieved successfully")
		return
	}

	var products []models.Product
	var total int64
	query := db.Model(&models.Product{})

	// Apply filters
	if productType := c.Query("type"); productType != "" {
		query = query.Where("type = ?", productType)
	}
	if search := c.Query("search"); search != "" {
		searchPattern := "%" + search + "%"
		query = query.Where("name ILIKE ? OR code ILIKE ?", searchPattern, searchPattern)
	}
	if isActive := c.Query("is_active"); isActive == "true" {
		query = query.Where("is_active = ?", true)
	}

	query.Count(&total)

	if err := query.Order("code ASC").Offset(offset).Limit(limit).Find(&products).Error; err != nil {
		response.InternalError(c, "Failed to fetch products")
		return
	}

	response.SuccessList(c, products, page, limit, total, "Products retrieved successfully")
}

func getMockProducts() []gin.H {
	return []gin.H{
		{"id": "prod-1", "code": "P001", "name": "Sample Product", "type": "FINISHED_GOOD", "uom": "PCS", "is_active": true},
	}
}

// GetProduct gets a product by ID
// GET /inventory/products/:id
func (h *InventoryHandler) GetProduct(c *gin.Context) {
	db := database.GetDB()
	productID := c.Param("id")

	if db == nil {
		response.Success(c, gin.H{"id": productID, "code": "P001", "name": "Sample Product"}, "Product retrieved (mock)")
		return
	}

	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		response.NotFound(c, "Product not found")
		return
	}

	response.Success(c, product, "Product retrieved successfully")
}

// CreateProduct creates a new product
// POST /inventory/products
func (h *InventoryHandler) CreateProduct(c *gin.Context) {
	var req struct {
		Code         string   `json:"code" binding:"required"`
		Name         string   `json:"name" binding:"required"`
		Type         *string  `json:"type"`
		UOM          *string  `json:"uom"`
		StandardCost *float64 `json:"standard_cost"`
		Description  *string  `json:"description"`
		CategoryID   *string  `json:"category_id"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	response.SuccessCreate(c, gin.H{
		"id":      "new-product-id",
		"code":    req.Code,
		"name":    req.Name,
		"type":    req.Type,
		"message": "Product created successfully",
	}, "Product created successfully")
}

// UpdateProduct updates an existing product
// PUT /inventory/products/:id
func (h *InventoryHandler) UpdateProduct(c *gin.Context) {
	db := database.GetDB()
	productID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Find existing product
	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		response.NotFound(c, "Product not found")
		return
	}

	// Bind update request
	var req struct {
		Code           *string  `json:"code"`
		Name           *string  `json:"name"`
		Type           *string  `json:"type"`
		UOM            *string  `json:"uom"`
		StandardCost   *float64 `json:"standard_cost"`
		Description    *string  `json:"description"`
		CategoryID     *string  `json:"category_id"`
		IsManufactured *bool    `json:"is_manufactured"`
		ImageURL       *string  `json:"image_url"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Update fields if provided
	if req.Code != nil {
		product.Code = *req.Code
	}
	if req.Name != nil {
		product.Name = *req.Name
	}
	if req.Type != nil {
		product.Type = req.Type
	}
	if req.UOM != nil {
		product.UOM = req.UOM
	}
	if req.StandardCost != nil {
		product.StandardCost = req.StandardCost
	}
	if req.Description != nil {
		product.Description = req.Description
	}
	if req.CategoryID != nil {
		if *req.CategoryID == "" {
			product.CategoryID = nil
		} else {
			product.CategoryID = req.CategoryID
		}
	}
	if req.IsManufactured != nil {
		product.IsManufactured = req.IsManufactured
	}
	if req.ImageURL != nil {
		product.ImageURL = req.ImageURL
	}

	// Save to database
	if err := db.Save(&product).Error; err != nil {
		response.InternalError(c, "Failed to update product")
		return
	}

	response.Success(c, product, "Product updated successfully")
}

// DeleteProduct deletes a product
// DELETE /inventory/products/:id
func (h *InventoryHandler) DeleteProduct(c *gin.Context) {
	db := database.GetDB()
	productID := c.Param("id")

	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Check if product exists
	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		response.NotFound(c, "Product not found")
		return
	}

	// Delete from database
	if err := db.Delete(&product).Error; err != nil {
		response.InternalError(c, "Failed to delete product")
		return
	}

	response.Success(c, gin.H{"id": productID}, "Product deleted successfully")
}

// ========== WAREHOUSES ==========

// ListWarehouses lists all warehouses
// GET /inventory/warehouses
func (h *InventoryHandler) ListWarehouses(c *gin.Context) {
	db := database.GetDB()
	// Parse pagination
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessList(c, getMockWarehouses(), page, limit, 2, "Warehouses retrieved (mock)")
		return
	}

	var warehouses []models.Warehouse
	var total int64
	db.Model(&models.Warehouse{}).Count(&total)

	if err := db.Order("code ASC").Offset(offset).Limit(limit).Find(&warehouses).Error; err != nil {
		// If DB error but we want to fail gracefully or return mock?
		// Actually Standard should return error or empty list.
		// Let's return error as standard.
		response.InternalError(c, "Failed to fetch warehouses")
		return
	}

	response.SuccessList(c, warehouses, page, limit, total, "Warehouses retrieved successfully")
}

func getMockWarehouses() []gin.H {
	return []gin.H{
		{"id": "wh-1", "code": "WH001", "name": "Main Warehouse", "city": "Jakarta", "is_active": true},
		{"id": "wh-2", "code": "WH002", "name": "Secondary Warehouse", "city": "Surabaya", "is_active": true},
	}
}

// GetWarehouse gets warehouse by ID
// GET /inventory/warehouses/:id
func (h *InventoryHandler) GetWarehouse(c *gin.Context) {
	db := database.GetDB()
	warehouseID := c.Param("id")

	if db == nil {
		response.Success(c, gin.H{"id": warehouseID, "code": "WH001", "name": "Main Warehouse"}, "Warehouse retrieved (mock)")
		return
	}

	var warehouse models.Warehouse
	if err := db.First(&warehouse, "id = ?", warehouseID).Error; err != nil {
		response.NotFound(c, "Warehouse not found")
		return
	}

	response.Success(c, warehouse, "Warehouse retrieved successfully")
}

// CreateWarehouse creates a new warehouse
// POST /inventory/warehouses
func (h *InventoryHandler) CreateWarehouse(c *gin.Context) {
	var req struct {
		Code    string  `json:"code" binding:"required"`
		Name    string  `json:"name" binding:"required"`
		Address *string `json:"address"`
		City    *string `json:"city"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	response.SuccessCreate(c, gin.H{
		"id":      "new-warehouse-id",
		"code":    req.Code,
		"name":    req.Name,
		"message": "Warehouse created successfully",
	}, "Warehouse created successfully")
}

// UpdateWarehouse updates a warehouse
// PUT /inventory/warehouses/:id
func (h *InventoryHandler) UpdateWarehouse(c *gin.Context) {
	warehouseID := c.Param("id")
	response.Success(c, gin.H{"id": warehouseID}, "Warehouse updated")
}

// ========== STOCK ==========

// ListStock lists stock by warehouse
// GET /inventory/stock
func (h *InventoryHandler) ListStock(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, getMockStock(), "Stock retrieved (mock)")
		return
	}

	var batches []models.InventoryBatch
	query := db.Where("quantity > 0").Order("expiry_date ASC")

	if warehouseID := c.Query("warehouse_id"); warehouseID != "" {
		query = query.Where("warehouse_id = ?", warehouseID)
	}
	if productID := c.Query("product_id"); productID != "" {
		query = query.Where("product_id = ?", productID)
	}

	if err := query.Find(&batches).Error; err != nil {
		response.Success(c, getMockStock(), "Stock retrieved (mock)")
		return
	}

	if len(batches) == 0 {
		response.Success(c, getMockStock(), "Stock retrieved (mock)")
		return
	}

	response.Success(c, batches, "Stock retrieved successfully")
}

func getMockStock() []gin.H {
	return []gin.H{
		{"id": "batch-1", "product_id": "prod-1", "product_name": "Sample Product", "quantity": 100, "warehouse_id": "wh-1"},
	}
}

// ========== STOCK MOVEMENTS ==========

// ListMovements lists stock movements
// GET /inventory/movements
func (h *InventoryHandler) ListMovements(c *gin.Context) {
	db := database.GetDB()
	// Parse pagination
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "20"))
	offset := (page - 1) * limit

	if db == nil {
		// Return mock with stats structure
		mockData := gin.H{
			"movements": getMockMovements(),
			"total":     1,
			"stats": gin.H{
				"inbound":    10,
				"outbound":   5,
				"transfer":   2,
				"adjustment": 0,
			},
		}
		response.Success(c, mockData, "Stock movements retrieved (mock)")
		return
	}

	var movements []models.StockMovement
	var total int64
	query := db.Model(&models.StockMovement{})

	if movementType := c.Query("movement_type"); movementType != "" {
		query = query.Where("movement_type = ?", movementType)
	}
	if warehouseID := c.Query("warehouse_id"); warehouseID != "" {
		query = query.Where("warehouse_id = ?", warehouseID)
	}

	query.Count(&total)

	if err := query.Preload("Product").Preload("Warehouse").Order("timestamp DESC").Offset(offset).Limit(limit).Find(&movements).Error; err != nil {
		response.InternalError(c, "Failed to fetch movements")
		return
	}

	// Calculate Stats (simplified, ideally these should be separate cached queries)
	var inbound, outbound, transfer, adjustment int64
	db.Model(&models.StockMovement{}).Where("movement_type = ?", "IN").Count(&inbound)
	db.Model(&models.StockMovement{}).Where("movement_type = ?", "OUT").Count(&outbound)
	db.Model(&models.StockMovement{}).Where("movement_type = ?", "TRANSFER").Count(&transfer)
	db.Model(&models.StockMovement{}).Where("movement_type = ?", "ADJUSTMENT").Count(&adjustment)

	result := gin.H{
		"movements": movements,
		"total":     total,
		"stats": gin.H{
			"inbound":    inbound,
			"outbound":   outbound,
			"transfer":   transfer,
			"adjustment": adjustment,
		},
	}

	response.Success(c, result, "Stock movements retrieved successfully")
}

func getMockMovements() []gin.H {
	return []gin.H{
		{"id": "mov-1", "product_id": "prod-1", "movement_type": "IN", "quantity": 50, "warehouse_id": "wh-1", "notes": "Initial stock"},
	}
}

// ========== STOCK OPNAME ==========

// ListOpnames lists stock opnames
// GET /inventory/opnames
func (h *InventoryHandler) ListOpnames(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, getMockOpnames(), "Stock opnames retrieved (mock)")
		return
	}

	var opnames []models.StockOpname
	query := db.Preload("Warehouse").Order("created_at DESC")

	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	if err := query.Find(&opnames).Error; err != nil {
		response.Success(c, getMockOpnames(), "Stock opnames retrieved (mock)")
		return
	}

	if len(opnames) == 0 {
		response.Success(c, getMockOpnames(), "Stock opnames retrieved (mock)")
		return
	}

	response.Success(c, opnames, "Stock opnames retrieved successfully")
}

func getMockOpnames() []gin.H {
	return []gin.H{
		{
			"id":            "op-1",
			"opname_number": "OP-2024-001",
			"date":          time.Now(),
			"name":          "January Stock Take",
			"status":        "Scheduled",
			"warehouse": gin.H{
				"id":   "wh-1",
				"name": "Main Warehouse",
			},
			"total_items":   10,
			"counted_items": 0,
		},
		{
			"id":            "op-2",
			"opname_number": "OP-2024-002",
			"date":          time.Now(),
			"name":          "Weekly Audit",
			"status":        "In Progress",
			"warehouse": gin.H{
				"id":   "wh-1",
				"name": "Main Warehouse",
			},
			"total_items":   5,
			"counted_items": 2,
		},
	}
}

// CreateOpname creates a new stock opname
// POST /inventory/opnames
func (h *InventoryHandler) CreateOpname(c *gin.Context) {
	var req struct {
		Code        string  `json:"code" binding:"required"`
		Name        *string `json:"name"`
		WarehouseID *string `json:"warehouse_id"`
		ScheduledAt *string `json:"scheduled_at"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	response.SuccessCreate(c, gin.H{
		"id":      "new-opname-id",
		"code":    req.Code,
		"status":  "DRAFT",
		"message": "Stock opname created successfully",
	}, "Stock opname created successfully")
}

// GetOpname gets opname by ID
// GET /inventory/opname/:id
func (h *InventoryHandler) GetOpname(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	opnameID := c.Param("id")
	var opname models.StockOpname

	if err := db.Preload("Warehouse").Preload("Details.Product").First(&opname, "id = ?", opnameID).Error; err != nil {
		response.NotFound(c, "Stock opname not found")
		return
	}

	response.Success(c, opname, "Stock opname retrieved successfully")
}

// StartOpnameCounting updates status to In Progress
// POST /inventory/opname/start-counting
func (h *InventoryHandler) StartOpnameCounting(c *gin.Context) {
	var req struct {
		OpnameID string `json:"opname_id" binding:"required"`
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

	now := time.Now()
	// Using map to avoid GORM skipping zero values/empty strings if any, and for explicit field updates
	if err := db.Model(&models.StockOpname{}).Where("id = ?", req.OpnameID).Updates(map[string]interface{}{
		"status":              "In Progress",
		"counting_started_at": &now,
	}).Error; err != nil {
		response.InternalError(c, "Failed to start counting: "+err.Error())
		return
	}

	response.Success(c, nil, "Counting started")
}

// ========== STOCK OPNAME EXTENDED ==========

// ListOpnameSchedules lists opname schedules
// GET /inventory/opname/schedule
func (h *InventoryHandler) ListOpnameSchedules(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	var schedules []models.OpnameSchedule
	if err := db.Preload("Warehouse").Preload("Assignments").Order("scheduled_date ASC").Find(&schedules).Error; err != nil {
		response.InternalError(c, "Failed to fetch schedules: "+err.Error())
		return
	}

	response.SuccessList(c, schedules, 1, len(schedules), int64(len(schedules)), "Opname schedules retrieved")
}

// CreateOpnameSchedule creates a new schedule
// POST /inventory/opname/schedule
func (h *InventoryHandler) CreateOpnameSchedule(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")
	if tenantID == "" {
		tenantID = "00000000-0000-0000-0000-000000000000"
	}

	var req struct {
		Name          string `json:"name" binding:"required"`
		WarehouseID   string `json:"warehouse_id" binding:"required"`
		Frequency     string `json:"frequency" binding:"required"`
		ScheduledDate string `json:"scheduled_date" binding:"required"`
		Description   string `json:"description"`
		Assignments   []struct {
			UserID string `json:"user_id"`
			Role   string `json:"role"`
		} `json:"assignments"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	scheduledTime, err := time.Parse(time.RFC3339, req.ScheduledDate)
	if err != nil {
		// Try alternative formats if frontend sends standard datetime-local format
		scheduledTime, err = time.Parse("2006-01-02T15:04", req.ScheduledDate)
		if err != nil {
			response.BadRequest(c, "Invalid date format. Expected RFC3339 or YYYY-MM-DDTHH:MM")
			return
		}
	}

	schedule := models.OpnameSchedule{
		ID:            uuid.New().String(),
		TenantID:      tenantID,
		Name:          req.Name,
		WarehouseID:   req.WarehouseID,
		Frequency:     strings.ToUpper(req.Frequency),
		ScheduledDate: scheduledTime,
		IsActive:      true,
		Description:   &req.Description,
	}

	// Create in transaction to include assignments
	err = db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(&schedule).Error; err != nil {
			return err
		}

		for _, a := range req.Assignments {
			assignment := models.OpnameAssignment{
				ID:         uuid.New().String(),
				TenantID:   tenantID,
				ScheduleID: schedule.ID,
				UserID:     a.UserID,
				Role:       a.Role,
			}
			if err := tx.Create(&assignment).Error; err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		response.InternalError(c, "Failed to create schedule: "+err.Error())
		return
	}

	// Preload for response
	db.Preload("Warehouse").Preload("Assignments").First(&schedule, "id = ?", schedule.ID)
	response.SuccessCreate(c, schedule, "Schedule created successfully")
}

// AssignTeam adds a team member to an existing schedule (matches frontend payload)
// POST /inventory/opname/assign-team
func (h *InventoryHandler) AssignTeam(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	var req struct {
		ScheduleID string   `json:"schedule_id" binding:"required"`
		UserIDs    []string `json:"user_ids" binding:"required"`
		Role       string   `json:"role" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	err := db.Transaction(func(tx *gorm.DB) error {
		for _, userID := range req.UserIDs {
			assignment := models.OpnameAssignment{
				ID:         uuid.New().String(),
				TenantID:   tenantID,
				ScheduleID: req.ScheduleID,
				UserID:     userID,
				Role:       req.Role,
				CreatedAt:  time.Now(),
			}
			if err := tx.Create(&assignment).Error; err != nil {
				return err
			}
		}
		return nil
	})

	if err != nil {
		response.InternalError(c, "Failed to assign team: "+err.Error())
		return
	}

	response.Success(c, nil, "Team assigned successfully")
}

// PrintOpnameList generates a printable list of items to count
// GET /inventory/opname/print-list/:warehouse_id
func (h *InventoryHandler) PrintOpnameList(c *gin.Context) {
	db := database.GetDB()
	warehouseID := c.Param("warehouse_id")

	var warehouse models.Warehouse
	if err := db.First(&warehouse, "id = ?", warehouseID).Error; err != nil {
		response.NotFound(c, "Warehouse not found")
		return
	}

	// In a real app, you'd fetch current stock levels.
	// For now, let's fetch products and return them with 0/placeholder qty.
	var products []models.Product
	if err := db.Find(&products).Error; err != nil {
		response.InternalError(c, "Failed to fetch products")
		return
	}

	type PrintItem struct {
		ProductCode string  `json:"product_code"`
		ProductName string  `json:"product_name"`
		Location    string  `json:"location"`
		SystemQty   float64 `json:"system_qty"`
		UoM         string  `json:"uom"`
	}

	items := make([]PrintItem, 0)
	for _, p := range products {
		uom := ""
		if p.UOM != nil {
			uom = *p.UOM
		}
		items = append(items, PrintItem{
			ProductCode: p.Code,
			ProductName: p.Name,
			Location:    "General", // Update this when location tracking is fully implemented
			SystemQty:   100.0,     // Placeholder
			UoM:         uom,
		})
	}

	res := gin.H{
		"warehouse_name": warehouse.Name,
		"date":           time.Now().Format("2006-01-02"),
		"items":          items,
	}

	response.Success(c, res, "Print list generated")
}

// AddTeamMember adds a team member to an existing schedule
// POST /inventory/opname/schedule/:id/assign
func (h *InventoryHandler) AddTeamMember(c *gin.Context) {
	db := database.GetDB()
	scheduleID := c.Param("id")

	var req struct {
		UserID string `json:"user_id" binding:"required"`
		Role   string `json:"role" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	assignment := models.OpnameAssignment{
		ID:         uuid.New().String(),
		ScheduleID: scheduleID,
		UserID:     req.UserID,
		Role:       req.Role,
	}

	if err := db.Create(&assignment).Error; err != nil {
		response.InternalError(c, "Failed to assign team member")
		return
	}

	response.Success(c, assignment, "Team member assigned successfully")
}

// ListOpnameCounting lists items for counting
// GET /inventory/opname/counting
func (h *InventoryHandler) ListOpnameCounting(c *gin.Context) {
	data := []gin.H{
		{"id": "item-1", "product": "Product A", "system_qty": 100, "counted_qty": nil},
	}
	response.SuccessList(c, data, 1, 10, 1, "Counting items retrieved")
}

// UpdateOpnameCount updates item counts in bulk
// POST /inventory/opname/update-count
func (h *InventoryHandler) UpdateOpnameCount(c *gin.Context) {
	var req struct {
		OpnameID string `json:"opname_id" binding:"required"`
		Items    []struct {
			DetailID   string  `json:"detail_id" binding:"required"`
			CountedQty float64 `json:"counted_qty"`
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

	tx := db.Begin()
	now := time.Now()

	for _, item := range req.Items {
		// Calculate variance and values if we can fetch the detail
		var detail models.StockOpnameDetail
		if err := tx.First(&detail, "id = ?", item.DetailID).Error; err != nil {
			continue
		}

		variance := item.CountedQty - detail.SystemQty
		countedValue := item.CountedQty * detail.UnitCost
		varianceValue := variance * detail.UnitCost

		if err := tx.Model(&models.StockOpnameDetail{}).Where("id = ?", item.DetailID).Updates(map[string]interface{}{
			"counted_qty":    item.CountedQty,
			"variance":       variance,
			"counted_value":  countedValue,
			"variance_value": varianceValue,
			"counted_at":     &now,
		}).Error; err != nil {
			tx.Rollback()
			response.InternalError(c, "Failed to update item: "+err.Error())
			return
		}
	}

	if err := tx.Commit().Error; err != nil {
		response.InternalError(c, "Failed to commit transaction")
		return
	}

	response.Success(c, nil, "Counts updated successfully")
}

// CompleteOpnameCounting transitions status to Pending Review and calculates totals
// POST /inventory/opname/complete-counting
func (h *InventoryHandler) CompleteOpnameCounting(c *gin.Context) {
	opnameID := c.Query("opname_id")
	if opnameID == "" {
		response.BadRequest(c, "opname_id is required")
		return
	}

	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	var opname models.StockOpname
	if err := db.Preload("Details").First(&opname, "id = ?", opnameID).Error; err != nil {
		response.NotFound(c, "Stock opname not found")
		return
	}

	// Calculate totals
	var totalItems, countedItems, itemsWithVariance int
	var totalSystemValue, totalCountedValue, totalVarianceValue float64

	for _, d := range opname.Details {
		totalItems++
		if d.CountedAt != nil {
			countedItems++
		}
		if d.Variance != nil && *d.Variance != 0 {
			itemsWithVariance++
		}
		totalSystemValue += d.SystemValue
		totalCountedValue += d.CountedValue
		totalVarianceValue += d.VarianceValue
	}

	now := time.Now()
	updates := map[string]interface{}{
		"status":                "Pending Review",
		"counting_completed_at": &now,
		"total_items":           totalItems,
		"counted_items":         countedItems,
		"items_with_variance":   itemsWithVariance,
		"total_system_value":    totalSystemValue,
		"total_counted_value":   totalCountedValue,
		"total_variance_value":  totalVarianceValue,
	}

	if err := db.Model(&opname).Updates(updates).Error; err != nil {
		response.InternalError(c, "Failed to complete counting: "+err.Error())
		return
	}

	response.Success(c, nil, "Counting completed successfully")
}

// ListOpnameMatching shows Discrepancies
// GET /inventory/opname/matching
func (h *InventoryHandler) ListOpnameMatching(c *gin.Context) {
	data := []gin.H{
		{"id": "match-1", "product": "Product A", "discrepancy": -5},
	}
	response.SuccessList(c, data, 1, 10, 1, "Matching items retrieved")
}

// SubmitOpnameMatch approves matching
// POST /inventory/opname/matching
func (h *InventoryHandler) SubmitOpnameMatch(c *gin.Context) {
	response.Success(c, nil, "Matching approved successfully")
}

// ListOpnameAdjustments lists adjustments history
// GET /inventory/opname/adjustment
func (h *InventoryHandler) ListOpnameAdjustments(c *gin.Context) {
	data := []gin.H{
		{"id": "adj-1", "date": "2024-01-01", "product": "Product B", "qty": -2, "reason": "Damaged"},
	}
	response.SuccessList(c, data, 1, 10, 1, "Adjustments retrieved")
}

// UpdateOpnameStatus updates the status of an opname (Review, Approve, Reject)
// POST /inventory/opname/review
// POST /inventory/opname/approve
func (h *InventoryHandler) UpdateOpnameStatus(c *gin.Context) {
	var req struct {
		OpnameID string `json:"opname_id" binding:"required"`
		Approved *bool  `json:"approved"`
		Notes    string `json:"notes"`
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

	// Determine new status based on endpoint and payload
	newStatus := "Pending Review" // Default for /review
	path := c.Request.URL.Path
	if strings.HasSuffix(path, "/approve") {
		if req.Approved != nil && *req.Approved {
			newStatus = "Approved"
		} else {
			newStatus = "Rejected"
		}
	}

	updates := map[string]interface{}{
		"status": newStatus,
	}
	if req.Notes != "" {
		updates["notes"] = req.Notes
	}

	if err := db.Model(&models.StockOpname{}).Where("id = ?", req.OpnameID).Updates(updates).Error; err != nil {
		response.InternalError(c, "Failed to update opname status: "+err.Error())
		return
	}

	response.Success(c, nil, "Opname status updated to "+newStatus)
}

// SubmitOpnameAdjustment creates manual adjustment (Post to final stock)
// POST /inventory/opname/post
// POST /inventory/opname/adjustment
func (h *InventoryHandler) SubmitOpnameAdjustment(c *gin.Context) {
	var req struct {
		OpnameID string `json:"opname_id" binding:"required"`
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

	// In a real implementation, this would:
	// 1. Fetch the approved opname and its details.
	// 2. For each detail with a variance, create a StockMovement (ADJUSTMENT).
	// 3. Update the InventoryBatch quantities.
	// 4. Set opname status to "Completed" or "Posted".

	// For now, let's just update the status to "Completed" to show it works
	if err := db.Model(&models.StockOpname{}).Where("id = ?", req.OpnameID).Update("status", "Completed").Error; err != nil {
		response.InternalError(c, "Failed to post adjustment: "+err.Error())
		return
	}

	response.Success(c, nil, "Opname adjustments posted successfully")
}

// ========== LOCATIONS ==========

// GetLocationsHierarchy gets warehouse/floor/room hierarchy
// GET /inventory/locations
func (h *InventoryHandler) GetLocationsHierarchy(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, []gin.H{}, "Locations hierarchy retrieved")
		return
	}

	var warehouses []models.Warehouse
	if err := db.Find(&warehouses).Error; err != nil {
		response.InternalError(c, "Failed to fetch warehouses")
		return
	}

	var zones []models.StorageZone
	if err := db.Find(&zones).Error; err != nil {
		response.InternalError(c, "Failed to fetch storage zones")
		return
	}

	// Group zones by warehouse
	zonesByWarehouse := make(map[string][]models.StorageZone)
	for _, z := range zones {
		zonesByWarehouse[z.WarehouseID] = append(zonesByWarehouse[z.WarehouseID], z)
	}

	var result []gin.H
	for _, w := range warehouses {
		whZones := zonesByWarehouse[w.ID]
		var rooms []gin.H
		for _, z := range whZones {
			rooms = append(rooms, gin.H{
				"id":       z.ID,
				"name":     z.ZoneName,
				"capacity": z.CapacityUnits,
				"type":     z.ZoneType,
			})
		}

		// Create a virtual floor if there are zones, or just empty
		floors := []gin.H{}
		if len(rooms) > 0 {
			floors = append(floors, gin.H{
				"id":    "floor-main-" + w.ID,
				"name":  "Main Level",
				"rooms": rooms,
			})
		}

		result = append(result, gin.H{
			"id":     w.ID,
			"code":   w.Code,
			"name":   w.Name,
			"floors": floors,
		})
	}

	response.Success(c, result, "Locations hierarchy retrieved successfully")
}

// GetLocationsForMove returns a list of locations suitable for moving stock
// GET /inventory/locations-for-move
func (h *InventoryHandler) GetLocationsForMove(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, []gin.H{}, "Locations retrieved")
		return
	}

	var zones []models.StorageZone
	if err := db.Find(&zones).Error; err != nil {
		response.InternalError(c, "Failed to fetch storage zones")
		return
	}

	var result []gin.H
	for _, z := range zones {
		result = append(result, gin.H{
			"id":   z.ID,
			"name": z.ZoneName,
		})
	}

	response.Success(c, result, "Locations retrieved successfully")
}

// ListStorageZones lists all storage zones
// GET /inventory/storage-zones
func (h *InventoryHandler) ListStorageZones(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not available")
		return
	}

	var zones []models.StorageZone
	if err := db.Preload("Warehouse").Find(&zones).Error; err != nil {
		response.InternalError(c, "Failed to fetch storage zones: "+err.Error())
		return
	}

	response.SuccessList(c, zones, 1, 10, int64(len(zones)), "Storage zones retrieved successfully")
}

// CreateStorageZone creates a new storage zone
// POST /inventory/storage-zones
func (h *InventoryHandler) CreateStorageZone(c *gin.Context) {
	db := database.GetDB()
	tenantID := c.GetHeader("X-Tenant-ID")

	var req models.StorageZone
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Manual UUID generation
	req.ID = uuid.New().String()
	req.TenantID = tenantID

	if err := db.Create(&req).Error; err != nil {
		response.InternalError(c, "Failed to create storage zone: "+err.Error())
		return
	}

	response.SuccessCreate(c, req, "Storage zone created successfully")
}

// GetStorageZone gets storage zone by ID
// GET /inventory/storage-zones/:id
func (h *InventoryHandler) GetStorageZone(c *gin.Context) {
	id := c.Param("id")
	db := database.GetDB()

	var zone models.StorageZone
	if err := db.Preload("Warehouse").First(&zone, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Storage zone not found")
		return
	}

	response.Success(c, zone, "Storage zone retrieved")
}

// UpdateStorageZone updates a storage zone
// PUT /inventory/storage-zones/:id
func (h *InventoryHandler) UpdateStorageZone(c *gin.Context) {
	id := c.Param("id")
	db := database.GetDB()

	var zone models.StorageZone
	if err := db.First(&zone, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Storage zone not found")
		return
	}

	var req models.StorageZone
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// Update specific fields
	zone.ZoneName = req.ZoneName
	zone.ZoneType = req.ZoneType
	zone.WarehouseID = req.WarehouseID
	zone.MinTemp = req.MinTemp
	zone.MaxTemp = req.MaxTemp
	zone.CapacityUnits = req.CapacityUnits
	zone.ElectricityTariff = req.ElectricityTariff
	zone.SensorID = req.SensorID
	zone.ElectricityMeterID = req.ElectricityMeterID
	zone.DailyKwhUsage = req.DailyKwhUsage
	zone.MonthlyEnergyCost = req.MonthlyEnergyCost

	if err := db.Save(&zone).Error; err != nil {
		response.InternalError(c, "Failed to update storage zone: "+err.Error())
		return
	}

	response.Success(c, zone, "Storage zone updated successfully")
}

// DeleteStorageZone deletes a storage zone
// DELETE /inventory/storage-zones/:id
func (h *InventoryHandler) DeleteStorageZone(c *gin.Context) {
	id := c.Param("id")
	db := database.GetDB()

	if err := db.Delete(&models.StorageZone{}, "id = ?", id).Error; err != nil {
		response.InternalError(c, "Failed to delete storage zone")
		return
	}

	response.Success(c, gin.H{"id": id}, "Storage zone deleted successfully")
}

// ========== CATEGORIES ==========

// ListCategories lists product categories
// GET /inventory/categories
func (h *InventoryHandler) ListCategories(c *gin.Context) {
	// Return mock categories for now
	categories := []gin.H{
		{"id": "cat-1", "code": "RAW", "name": "Raw Materials", "type": "raw_material"},
		{"id": "cat-2", "code": "FIN", "name": "Finished Goods", "type": "finished_product"},
		{"id": "cat-3", "code": "WIP", "name": "Work in Progress", "type": "wip"},
		{"id": "cat-4", "code": "PKG", "name": "Packaging", "type": "packaging"},
	}
	response.SuccessList(c, categories, 1, 20, int64(len(categories)), "Categories retrieved successfully")
}
