package models

import "time"

// ========== CATEGORY ==========

// Category represents a product category
type Category struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	Name        string     `gorm:"column:name;not null" json:"name"`
	Description *string    `gorm:"column:description" json:"description"`
	ImageURL    *string    `gorm:"column:image_url" json:"image_url"`
	IsActive    bool       `gorm:"column:is_active;default:true" json:"is_active"`
	CreatedAt   *time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt   *time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (Category) TableName() string { return "categories" }

// ========== WORK CENTER ==========

// WorkCenter represents a work center for production
type WorkCenter struct {
	ID            string   `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID      *string  `gorm:"column:tenant_id;type:uuid;index" json:"tenant_id"`
	Code          string   `gorm:"column:code;not null" json:"code"`
	Name          string   `gorm:"column:name;not null" json:"name"`
	CostPerHour   *float64 `gorm:"column:cost_per_hour" json:"cost_per_hour"`
	CapacityHours *float64 `gorm:"column:capacity_hours" json:"capacity_hours"`
	Location      *string  `gorm:"column:location" json:"location"`
	Latitude      *float64 `gorm:"column:latitude" json:"latitude"`
	Longitude     *float64 `gorm:"column:longitude" json:"longitude"`
	IsActive      bool     `gorm:"column:is_active;default:true" json:"is_active"`
	// Office Hours
	OpenTime  *string `gorm:"column:open_time" json:"open_time"`   // Format: "07:00"
	CloseTime *string `gorm:"column:close_time" json:"close_time"` // Format: "21:00"
	OpenDays  *string `gorm:"column:open_days" json:"open_days"`   // e.g. "Mon,Tue,Wed,Thu,Fri"
}

func (WorkCenter) TableName() string { return "work_centers" }

// ========== PRODUCT (for relations) ==========

// Product represents a product for relations
type Product struct {
	ID              string   `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID        string   `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	Code            string   `gorm:"column:code;not null" json:"code"`
	Name            string   `gorm:"column:name;not null" json:"name"`
	Description     *string  `gorm:"column:description" json:"description"`
	Type            *string  `gorm:"column:type" json:"type"`
	UOM             *string  `gorm:"column:uom" json:"uom"`
	CategoryID      *string  `gorm:"column:category_id;type:uuid" json:"category_id"`
	IsManufactured  *bool    `gorm:"column:is_manufactured" json:"is_manufactured"`
	IsActive        *bool    `gorm:"column:is_active" json:"is_active"`
	ImageURL        *string  `gorm:"column:image_url" json:"image_url"`
	StandardCost    *float64 `gorm:"column:standard_cost" json:"standard_cost"`
	WeightedAvgCost *float64 `gorm:"column:weighted_avg_cost" json:"weighted_avg_cost"`
	// Relations
	Category *Category `gorm:"foreignKey:CategoryID" json:"category,omitempty"`
}

func (Product) TableName() string { return "products" }

// ========== ROUTING ==========

// Routing represents a production routing
type Routing struct {
	ID             string   `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID       *string  `gorm:"column:tenant_id;type:uuid;index" json:"tenant_id"`
	ProductID      string   `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	Name           string   `gorm:"column:name;not null" json:"name"`
	Version        *string  `gorm:"column:version" json:"version"`
	IsActive       *bool    `gorm:"column:is_active;default:true" json:"is_active"`
	TotalTimeHours *float64 `gorm:"column:total_time_hours" json:"total_time_hours"`
	// Relations
	Product *Product      `gorm:"foreignKey:ProductID" json:"product,omitempty"`
	Steps   []RoutingStep `gorm:"foreignKey:RoutingID" json:"steps,omitempty"`
}

func (Routing) TableName() string { return "routings" }

// RoutingStep represents a step in a routing
type RoutingStep struct {
	ID            string   `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID      string   `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	RoutingID     string   `gorm:"column:routing_id;type:uuid;not null;index" json:"routing_id"`
	WorkCenterID  string   `gorm:"column:work_center_id;type:uuid;not null" json:"work_center_id"`
	Sequence      int      `gorm:"column:sequence;not null" json:"sequence"`
	OperationName string   `gorm:"column:operation_name;not null" json:"operation_name"`
	Description   *string  `gorm:"column:description" json:"description"`
	SetupTimeMins *float64 `gorm:"column:setup_time_mins;default:0" json:"setup_time_mins"`
	RunTimeMins   *float64 `gorm:"column:run_time_mins;default:0" json:"run_time_mins"`
	// Relations
	WorkCenter *WorkCenter `gorm:"foreignKey:WorkCenterID" json:"work_center,omitempty"`
}

func (RoutingStep) TableName() string { return "routing_steps" }

// ========== PRODUCTION ORDER ==========

// ProductionOrder represents a production order
type ProductionOrder struct {
	ID            string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID      string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	OrderNo       string     `gorm:"column:order_no;not null" json:"order_no"`
	Status        *string    `gorm:"column:status" json:"status"`
	Quantity      float64    `gorm:"column:quantity;not null" json:"quantity"`
	Progress      *int       `gorm:"column:progress" json:"progress"`
	ScheduledDate *time.Time `gorm:"column:scheduled_date" json:"scheduled_date"`
	Notes         *string    `gorm:"column:notes" json:"notes"`
	TargetQty     *float64   `gorm:"column:target_qty" json:"target_qty"`
	CompletedQty  *float64   `gorm:"column:completed_qty" json:"completed_qty"`
	Deadline      *time.Time `gorm:"column:deadline" json:"deadline"`
	StartedAt     *time.Time `gorm:"column:started_at" json:"started_at"`
	CompletedAt   *time.Time `gorm:"column:completed_at" json:"completed_at"`
	// Cost (HPP)
	LaborHours   *float64 `gorm:"column:labor_hours" json:"labor_hours"`
	HourlyRate   *float64 `gorm:"column:hourly_rate" json:"hourly_rate"`
	MaterialCost *float64 `gorm:"column:material_cost" json:"material_cost"`
	LaborCost    *float64 `gorm:"column:labor_cost" json:"labor_cost"`
	OverheadCost *float64 `gorm:"column:overhead_cost" json:"overhead_cost"`
	TotalHPP     *float64 `gorm:"column:total_hpp" json:"total_hpp"`
	HPPPerUnit   *float64 `gorm:"column:hpp_per_unit" json:"hpp_per_unit"`
	// Relations
	Products    []ProductionOrderProduct    `gorm:"foreignKey:ProductionOrderID" json:"products,omitempty"`
	WorkCenters []ProductionOrderWorkCenter `gorm:"foreignKey:ProductionOrderID" json:"work_centers,omitempty"`
}

func (ProductionOrder) TableName() string { return "production_orders" }

// ProductionOrderProduct links production order to products
type ProductionOrderProduct struct {
	ID                string   `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	ProductionOrderID string   `gorm:"column:production_order_id;type:uuid;not null" json:"production_order_id"`
	ProductID         string   `gorm:"column:product_id;type:uuid;not null" json:"product_id"`
	Product           *Product `gorm:"foreignKey:ProductID" json:"product,omitempty"`
}

