package models

import "time"

type Vendor struct {
	ID          string   `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string   `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code        string   `gorm:"column:code;not null" json:"code"`
	Name        string   `gorm:"column:name;not null" json:"name"`
	Email       *string  `gorm:"column:email" json:"email"`
	Phone       *string  `gorm:"column:phone" json:"phone"`
	Address     *string  `gorm:"column:address" json:"address"`
	Rating      *string  `gorm:"column:rating" json:"rating"`
	Category    *string  `gorm:"column:category" json:"category"`
	PaymentTerm *string  `gorm:"column:payment_term" json:"payment_term"`
	CreditLimit *float64 `gorm:"column:credit_limit" json:"credit_limit"`
}

func (Vendor) TableName() string { return "vendors" }

type PurchaseRequest struct {
	ID           string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID     string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	PRNumber     *string    `gorm:"column:pr_number" json:"pr_number"`
	RequestedBy  *string    `gorm:"column:requested_by;type:uuid" json:"requested_by"`
	Status       *string    `gorm:"column:status" json:"status"`
	Priority     *string    `gorm:"column:priority" json:"priority"`
	RequiredDate *time.Time `gorm:"column:required_date" json:"required_date"`
	Notes        *string    `gorm:"column:notes" json:"notes"`
	TotalAmount  *float64   `gorm:"column:total_amount" json:"total_amount"`
	ApprovedBy   *string    `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	ApprovedAt   *time.Time `gorm:"column:approved_at" json:"approved_at"`
	CreatedAt    time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (PurchaseRequest) TableName() string { return "purchase_requests" }

type PurchaseOrder struct {
	ID               string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID         string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VendorID         string     `gorm:"column:vendor_id;type:uuid;not null" json:"vendor_id"`
	PONumber         *string    `gorm:"column:po_number" json:"po_number"`
	PRID             *string    `gorm:"column:pr_id;type:uuid" json:"pr_id"`
	Status           *string    `gorm:"column:status" json:"status"`
	BudgetChecked    *bool      `gorm:"column:budget_checked" json:"budget_checked"`
	Subtotal         *float64   `gorm:"column:subtotal" json:"subtotal"`
	ShippingCost     *float64   `gorm:"column:shipping_cost" json:"shipping_cost"`
	TotalAmount      *float64   `gorm:"column:total_amount" json:"total_amount"`
	ExpectedDelivery *time.Time `gorm:"column:expected_delivery" json:"expected_delivery"`
	Notes            *string    `gorm:"column:notes" json:"notes"`
	ApprovedBy       *string    `gorm:"column:approved_by;type:uuid" json:"approved_by"`
	ApprovedAt       *time.Time `gorm:"column:approved_at" json:"approved_at"`
	CreatedAt        time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (PurchaseOrder) TableName() string { return "purchase_orders" }

type VendorBill struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	VendorID    string     `gorm:"column:vendor_id;type:uuid" json:"vendor_id"`
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
