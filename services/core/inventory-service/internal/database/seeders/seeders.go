package seeders

import (
	"log"
	"time"

	"github.com/elviskudo/mini-erp/services/inventory-service/internal/models"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func Seed(db *gorm.DB) {
	SeedWarehouses(db)
	SeedCategories(db)
	SeedProducts(db)
}

func SeedWarehouses(db *gorm.DB) {
	var count int64
	db.Model(&models.Warehouse{}).Count(&count)
	if count > 0 {
		return
	}

	log.Println("🌱 Seeding Warehouses...")
	warehouses := []models.Warehouse{
		{
			ID:        "wh-1",
			TenantID:  "00000000-0000-0000-0000-000000000000",
			Code:      "WH-JKT",
			Name:      "Jakarta Main Warehouse",
			City:      toPtr("Jakarta"),
			IsActive:  toPtr(true),
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
		{
			ID:        "wh-2",
			TenantID:  "00000000-0000-0000-0000-000000000000",
			Code:      "WH-SBY",
			Name:      "Surabaya Hub",
			City:      toPtr("Surabaya"),
			IsActive:  toPtr(true),
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
	}

	for _, wh := range warehouses {
		db.Create(&wh)
	}
}

func SeedCategories(db *gorm.DB) {
	// Note: Inventory Service might not have a dedicated Categories table model in the file I read,
	// but Products have 'Category' string and 'CategoryID'.
	// If there is no Category model in models.go, we skip this or just ensure Products have category names.
	// Checked models.go earlier: It does NOT have a Category struct, only Product struct has CategoryID and Category name.
	// So we define implicit categories in Products.
}

func SeedProducts(db *gorm.DB) {
	var count int64
	db.Model(&models.Product{}).Count(&count)
	if count > 0 {
		return
	}

	log.Println("🌱 Seeding Products...")

	rawType := "RAW_MATERIAL"
	finType := "FINISHED_GOOD"

	products := []models.Product{
		{
			ID:           uuid.NewString(),
			TenantID:     "00000000-0000-0000-0000-000000000000",
			Code:         "RM-001",
			Name:         "Cotton Fabric 100%",
			Type:         &rawType,
			UOM:          toPtr("Roll"),
			StandardCost: toPtr(500000.0),
			Category:     toPtr("Fabrics"),
			Description:  toPtr("High quality cotton fabric"),
			IsActive:     toPtr(true),
		},
		{
			ID:           uuid.NewString(),
			TenantID:     "00000000-0000-0000-0000-000000000000",
			Code:         "RM-002",
			Name:         "Polyester Thread",
			Type:         &rawType,
			UOM:          toPtr("Box"),
			StandardCost: toPtr(25000.0),
			Category:     toPtr("Threads"),
			IsActive:     toPtr(true),
		},
		{
			ID:           uuid.NewString(),
			TenantID:     "00000000-0000-0000-0000-000000000000",
			Code:         "FG-001",
			Name:         "Mens T-Shirt Basic",
			Type:         &finType,
			UOM:          toPtr("Pcs"),
			StandardCost: toPtr(35000.0),
			Category:     toPtr("Apparel"),
			IsActive:     toPtr(true),
		},
		{
			ID:           uuid.NewString(),
			TenantID:     "00000000-0000-0000-0000-000000000000",
			Code:         "FG-002",
			Name:         "Denim Jeans Classic",
			Type:         &finType,
			UOM:          toPtr("Pcs"),
			StandardCost: toPtr(120000.0),
			Category:     toPtr("Apparel"),
			IsActive:     toPtr(true),
		},
		{
			ID:           uuid.NewString(),
			TenantID:     "00000000-0000-0000-0000-000000000000",
			Code:         "PKG-001",
			Name:         "Cardboard Box L",
			Type:         &rawType,
			UOM:          toPtr("Pcs"),
			StandardCost: toPtr(5000.0),
			Category:     toPtr("Packaging"),
			IsActive:     toPtr(true),
		},
	}

	for _, p := range products {
		db.Create(&p)
	}

	// Also Seed Stock for these products so they are usable
	SeedStock(db, products)
}

func SeedStock(db *gorm.DB, products []models.Product) {
	// Create some initial stock batches
	whID := "wh-1"

	for _, p := range products {
		batch := models.InventoryBatch{
			ID:          uuid.NewString(),
			TenantID:    "00000000-0000-0000-0000-000000000000",
			ProductID:   p.ID,
			WarehouseID: &whID,
			Quantity:    100,
			UnitCost:    p.StandardCost,
		}
		db.Create(&batch)
	}
}

func toPtr[T any](v T) *T {
	return &v
}
