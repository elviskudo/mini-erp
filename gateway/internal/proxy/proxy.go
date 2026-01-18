package proxy

import (
	"io"
	"net/http"
	"time"

	"github.com/elviskudo/mini-erp/gateway/internal/services"
	"github.com/gin-gonic/gin"
)

// ProxyConfig holds proxy configuration
type ProxyConfig struct {
	Timeout time.Duration
}

var httpClient *http.Client

func init() {
	httpClient = &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 10,
			IdleConnTimeout:     90 * time.Second,
		},
	}
}

// ProxyRequest forwards a request to a backend service
func ProxyRequest(c *gin.Context, serviceName string, path string) {
	registry := services.GetRegistry()

	targetURL := registry.ProxyURL(serviceName, path)
	if targetURL == "" {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error":   "service_unavailable",
			"message": "Service " + serviceName + " is not available",
		})
		return
	}

	// Create the proxy request
	req, err := http.NewRequestWithContext(
		c.Request.Context(),
		c.Request.Method,
		targetURL,
		c.Request.Body,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "proxy_error",
			"message": "Failed to create proxy request",
		})
		return
	}

	// Copy headers
	for key, values := range c.Request.Header {
		for _, value := range values {
			req.Header.Add(key, value)
		}
	}

	// Add proxy headers
	req.Header.Set("X-Forwarded-For", c.ClientIP())
	req.Header.Set("X-Forwarded-Proto", c.Request.URL.Scheme)
	req.Header.Set("X-Gateway-Service", serviceName)

	// Forward tenant and user info from JWT context
	if tenantID, exists := c.Get("tenant_id"); exists {
		req.Header.Set("X-Tenant-ID", tenantID.(string))
	}
	if userID, exists := c.Get("user_id"); exists {
		req.Header.Set("X-User-ID", userID.(string))
	}
	if role, exists := c.Get("role"); exists {
		req.Header.Set("X-Role", role.(string))
	}

	// Execute request
	resp, err := httpClient.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"error":   "backend_error",
			"message": "Failed to reach backend service",
		})
		return
	}
	defer resp.Body.Close()

	// Copy response headers
	for key, values := range resp.Header {
		for _, value := range values {
			c.Header(key, value)
		}
	}

	// Copy response body
	c.Status(resp.StatusCode)
	io.Copy(c.Writer, resp.Body)
}

// ProxyToLegacy proxies to the legacy Python backend
func ProxyToLegacy(c *gin.Context) {
	path := c.Request.URL.Path
	if query := c.Request.URL.RawQuery; query != "" {
		path += "?" + query
	}

	// Determine service from path
	serviceName := "auth" // default
	pathParts := []string{}
	if len(c.Request.URL.Path) > 1 {
		pathParts = splitPath(c.Request.URL.Path)
	}

	if len(pathParts) >= 2 {
		// /api/v1/finance/... -> service = finance
		serviceName = pathParts[1]
	}

	ProxyRequest(c, serviceName, path)
}

func splitPath(path string) []string {
	parts := []string{}
	current := ""
	for _, c := range path {
		if c == '/' {
			if current != "" {
				parts = append(parts, current)
				current = ""
			}
		} else {
			current += string(c)
		}
	}
	if current != "" {
		parts = append(parts, current)
	}
	return parts
}
