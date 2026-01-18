package handlers

import "github.com/gin-gonic/gin"

// ScalarDocs serves the Scalar API documentation UI
func ScalarDocs(c *gin.Context) {
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Sales Service API</title>
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
			"title":       "Sales Service API",
			"description": "Mini-ERP Sales Service - Quotations, Orders, Invoices",
			"version":     "1.0.0",
		},
		"servers": []gin.H{
			{"url": "http://localhost:8023", "description": "Local development"},
		},
		"paths": gin.H{
			"/sales/quotations": gin.H{
				"get":  gin.H{"summary": "List quotations", "tags": []string{"Quotations"}},
				"post": gin.H{"summary": "Create quotation", "tags": []string{"Quotations"}},
			},
			"/sales/orders": gin.H{
				"get":  gin.H{"summary": "List sales orders", "tags": []string{"Sales Orders"}},
				"post": gin.H{"summary": "Create sales order", "tags": []string{"Sales Orders"}},
			},
			"/sales/invoices": gin.H{
				"get":  gin.H{"summary": "List invoices", "tags": []string{"Invoices"}},
				"post": gin.H{"summary": "Create invoice", "tags": []string{"Invoices"}},
			},
		},
	}
	c.JSON(200, spec)
}
