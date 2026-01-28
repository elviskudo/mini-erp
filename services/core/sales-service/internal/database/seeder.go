package database

import (
	"log"
	"time"

	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"
	"gorm.io/gorm"
)

// Seed populates the database with initial data
func Seed(db *gorm.DB) {
	tenantID := "00000000-0000-0000-0000-000000000000"

	// Seed Price Lists
	var count int64
	db.Model(&models.PriceList{}).Count(&count)
	if count == 0 {
		log.Println("🌱 Seeding Price Lists...")
		lists := []models.PriceList{
			{
				TenantID:    tenantID,
				Name:        "Standard Retail",
				Description: "Default prices for retail customers",
				Currency:    "IDR",
				IsActive:    true,
				IsDefault:   true,
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
			{
				TenantID:    tenantID,
				Name:        "Wholesale",
				Description: "Prices for wholesale partners",
				Currency:    "IDR",
				IsActive:    true,
				IsDefault:   false,
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
		}
		for _, l := range lists {
			db.Create(&l)
		}
	}

	// Seed Discount Rules
	db.Model(&models.DiscountRule{}).Count(&count)
	if count == 0 {
		log.Println("🌱 Seeding Discount Rules...")
		rules := []models.DiscountRule{
			{
				TenantID:    tenantID,
				Name:        "Bulk Purchase Discount",
				Description: "5% off for orders over 10M",
				Type:        "PERCENTAGE",
				Value:       5,
				MinAmount:   pointFloat(10000000),
				AppliesTo:   "ALL",
				IsActive:    true,
				Priority:    10,
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
		}
		for _, r := range rules {
			db.Create(&r)
		}
	}
}

func pointFloat(f float64) *float64 { return &f }
