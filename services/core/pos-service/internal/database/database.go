package database

import (
	"fmt"
	"log"
	"os"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"github.com/elviskudo/mini-erp/services/pos-service/internal/models"
)

var DB *gorm.DB

func Connect() error {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://postgres:postgres@supabase-db:5432/mini_erp?sslmode=disable"
	}
	gormLogger := logger.New(log.New(os.Stdout, "\r\n", log.LstdFlags), logger.Config{SlowThreshold: time.Second, LogLevel: logger.Warn, IgnoreRecordNotFoundError: true, Colorful: true})
	var err error
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{Logger: gormLogger})
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	sqlDB, _ := DB.DB()
	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(100)
	// Auto Migrate
	err = DB.AutoMigrate(
		&models.POSTransaction{},
		&models.Promo{},
	)
	if err != nil {
		return fmt.Errorf("failed to migrate database: %w", err)
	}
	log.Println("✅ POS Service: Database connected")
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
