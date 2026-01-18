package models

import "time"

type DeliveryOrder struct {
	ID                 string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID           string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	DONumber           *string    `gorm:"column:do_number" json:"do_number"`
	SalesOrderID       *string    `gorm:"column:sales_order_id;type:uuid" json:"sales_order_id"`
	CustomerID         *string    `gorm:"column:customer_id;type:uuid" json:"customer_id"`
	Status             *string    `gorm:"column:status" json:"status"`
	DeliveryDate       *time.Time `gorm:"column:delivery_date" json:"delivery_date"`
	DriverID           *string    `gorm:"column:driver_id;type:uuid" json:"driver_id"`
	VehicleID          *string    `gorm:"column:vehicle_id;type:uuid" json:"vehicle_id"`
	OriginAddress      *string    `gorm:"column:origin_address" json:"origin_address"`
	DestinationAddress *string    `gorm:"column:destination_address" json:"destination_address"`
	Notes              *string    `gorm:"column:notes" json:"notes"`
	ShippedAt          *time.Time `gorm:"column:shipped_at" json:"shipped_at"`
	DeliveredAt        *time.Time `gorm:"column:delivered_at" json:"delivered_at"`
	CreatedAt          time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (DeliveryOrder) TableName() string { return "delivery_orders" }

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
}

func (Shipment) TableName() string { return "shipments" }
