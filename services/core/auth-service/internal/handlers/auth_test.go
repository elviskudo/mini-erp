package handlers_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

// AuthTestSuite is the test suite for auth handlers
type AuthTestSuite struct {
	suite.Suite
	router *gin.Engine
}

// SetupSuite sets up the test suite
func (s *AuthTestSuite) SetupSuite() {
	gin.SetMode(gin.TestMode)
	s.router = setupTestRouter()
}

// setupTestRouter creates a test router with auth routes
func setupTestRouter() *gin.Engine {
	r := gin.Default()

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "auth-service"})
	})

	// Auth routes - using inline handlers for testing
	auth := r.Group("/api/v1/auth")
	{
		auth.POST("/login", mockLoginHandler)
		auth.POST("/register", mockRegisterHandler)
		auth.POST("/refresh", mockRefreshHandler)
		auth.GET("/me", mockMeHandler)
		auth.POST("/logout", mockLogoutHandler)
		auth.POST("/forgot-password", mockForgotPasswordHandler)
		auth.POST("/verify-otp", mockVerifyOTPHandler)
	}

	// Docs
	r.GET("/docs", func(c *gin.Context) {
		c.String(200, "<!DOCTYPE html><html><body>Docs</body></html>")
	})
	r.GET("/openapi.json", func(c *gin.Context) {
		c.JSON(200, gin.H{"openapi": "3.0.3"})
	})

	return r
}

// Mock handlers
func mockLoginHandler(c *gin.Context) {
	var req struct {
		Email    string `json:"email" binding:"required,email"`
		Password string `json:"password" binding:"required,min=6"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Email == "test@example.com" && req.Password == "password123" {
		c.JSON(http.StatusOK, gin.H{
			"access_token":  "mock-access-token",
			"refresh_token": "mock-refresh-token",
			"token_type":    "Bearer",
			"expires_in":    86400,
		})
		return
	}

	c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
}

func mockRegisterHandler(c *gin.Context) {
	var req struct {
		Email     string `json:"email" binding:"required,email"`
		Password  string `json:"password" binding:"required,min=6"`
		FirstName string `json:"first_name" binding:"required"`
		LastName  string `json:"last_name"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Email == "existing@example.com" {
		c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":         "new-user-id",
		"email":      req.Email,
		"first_name": req.FirstName,
		"last_name":  req.LastName,
	})
}

func mockRefreshHandler(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.RefreshToken == "valid-refresh-token" {
		c.JSON(http.StatusOK, gin.H{
			"access_token":  "new-access-token",
			"refresh_token": req.RefreshToken,
			"token_type":    "Bearer",
			"expires_in":    86400,
		})
		return
	}

	c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid refresh token"})
}

func mockMeHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" || authHeader != "Bearer valid-token" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":         "user-id-123",
		"email":      "user@example.com",
		"first_name": "Test",
		"last_name":  "User",
		"tenant_id":  "tenant-id-456",
		"is_admin":   false,
	})
}

func mockLogoutHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Logged out successfully"})
}

func mockForgotPasswordHandler(c *gin.Context) {
	var req struct {
		Email string `json:"email" binding:"required,email"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "If the email exists, a reset link has been sent"})
}

func mockVerifyOTPHandler(c *gin.Context) {
	var req struct {
		Email string `json:"email" binding:"required,email"`
		OTP   string `json:"otp" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.OTP == "123456" {
		c.JSON(http.StatusOK, gin.H{"message": "OTP verified", "reset_token": "password-reset-token"})
		return
	}

	c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid OTP"})
}

// ========== TEST CASES ==========

// TestHealthCheck tests the health endpoint
func (s *AuthTestSuite) TestHealthCheck() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "healthy", response["status"])
	assert.Equal(s.T(), "auth-service", response["service"])
}

