package response

import (
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// Response is the standardized API response format
type Response struct {
	Success   bool        `json:"success"`
	Code      string      `json:"code"`
	Message   string      `json:"message"`
	Data      interface{} `json:"data"`
	Meta      *Meta       `json:"meta"`
	Errors    []Error     `json:"errors"`
	Timestamp string      `json:"timestamp"`
	RequestID string      `json:"request_id"`
}

// Meta contains pagination, sort and filter info
type Meta struct {
	Pagination *Pagination       `json:"pagination,omitempty"`
	Sort       *Sort             `json:"sort,omitempty"`
	Filters    map[string]string `json:"filters,omitempty"`
}

// Pagination info for list endpoints
type Pagination struct {
	Page       int   `json:"page"`
	Limit      int   `json:"limit"`
	TotalItems int64 `json:"total_items"`
	TotalPages int   `json:"total_pages"`
	HasNext    bool  `json:"has_next"`
	HasPrev    bool  `json:"has_prev"`
}

// Sort info
type Sort struct {
	By    string `json:"by"`
	Order string `json:"order"`
}

// Error for validation errors
type Error struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// generateRequestID creates a unique request ID
func generateRequestID() string {
	return "req_" + uuid.New().String()[:8]
}

// getTimestamp returns current UTC timestamp
func getTimestamp() string {
	return time.Now().UTC().Format(time.RFC3339)
}

// Success returns a successful response with data
func Success(c *gin.Context, data interface{}, message string) {
	c.JSON(200, Response{
		Success:   true,
		Code:      "SUCCESS",
		Message:   message,
		Data:      data,
		Meta:      nil,
		Errors:    nil,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// SuccessCreate returns 201 for created resources
func SuccessCreate(c *gin.Context, data interface{}, message string) {
	c.JSON(201, Response{
		Success:   true,
		Code:      "CREATED",
		Message:   message,
		Data:      data,
		Meta:      nil,
		Errors:    nil,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// SuccessList returns a successful list response with pagination
func SuccessList(c *gin.Context, data interface{}, page, limit int, total int64, message string) {
	totalPages := int(total) / limit
	if int(total)%limit > 0 {
		totalPages++
	}

	c.JSON(200, Response{
		Success: true,
		Code:    "SUCCESS",
		Message: message,
		Data:    data,
		Meta: &Meta{
			Pagination: &Pagination{
				Page:       page,
				Limit:      limit,
				TotalItems: total,
				TotalPages: totalPages,
				HasNext:    page < totalPages,
				HasPrev:    page > 1,
			},
		},
		Errors:    nil,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// SuccessListWithSort returns list with pagination and sort/filter info
func SuccessListWithSort(c *gin.Context, data interface{}, page, limit int, total int64, sortBy, sortOrder string, filters map[string]string, message string) {
	totalPages := int(total) / limit
	if int(total)%limit > 0 {
		totalPages++
	}

	c.JSON(200, Response{
		Success: true,
		Code:    "SUCCESS",
		Message: message,
		Data:    data,
		Meta: &Meta{
			Pagination: &Pagination{
				Page:       page,
				Limit:      limit,
				TotalItems: total,
				TotalPages: totalPages,
				HasNext:    page < totalPages,
				HasPrev:    page > 1,
			},
			Sort: &Sort{
				By:    sortBy,
				Order: sortOrder,
			},
			Filters: filters,
		},
		Errors:    nil,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// ErrorResponse returns an error response
func ErrorResponse(c *gin.Context, statusCode int, code, message string) {
	c.JSON(statusCode, Response{
		Success:   false,
		Code:      code,
		Message:   message,
		Data:      nil,
		Meta:      nil,
		Errors:    nil,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// ValidationError returns 422 with field errors
func ValidationError(c *gin.Context, errors []Error) {
	c.JSON(422, Response{
		Success:   false,
		Code:      "VALIDATION_ERROR",
		Message:   "Validation failed",
		Data:      nil,
		Meta:      nil,
		Errors:    errors,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// NotFound returns 404 error
func NotFound(c *gin.Context, message string) {
	ErrorResponse(c, 404, "NOT_FOUND", message)
}

// BadRequest returns 400 error
func BadRequest(c *gin.Context, message string) {
	ErrorResponse(c, 400, "BAD_REQUEST", message)
}

// Unauthorized returns 401 error
func Unauthorized(c *gin.Context, message string) {
	ErrorResponse(c, 401, "UNAUTHORIZED", message)
}

// InternalError returns 500 error
func InternalError(c *gin.Context, message string) {
	ErrorResponse(c, 500, "INTERNAL_ERROR", message)
}

// SuccessWithPagination is an alias for SuccessList with different argument order (for backward compatibility)
func SuccessWithPagination(c *gin.Context, message string, data interface{}, page, limit int, total int64) {
	SuccessList(c, data, page, limit, total, message)
}

// Created returns 201 response (alias with message-first ordering for backward compatibility)
func Created(c *gin.Context, message string, data interface{}) {
	c.JSON(201, Response{
		Success:   true,
		Code:      "CREATED",
		Message:   message,
		Data:      data,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}

// Updated returns 200 response for updates (alias with message-first ordering)
func Updated(c *gin.Context, message string, data interface{}) {
	c.JSON(200, Response{
		Success:   true,
		Code:      "UPDATED",
		Message:   message,
		Data:      data,
		Timestamp: getTimestamp(),
		RequestID: generateRequestID(),
	})
}
