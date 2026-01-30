package models

import "time"

type DeliveryOrder struct {
	ID                 string              `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID           string              `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	DONumber           *string             `gorm:"column:do_number" json:"do_number"`
	SalesOrderID       *string             `gorm:"column:sales_order_id;type:uuid" json:"so_id"` // Standardized for UI
	CustomerID         *string             `gorm:"column:customer_id;type:uuid" json:"customer_id"`
	CustomerName       *string             `gorm:"column:customer_name" json:"customer_name"` // For display/walk-in
	Status             *string             `gorm:"column:status" json:"status"`
	DeliveryDate       *time.Time          `gorm:"column:delivery_date" json:"delivery_date"`
	DriverID           *string             `gorm:"column:driver_id;type:uuid" json:"driver_id"`
	VehicleID          *string             `gorm:"column:vehicle_id;type:uuid" json:"vehicle_id"`
	OriginAddress      *string             `gorm:"column:origin_address" json:"origin_address"`
	DestinationAddress *string             `gorm:"column:destination_address" json:"shipping_address"` // Match UI
	Notes              *string             `gorm:"column:notes" json:"notes"`
	ShippedAt          *time.Time          `gorm:"column:shipped_at" json:"shipped_at"`
	DeliveredAt        *time.Time          `gorm:"column:delivered_at" json:"delivered_at"`
	ItemsCount         int                 `gorm:"-" json:"items_count"` // Calculated
	Items              []DeliveryOrderItem `gorm:"foreignKey:DeliveryOrderID" json:"items"`
	CreatedAt          time.Time           `gorm:"column:created_at" json:"created_at"`
	UpdatedAt          time.Time           `gorm:"column:updated_at" json:"updated_at"`
}

func (DeliveryOrder) TableName() string { return "delivery_orders" }

type DeliveryOrderItem struct {
	ID              string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	DeliveryOrderID string    `gorm:"column:delivery_order_id;type:uuid;index;not null" json:"delivery_order_id"`
	ProductID       string    `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	ProductName     string    `gorm:"column:product_name" json:"product_name"` // Denormalized for easy display
	BatchID         *string   `gorm:"column:batch_id;type:uuid" json:"batch_id"`
	BatchNumber     string    `gorm:"column:batch_number" json:"batch_number"` // Denormalized
	Quantity        float64   `gorm:"column:quantity" json:"quantity"`
	CreatedAt       time.Time `gorm:"column:created_at" json:"created_at"`
}

func (DeliveryOrderItem) TableName() string { return "delivery_order_items" }

type Shipment struct {
	ID               string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID         string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	ShipmentNumber   *string    `gorm:"column:shipment_number" json:"shipment_number"`
	DeliveryOrderID  *string    `gorm:"column:delivery_order_id;type:uuid" json:"delivery_order_id"`
	Carrier          *string    `gorm:"column:carrier" json:"carrier"`
	TrackingNumber   *string    `gorm:"column:tracking_number" json:"tracking_number"`
	Status           *string    `gorm:"column:status" json:"status"`
	EstimatedArrival *time.Time `gorm:"column:estimated_arrival" json:"estimated_arrival"`
	ActualArrival    *time.Time `gorm:"column:actual_arrival" json:"actual_arrival"`
	Cost             *float64   `gorm:"column:cost" json:"cost"`
	CreatedAt        time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt        time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Shipment) TableName() string { return "shipments" }

type StockTransferStatus string

const (
	TransferPending   StockTransferStatus = "PENDING"
	TransferInTransit StockTransferStatus = "IN_TRANSIT"
	TransferCompleted StockTransferStatus = "COMPLETED"
	TransferCancelled StockTransferStatus = "CANCELLED"
)

type StockTransfer struct {
	ID              string              `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string              `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	TransferNumber  string              `gorm:"column:transfer_number;not null" json:"transfer_number"`
	FromWarehouseID string              `gorm:"column:from_warehouse_id;type:uuid;not null" json:"from_warehouse_id"`
	ToWarehouseID   string              `gorm:"column:to_warehouse_id;type:uuid;not null" json:"to_warehouse_id"`
	TransferDate    *time.Time          `gorm:"column:transfer_date" json:"transfer_date"`
	TransferType    string              `gorm:"column:transfer_type" json:"transfer_type"`
	Status          StockTransferStatus `gorm:"column:status" json:"status"`
	Notes           string              `gorm:"column:notes" json:"notes"`
	StartedAt       *time.Time          `gorm:"column:started_at" json:"started_at"`
	CompletedAt     *time.Time          `gorm:"column:completed_at" json:"completed_at"`
	CreatedBy       *string             `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt       time.Time           `gorm:"column:created_at" json:"created_at"`
	UpdatedAt       time.Time           `gorm:"column:updated_at" json:"updated_at"`
	Items           []StockTransferItem `gorm:"foreignKey:TransferID" json:"items"`

	// Virtual fields for display
	FromWarehouse string `gorm:"-" json:"from_warehouse"`
	ToWarehouse   string `gorm:"-" json:"to_warehouse"`
}

func (StockTransfer) TableName() string { return "stock_transfers" }

type StockTransferItem struct {
	ID         string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID   string  `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	TransferID string  `gorm:"column:transfer_id;type:uuid;index;not null" json:"transfer_id"`
	ProductID  string  `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	Quantity   float64 `gorm:"column:quantity" json:"quantity"`
}

func (StockTransferItem) TableName() string { return "stock_transfer_items" }
