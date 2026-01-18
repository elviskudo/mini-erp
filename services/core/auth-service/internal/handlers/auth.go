package handlers

import (
	"net/http"
	"os"
	"time"

	"github.com/elviskudo/mini-erp/services/auth-service/internal/database"
	"github.com/elviskudo/mini-erp/services/auth-service/internal/models"
	"github.com/elviskudo/mini-erp/services/auth-service/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// AuthHandler handles authentication endpoints
type AuthHandler struct {
	jwtSecret []byte
}

// NewAuthHandler creates new auth handler
func NewAuthHandler() *AuthHandler {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = os.Getenv("SECRET_KEY")
	}
	if secret == "" {
		secret = "supersecretkey123changethisinproduction"
	}
	return &AuthHandler{jwtSecret: []byte(secret)}
}

// Login handles user login with real database
// POST /auth/login or /auth/token
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request", "detail": err.Error()})
		return
	}

	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not connected"})
		return
	}

	// Find user by username or email
	var user models.User
	result := db.Where("username = ? OR email = ?", req.Username, req.Username).First(&user)
	if result.Error != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Generate JWT token
	expiresAt := time.Now().Add(24 * time.Hour)
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":   user.ID,
		"username":  user.Username,
		"email":     user.Email,
		"role":      user.Role,
		"tenant_id": user.TenantID,
		"exp":       expiresAt.Unix(),
		"iat":       time.Now().Unix(),
	})

	tokenString, err := token.SignedString(h.jwtSecret)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, models.TokenResponse{
		AccessToken: tokenString,
		TokenType:   "Bearer",
		ExpiresIn:   int64(24 * time.Hour.Seconds()),
	})
}

// Register handles user registration
// POST /auth/register
func (h *AuthHandler) Register(c *gin.Context) {
	var req models.RegisterRequest
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request", "detail": err.Error()})
		return
	}

	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not connected"})
		return
	}

	// Check if username/email exists
	var existingUser models.User
	if db.Where("username = ? OR email = ?", req.Username, req.Email).First(&existingUser).Error == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "Username or email already exists"})
		return
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	// Create user
	user := models.User{
		Username:     req.Username,
		Email:        req.Email,
		PasswordHash: string(hashedPassword),
		Role:         "STAFF",
		IsVerified:   false,
	}

	if result := db.Create(&user); result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create user", "detail": result.Error.Error()})
		return
	}

	// Auto-join tenant if code provided
	if req.TenantCode != "" {
		var tenant models.Tenant
		if result := db.Where("company_code = ?", req.TenantCode).First(&tenant); result.Error == nil {
			role := req.Role
			if role == "" {
				role = "MEMBER"
			}

			now := time.Now()
			member := models.TenantMember{
				ID:       uuid.NewString(),
				TenantID: tenant.ID,
				UserID:   user.ID,
				Role:     role,
				JoinedAt: &now,
			}

			if err := db.Create(&member).Error; err == nil {
				// Update user's default tenant_id
				db.Model(&user).Update("tenant_id", tenant.ID)

				c.JSON(http.StatusCreated, gin.H{
					"message": "User registered and joined tenant successfully",
					"user": models.UserResponse{
						ID:         user.ID,
						Username:   user.Username,
						Email:      user.Email,
						Role:       user.Role,
						IsVerified: user.IsVerified,
						TenantID:   &tenant.ID,
					},
				})
				return
			}
		}
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "User registered successfully",
		"user": models.UserResponse{
			ID:         user.ID,
			Username:   user.Username,
			Email:      user.Email,
			Role:       user.Role,
			IsVerified: user.IsVerified,
		},
	})
}

// GetProfile gets current user profile
// GET /auth/me
func (h *AuthHandler) GetProfile(c *gin.Context) {
	// Get user_id from X-User-ID header (set by gateway after JWT validation)
	// or from context (for direct calls)
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		// Fallback to context (for backward compatibility)
		if id, exists := c.Get("user_id"); exists {
			userID = id.(string)
		}
	}

	if userID == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
		return
	}

	db := database.GetDB()
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not connected"})
		return
	}

	var user models.User
	if result := db.First(&user, "id = ?", userID); result.Error != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	c.JSON(http.StatusOK, models.UserResponse{
		ID:         user.ID,
		Username:   user.Username,
		Email:      user.Email,
		Role:       user.Role,
		IsVerified: user.IsVerified,
		TenantID:   user.TenantID,
	})
}

