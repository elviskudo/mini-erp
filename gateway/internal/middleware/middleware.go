package middleware

import (
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/elviskudo/mini-erp/gateway/internal/response"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

var jwtSecret []byte

func init() {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = os.Getenv("SECRET_KEY")
	}
	if secret == "" {
		// Must match auth-service default
		secret = "supersecretkey123changethisinproduction"
	}
	jwtSecret = []byte(secret)
}

// Claims represents the JWT claims
type Claims struct {
	UserID   string `json:"user_id"`
	TenantID string `json:"tenant_id"`
	Role     string `json:"role"`
	jwt.RegisteredClaims
}

// CORS middleware for cross-origin requests
func CORS() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Credentials", "true")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With, X-Tenant-ID")
		c.Header("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE, PATCH")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

// RateLimiter implements a simple rate limiting middleware
func RateLimiter() gin.HandlerFunc {
	// TODO: Implement proper rate limiting with Redis
	return func(c *gin.Context) {
		c.Next()
	}
}

// RequestLogger logs all incoming requests
func RequestLogger() gin.HandlerFunc {
	return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		return param.TimeStamp.Format(time.RFC3339) + " | " +
			param.ClientIP + " | " +
			param.Method + " " + param.Path + " | " +
			string(rune(param.StatusCode)) + " | " +
			param.Latency.String() + "\n"
	})
}

// JWTAuth middleware for authenticating JWT tokens
func JWTAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			response.Unauthorized(c, "Authorization header required")
			c.Abort()
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		if tokenString == authHeader {
			response.Unauthorized(c, "Bearer token required")
			c.Abort()
			return
		}

		claims := &Claims{}
		token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
			return jwtSecret, nil
		})

		if err != nil || !token.Valid {
			response.Unauthorized(c, "Invalid token")
			c.Abort()
			return
		}

		// Set user info in context
		c.Set("user_id", claims.UserID)
		c.Set("tenant_id", claims.TenantID)
		c.Set("role", claims.Role)

		c.Next()
	}
}

// TenantExtractor extracts tenant ID from header or JWT
func TenantExtractor() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Try to get from header first
		tenantID := c.GetHeader("X-Tenant-ID")
		if tenantID == "" {
			// Fallback to JWT claim
			if id, exists := c.Get("tenant_id"); exists {
				tenantID = id.(string)
			}
		}
		c.Set("tenant_id", tenantID)
		c.Next()
	}
}

// RoleMiddleware enforces role-based access control
func RoleMiddleware(allowedRoles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userRole, exists := c.Get("role")
		if !exists {
			response.Forbidden(c, "Role not found in context")
			c.Abort()
			return
		}

		roleStr := userRole.(string)

		// Admin always has access
		if roleStr == "ADMIN" || roleStr == "OWNER" {
			c.Next()
			return
		}

		// Check if user role is allowed
		allowed := false
		for _, role := range allowedRoles {
			if role == roleStr {
				allowed = true
				break
			}
		}

		if !allowed {
			response.Forbidden(c, "Insufficient permissions")
			c.Abort()
			return
		}

		c.Next()
	}
}
