package seeders

import (
	"log"
	"time"

	"github.com/elviskudo/mini-erp/services/procurement-service/internal/models"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func Seed(db *gorm.DB) {
	SeedVendors(db)
}

func SeedVendors(db *gorm.DB) {
	var count int64
	db.Model(&models.Vendor{}).Count(&count)
	if count > 0 {
		return
	}

	log.Println("🌱 Seeding Vendors...")

	vendors := []models.Vendor{
		{
			ID:        uuid.NewString(),
			Code:      "VND-001",
			Name:      "PT Supplier Jaya",
			Email:     toPtr("sales@supplierjaya.com"),
			Phone:     toPtr("021-12345678"),
			Address:   toPtr("Jl. Industri Raya No. 1, Jakarta"),
			City:      toPtr("Jakarta"),
			IsActive:  toPtr(true),
			CreatedAt: time.Now(),
		},
		{
			ID:        uuid.NewString(),
			Code:      "VND-002",
			Name:      "CV Maju Bersama",
			Email:     toPtr("info@majubersama.co.id"),
			Phone:     toPtr("031-87654321"),
			Address:   toPtr("Jl. Rungkut Industri No. 5, Surabaya"),
			City:      toPtr("Surabaya"),
			IsActive:  toPtr(true),
			CreatedAt: time.Now(),
		},
		{
			ID:        uuid.NewString(),
			Code:      "VND-IMPT",
			Name:      "Global Imports Ltd.",
			Email:     toPtr("sales@globalimports.com"),
			Phone:     toPtr("+65-67890123"),
			Address:   toPtr("1 Raffles Place, Singapore"),
			City:      toPtr("Singapore"),
			Country:   toPtr("Singapore"),
			IsActive:  toPtr(true),
			CreatedAt: time.Now(),
		},
	}

	for _, v := range vendors {
		db.Create(&v)
	}
}

func toPtr[T any](v T) *T {
	return &v
}
