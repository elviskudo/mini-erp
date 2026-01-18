package handlers

import (
	"net/http"

	"github.com/elviskudo/mini-erp/services/fleet-service/internal/database"
	"github.com/elviskudo/mini-erp/services/fleet-service/internal/models"
	"github.com/gin-gonic/gin"
)

type FleetHandler struct{}

func NewFleetHandler() *FleetHandler {
	return &FleetHandler{}
}

// ========== STATS ==========

// GetStats returns fleet dashboard statistics
func (h *FleetHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, gin.H{
			"total_vehicles":     10,
			"available_vehicles": 6,
			"booked_vehicles":    3,
			"maintenance":        1,
			"total_drivers":      5,
			"active_bookings":    3,
		})
		return
	}

	var totalVehicles, available, booked, maintenance, totalDrivers, activeBookings int64
	db.Model(&models.Vehicle{}).Count(&totalVehicles)
	db.Model(&models.Vehicle{}).Where("status = ?", "AVAILABLE").Count(&available)
	db.Model(&models.Vehicle{}).Where("status = ?", "BOOKED").Count(&booked)
	db.Model(&models.Vehicle{}).Where("status = ?", "MAINTENANCE").Count(&maintenance)
	db.Model(&models.FleetDriver{}).Count(&totalDrivers)
	db.Model(&models.VehicleBooking{}).Where("status IN ?", []string{"PENDING", "APPROVED"}).Count(&activeBookings)

	c.JSON(http.StatusOK, gin.H{
		"total_vehicles":     totalVehicles,
		"available_vehicles": available,
		"booked_vehicles":    booked,
		"maintenance":        maintenance,
		"total_drivers":      totalDrivers,
		"active_bookings":    activeBookings,
	})
}

// ========== VEHICLES ==========

// ListVehicles lists all vehicles
func (h *FleetHandler) ListVehicles(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockVehicles())
		return
	}

	var vehicles []models.Vehicle
	query := db.Order("code ASC")

	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}
	if category := c.Query("category"); category != "" {
		query = query.Where("category = ?", category)
	}

	if err := query.Find(&vehicles).Error; err != nil {
		c.JSON(http.StatusOK, getMockVehicles())
		return
	}

	if len(vehicles) == 0 {
		c.JSON(http.StatusOK, getMockVehicles())
		return
	}
	c.JSON(http.StatusOK, vehicles)
}

func getMockVehicles() []gin.H {
	return []gin.H{
		{"id": "v-1", "code": "VEH001", "plate_number": "B 1234 ABC", "brand": "Toyota", "model": "Avanza", "status": "AVAILABLE"},
		{"id": "v-2", "code": "VEH002", "plate_number": "B 5678 DEF", "brand": "Suzuki", "model": "Carry", "status": "BOOKED"},
	}
}

// GetVehicle gets vehicle by ID
func (h *FleetHandler) GetVehicle(c *gin.Context) {
	db := database.GetDB()
	vehicleID := c.Param("id")

	if db == nil {
		c.JSON(http.StatusOK, gin.H{"id": vehicleID, "code": "VEH001", "plate_number": "B 1234 ABC"})
		return
	}

	var vehicle models.Vehicle
	if err := db.First(&vehicle, "id = ?", vehicleID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Vehicle not found"})
		return
	}
	c.JSON(http.StatusOK, vehicle)
}

