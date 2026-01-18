package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Base model adds standardized UUID and Timestamps
type Base struct {
	ID        string         `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	TenantID  string         `gorm:"type:uuid;not null;index" json:"tenant_id"`
	CreatedBy string         `gorm:"type:uuid" json:"created_by"`
}

// Quotation
type Quotation struct {
	Base
	QuotationNumber string          `gorm:"type:varchar(50);not null" json:"quotation_number"`
	CustomerID      string          `gorm:"type:uuid" json:"customer_id"`
	Date            time.Time       `gorm:"type:date;default:CURRENT_DATE" json:"date"`
	ValidUntil      *time.Time      `gorm:"type:date" json:"valid_until"`
	Status          string          `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, sent, accepted, rejected
	Subtotal        float64         `gorm:"type:decimal(15,2)" json:"subtotal"`
	TaxAmount       float64         `gorm:"type:decimal(15,2)" json:"tax_amount"`
	DiscountAmount  float64         `gorm:"type:decimal(15,2)" json:"discount_amount"`
	TotalAmount     float64         `gorm:"type:decimal(15,2)" json:"total_amount"`
	Notes           string          `gorm:"type:text" json:"notes"`
	Items           []QuotationItem `gorm:"foreignKey:QuotationID" json:"items"`
}

type QuotationItem struct {
	ID          string  `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	QuotationID string  `gorm:"type:uuid;not null" json:"quotation_id"`
	ProductID   string  `gorm:"type:uuid" json:"product_id"`
	Description string  `gorm:"type:text" json:"description"`
	Quantity    float64 `gorm:"type:decimal(10,2)" json:"quantity"`
	UnitPrice   float64 `gorm:"type:decimal(15,2)" json:"unit_price"`
	Discount    float64 `gorm:"type:decimal(5,2)" json:"discount"` // Percent
	Tax         float64 `gorm:"type:decimal(5,2)" json:"tax"`      // Percent
	Total       float64 `gorm:"type:decimal(15,2)" json:"total"`
}

// SalesOrder
type SalesOrder struct {
	Base
	OrderNumber    string           `gorm:"type:varchar(50);not null" json:"order_number"`
	QuotationID    *string          `gorm:"type:uuid" json:"quotation_id"`
	CustomerID     string           `gorm:"type:uuid" json:"customer_id"`
	Date           time.Time        `gorm:"type:date;default:CURRENT_DATE" json:"date"`
	Status         string           `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, confirmed, processing, shipped, delivered, cancelled
	Subtotal       float64          `gorm:"type:decimal(15,2)" json:"subtotal"`
	TaxAmount      float64          `gorm:"type:decimal(15,2)" json:"tax_amount"`
	DiscountAmount float64          `gorm:"type:decimal(15,2)" json:"discount_amount"`
	TotalAmount    float64          `gorm:"type:decimal(15,2)" json:"total_amount"`
	PaymentStatus  string           `gorm:"type:varchar(20);default:'unpaid'" json:"payment_status"` // unpaid, partial, paid
	Notes          string           `gorm:"type:text" json:"notes"`
	Items          []SalesOrderItem `gorm:"foreignKey:SalesOrderID" json:"items"`
}

type SalesOrderItem struct {
	ID           string  `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	SalesOrderID string  `gorm:"type:uuid;not null" json:"sales_order_id"`
	ProductID    string  `gorm:"type:uuid" json:"product_id"`
	Description  string  `gorm:"type:text" json:"description"`
	Quantity     float64 `gorm:"type:decimal(10,2)" json:"quantity"`
	UnitPrice    float64 `gorm:"type:decimal(15,2)" json:"unit_price"`
	Discount     float64 `gorm:"type:decimal(5,2)" json:"discount"`
	Tax          float64 `gorm:"type:decimal(5,2)" json:"tax"`
	Total        float64 `gorm:"type:decimal(15,2)" json:"total"`
}

// Invoice
type Invoice struct {
	Base
	InvoiceNumber  string        `gorm:"type:varchar(50);not null" json:"invoice_number"`
	SalesOrderID   *string       `gorm:"type:uuid" json:"sales_order_id"`
	CustomerID     string        `gorm:"type:uuid" json:"customer_id"`
	Date           time.Time     `gorm:"type:date;default:CURRENT_DATE" json:"date"`
	DueDate        *time.Time    `gorm:"type:date" json:"due_date"`
	Status         string        `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, sent, paid, overdue, cancelled
	Subtotal       float64       `gorm:"type:decimal(15,2)" json:"subtotal"`
	TaxAmount      float64       `gorm:"type:decimal(15,2)" json:"tax_amount"`
	DiscountAmount float64       `gorm:"type:decimal(15,2)" json:"discount_amount"`
	TotalAmount    float64       `gorm:"type:decimal(15,2)" json:"total_amount"`
	PaidAmount     float64       `gorm:"type:decimal(15,2);default:0" json:"paid_amount"`
	Currency       string        `gorm:"type:varchar(3);default:'IDR'" json:"currency"`
	Notes          string        `gorm:"type:text" json:"notes"`
	Items          []InvoiceItem `gorm:"foreignKey:InvoiceID" json:"items"`
}

type InvoiceItem struct {
	ID          string  `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	InvoiceID   string  `gorm:"type:uuid;not null" json:"invoice_id"`
	ProductID   string  `gorm:"type:uuid" json:"product_id"`
	Description string  `gorm:"type:text" json:"description"`
	Quantity    float64 `gorm:"type:decimal(10,2)" json:"quantity"`
	UnitPrice   float64 `gorm:"type:decimal(15,2)" json:"unit_price"`
	Discount    float64 `gorm:"type:decimal(5,2)" json:"discount"`
	Tax         float64 `gorm:"type:decimal(5,2)" json:"tax"`
	Total       float64 `gorm:"type:decimal(15,2)" json:"total"`
}

func (base *Base) BeforeCreate(tx *gorm.DB) (err error) {
	if base.ID == "" {
		base.ID = uuid.New().String()
	}
	return
}