// RefreshToken refreshes access token
// POST /auth/refresh
func (h *AuthHandler) RefreshToken(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Refresh token required"})
		return
	}

	// Verify refresh token (simplified - in production use database)
	token, err := jwt.Parse(req.RefreshToken, func(token *jwt.Token) (interface{}, error) {
		return h.jwtSecret, nil
	})

	if err != nil || !token.Valid {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid refresh token"})
		return
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims"})
		return
	}

	// Generate new access token
	expiresAt := time.Now().Add(24 * time.Hour)
	newToken := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":   claims["user_id"],
		"username":  claims["username"],
		"email":     claims["email"],
		"role":      claims["role"],
		"tenant_id": claims["tenant_id"],
		"exp":       expiresAt.Unix(),
		"iat":       time.Now().Unix(),
	})

	tokenString, err := newToken.SignedString(h.jwtSecret)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}

	c.JSON(http.StatusOK, models.TokenResponse{
		AccessToken: tokenString,
		TokenType:   "Bearer",
		ExpiresIn:   int64(24 * time.Hour.Seconds()),
	})
}

// Logout handles logout
// POST /auth/logout
func (h *AuthHandler) Logout(c *gin.Context) {
	// In a real app, invalidate the token in database/redis
	c.JSON(http.StatusOK, gin.H{"message": "Logged out successfully"})
}

// SendOTP sends OTP to user
// POST /auth/send-otp
func (h *AuthHandler) SendOTP(c *gin.Context) {
	var req struct {
		Email string `json:"email" binding:"required,email"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Valid email required"})
		return
	}

	// In production, generate OTP, save to DB, send email
	c.JSON(http.StatusOK, gin.H{"message": "OTP sent to " + req.Email})
}

// VerifyOTP verifies OTP
// POST /auth/verify-otp
func (h *AuthHandler) VerifyOTP(c *gin.Context) {
	var req struct {
		Email string `json:"email" binding:"required,email"`
		OTP   string `json:"otp" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Email and OTP required"})
		return
	}

	// In production, verify OTP from DB
	c.JSON(http.StatusOK, gin.H{"message": "OTP verified", "verified": true})
}

// ForgotPassword initiates password reset
// POST /auth/forgot-password
func (h *AuthHandler) ForgotPassword(c *gin.Context) {
	var req struct {
		Email string `json:"email" binding:"required,email"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Valid email required"})
		return
	}

	// In production, send reset email
	c.JSON(http.StatusOK, gin.H{"message": "Password reset instructions sent to " + req.Email})
}

// GetUserTenants returns list of tenants the user belongs to
// GET /auth/tenants
func (h *AuthHandler) GetUserTenants(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		response.Unauthorized(c, "User ID required")
		return
	}

	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Query tenant_members with tenant details
	var memberships []models.TenantMember
	if err := db.Preload("Tenant").Where("user_id = ?", userID).Find(&memberships).Error; err != nil {
		response.InternalError(c, "Failed to fetch tenants")
		return
	}

	// Transform to response format
	tenants := make([]models.TenantWithRole, 0, len(memberships))
	for _, m := range memberships {
		tenants = append(tenants, models.TenantWithRole{
			ID:       m.TenantID,
			Name:     m.Tenant.Name,
			Slug:     m.Tenant.Slug,
			Role:     m.Role,
			IsActive: m.Tenant.IsActive,
		})
	}

	response.SuccessList(c, tenants, 1, len(tenants), int64(len(tenants)), "User tenants retrieved successfully")
}

// SwitchTenant generates a new token for a different tenant
// POST /auth/switch-tenant
func (h *AuthHandler) SwitchTenant(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		response.Unauthorized(c, "User ID required")
		return
	}

	var req struct {
		TenantID string `json:"tenant_id" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, "Tenant ID required")
		return
	}

	db := database.GetDB()
	if db == nil {
		response.InternalError(c, "Database not connected")
		return
	}

	// Verify user has access to this tenant
	var membership models.TenantMember
	if err := db.Preload("Tenant").Where("user_id = ? AND tenant_id = ?", userID, req.TenantID).First(&membership).Error; err != nil {
		response.ErrorResponse(c, 403, "FORBIDDEN", "You don't have access to this tenant")
		return
	}

	// Get user details
	var user models.User
	if err := db.First(&user, "id = ?", userID).Error; err != nil {
		response.NotFound(c, "User not found")
		return
	}

	// Generate new JWT token with selected tenant
	expiresAt := time.Now().Add(24 * time.Hour)
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":     user.ID,
		"username":    user.Username,
		"email":       user.Email,
		"role":        membership.Role, // Use tenant-specific role
		"tenant_id":   req.TenantID,
		"tenant_name": membership.Tenant.Name,
		"exp":         expiresAt.Unix(),
		"iat":         time.Now().Unix(),
	})

	tokenString, err := token.SignedString(h.jwtSecret)
	if err != nil {
		response.InternalError(c, "Failed to generate token")
		return
	}

	// Custom response with token and tenant info
	response.Success(c, gin.H{
		"token": models.TokenResponse{
			AccessToken: tokenString,
			TokenType:   "Bearer",
			ExpiresIn:   int64(24 * time.Hour.Seconds()),
		},
		"tenant": models.TenantWithRole{
			ID:       membership.TenantID,
			Name:     membership.Tenant.Name,
			Slug:     membership.Tenant.Slug,
			Role:     membership.Role,
			IsActive: membership.Tenant.IsActive,
		},
	}, "Tenant switched successfully")
}
