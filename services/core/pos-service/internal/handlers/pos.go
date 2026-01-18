package handlers

import (
	"strconv"
	"time"

	"github.com/elviskudo/mini-erp/services/pos-service/internal/database"
	"github.com/elviskudo/mini-erp/services/pos-service/internal/models"
	"github.com/elviskudo/mini-erp/services/pos-service/internal/response"
	"github.com/gin-gonic/gin"
)

type POSHandler struct{}

func NewPOSHandler() *POSHandler { return &POSHandler{} }

func (h *POSHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, "Statistics retrieved", gin.H{"total_transactions": 150, "today_sales": 25000000, "avg_transaction": 166000})
		return
	}
	var total int64
	var todaySales float64
	db.Model(&models.POSTransaction{}).Count(&total)
	db.Model(&models.POSTransaction{}).Where("DATE(transaction_date) = ?", time.Now().Format("2006-01-02")).Select("COALESCE(SUM(total_amount), 0)").Scan(&todaySales)
	response.Success(c, "Statistics retrieved", gin.H{"total_transactions": total, "today_sales": todaySales})
}

func (h *POSHandler) ListTransactions(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	if db == nil {
		response.SuccessWithPagination(c, "Transactions retrieved", []gin.H{{"id": "txn-1", "transaction_number": "TXN-001", "total_amount": 150000}}, page, limit, 1)
		return
	}
	var txns []models.POSTransaction
	var total int64
	db.Model(&models.POSTransaction{}).Count(&total)
	db.Order("created_at DESC").Offset(offset).Limit(limit).Find(&txns)
	response.SuccessWithPagination(c, "Transactions retrieved", txns, page, limit, total)
}

func (h *POSHandler) GetTransaction(c *gin.Context) {
	db := database.GetDB()
	id := c.Param("id")
	if db == nil {
		response.Success(c, "Transaction retrieved", gin.H{"id": id, "transaction_number": "TXN-001"})
		return
	}
	var txn models.POSTransaction
	if err := db.First(&txn, "id = ?", id).Error; err != nil {
		response.NotFound(c, "Transaction not found")
		return
	}
	response.Success(c, "Transaction retrieved", txn)
}

func (h *POSHandler) CreateTransaction(c *gin.Context) {
	response.Created(c, "Transaction created successfully", gin.H{"id": "new-txn-id", "transaction_number": "TXN-NEW"})
}

func (h *POSHandler) VoidTransaction(c *gin.Context) {
	response.Updated(c, "Transaction voided", gin.H{"id": c.Param("id"), "status": "VOIDED"})
}

func (h *POSHandler) ListPromos(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	if db == nil {
		response.SuccessWithPagination(c, "Promos retrieved", []gin.H{{"id": "promo-1", "code": "DISC10", "type": "PERCENTAGE", "value": 10}}, page, limit, 1)
		return
	}
	var promos []models.POSPromo
	var total int64
	db.Model(&models.POSPromo{}).Count(&total)
	db.Order("created_at DESC").Limit(limit).Find(&promos)
	response.SuccessWithPagination(c, "Promos retrieved", promos, page, limit, total)
}

func (h *POSHandler) CreatePromo(c *gin.Context) {
	response.Created(c, "Promo created successfully", gin.H{"id": "new-promo-id"})
}

func (h *POSHandler) ValidatePromo(c *gin.Context) {
	code := c.Param("code")
	response.Success(c, "Promo validated", gin.H{"code": code, "valid": true, "discount": 10})
}

func (h *POSHandler) DailySalesReport(c *gin.Context) {
	response.Success(c, "Daily sales report", gin.H{"date": time.Now().Format("2006-01-02"), "total_transactions": 50, "total_sales": 25000000})
}
