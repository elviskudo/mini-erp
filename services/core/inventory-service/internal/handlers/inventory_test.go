package handlers

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/elviskudo/mini-erp/services/inventory-service/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestGetLocationsForMove(t *testing.T) {
	// Setup
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	// Since we mock DB inside handlers often by checking for nil,
	// and we don't have a full mock DB setup in this simple test file yet,
	// we will verify that standard response format is returned even if empty/mock.

	// Assuming GetDB() returns nil in test environment without setup,
	// the handler returns empty list with success.

	h := NewInventoryHandler()
	h.GetLocationsForMove(c)

	assert.Equal(t, http.StatusOK, w.Code)

	var res response.Response
	err := json.Unmarshal(w.Body.Bytes(), &res)
	assert.NoError(t, err)
	assert.True(t, res.Success)
	assert.Equal(t, "Locations retrieved", res.Message) // Or "Locations retrieved successfully" depending on DB state
}

func TestGetLocationsHierarchy(t *testing.T) {
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	h := NewInventoryHandler()
	h.GetLocationsHierarchy(c)

	assert.Equal(t, http.StatusOK, w.Code)

	var res response.Response
	err := json.Unmarshal(w.Body.Bytes(), &res)
	assert.NoError(t, err)
	assert.True(t, res.Success)
}
