package database

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/elviskudo/mini-erp/services/sales-service/internal/models"

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
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: gormLogger,
	})
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	sqlDB, err := DB.DB()
	if err != nil {
		return fmt.Errorf("failed to get database instance: %w", err)
	}

	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(100)
	sqlDB.SetConnMaxLifetime(time.Hour)

	log.Println("💰 Sales Service: Database connected")

	// Auto Migrate
	err = DB.AutoMigrate(
		&models.Quotation{},
		&models.QuotationItem{},
		&models.SalesOrder{},
		&models.SalesOrderItem{},
		&models.Invoice{},
		&models.InvoiceItem{},
		&models.CreditNote{},
		&models.CreditNoteItem{},
		&models.PaymentRecord{},
		&models.PriceList{},
		&models.PriceListItem{},
		&models.DiscountRule{},
		&models.SalesContract{},
		&models.Commission{},
	)
	if err != nil {
		return fmt.Errorf("failed to migrate database: %w", err)
	}

	return nil
}

func GetDB() *gorm.DB {
	return DB
}

func Close() {
	if DB != nil {
		sqlDB, _ := DB.DB()
		if sqlDB != nil {
			sqlDB.Close()
		}
	}
}
