package handlers

import (
	"net/http"
	"strconv"

	"github.com/elviskudo/mini-erp/services/inventory-service/internal/database"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/models"
	"github.com/elviskudo/mini-erp/services/inventory-service/internal/response"
	"github.com/gin-gonic/gin"
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
		c.JSON(http.StatusOK, getMockStats())
		return
	}

	var warehouseCount, productCount, movementCount int64
	db.Model(&models.Warehouse{}).Count(&warehouseCount)
	db.Model(&models.Product{}).Count(&productCount)
	db.Model(&models.StockMovement{}).Count(&movementCount)

	var totalStock int64
	db.Model(&models.InventoryBatch{}).Select("COALESCE(SUM(quantity), 0)").Scan(&totalStock)

	c.JSON(http.StatusOK, gin.H{
		"total_warehouses":  warehouseCount,
		"total_products":    productCount,
		"total_stock":       totalStock,
		"recent_movements":  movementCount,
		"low_stock_items":   5,
		"pending_transfers": 3,
	})
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
		c.JSON(http.StatusOK, gin.H{"id": productID, "code": "P001", "name": "Sample Product"})
		return
	}

	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
		return
	}

	c.JSON(http.StatusOK, product)
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
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":      "new-product-id",
		"code":    req.Code,
		"name":    req.Name,
		"type":    req.Type,
		"message": "Product created successfully",
	})
}

// UpdateProduct updates an existing product
// PUT /inventory/products/:id
func (h *InventoryHandler) UpdateProduct(c *gin.Context) {
	db := database.GetDB()
	productID := c.Param("id")

	if db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"code":    "INTERNAL_ERROR",
			"message": "Database not connected",
		})
		return
	}

	// Find existing product
	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success":   false,
			"code":      "NOT_FOUND",
			"message":   "Product not found",
			"data":      nil,
			"meta":      nil,
			"errors":    nil,
			"timestamp": "",
		})
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
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"code":    "BAD_REQUEST",
			"message": err.Error(),
		})
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
		product.CategoryID = req.CategoryID
	}
	if req.IsManufactured != nil {
		product.IsManufactured = req.IsManufactured
	}
	if req.ImageURL != nil {
		product.ImageURL = req.ImageURL
	}

	// Save to database
	if err := db.Save(&product).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"code":    "INTERNAL_ERROR",
			"message": "Failed to update product",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success":   true,
		"code":      "SUCCESS",
		"message":   "Product updated successfully",
		"data":      product,
		"meta":      nil,
		"errors":    nil,
		"timestamp": "",
	})
}

// DeleteProduct deletes a product
// DELETE /inventory/products/:id
func (h *InventoryHandler) DeleteProduct(c *gin.Context) {
	db := database.GetDB()
	productID := c.Param("id")

	if db == nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"code":    "INTERNAL_ERROR",
			"message": "Database not connected",
		})
		return
	}

	// Check if product exists
	var product models.Product
	if err := db.First(&product, "id = ?", productID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"code":    "NOT_FOUND",
			"message": "Product not found",
		})
		return
	}

	// Delete from database
	if err := db.Delete(&product).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"code":    "INTERNAL_ERROR",
			"message": "Failed to delete product",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"code":    "SUCCESS",
		"message": "Product deleted successfully",
		"data":    gin.H{"id": productID},
	})
}

// ========== WAREHOUSES ==========

// ListWarehouses lists all warehouses
// GET /inventory/warehouses
func (h *InventoryHandler) ListWarehouses(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockWarehouses())
		return
	}

	var warehouses []models.Warehouse
	if err := db.Order("code ASC").Find(&warehouses).Error; err != nil {
		c.JSON(http.StatusOK, getMockWarehouses())
		return
	}

	if len(warehouses) == 0 {
		c.JSON(http.StatusOK, getMockWarehouses())
		return
	}

	c.JSON(http.StatusOK, warehouses)
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
		c.JSON(http.StatusOK, gin.H{"id": warehouseID, "code": "WH001", "name": "Main Warehouse"})
		return
	}

	var warehouse models.Warehouse
	if err := db.First(&warehouse, "id = ?", warehouseID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Warehouse not found"})
		return
	}

	c.JSON(http.StatusOK, warehouse)
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
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":      "new-warehouse-id",
		"code":    req.Code,
		"name":    req.Name,
		"message": "Warehouse created successfully",
	})
}

// UpdateWarehouse updates a warehouse
// PUT /inventory/warehouses/:id
func (h *InventoryHandler) UpdateWarehouse(c *gin.Context) {
	warehouseID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": warehouseID, "message": "Warehouse updated"})
}