func (ProductionOrderProduct) TableName() string { return "production_order_products" }

// ProductionOrderWorkCenter links production order to work centers
type ProductionOrderWorkCenter struct {
	ID                string      `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	ProductionOrderID string      `gorm:"column:production_order_id;type:uuid;not null" json:"production_order_id"`
	WorkCenterID      string      `gorm:"column:work_center_id;type:uuid;not null" json:"work_center_id"`
	WorkCenter        *WorkCenter `gorm:"foreignKey:WorkCenterID" json:"work_center,omitempty"`
}

func (ProductionOrderWorkCenter) TableName() string { return "production_order_work_centers" }

// ========== WORK ORDER ==========

// WorkOrder represents a work order linked to a production order
type WorkOrder struct {
	ID                string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID          string     `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	ProductionOrderID string     `gorm:"column:production_order_id;type:uuid;not null;index" json:"production_order_id"`
	RoutingStepID     *string    `gorm:"column:routing_step_id;type:uuid" json:"routing_step_id"`
	WorkCenterID      string     `gorm:"column:work_center_id;type:uuid;not null" json:"work_center_id"`
	WorkOrderNo       string     `gorm:"column:work_order_no;not null" json:"work_order_no"`
	Sequence          int        `gorm:"column:sequence;default:10" json:"sequence"`
	OperationName     string     `gorm:"column:operation_name;not null" json:"operation_name"`
	Status            string     `gorm:"column:status;default:'Pending'" json:"status"`
	PlannedQty        *float64   `gorm:"column:planned_qty;default:0" json:"planned_qty"`
	CompletedQty      *float64   `gorm:"column:completed_qty;default:0" json:"completed_qty"`
	ScrapQty          *float64   `gorm:"column:scrap_qty;default:0" json:"scrap_qty"`
	PlannedStart      *time.Time `gorm:"column:planned_start" json:"planned_start"`
	PlannedEnd        *time.Time `gorm:"column:planned_end" json:"planned_end"`
	ActualStart       *time.Time `gorm:"column:actual_start" json:"actual_start"`
	ActualEnd         *time.Time `gorm:"column:actual_end" json:"actual_end"`
	AssignedTo        *string    `gorm:"column:assigned_to;type:uuid" json:"assigned_to"`
	LaborHours        *float64   `gorm:"column:labor_hours;default:0" json:"labor_hours"`
	Notes             *string    `gorm:"column:notes" json:"notes"`
	// Relations
	WorkCenter *WorkCenter `gorm:"foreignKey:WorkCenterID" json:"work_center,omitempty"`
}

