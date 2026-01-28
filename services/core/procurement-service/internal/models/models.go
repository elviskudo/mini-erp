package models

import "time"

type Vendor struct {
	ID          string    `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string    `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code        string    `gorm:"column:code;not null" json:"code"`
	Name        string    `gorm:"column:name;not null" json:"name"`
	Email       *string   `gorm:"column:email" json:"email"`
	Phone       *string   `gorm:"column:phone" json:"phone"`
	Address     *string   `gorm:"column:address" json:"address"`
	City        *string   `gorm:"column:city" json:"city"`
	Country     *string   `gorm:"column:country" json:"country"`
	Rating      *string   `gorm:"column:rating" json:"rating"`
	Category    *string   `gorm:"column:category" json:"category"`
	PaymentTerm *string   `gorm:"column:payment_term" json:"payment_term"`
	CreditLimit *float64  `gorm:"column:credit_limit" json:"credit_limit"`
	IsActive    *bool     `gorm:"column:is_active;default:true" json:"is_active"`
	CreatedAt   time.Time `gorm:"column:created_at" json:"created_at"`
	UpdatedAt   time.Time `gorm:"column:updated_at" json:"updated_at"`
}

func (Vendor) TableName() string { return "vendors" }

type PurchaseRequest struct {
	ID           string                `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string                `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	PRNumber     *string               `gorm:"column:pr_number" json:"pr_number"`
	RequestedBy  *string               `gorm:"column:requested_by;type:uuid" json:"requested_by"`
	Status       *string               `gorm:"column:status" json:"status"`
	Priority     *string               `gorm:"column:priority" json:"priority"`
	RequiredDate *time.Time            `gorm:"column:required_date" json:"required_date"`
	Notes        *string               `gorm:"column:notes" json:"notes"`
	TotalAmount  *float64              `gorm:"column:total_amount" json:"total_amount"`
	ApprovedBy   *string               `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	ApprovedAt   *time.Time            `gorm:"column:approved_at" json:"approved_at"`
	CreatedAt    time.Time             `gorm:"column:created_at" json:"created_at"`
	RejectReason *string               `gorm:"column:reject_reason" json:"reject_reason"`
	RejectedAt   *time.Time            `gorm:"column:rejected_at" json:"rejected_at"`
	Items        []PurchaseRequestItem `gorm:"foreignKey:PRID" json:"items"`
}

func (PurchaseRequest) TableName() string { return "purchase_requests" }

type PurchaseRequestItem struct {
	ID        string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	PRID      string  `gorm:"column:pr_id;type:uuid;index;not null" json:"pr_id"`
	ProductID string  `gorm:"column:product_id;type:uuid;not null" json:"product_id"`
	Quantity  float64 `gorm:"column:quantity;not null" json:"quantity"`
	Notes     *string `gorm:"column:notes" json:"notes"`
}

func (PurchaseRequestItem) TableName() string { return "purchase_request_items" }

type PurchaseOrder struct {
	ID               string              `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID         string              `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VendorID         string              `gorm:"column:vendor_id;type:uuid;not null" json:"vendor_id"`
	Vendor           *Vendor             `gorm:"foreignKey:VendorID" json:"vendor"`
	PONumber         *string             `gorm:"column:po_number" json:"po_number"`
	PRID             *string             `gorm:"column:pr_id;type:uuid" json:"pr_id"`
	Status           *string             `gorm:"column:status" json:"status"`
	BudgetChecked    *bool               `gorm:"column:budget_checked" json:"budget_checked"`
	Subtotal         *float64            `gorm:"column:subtotal" json:"subtotal"`
	ShippingCost     *float64            `gorm:"column:shipping_cost" json:"shipping_cost"`
	TotalAmount      *float64            `gorm:"column:total_amount" json:"total_amount"`
	ExpectedDelivery *time.Time          `gorm:"column:expected_delivery" json:"expected_delivery"`
	Notes            *string             `gorm:"column:notes" json:"notes"`
	ApprovedBy       *string             `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	ApprovedAt       *time.Time          `gorm:"column:approved_at" json:"approved_at"`
	CreatedAt        time.Time           `gorm:"column:created_at" json:"created_at"`
	Items            []PurchaseOrderItem `gorm:"foreignKey:POID" json:"items"`
}

func (PurchaseOrder) TableName() string { return "purchase_orders" }

