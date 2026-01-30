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
	ID            string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ProductID     string     `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	Product       *Product   `gorm:"foreignKey:ProductID" json:"product,omitempty"`
	WarehouseID   *string    `gorm:"column:warehouse_id;type:uuid" json:"warehouse_id"`
	Warehouse     *Warehouse `gorm:"foreignKey:WarehouseID" json:"warehouse,omitempty"`
	MovementType  string     `gorm:"column:movement_type;not null" json:"movement_type"` // IN, OUT, TRANSFER, ADJUSTMENT
	Quantity      float64    `gorm:"column:quantity" json:"quantity"`
	ReferenceType *string    `gorm:"column:reference_type" json:"reference_type"`
	ReferenceID   *string    `gorm:"column:reference_id;type:uuid" json:"reference_id"`
	Notes         *string    `gorm:"column:notes" json:"notes"`
	CreatedBy     *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	Timestamp     time.Time  `gorm:"column:timestamp" json:"timestamp"`
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
	ID                 string              `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID           string              `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Number             string              `gorm:"column:opname_number" json:"opname_number"`
	Code               string              `gorm:"-" json:"code,omitempty"` // Alias if needed
	Name               *string             `gorm:"column:name" json:"name"`
	WarehouseID        *string             `gorm:"column:warehouse_id;type:uuid" json:"warehouse_id"`
	Warehouse          *Warehouse          `gorm:"foreignKey:WarehouseID" json:"warehouse,omitempty"`
	Status             string              `gorm:"column:status;not null" json:"status"`
	Date               *time.Time          `gorm:"column:date" json:"date"`
	ScheduledAt        *time.Time          `gorm:"-" json:"scheduled_at,omitempty"` // Alias if needed
	TotalItems         int                 `gorm:"column:total_items" json:"total_items"`
	CountedItems       int                 `gorm:"column:counted_items" json:"counted_items"`
	ItemsWithVariance  int                 `gorm:"column:items_with_variance" json:"items_with_variance"`
	TotalSystemValue   float64             `gorm:"column:total_system_value" json:"total_system_value"`
	TotalCountedValue  float64             `gorm:"column:total_counted_value" json:"total_counted_value"`
	TotalVarianceValue float64             `gorm:"column:total_variance_value" json:"total_variance_value"`
	StartedAt          *time.Time          `gorm:"column:counting_started_at" json:"started_at"`
	CompletedAt        *time.Time          `gorm:"column:counting_completed_at" json:"completed_at"`
	CreatedBy          *string             `gorm:"column:created_by;type:uuid" json:"created_by"`
	ApprovedBy         *string             `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	Notes              *string             `gorm:"column:notes" json:"notes"`
	Details            []StockOpnameDetail `gorm:"foreignKey:OpnameID" json:"details"`
	CreatedAt          time.Time           `gorm:"column:created_at" json:"created_at"`
	UpdatedAt          time.Time           `gorm:"column:updated_at" json:"updated_at"`
}

func (StockOpname) TableName() string {
	return "stock_opnames"
}

// StockOpnameDetail represents an item in a stock take
type StockOpnameDetail struct {
	ID            string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	OpnameID      string     `gorm:"column:opname_id;type:uuid;index;not null" json:"opname_id"`
	ProductID     string     `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	Product       *Product   `gorm:"foreignKey:ProductID" json:"product,omitempty"`
	BatchID       *string    `gorm:"column:batch_id;type:uuid" json:"batch_id"`
	SystemQty     float64    `gorm:"column:system_qty" json:"system_qty"`
	CountedQty    *float64   `gorm:"column:counted_qty" json:"counted_qty"`
	LocationID    *string    `gorm:"column:location_id;type:uuid" json:"location_id"`
	Variance      *float64   `gorm:"column:variance" json:"variance"`
	UnitCost      float64    `gorm:"column:unit_cost" json:"unit_cost"`
	SystemValue   float64    `gorm:"column:system_value" json:"system_value"`
	CountedValue  float64    `gorm:"column:counted_value" json:"counted_value"`
	VarianceValue float64    `gorm:"column:variance_value" json:"variance_value"`
	CountedAt     *time.Time `gorm:"column:counted_at" json:"counted_at"`
	CountedBy     *string    `gorm:"column:counted_by;type:uuid" json:"counted_by"`
	NeedsRecount  bool       `gorm:"column:needs_recount" json:"needs_recount"`
}

func (StockOpnameDetail) TableName() string {
	return "stock_opname_details"
}

// StorageZone represents a specific zone within a warehouse
type StorageZone struct {
	ID                 string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID           string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ZoneName           string     `gorm:"column:zone_name;not null" json:"zone_name"`
	ZoneType           string     `gorm:"column:zone_type;not null" json:"zone_type"` // Ambient, Chiller, Frozen, Dangerous
	WarehouseID        string     `gorm:"column:warehouse_id;type:uuid;not null" json:"warehouse_id"`
	Warehouse          *Warehouse `gorm:"foreignKey:WarehouseID" json:"warehouse,omitempty"`
	MinTemp            *float64   `gorm:"column:min_temp" json:"min_temp"`
	MaxTemp            *float64   `gorm:"column:max_temp" json:"max_temp"`
	CapacityUnits      float64    `gorm:"column:capacity_units" json:"capacity_units"`
	ElectricityTariff  *float64   `gorm:"column:electricity_tariff" json:"electricity_tariff"`
	SensorID           *string    `gorm:"column:sensor_id" json:"sensor_id"`
	ElectricityMeterID *string    `gorm:"column:electricity_meter_id" json:"electricity_meter_id"`
	DailyKwhUsage      *float64   `gorm:"column:daily_kwh_usage" json:"daily_kwh_usage"`
	MonthlyEnergyCost  *float64   `gorm:"column:monthly_energy_cost" json:"monthly_energy_cost"`
	CreatedAt          time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt          time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (StorageZone) TableName() string {
	return "storage_zones"
}

// OpnameSchedule represents a planned stock take event
type OpnameSchedule struct {
	ID                     string             `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID               string             `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Name                   string             `gorm:"column:name;not null" json:"name"`
	WarehouseID            string             `gorm:"column:warehouse_id;type:uuid;not null" json:"warehouse_id"`
	Warehouse              *Warehouse         `gorm:"foreignKey:WarehouseID" json:"warehouse,omitempty"`
	Frequency              string             `gorm:"column:frequency" json:"frequency"`
	ScheduledDate          time.Time          `gorm:"column:scheduled_date;not null" json:"scheduled_date"`
	StartTime              *string            `gorm:"column:start_time" json:"start_time"`
	EstimatedDurationHours int                `gorm:"column:estimated_duration_hours" json:"estimated_duration_hours"`
	Description            *string            `gorm:"column:description" json:"description"`
	IsActive               bool               `gorm:"column:is_active;default:true" json:"is_active"`
	Assignments            []OpnameAssignment `gorm:"foreignKey:ScheduleID" json:"assignments"`
	CreatedAt              time.Time          `gorm:"column:created_at" json:"created_at"`
}

func (OpnameSchedule) TableName() string {
	return "opname_schedules"
}

// OpnameAssignment represents a user assigned to a schedule
type OpnameAssignment struct {
	ID         string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID   string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ScheduleID string    `gorm:"column:schedule_id;type:uuid;index;not null" json:"schedule_id"`
	UserID     string    `gorm:"column:user_id;type:uuid;not null" json:"user_id"`
	Role       string    `gorm:"column:role" json:"role"`
	CreatedAt  time.Time `gorm:"column:created_at" json:"created_at"`
}

func (OpnameAssignment) TableName() string {
	return "opname_assignments"
}
