package database

import (
	"log"
	"time"

	"github.com/elviskudo/mini-erp/services/crm-service/internal/models"
	"gorm.io/gorm"
)

// Seed populates the database with initial data
func Seed(db *gorm.DB) {
	// Seed Promos
	var count int64
	db.Model(&models.Promo{}).Count(&count)
	if count == 0 {
		log.Println("🌱 Seeding Promos...")
		promos := []models.Promo{
			{
				Code:        "WELCOME10",
				Name:        "Welcome Discount",
				Description: pointString("10% off for new customers"),
				PromoType:   pointString("PERCENTAGE"),
				Value:       pointFloat(10),
				IsActive:    pointBool(true),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
			{
				Code:        "SUMMERSALE",
				Name:        "Summer Sale",
				Description: pointString("Fixed 50k off"),
				PromoType:   pointString("FIXED"),
				Value:       pointFloat(50000),
				IsActive:    pointBool(true),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
		}
		for _, p := range promos {
			// Assume default tenant for seeding
			tenantID := "00000000-0000-0000-0000-000000000000"
			p.TenantID = &tenantID
			db.Create(&p)
		}
	}

	// Seed Email Broadcasts
	db.Model(&models.EmailBroadcast{}).Count(&count)
	if count == 0 {
		log.Println("🌱 Seeding Email Broadcasts...")
		broadcasts := []models.EmailBroadcast{
			{
				TenantID:   "00000000-0000-0000-0000-000000000000",
				Subject:    "Monthly Newsletter",
				Body:       "Check out our latest updates...",
				Status:     "draft",
				Recipients: `["all_customers"]`,
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			},
		}
		for _, b := range broadcasts {
			db.Create(&b)
		}
	}
}

func pointString(s string) *string  { return &s }
func pointFloat(f float64) *float64 { return &f }
func pointBool(b bool) *bool        { return &b }
