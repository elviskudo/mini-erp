package handlers

import "github.com/gin-gonic/gin"

// ScalarDocs serves the Scalar API documentation UI
func ScalarDocs(c *gin.Context) {
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Inventory Service API</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>`
	c.Header("Content-Type", "text/html")
	c.String(200, html)
}

// OpenAPISpec returns the OpenAPI specification
func OpenAPISpec(c *gin.Context) {
	spec := gin.H{
		"openapi": "3.0.3",
		"info": gin.H{
			"title":       "Inventory Service API",
			"description": "Mini-ERP Inventory Service - Products, Warehouses, Stock, Movements, Opname",
			"version":     "1.0.0",
		},
		"servers": []gin.H{
			{"url": "http://localhost:8013", "description": "Local development"},
		},
		"paths": gin.H{
			"/inventory/products": gin.H{
				"get":  gin.H{"summary": "List all products", "tags": []string{"Products"}},
				"post": gin.H{"summary": "Create a product", "tags": []string{"Products"}},
			},
			"/inventory/products/{id}": gin.H{
				"get": gin.H{"summary": "Get product by ID", "tags": []string{"Products"}},
			},
			"/inventory/warehouses": gin.H{
				"get":  gin.H{"summary": "List all warehouses", "tags": []string{"Warehouses"}},
				"post": gin.H{"summary": "Create a warehouse", "tags": []string{"Warehouses"}},
			},
			"/inventory/warehouses/{id}": gin.H{
				"get": gin.H{"summary": "Get warehouse by ID", "tags": []string{"Warehouses"}},
				"put": gin.H{"summary": "Update warehouse", "tags": []string{"Warehouses"}},
			},
			"/inventory/stock": gin.H{
				"get": gin.H{"summary": "List stock by warehouse", "tags": []string{"Stock"}},
			},
			"/inventory/movements": gin.H{
				"get": gin.H{"summary": "List stock movements", "tags": []string{"Movements"}},
			},
			"/inventory/opnames": gin.H{
				"get":  gin.H{"summary": "List stock opnames", "tags": []string{"Opname"}},
				"post": gin.H{"summary": "Create stock opname", "tags": []string{"Opname"}},
			},
			"/inventory/opnames/{id}": gin.H{
				"get": gin.H{"summary": "Get opname by ID", "tags": []string{"Opname"}},
			},
			"/inventory/locations": gin.H{
				"get": gin.H{"summary": "Get locations hierarchy", "tags": []string{"Locations"}},
			},
		},
	}
	c.JSON(200, spec)
}