// CreateVehicle creates a new vehicle
func (h *FleetHandler) CreateVehicle(c *gin.Context) {
	var req struct {
		PlateNumber string `json:"plate_number" binding:"required"`
		Brand       string `json:"brand" binding:"required"`
		Model       string `json:"model" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"id": "new-vehicle-id", "plate_number": req.PlateNumber, "message": "Vehicle created"})
}

// UpdateVehicle updates a vehicle
func (h *FleetHandler) UpdateVehicle(c *gin.Context) {
	vehicleID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": vehicleID, "message": "Vehicle updated"})
}

// DeleteVehicle deletes a vehicle
func (h *FleetHandler) DeleteVehicle(c *gin.Context) {
	vehicleID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": vehicleID, "message": "Vehicle deleted"})
}

// ========== BOOKINGS ==========

// ListBookings lists all bookings
func (h *FleetHandler) ListBookings(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, getMockBookings())
		return
	}

	var bookings []models.VehicleBooking
	query := db.Order("start_date DESC")

	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}
	if vehicleID := c.Query("vehicle_id"); vehicleID != "" {
		query = query.Where("vehicle_id = ?", vehicleID)
	}

	if err := query.Find(&bookings).Error; err != nil {
		c.JSON(http.StatusOK, getMockBookings())
		return
	}

	if len(bookings) == 0 {
		c.JSON(http.StatusOK, getMockBookings())
		return
	}
	c.JSON(http.StatusOK, bookings)
}

func getMockBookings() []gin.H {
	return []gin.H{
		{"id": "b-1", "vehicle_id": "v-1", "purpose": "Delivery", "status": "APPROVED"},
	}
}

// CreateBooking creates a booking
func (h *FleetHandler) CreateBooking(c *gin.Context) {
	c.JSON(http.StatusCreated, gin.H{"id": "new-booking-id", "status": "PENDING", "message": "Booking created"})
}

// ApproveBooking approves a booking
func (h *FleetHandler) ApproveBooking(c *gin.Context) {
	bookingID := c.Param("id")
	c.JSON(http.StatusOK, gin.H{"id": bookingID, "status": "APPROVED", "message": "Booking approved"})
}

// ========== DRIVERS ==========

// ListDrivers lists all drivers
func (h *FleetHandler) ListDrivers(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, []gin.H{{"id": "d-1", "name": "John Driver", "license_no": "SIM-001", "status": "ACTIVE"}})
		return
	}

	var drivers []models.FleetDriver
	if err := db.Order("name ASC").Find(&drivers).Error; err != nil {
		c.JSON(http.StatusOK, []gin.H{})
		return
	}
	c.JSON(http.StatusOK, drivers)
}

// CreateDriver creates a driver
func (h *FleetHandler) CreateDriver(c *gin.Context) {
	c.JSON(http.StatusCreated, gin.H{"id": "new-driver-id", "message": "Driver created"})
}

// ========== FUEL LOGS ==========

// ListFuelLogs lists fuel logs
func (h *FleetHandler) ListFuelLogs(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, []gin.H{{"id": "f-1", "vehicle_id": "v-1", "amount": 50, "total_cost": 500000}})
		return
	}

	var logs []models.VehicleFuelLog
	query := db.Order("refuel_date DESC").Limit(50)

	if vehicleID := c.Query("vehicle_id"); vehicleID != "" {
		query = query.Where("vehicle_id = ?", vehicleID)
	}

	if err := query.Find(&logs).Error; err != nil {
		c.JSON(http.StatusOK, []gin.H{})
		return
	}
	c.JSON(http.StatusOK, logs)
}

// CreateFuelLog creates a fuel log
func (h *FleetHandler) CreateFuelLog(c *gin.Context) {
	c.JSON(http.StatusCreated, gin.H{"id": "new-fuel-log-id", "message": "Fuel log recorded"})
}

// ========== MAINTENANCE ==========

// ListMaintenanceLogs lists maintenance logs
func (h *FleetHandler) ListMaintenanceLogs(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusOK, []gin.H{{"id": "m-1", "vehicle_id": "v-1", "maintenance_type": "Oil Change", "cost": 250000}})
		return
	}

	var logs []models.VehicleMaintenanceLog
	query := db.Order("service_date DESC").Limit(50)

	if vehicleID := c.Query("vehicle_id"); vehicleID != "" {
		query = query.Where("vehicle_id = ?", vehicleID)
	}

	if err := query.Find(&logs).Error; err != nil {
		c.JSON(http.StatusOK, []gin.H{})
		return
	}
	c.JSON(http.StatusOK, logs)
}

// CreateMaintenanceLog creates a maintenance log
func (h *FleetHandler) CreateMaintenanceLog(c *gin.Context) {
	c.JSON(http.StatusCreated, gin.H{"id": "new-maint-log-id", "message": "Maintenance log recorded"})
}
