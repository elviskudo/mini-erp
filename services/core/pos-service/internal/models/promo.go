package models

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// Promo represents a promotional offer for POS
type Promo struct {
	ID               string     `gorm:"column:id;type:uuid;primaryKey" json:"id"`
	TenantID         *string    `gorm:"column:tenant_id;type:uuid" json:"tenant_id"`
	Code             string     `gorm:"column:code;not null;index" json:"code"`
	Name             string     `gorm:"column:name;not null" json:"name"`
	Description      *string    `gorm:"column:description" json:"description"`
	PromoType        *string    `gorm:"column:promo_type" json:"promo_type"` // PERCENTAGE, FIXED, FREE_ITEM
	Value            *float64   `gorm:"column:value" json:"value"`
	MinOrder         *float64   `gorm:"column:min_order" json:"min_order"`
	MaxDiscount      *float64   `gorm:"column:max_discount" json:"max_discount"`
	StartDate        *time.Time `gorm:"column:start_date" json:"start_date"`
	EndDate          *time.Time `gorm:"column:end_date" json:"end_date"`
	IsActive         *bool      `gorm:"column:is_active;default:true" json:"is_active"`
	UsageLimit       *int       `gorm:"column:usage_limit" json:"usage_limit"`
	UsageCount       *int       `gorm:"column:usage_count;default:0" json:"usage_count"`
	PerCustomerLimit *int       `gorm:"column:per_customer_limit;default:1" json:"per_customer_limit"`
	CreatedBy        *string    `gorm:"column:created_by;type:uuid" json:"created_by"`
	CreatedAt        time.Time  `gorm:"column:created_at" json:"created_at"`
	UpdatedAt        time.Time  `gorm:"column:updated_at" json:"updated_at"`
}

func (Promo) TableName() string { return "pos_promos" }

func (p *Promo) BeforeCreate(tx *gorm.DB) (err error) {
	if p.ID == "" {
		p.ID = uuid.New().String()
	}
	return
}
