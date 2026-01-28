package models

import (
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// CreditNote represents a credit memo for returns or adjustments
type CreditNote struct {
	Base
	CreditNoteNumber string           `gorm:"type:varchar(50);not null" json:"credit_note_number"`
	InvoiceID        *string          `gorm:"type:uuid" json:"invoice_id"`
	CustomerID       *string          `gorm:"type:uuid" json:"customer_id"`
	Date             Date             `gorm:"type:date;default:CURRENT_DATE" json:"date"`
	Reason           string           `gorm:"type:varchar(100)" json:"reason"`                // return, adjustment, discount, other
	Status           string           `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, issued, applied, cancelled
	Subtotal         float64          `gorm:"type:decimal(15,2)" json:"subtotal"`
	TaxAmount        float64          `gorm:"type:decimal(15,2)" json:"tax_amount"`
	TotalAmount      float64          `gorm:"type:decimal(15,2)" json:"total_amount"`
	AppliedAmount    float64          `gorm:"type:decimal(15,2);default:0" json:"applied_amount"`
	Notes            string           `gorm:"type:text" json:"notes"`
	Items            []CreditNoteItem `gorm:"foreignKey:CreditNoteID" json:"items"`
}

func (CreditNote) TableName() string { return "sales_credit_notes" }

type CreditNoteItem struct {
	ID           string  `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	CreditNoteID string  `gorm:"type:uuid;not null;index" json:"credit_note_id"`
	ProductID    *string `gorm:"type:uuid" json:"product_id"`
	Description  string  `gorm:"type:text" json:"description"`
	Quantity     float64 `gorm:"type:decimal(10,2)" json:"quantity"`
	UnitPrice    float64 `gorm:"type:decimal(15,2)" json:"unit_price"`
	Total        float64 `gorm:"type:decimal(15,2)" json:"total"`
}

func (CreditNoteItem) TableName() string { return "sales_credit_note_items" }

func (item *CreditNoteItem) BeforeCreate(tx *gorm.DB) (err error) {
	if item.ID == "" {
		item.ID = uuid.New().String()
	}
	return
}

// PaymentRecord tracks payments against invoices
type PaymentRecord struct {
	ID        string  `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID  string  `gorm:"type:uuid;not null;index" json:"tenant_id"`
	InvoiceID string  `gorm:"type:uuid;not null;index" json:"invoice_id"`
	Date      Date    `gorm:"type:date;default:CURRENT_DATE" json:"date"`
	Amount    float64 `gorm:"type:decimal(15,2);not null" json:"amount"`
	Method    string  `gorm:"type:varchar(50)" json:"method"`     // cash, bank_transfer, credit_card, etc
	Reference string  `gorm:"type:varchar(100)" json:"reference"` // check number, transfer ref, etc
	Notes     string  `gorm:"type:text" json:"notes"`
	CreatedBy *string `gorm:"type:uuid" json:"created_by"`
}

func (PaymentRecord) TableName() string {
	return "payment_records"
}

func (p *PaymentRecord) BeforeCreate(tx *gorm.DB) (err error) {
	if p.ID == "" {
		p.ID = uuid.New().String()
	}
	return
}
