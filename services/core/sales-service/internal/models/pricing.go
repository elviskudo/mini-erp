package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// PriceList represents a price list for products
type PriceList struct {
	ID          string          `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID    string          `gorm:"type:uuid;not null;index" json:"tenant_id"`
	Name        string          `gorm:"type:varchar(100);not null" json:"name"`
	Description string          `gorm:"type:text" json:"description"`
	Currency    string          `gorm:"type:varchar(3);default:'IDR'" json:"currency"`
	ValidFrom   *Date           `gorm:"type:date" json:"valid_from"`
	ValidTo     *Date           `gorm:"type:date" json:"valid_to"`
	IsActive    bool            `gorm:"default:true" json:"is_active"`
	IsDefault   bool            `gorm:"default:false" json:"is_default"`
	CustomerID  *string         `gorm:"type:uuid;index" json:"customer_id"` // Optional: specific customer price list
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
	Items       []PriceListItem `gorm:"foreignKey:PriceListID" json:"items,omitempty"`
}

func (PriceList) TableName() string { return "sales_price_lists" }

// PriceListItem represents a product price in a price list
type PriceListItem struct {
	ID          string    `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	PriceListID string    `gorm:"type:uuid;not null;index" json:"price_list_id"`
	ProductID   string    `gorm:"type:uuid;not null;index" json:"product_id"`
	MinQuantity float64   `gorm:"type:decimal(10,2);default:1" json:"min_quantity"`
	Price       float64   `gorm:"type:decimal(15,2);not null" json:"price"`
	CreatedAt   time.Time `json:"created_at"`
}

func (PriceListItem) TableName() string { return "sales_price_list_items" }

func (item *PriceListItem) BeforeCreate(tx *gorm.DB) (err error) {
	if item.ID == "" {
		item.ID = uuid.New().String()
	}
	return
}

// DiscountRule represents a discount rule
type DiscountRule struct {
	ID          string    `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID    string    `gorm:"type:uuid;not null;index" json:"tenant_id"`
	Name        string    `gorm:"type:varchar(100);not null" json:"name"`
	Description string    `gorm:"type:text" json:"description"`
	Type        string    `gorm:"type:varchar(20);not null" json:"type"`            // PERCENTAGE, FIXED_AMOUNT, BUY_X_GET_Y
	Value       float64   `gorm:"type:decimal(15,2)" json:"value"`                  // Discount percentage or amount
	MinQuantity *float64  `gorm:"type:decimal(10,2)" json:"min_quantity"`           // Min qty to apply
	MinAmount   *float64  `gorm:"type:decimal(15,2)" json:"min_amount"`             // Min order amount
	MaxDiscount *float64  `gorm:"type:decimal(15,2)" json:"max_discount"`           // Max discount cap
	AppliesTo   string    `gorm:"type:varchar(20);default:'ALL'" json:"applies_to"` // ALL, PRODUCT, CATEGORY, CUSTOMER
	ProductID   *string   `gorm:"type:uuid" json:"product_id"`
	CategoryID  *string   `gorm:"type:uuid" json:"category_id"`
	CustomerID  *string   `gorm:"type:uuid" json:"customer_id"`
	ValidFrom   *Date     `gorm:"type:date" json:"valid_from"`
	ValidTo     *Date     `gorm:"type:date" json:"valid_to"`
	IsActive    bool      `gorm:"default:true" json:"is_active"`
	Priority    int       `gorm:"default:0" json:"priority"` // Higher priority applies first
	UsageLimit  *int      `gorm:"type:int" json:"usage_limit"`
	UsageCount  int       `gorm:"type:int;default:0" json:"usage_count"`
	PromoCode   *string   `gorm:"type:varchar(50);index" json:"promo_code"` // Optional promo code
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

func (DiscountRule) TableName() string { return "sales_discount_rules" }

// SalesContract represents a sales contract with a customer
type SalesContract struct {
	ID             string    `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID       string    `gorm:"type:uuid;not null;index" json:"tenant_id"`
	ContractNumber string    `gorm:"type:varchar(50);not null" json:"contract_number"`
	CustomerID     string    `gorm:"type:uuid;not null;index" json:"customer_id"`
	StartDate      Date      `gorm:"type:date;not null" json:"start_date"`
	EndDate        *Date     `gorm:"type:date" json:"end_date"`
	Status         string    `gorm:"type:varchar(20);default:'draft'" json:"status"` // draft, active, expired, cancelled
	TotalValue     float64   `gorm:"type:decimal(15,2)" json:"total_value"`
	PaymentTerms   string    `gorm:"type:varchar(50)" json:"payment_terms"`
	Terms          string    `gorm:"type:text" json:"terms"`
	Notes          string    `gorm:"type:text" json:"notes"`
	RenewalDate    *Date     `gorm:"type:date" json:"renewal_date"`
	AutoRenew      bool      `gorm:"default:false" json:"auto_renew"`
	CreatedBy      *string   `gorm:"type:uuid" json:"created_by"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

func (SalesContract) TableName() string { return "sales_contracts" }

// Commission represents sales commission tracking
type Commission struct {
	ID            string    `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
	TenantID      string    `gorm:"type:uuid;not null;index" json:"tenant_id"`
	SalespersonID string    `gorm:"type:uuid;not null;index" json:"salesperson_id"`
	OrderID       *string   `gorm:"type:uuid;index" json:"order_id"`
	InvoiceID     *string   `gorm:"type:uuid;index" json:"invoice_id"`
	OrderAmount   float64   `gorm:"type:decimal(15,2)" json:"order_amount"`
	Rate          float64   `gorm:"type:decimal(5,2)" json:"rate"` // Commission rate percentage
	Amount        float64   `gorm:"type:decimal(15,2)" json:"amount"`
	Status        string    `gorm:"type:varchar(20);default:'pending'" json:"status"` // pending, approved, paid, cancelled
	PaidDate      *Date     `gorm:"type:date" json:"paid_date"`
	Notes         string    `gorm:"type:text" json:"notes"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

func (Commission) TableName() string { return "sales_commissions" }