func (WorkOrder) TableName() string { return "work_orders" }

// ========== QUALITY CHECK ==========

// QualityCheck represents a quality check
type QualityCheck struct {
	ID                string    `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID          string    `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	ProductionOrderID *string   `gorm:"column:production_order_id;type:uuid" json:"production_order_id"`
	WorkOrderID       *string   `gorm:"column:work_order_id;type:uuid" json:"work_order_id"`
	ProductID         string    `gorm:"column:product_id;type:uuid;not null" json:"product_id"`
	QCNumber          string    `gorm:"column:qc_number;not null" json:"qc_number"`
	CheckDate         time.Time `gorm:"column:check_date;not null" json:"check_date"`
	Status            string    `gorm:"column:status;default:'Pending'" json:"status"`
	InspectedQty      *float64  `gorm:"column:inspected_qty;default:0" json:"inspected_qty"`
	PassedQty         *float64  `gorm:"column:passed_qty;default:0" json:"passed_qty"`
	FailedQty         *float64  `gorm:"column:failed_qty;default:0" json:"failed_qty"`
	InspectorID       *string   `gorm:"column:inspector_id;type:uuid" json:"inspector_id"`
	Notes             *string   `gorm:"column:notes" json:"notes"`
	DefectTypes       *string   `gorm:"column:defect_types" json:"defect_types"`
	// Relations
	Product     *Product       `gorm:"foreignKey:ProductID" json:"product,omitempty"`
	Checkpoints []QCCheckpoint `gorm:"foreignKey:QualityCheckID" json:"checkpoints,omitempty"`
}

func (QualityCheck) TableName() string { return "quality_checks" }

// QCCheckpoint represents a checkpoint in a quality check
type QCCheckpoint struct {
	ID             string  `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID       string  `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	QualityCheckID string  `gorm:"column:quality_check_id;type:uuid;not null;index" json:"quality_check_id"`
	CheckpointName string  `gorm:"column:checkpoint_name;not null" json:"checkpoint_name"`
	Specification  *string `gorm:"column:specification" json:"specification"`
	ActualValue    *string `gorm:"column:actual_value" json:"actual_value"`
	Passed         *bool   `gorm:"column:passed" json:"passed"`
	Notes          *string `gorm:"column:notes" json:"notes"`
}

func (QCCheckpoint) TableName() string { return "qc_checkpoints" }

// ========== BOM ==========

// BOMItem represents a BOM item
type BOMItem struct {
	ID              string   `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID        string   `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	BOMID           *string  `gorm:"column:bom_id;type:uuid" json:"bom_id"`
	ProductID       string   `gorm:"column:product_id;type:uuid;index;not null" json:"product_id"`
	ComponentID     *string  `gorm:"column:component_id;type:uuid" json:"component_id"`
	Quantity        float64  `gorm:"column:quantity;not null" json:"quantity"`
	UOM             *string  `gorm:"column:uom" json:"uom"`
	WastePercentage *float64 `gorm:"column:waste_percentage" json:"waste_percentage"`
	Notes           *string  `gorm:"column:notes" json:"notes"`
	// Relations
	Product   *Product `gorm:"foreignKey:ProductID" json:"product,omitempty"`
	Component *Product `gorm:"foreignKey:ComponentID" json:"component,omitempty"`
}

func (BOMItem) TableName() string { return "bom_items" }

// ========== LEGACY ==========

// ProductionQCResult represents legacy QC inspection result
type ProductionQCResult struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;not null;index" json:"tenant_id"`
	OrderID     string     `gorm:"column:order_id;type:uuid;index;not null" json:"order_id"`
	Inspector   *string    `gorm:"column:inspector" json:"inspector"`
	PassedQty   *float64   `gorm:"column:passed_qty" json:"passed_qty"`
	RejectedQty *float64   `gorm:"column:rejected_qty" json:"rejected_qty"`
	Notes       *string    `gorm:"column:notes" json:"notes"`
	InspectedAt *time.Time `gorm:"column:inspected_at" json:"inspected_at"`
}

func (ProductionQCResult) TableName() string { return "production_qc_results" }