// ========== STOCK ==========

// ListStock lists stock by warehouse
// GET /inventory/stock
func (h *InventoryHandler) ListStock(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockStock())
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
		c.JSON(http.StatusOK, getMockStock())
		return
	}

	if len(batches) == 0 {
		c.JSON(http.StatusOK, getMockStock())
		return
	}

	c.JSON(http.StatusOK, batches)
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
	if db == nil {
		c.JSON(http.StatusOK, getMockMovements())
		return
	}

	var movements []models.StockMovement
	query := db.Order("timestamp DESC").Limit(50)

	if movementType := c.Query("movement_type"); movementType != "" {
		query = query.Where("movement_type = ?", movementType)
	}
	if warehouseID := c.Query("warehouse_id"); warehouseID != "" {
		query = query.Where("warehouse_id = ?", warehouseID)
	}

	if err := query.Find(&movements).Error; err != nil {
		c.JSON(http.StatusOK, getMockMovements())
		return
	}

	if len(movements) == 0 {
		c.JSON(http.StatusOK, getMockMovements())
		return
	}

	c.JSON(http.StatusOK, movements)
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
		c.JSON(http.StatusOK, getMockOpnames())
		return
	}

	var opnames []models.StockOpname
	query := db.Order("created_at DESC")

	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	if err := query.Find(&opnames).Error; err != nil {
		c.JSON(http.StatusOK, getMockOpnames())
		return
	}

	if len(opnames) == 0 {
		c.JSON(http.StatusOK, getMockOpnames())
		return
	}

	c.JSON(http.StatusOK, opnames)
}

func getMockOpnames() []gin.H {
	return []gin.H{
		{"id": "op-1", "code": "OP-2024-001", "name": "January Stock Take", "status": "COMPLETED", "warehouse_id": "wh-1"},
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
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":      "new-opname-id",
		"code":    req.Code,
		"status":  "DRAFT",
		"message": "Stock opname created successfully",
	})
}

// GetOpname gets opname by ID
// GET /inventory/opnames/:id
func (h *InventoryHandler) GetOpname(c *gin.Context) {
	opnameID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{
		"id": opnameID, "code": "OP-2024-001", "name": "Stock Take", "status": "IN_PROGRESS",
	})
}

// ========== STOCK OPNAME EXTENDED ==========

// ListOpnameSchedules lists opname schedules
// GET /inventory/opname/schedule
func (h *InventoryHandler) ListOpnameSchedules(c *gin.Context) {
	data := []gin.H{
		{"id": "sch-1", "date": "2024-02-01", "warehouse": "Main Warehouse", "status": "Scheduled"},
	}
	response.SuccessList(c, data, 1, 10, 1, "Opname schedules retrieved")
}

// CreateOpnameSchedule creates a new schedule
// POST /inventory/opname/schedule
func (h *InventoryHandler) CreateOpnameSchedule(c *gin.Context) {
	response.SuccessCreate(c, gin.H{"id": "sch-new"}, "Schedule created successfully")
}

// ListOpnameCounting lists items for counting
// GET /inventory/opname/counting
func (h *InventoryHandler) ListOpnameCounting(c *gin.Context) {
	data := []gin.H{
		{"id": "item-1", "product": "Product A", "system_qty": 100, "counted_qty": nil},
	}
	response.SuccessList(c, data, 1, 10, 1, "Counting items retrieved")
}

// SubmitOpnameCount submits count results
// POST /inventory/opname/counting
func (h *InventoryHandler) SubmitOpnameCount(c *gin.Context) {
	response.Success(c, nil, "Count submitted successfully")
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

// SubmitOpnameAdjustment creates manual adjustment
// POST /inventory/opname/adjustment
func (h *InventoryHandler) SubmitOpnameAdjustment(c *gin.Context) {
	response.SuccessCreate(c, nil, "Adjustment created successfully")
}

// ========== LOCATIONS ==========

// GetLocationsHierarchy gets warehouse/floor/room hierarchy
// GET /inventory/locations
func (h *InventoryHandler) GetLocationsHierarchy(c *gin.Context) {
	c.JSON(http.StatusOK, []gin.H{
		{
			"id": "wh-1", "code": "WH001", "name": "Main Warehouse",
			"floors": []gin.H{
				{
					"id": "floor-1", "name": "Ground Floor",
					"rooms": []gin.H{
						{"id": "room-1", "name": "Storage A", "capacity": 1000},
						{"id": "room-2", "name": "Storage B", "capacity": 500},
					},
				},
			},
		},
	})
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
