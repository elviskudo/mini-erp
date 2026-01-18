package main

import (
	"log"

	"github.com/elviskudo/mini-erp/services/auth-service/internal/database"
)

func main() {
	log.Println("🌱 Starting manual menu seeding...")

	if err := database.Connect(); err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	defer database.Close()

	if err := database.SeedMenus(); err != nil {
		log.Fatalf("❌ Menu seeding failed: %v", err)
	}

	log.Println("✨ Manual menu seeding completed successfully!")
}
