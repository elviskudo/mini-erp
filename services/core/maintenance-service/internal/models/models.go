package models

import "time"

type Asset struct {
	ID              string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	AssetCode       string     `gorm:"column:asset_code;not null" json:"asset_code"`
	Name            string     `gorm:"column:name;not null" json:"name"`
	Category        *string    `gorm:"column:category" json:"category"`
	Location        *string    `gorm:"column:location" json:"location"`
	Status          *string    `gorm:"column:status" json:"status"`
	PurchaseDate    *time.Time `gorm:"column:purchase_date" json:"purchase_date"`
	PurchaseCost    *float64   `gorm:"column:purchase_cost" json:"purchase_cost"`
	WarrantyExpiry  *time.Time `gorm:"column:warranty_expiry" json:"warranty_expiry"`
	LastMaintenance *time.Time `gorm:"column:last_maintenance" json:"last_maintenance"`
	NextMaintenance *time.Time `gorm:"column:next_maintenance" json:"next_maintenance"`
	CreatedAt       time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (Asset) TableName() string { return "assets" }

type MaintenanceWorkOrder struct {
	ID            string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	WONumber      *string    `gorm:"column:wo_number" json:"wo_number"`
	AssetID       *string    `gorm:"column:asset_id;type:uuid" json:"asset_id"`
	Type          *string    `gorm:"column:type" json:"type"`
	Priority      *string    `gorm:"column:priority" json:"priority"`
	Status        *string    `gorm:"column:status" json:"status"`
	Description   *string    `gorm:"column:description" json:"description"`
	AssignedTo    *string    `gorm:"column:assigned_to;type:uuid" json:"assigned_to"`
	ScheduledDate *time.Time `gorm:"column:scheduled_date" json:"scheduled_date"`
	CompletedDate *time.Time `gorm:"column:completed_date" json:"completed_date"`
	LaborHours    *float64   `gorm:"column:labor_hours" json:"labor_hours"`
	LaborCost     *float64   `gorm:"column:labor_cost" json:"labor_cost"`
	PartsCost     *float64   `gorm:"column:parts_cost" json:"parts_cost"`
	TotalCost     *float64   `gorm:"column:total_cost" json:"total_cost"`
	CreatedAt     time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (MaintenanceWorkOrder) TableName() string { return "maintenance_work_orders" }

type MaintenanceSchedule struct {
	ID            string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	AssetID       *string    `gorm:"column:asset_id;type:uuid" json:"asset_id"`
	Frequency     *string    `gorm:"column:frequency" json:"frequency"`
	IntervalDays  *int       `gorm:"column:interval_days" json:"interval_days"`
	LastPerformed *time.Time `gorm:"column:last_performed" json:"last_performed"`
	NextDue       *time.Time `gorm:"column:next_due" json:"next_due"`
	Description   *string    `gorm:"column:description" json:"description"`
	IsActive      *bool      `gorm:"column:is_active" json:"is_active"`
	CreatedAt     time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (MaintenanceSchedule) TableName() string { return "maintenance_schedules" }
