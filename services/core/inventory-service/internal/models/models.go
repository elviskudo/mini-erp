package models

import (
	"time"
)

// Product represents a product (matches migrated DB)
type Product struct {
	ID                    string   `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID              string   `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code                  string   `gorm:"column:code;not null" json:"code"`
	Name                  string   `gorm:"column:name;not null" json:"name"`
	Type                  *string  `gorm:"column:type" json:"type"` // RAW_MATERIAL, FINISHED_GOOD, etc
	UOM                   *string  `gorm:"column:uom" json:"uom"`
	StandardCost          *float64 `gorm:"column:standard_cost" json:"standard_cost"`
	IsManufactured        *bool    `gorm:"column:is_manufactured" json:"is_manufactured"`
	ImageURL              *string  `gorm:"column:image_url" json:"image_url"`
	WeightedAvgCost       *float64 `gorm:"column:weighted_avg_cost" json:"weighted_avg_cost"`
	DesiredMargin         *float64 `gorm:"column:desired_margin" json:"desired_margin"`
	SuggestedSellingPrice *float64 `gorm:"column:suggested_selling_price" json:"suggested_selling_price"`
	RequiresColdChain     *bool    `gorm:"column:requires_cold_chain" json:"requires_cold_chain"`
	MaxStorageTemp        *float64 `gorm:"column:max_storage_temp" json:"max_storage_temp"`
	Description           *string  `gorm:"column:description" json:"description"`
	CategoryID            *string  `gorm:"column:category_id;type:uuid" json:"category_id"`
	Category              *string  `gorm:"column:category" json:"category"`
	IsActive              *bool    `gorm:"column:is_active" json:"is_active"`
}

func (Product) TableName() string {
	return "products"
}

// Warehouse represents a warehouse
type Warehouse struct {
	ID        string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID  string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code      string    `gorm:"column:code;not null" json:"code"`
	Name      string    `gorm:"column:name;not null" json:"name"`
	Address   *string   `gorm:"column:address" json:"address"`
	City      *string   `gorm:"column:city" json:"city"`
	Phone     *string   `gorm:"column:phone" json:"phone"`
	IsActive  *bool     `gorm:"column:is_active" json:"is_active"`
	TotalArea *float64  `gorm:"column:total_area" json:"total_area"`
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (Warehouse) TableName() string {
	return "warehouses"
}

// StockMovement represents a stock movement record
type StockMovement struct {
	ID            string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProductID     string    `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	WarehouseID   *string   `gorm:"column:warehouse_id;type:uuid" json:"warehouse_id"`
	MovementType  string    `gorm:"column:movement_type;not null" json:"movement_type"` // IN, OUT, TRANSFER, ADJUSTMENT
	Quantity      float64   `gorm:"column:quantity;not null" json:"quantity"`
	ReferenceType *string   `gorm:"column:reference_type" json:"reference_type"`
	ReferenceID   *string   `gorm:"column:reference_id;type:uuid" json:"reference_id"`
	Notes         *string   `gorm:"column:notes" json:"notes"`
	CreatedBy     *string   `gorm:"column:created_by;type:uuid" json:"created_by"`
	Timestamp     time.Time `gorm:"column:timestamp" json:"timestamp"`
}

func (StockMovement) TableName() string {
	return "stock_movements"
}

// InventoryBatch represents inventory batch with expiry
type InventoryBatch struct {
	ID           string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProductID    string     `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	WarehouseID  *string    `gorm:"column:warehouse_id;type:uuid" json:"warehouse_id"`
	BatchNumber  *string    `gorm:"column:batch_number" json:"batch_number"`
	Quantity     float64    `gorm:"column:quantity;not null" json:"quantity"`
	ExpiryDate   *time.Time `gorm:"column:expiry_date;type:date" json:"expiry_date"`
	ReceivedDate *time.Time `gorm:"column:received_date;type:date" json:"received_date"`
	UnitCost     *float64   `gorm:"column:unit_cost" json:"unit_cost"`
	LocationID   *string    `gorm:"column:location_id;type:uuid" json:"location_id"`
}

func (InventoryBatch) TableName() string {
	return "inventory_batches"
}

// StockOpname represents stock take/opname
type StockOpname struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code        string     `gorm:"column:code;not null" json:"code"`
	Name        *string    `gorm:"column:name" json:"name"`
	WarehouseID *string    `gorm:"column:warehouse_id;type:uuid" json:"warehouse_id"`
	Status      string     `gorm:"column:status;not null" json:"status"` // DRAFT, IN_PROGRESS, COMPLETED
	ScheduledAt *time.Time `gorm:"column:scheduled_at" json:"scheduled_at"`
	StartedAt   *time.Time `gorm:"column:started_at" json:"started_at"`
	CompletedAt *time.Time `gorm:"column:completed_at" json:"completed_at"`
	CreatedBy   *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	ApprovedBy  *string    `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	Notes       *string    `gorm:"column:notes" json:"notes"`
	CreatedAt   time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt   time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (StockOpname) TableName() string {
	return "stock_opnames"
}
