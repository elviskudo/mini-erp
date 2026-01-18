package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// ScalarDocs serves the Scalar API documentation
func ScalarDocs(c *gin.Context) {
	html := `<!DOCTYPE html>
<html>
<head>
  <title>Auth Service - API Documentation</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <script id="api-reference" data-url="/openapi.json"></script>
  <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>`
	c.Header("Content-Type", "text/html")
	c.String(http.StatusOK, html)
}

// OpenAPISpec returns the OpenAPI specification for Auth Service
func OpenAPISpec(c *gin.Context) {
	spec := gin.H{
		"openapi": "3.0.3",
		"info": gin.H{
			"title":       "Mini-ERP Auth Service API",
			"version":     "1.0.0",
			"description": "Authentication and Authorization service for Mini-ERP",
		},
		"servers": []gin.H{
			{"url": "http://localhost:8010", "description": "Development server"},
		},
		"tags": []gin.H{
			{"name": "Auth", "description": "Authentication endpoints"},
			{"name": "Users", "description": "User management endpoints"},
		},
		"paths": gin.H{
			"/api/v1/auth/login": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "User login",
					"description": "Authenticate user and return JWT tokens",
					"requestBody": gin.H{
						"required": true,
						"content": gin.H{
							"application/json": gin.H{
								"schema": gin.H{
									"type":     "object",
									"required": []string{"email", "password"},
									"properties": gin.H{
										"email":    gin.H{"type": "string", "format": "email", "example": "user@example.com"},
										"password": gin.H{"type": "string", "minLength": 6, "example": "password123"},
									},
								},
							},
						},
					},
					"responses": gin.H{
						"200": gin.H{
							"description": "Successful login",
							"content": gin.H{
								"application/json": gin.H{
									"schema": gin.H{"$ref": "#/components/schemas/TokenResponse"},
								},
							},
						},
						"401": gin.H{"description": "Invalid credentials"},
					},
				},
			},
			"/api/v1/auth/register": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "User registration",
					"description": "Register a new user account",
					"requestBody": gin.H{
						"required": true,
						"content": gin.H{
							"application/json": gin.H{
								"schema": gin.H{
									"type":     "object",
									"required": []string{"email", "password", "first_name"},
									"properties": gin.H{
										"email":      gin.H{"type": "string", "format": "email", "example": "newuser@example.com"},
										"password":   gin.H{"type": "string", "minLength": 6, "example": "password123"},
										"first_name": gin.H{"type": "string", "example": "John"},
										"last_name":  gin.H{"type": "string", "example": "Doe"},
										"tenant_id":  gin.H{"type": "string", "format": "uuid"},
									},
								},
							},
						},
					},
					"responses": gin.H{
						"201": gin.H{"description": "User created successfully"},
						"400": gin.H{"description": "Invalid request data"},
					},
				},
			},
			"/api/v1/auth/refresh": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "Refresh access token",
					"description": "Get a new access token using refresh token",
					"requestBody": gin.H{
						"required": true,
						"content": gin.H{
							"application/json": gin.H{
								"schema": gin.H{
									"type":     "object",
									"required": []string{"refresh_token"},
									"properties": gin.H{
										"refresh_token": gin.H{"type": "string"},
									},
								},
							},
						},
					},
					"responses": gin.H{
						"200": gin.H{"description": "Token refreshed successfully"},
						"401": gin.H{"description": "Invalid refresh token"},
					},
				},
			},
			"/api/v1/auth/me": gin.H{
				"get": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "Get current user",
					"description": "Get authenticated user's profile",
					"security":    []gin.H{{"BearerAuth": []string{}}},
					"responses": gin.H{
						"200": gin.H{
							"description": "User profile",
							"content": gin.H{
								"application/json": gin.H{
									"schema": gin.H{"$ref": "#/components/schemas/UserResponse"},
								},
							},
						},
						"401": gin.H{"description": "Unauthorized"},
					},
				},
			},
			"/api/v1/auth/logout": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "User logout",
					"description": "Invalidate the current session",
					"security":    []gin.H{{"BearerAuth": []string{}}},
					"responses": gin.H{
						"200": gin.H{"description": "Logged out successfully"},
					},
				},
			},
			"/api/v1/auth/forgot-password": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "Forgot password",
					"description": "Send password reset email",
					"requestBody": gin.H{
						"required": true,
						"content": gin.H{
							"application/json": gin.H{
								"schema": gin.H{
									"type":     "object",
									"required": []string{"email"},
									"properties": gin.H{
										"email": gin.H{"type": "string", "format": "email"},
									},
								},
							},
						},
					},
					"responses": gin.H{
						"200": gin.H{"description": "Reset email sent if account exists"},
					},
				},
			},
			"/api/v1/auth/verify-otp": gin.H{
				"post": gin.H{
					"tags":        []string{"Auth"},
					"summary":     "Verify OTP",
					"description": "Verify OTP for password reset",
					"requestBody": gin.H{
						"required": true,
						"content": gin.H{
							"application/json": gin.H{
								"schema": gin.H{
									"type":     "object",
									"required": []string{"email", "otp"},
									"properties": gin.H{
										"email": gin.H{"type": "string", "format": "email"},
										"otp":   gin.H{"type": "string", "example": "123456"},
									},
								},
							},
						},
					},
					"responses": gin.H{
						"200": gin.H{"description": "OTP verified"},
						"400": gin.H{"description": "Invalid OTP"},
					},
				},
			},
			"/health": gin.H{
				"get": gin.H{
					"tags":    []string{"Health"},
					"summary": "Health check",
					"responses": gin.H{
						"200": gin.H{"description": "Service is healthy"},
					},
				},
			},
		},
		"components": gin.H{
			"schemas": gin.H{
				"TokenResponse": gin.H{
					"type": "object",
					"properties": gin.H{
						"access_token":  gin.H{"type": "string"},
						"refresh_token": gin.H{"type": "string"},
						"token_type":    gin.H{"type": "string", "example": "Bearer"},
						"expires_in":    gin.H{"type": "integer", "example": 86400},
					},
				},
				"UserResponse": gin.H{
					"type": "object",
					"properties": gin.H{
						"id":         gin.H{"type": "string", "format": "uuid"},
						"email":      gin.H{"type": "string", "format": "email"},
						"first_name": gin.H{"type": "string"},
						"last_name":  gin.H{"type": "string"},
						"tenant_id":  gin.H{"type": "string", "format": "uuid"},
						"is_admin":   gin.H{"type": "boolean"},
					},
				},
			},
			"securitySchemes": gin.H{
				"BearerAuth": gin.H{
					"type":         "http",
					"scheme":       "bearer",
					"bearerFormat": "JWT",
				},
			},
		},
	}
	c.JSON(http.StatusOK, spec)
}