type PurchaseOrderItem struct {
	ID          string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	POID        string  `gorm:"column:po_id;type:uuid;index;not null" json:"po_id"`
	ProductID   string  `gorm:"column:product_id;type:uuid;not null" json:"product_id"`
	Quantity    float64 `gorm:"column:quantity;not null" json:"quantity"`
	UnitPrice   float64 `gorm:"column:unit_price;not null" json:"unit_price"`
	ReceivedQty float64 `gorm:"column:received_qty;default:0" json:"received_qty"`
	LineTotal   float64 `gorm:"column:line_total" json:"line_total"`
}

func (PurchaseOrderItem) TableName() string { return "purchase_order_items" }

type VendorBill struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VendorID    string     `gorm:"column:vendor_id;type:uuid" json:"vendor_id"`
	Vendor      *Vendor    `gorm:"foreignKey:VendorID" json:"vendor"`
	POID        *string    `gorm:"column:po_id;type:uuid" json:"po_id"`
	BillNumber  *string    `gorm:"column:bill_number" json:"bill_number"`
	BillDate    *time.Time `gorm:"column:bill_date" json:"bill_date"`
	DueDate     *time.Time `gorm:"column:due_date" json:"due_date"`
	Status      *string    `gorm:"column:status" json:"status"`
	TotalAmount *float64   `gorm:"column:total_amount" json:"total_amount"`
	PaidAmount  *float64   `gorm:"column:paid_amount" json:"paid_amount"`
	CreatedAt   time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (VendorBill) TableName() string { return "vendor_bills" }

type Payment struct {
	ID            string      `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID      string      `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	BillID        string      `gorm:"column:bill_id;type:uuid;index;not null" json:"bill_id"`
	Bill          *VendorBill `gorm:"foreignKey:BillID" json:"bill"`
	Amount        float64     `gorm:"column:amount;not null" json:"amount"`
	PaymentMethod string      `gorm:"column:payment_method" json:"payment_method"`
	Reference     *string     `gorm:"column:reference" json:"reference"`
	PaymentDate   time.Time   `gorm:"column:payment_date" json:"payment_date"`
	CreatedAt     time.Time   `gorm:"column:created_at" json:"created_at"`
}

func (Payment) TableName() string { return "payments" }

type RFQ struct {
	ID        string      `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID  string      `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	RFQNumber string      `gorm:"column:rfq_number;not null" json:"rfq_number"`
	Status    string      `gorm:"column:status;not null" json:"status"` // Draft, Sent, Received, Closed
	Deadline  *time.Time  `gorm:"column:deadline" json:"deadline"`
	Priority  string      `gorm:"column:priority" json:"priority"`
	Notes     *string     `gorm:"column:notes" json:"notes"`
	CreatedAt time.Time   `gorm:"column:created_at" json:"created_at"`
	UpdatedAt time.Time   `gorm:"column:updated_at" json:"updated_at"`
	Items     []RFQItem   `gorm:"foreignKey:RFQID" json:"items"`
	Vendors   []RFQVendor `gorm:"foreignKey:RFQID" json:"vendors"`
}

func (RFQ) TableName() string { return "rfqs" }

type RFQItem struct {
	ID             string  `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID       string  `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	RFQID          string  `gorm:"column:rfq_id;type:uuid;index;not null" json:"rfq_id"`
	ProductID      string  `gorm:"column:product_id;type:uuid;not null" json:"product_id"`
	Quantity       float64 `gorm:"column:quantity;not null" json:"quantity"`
	Specifications *string `gorm:"column:specifications" json:"specifications"`
}

func (RFQItem) TableName() string { return "rfq_items" }

type RFQVendor struct {
	ID           string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	RFQID        string     `gorm:"column:rfq_id;type:uuid;index;not null" json:"rfq_id"`
	VendorID     string     `gorm:"column:vendor_id;type:uuid;not null" json:"vendor_id"`
	Vendor       *Vendor    `gorm:"foreignKey:VendorID" json:"vendor"`
	IsSelected   bool       `gorm:"column:is_selected;default:false" json:"is_selected"`
	QuotedAmount *float64   `gorm:"column:quoted_amount" json:"quoted_amount"`
	DeliveryDays *int       `gorm:"column:delivery_days" json:"delivery_days"`
	QuoteDate    *time.Time `gorm:"column:quote_date" json:"quote_date"`
}

func (RFQVendor) TableName() string { return "rfq_vendors" }