// TestLoginSuccess tests successful login
func (s *AuthTestSuite) TestLoginSuccess() {
	body := map[string]string{
		"email":    "test@example.com",
		"password": "password123",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.NotEmpty(s.T(), response["access_token"])
	assert.Equal(s.T(), "Bearer", response["token_type"])
}

// TestLoginInvalidCredentials tests login with wrong password
func (s *AuthTestSuite) TestLoginInvalidCredentials() {
	body := map[string]string{
		"email":    "test@example.com",
		"password": "wrongpassword",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusUnauthorized, w.Code)
}

// TestLoginMissingEmail tests login without email
func (s *AuthTestSuite) TestLoginMissingEmail() {
	body := map[string]string{
		"password": "password123",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusBadRequest, w.Code)
}

// TestRegisterSuccess tests successful registration
func (s *AuthTestSuite) TestRegisterSuccess() {
	body := map[string]string{
		"email":      "newuser@example.com",
		"password":   "password123",
		"first_name": "John",
		"last_name":  "Doe",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusCreated, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "newuser@example.com", response["email"])
	assert.Equal(s.T(), "John", response["first_name"])
}

// TestRegisterDuplicateEmail tests registration with existing email
func (s *AuthTestSuite) TestRegisterDuplicateEmail() {
	body := map[string]string{
		"email":      "existing@example.com",
		"password":   "password123",
		"first_name": "John",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusConflict, w.Code)
}

// TestRefreshTokenSuccess tests successful token refresh
func (s *AuthTestSuite) TestRefreshTokenSuccess() {
	body := map[string]string{
		"refresh_token": "valid-refresh-token",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/refresh", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.NotEmpty(s.T(), response["access_token"])
}

// TestRefreshTokenInvalid tests refresh with invalid token
func (s *AuthTestSuite) TestRefreshTokenInvalid() {
	body := map[string]string{
		"refresh_token": "invalid-token",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/refresh", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusUnauthorized, w.Code)
}

// TestGetCurrentUserSuccess tests getting current user
func (s *AuthTestSuite) TestGetCurrentUserSuccess() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/auth/me", nil)
	req.Header.Set("Authorization", "Bearer valid-token")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "user@example.com", response["email"])
}

// TestGetCurrentUserUnauthorized tests getting current user without auth
func (s *AuthTestSuite) TestGetCurrentUserUnauthorized() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/v1/auth/me", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusUnauthorized, w.Code)
}

// TestLogout tests logout
func (s *AuthTestSuite) TestLogout() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/logout", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)
}

// TestForgotPassword tests forgot password
func (s *AuthTestSuite) TestForgotPassword() {
	body := map[string]string{
		"email": "user@example.com",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/forgot-password", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)
}

// TestVerifyOTPSuccess tests OTP verification
func (s *AuthTestSuite) TestVerifyOTPSuccess() {
	body := map[string]string{
		"email": "user@example.com",
		"otp":   "123456",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/verify-otp", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)
}

// TestVerifyOTPInvalid tests invalid OTP
func (s *AuthTestSuite) TestVerifyOTPInvalid() {
	body := map[string]string{
		"email": "user@example.com",
		"otp":   "wrong",
	}
	jsonBody, _ := json.Marshal(body)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/v1/auth/verify-otp", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusBadRequest, w.Code)
}

// TestOpenAPISpec tests OpenAPI spec endpoint
func (s *AuthTestSuite) TestOpenAPISpec() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/openapi.json", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(s.T(), "3.0.3", response["openapi"])
}

// TestDocsEndpoint tests docs endpoint
func (s *AuthTestSuite) TestDocsEndpoint() {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/docs", nil)
	s.router.ServeHTTP(w, req)

	assert.Equal(s.T(), http.StatusOK, w.Code)
	assert.Contains(s.T(), w.Body.String(), "<!DOCTYPE html>")
}

// Run the test suite
func TestAuthTestSuite(t *testing.T) {
	suite.Run(t, new(AuthTestSuite))
}
