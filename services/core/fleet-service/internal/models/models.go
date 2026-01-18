package models

import "time"

// Vehicle represents a vehicle
type Vehicle struct {
	ID              string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code            string     `gorm:"column:code;not null" json:"code"`
	PlateNumber     string     `gorm:"column:plate_number;not null" json:"plate_number"`
	Brand           string     `gorm:"column:brand;not null" json:"brand"`
	Model           string     `gorm:"column:model;not null" json:"model"`
	Year            *int       `gorm:"column:year" json:"year"`
	Color           *string    `gorm:"column:color" json:"color"`
	VehicleType     *string    `gorm:"column:vehicle_type" json:"vehicle_type"`
	Category        *string    `gorm:"column:category" json:"category"` // MOTORCYCLE, CAR, TRUCK, BUS
	Capacity        *string    `gorm:"column:capacity" json:"capacity"`
	FuelType        *string    `gorm:"column:fuel_type" json:"fuel_type"`
	ChassisNumber   *string    `gorm:"column:chassis_number" json:"chassis_number"`
	EngineNumber    *string    `gorm:"column:engine_number" json:"engine_number"`
	STNKNumber      *string    `gorm:"column:stnk_number" json:"stnk_number"`
	BPKBNumber      *string    `gorm:"column:bpkb_number" json:"bpkb_number"`
	Status          *string    `gorm:"column:status" json:"status"` // AVAILABLE, BOOKED, MAINTENANCE, INACTIVE
	CurrentOdometer *float64   `gorm:"column:current_odometer" json:"current_odometer"`
	PurchaseDate    *time.Time `gorm:"column:purchase_date;type:date" json:"purchase_date"`
	PurchaseCost    *float64   `gorm:"column:purchase_cost" json:"purchase_cost"`
}

func (Vehicle) TableName() string { return "vehicles" }

// VehicleBooking represents a booking
type VehicleBooking struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VehicleID   string     `gorm:"column:vehicle_id;type:uuid;index;not null" json:"vehicle_id"`
	DriverID    *string    `gorm:"column:driver_id;type:uuid" json:"driver_id"`
	BookedBy    *string    `gorm:"column:booked_by;type:uuid" json:"booked_by"`
	Purpose     *string    `gorm:"column:purpose" json:"purpose"`
	Destination *string    `gorm:"column:destination" json:"destination"`
	StartDate   *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate     *time.Time `gorm:"column:end_date" json:"end_date"`
	Status      *string    `gorm:"column:status" json:"status"` // PENDING, APPROVED, REJECTED, COMPLETED, CANCELLED
	Notes       *string    `gorm:"column:notes" json:"notes"`
}

func (VehicleBooking) TableName() string { return "vehicle_bookings" }

// FleetDriver represents a driver
type FleetDriver struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	EmployeeID  *string    `gorm:"column:employee_id;type:uuid" json:"employee_id"`
	Name        string     `gorm:"column:name;not null" json:"name"`
	Phone       *string    `gorm:"column:phone" json:"phone"`
	LicenseNo   *string    `gorm:"column:license_no" json:"license_no"`
	LicenseType *string    `gorm:"column:license_type" json:"license_type"` // SIM A, SIM B, SIM C
	ExpiryDate  *time.Time `gorm:"column:expiry_date;type:date" json:"expiry_date"`
	Status      *string    `gorm:"column:status" json:"status"` // ACTIVE, INACTIVE
	QRCode      *string    `gorm:"column:qr_code" json:"qr_code"`
}

func (FleetDriver) TableName() string { return "fleet_drivers" }

// VehicleFuelLog represents fuel log
type VehicleFuelLog struct {
	ID         string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID   string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VehicleID  string     `gorm:"column:vehicle_id;type:uuid;index;not null" json:"vehicle_id"`
	DriverID   *string    `gorm:"column:driver_id;type:uuid" json:"driver_id"`
	FuelType   *string    `gorm:"column:fuel_type" json:"fuel_type"`
	Amount     *float64   `gorm:"column:amount" json:"amount"` // Liters
	TotalCost  *float64   `gorm:"column:total_cost" json:"total_cost"`
	Odometer   *float64   `gorm:"column:odometer" json:"odometer"`
	RefuelDate *time.Time `gorm:"column:refuel_date" json:"refuel_date"`
}

func (VehicleFuelLog) TableName() string { return "vehicle_fuel_logs" }

// VehicleMaintenanceLog represents maintenance
type VehicleMaintenanceLog struct {
	ID              string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VehicleID       string     `gorm:"column:vehicle_id;type:uuid;index;not null" json:"vehicle_id"`
	MaintenanceType *string    `gorm:"column:maintenance_type" json:"maintenance_type"`
	Description     *string    `gorm:"column:description" json:"description"`
	Cost            *float64   `gorm:"column:cost" json:"cost"`
	Odometer        *float64   `gorm:"column:odometer" json:"odometer"`
	ServiceDate     *time.Time `gorm:"column:service_date" json:"service_date"`
	NextServiceDate *time.Time `gorm:"column:next_service_date" json:"next_service_date"`
}

func (VehicleMaintenanceLog) TableName() string { return "vehicle_maintenance_logs" }
