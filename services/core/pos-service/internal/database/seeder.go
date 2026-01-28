package database

import (
	"log"
	"time"

	"github.com/elviskudo/mini-erp/services/pos-service/internal/models"
	"gorm.io/gorm"
)

// Seed populates the database with initial data
func Seed(db *gorm.DB) {
	var count int64
	db.Model(&models.Promo{}).Count(&count)
	if count == 0 {
		log.Println("🌱 Seeding POS Promos...")
		promos := []models.Promo{
			{
				TenantID:    pointString("00000000-0000-0000-0000-000000000000"),
				Code:        "FLASH50",
				Name:        "Flash Sale 50%",
				Description: pointString("50% off for next hour"),
				PromoType:   pointString("PERCENTAGE"),
				Value:       pointFloat(50),
				IsActive:    pointBool(true),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
			{
				TenantID:    pointString("00000000-0000-0000-0000-000000000000"),
				Code:        "BUY1GET1",
				Name:        "Buy 1 Get 1 Free",
				Description: pointString("Buy any item, get cheapest free"),
				PromoType:   pointString("FREE_ITEM"),
				IsActive:    pointBool(true),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
		}
		for _, p := range promos {
			db.Create(&p)
		}
	}
}

func pointString(s string) *string  { return &s }
func pointFloat(f float64) *float64 { return &f }
func pointBool(b bool) *bool        { return &b }
