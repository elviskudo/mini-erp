package database

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/elviskudo/mini-erp/services/procurement-service/internal/database/seeders"
	"github.com/elviskudo/mini-erp/services/procurement-service/internal/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

func Connect() error {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://postgres:postgres@supabase-db:5432/mini_erp?sslmode=disable"
	}

	gormLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             time.Second,
			LogLevel:                  logger.Warn,
			IgnoreRecordNotFoundError: true,
			Colorful:                  true,
		},
	)

	var err error
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{Logger: gormLogger})
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Auto Migrate
	log.Println("🔄 Procurement Service: Running AutoMigrate...")
	if err := DB.AutoMigrate(
		&models.Vendor{},
		&models.PurchaseRequest{},
		&models.PurchaseRequestItem{},
		&models.PurchaseOrder{},
		&models.PurchaseOrderItem{},
		&models.VendorBill{},
		&models.RFQ{},
		&models.RFQItem{},
		&models.RFQVendor{},
		&models.Payment{},
	); err != nil {
		return fmt.Errorf("failed to migrate database: %w", err)
	}

	// Seed Data
	log.Println("🌱 Procurement Service: Checking if seeding is needed...")
	seeders.Seed(DB)

	sqlDB, err := DB.DB()
	if err != nil {
		return fmt.Errorf("failed to get database instance: %w", err)
	}

	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(100)
	sqlDB.SetConnMaxLifetime(time.Hour)

	log.Println("✅ Procurement Service: Database connected")
	return nil
}

func GetDB() *gorm.DB { return DB }

func Close() {
	if DB != nil {
		if sqlDB, _ := DB.DB(); sqlDB != nil {
			sqlDB.Close()
		}
	}
}
