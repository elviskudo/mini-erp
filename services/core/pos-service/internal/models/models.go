package models

import "time"

type POSTransaction struct {
	ID                string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID          string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	TransactionNumber *string    `gorm:"column:transaction_number" json:"transaction_number"`
	TerminalID        *string    `gorm:"column:terminal_id" json:"terminal_id"`
	CashierID         *string    `gorm:"column:cashier_id;type:uuid" json:"cashier_id"`
	CustomerID        *string    `gorm:"column:customer_id;type:uuid" json:"customer_id"`
	TransactionType   *string    `gorm:"column:transaction_type" json:"transaction_type"`
	Status            *string    `gorm:"column:status" json:"status"`
	Subtotal          *float64   `gorm:"column:subtotal" json:"subtotal"`
	TaxAmount         *float64   `gorm:"column:tax_amount" json:"tax_amount"`
	DiscountAmount    *float64   `gorm:"column:discount_amount" json:"discount_amount"`
	TotalAmount       *float64   `gorm:"column:total_amount" json:"total_amount"`
	PaymentMethod     *string    `gorm:"column:payment_method" json:"payment_method"`
	PaymentReference  *string    `gorm:"column:payment_reference" json:"payment_reference"`
	ChangeAmount      *float64   `gorm:"column:change_amount" json:"change_amount"`
	Notes             *string    `gorm:"column:notes" json:"notes"`
	TransactionDate   *time.Time `gorm:"column:transaction_date" json:"transaction_date"`
	CreatedAt         time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (POSTransaction) TableName() string { return "pos_transactions" }

type POSPromo struct {
	ID          string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID    string     `gorm:"column:tenant_id;type:uuid;index;not null" json:"tenant_id"`
	Code        string     `gorm:"column:code;not null" json:"code"`
	Name        *string    `gorm:"column:name" json:"name"`
	Type        *string    `gorm:"column:type" json:"type"`
	Value       *float64   `gorm:"column:value" json:"value"`
	MinPurchase *float64   `gorm:"column:min_purchase" json:"min_purchase"`
	StartDate   *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate     *time.Time `gorm:"column:end_date" json:"end_date"`
	IsActive    *bool      `gorm:"column:is_active" json:"is_active"`
	CreatedAt   time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (POSPromo) TableName() string { return "pos_promos" }
