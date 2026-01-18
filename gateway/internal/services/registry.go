package services

import (
	"fmt"
	"os"
	"sync"
)

// ServiceConfig holds configuration for a microservice
type ServiceConfig struct {
	Name      string
	URL       string
	HealthURL string
	Priority  int
}

// ServiceRegistry provides service discovery functionality
type ServiceRegistry struct {
	services map[string]ServiceConfig
	mu       sync.RWMutex
}

var registry *ServiceRegistry
var once sync.Once

// GetRegistry returns the singleton service registry
func GetRegistry() *ServiceRegistry {
	once.Do(func() {
		registry = &ServiceRegistry{
			services: make(map[string]ServiceConfig),
		}
		registry.initDefaultServices()
	})
	return registry
}

// initDefaultServices registers all known microservices
func (r *ServiceRegistry) initDefaultServices() {
	// Get service URLs from environment or use Docker service names
	legacyBackend := getEnv("LEGACY_BACKEND_URL", "http://backend_api:8000")
	mlService := getEnv("ML_SERVICE_URL", "http://ml-service:8000")

	// New Go microservices
	authService := getEnv("AUTH_SERVICE_URL", "http://auth-service:8010")
	financeService := getEnv("FINANCE_SERVICE_URL", "http://finance-service:8011")
	hrService := getEnv("HR_SERVICE_URL", "http://hr-service:8012")
	inventoryService := getEnv("INVENTORY_SERVICE_URL", "http://inventory-service:8013")
	manufacturingService := getEnv("MANUFACTURING_SERVICE_URL", "http://manufacturing-service:8014")
	fleetService := getEnv("FLEET_SERVICE_URL", "http://fleet-service:8015")
	projectsService := getEnv("PROJECTS_SERVICE_URL", "http://projects-service:8016")
	crmService := getEnv("CRM_SERVICE_URL", "http://crm-service:8017")

	// ========== CORE SERVICES ==========
	// Auth service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "auth", URL: authService, Priority: 1})

	// Finance service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "finance", URL: financeService, Priority: 1})

	// HR service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "hr", URL: hrService, Priority: 1})

	// Inventory service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "inventory", URL: inventoryService, Priority: 1})

	// Manufacturing service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "manufacturing", URL: manufacturingService, Priority: 1})

	// Fleet service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "fleet", URL: fleetService, Priority: 1})

	// Projects service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "projects", URL: projectsService, Priority: 1})

	// CRM service (NEW - Go microservice)
	r.Register(ServiceConfig{Name: "crm", URL: crmService, Priority: 1})

	// Procurement service (NEW - Go microservice)
	procurementService := getEnv("PROCUREMENT_SERVICE_URL", "http://procurement-service:8018")
	r.Register(ServiceConfig{Name: "procurement", URL: procurementService, Priority: 1})

	// Logistics service (NEW - Go microservice)
	logisticsService := getEnv("LOGISTICS_SERVICE_URL", "http://logistics-service:8019")
	r.Register(ServiceConfig{Name: "logistics", URL: logisticsService, Priority: 1})

	// Maintenance service (NEW - Go microservice)
	maintenanceService := getEnv("MAINTENANCE_SERVICE_URL", "http://maintenance-service:8020")
	r.Register(ServiceConfig{Name: "maintenance", URL: maintenanceService, Priority: 1})

	// POS service (NEW - Go microservice)
	posService := getEnv("POS_SERVICE_URL", "http://pos-service:8021")
	r.Register(ServiceConfig{Name: "pos", URL: posService, Priority: 1})

	// ========== DOMAIN SERVICES (remaining legacy) ==========
	r.Register(ServiceConfig{Name: "receiving", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "issuance", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "opname", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "delivery", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "mrp", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "qc", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "iot", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "ap", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "ar", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "sales", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "ecommerce", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "compliance", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "subscription", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "upload", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "tenants", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "saas", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "menu", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "users", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "dashboard", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "export", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "settings", URL: legacyBackend, Priority: 2})
	r.Register(ServiceConfig{Name: "config", URL: legacyBackend, Priority: 2})

	// ========== ML SERVICE ==========
	r.Register(ServiceConfig{Name: "ml", URL: mlService, HealthURL: mlService + "/health", Priority: 3})

	// ========== FUTURE SERVICES (Nuxt.js apps) ==========
	r.Register(ServiceConfig{Name: "marketplace", URL: "", Priority: 4})
	r.Register(ServiceConfig{Name: "clinic", URL: "", Priority: 4})
	r.Register(ServiceConfig{Name: "travel", URL: "", Priority: 4})
	r.Register(ServiceConfig{Name: "sports", URL: "", Priority: 4})
}

// Register adds a service to the registry
func (r *ServiceRegistry) Register(config ServiceConfig) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.services[config.Name] = config
}

// Get retrieves a service configuration
func (r *ServiceRegistry) Get(name string) (ServiceConfig, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	config, ok := r.services[name]
	return config, ok
}

// GetURL returns the URL for a service
func (r *ServiceRegistry) GetURL(name string) string {
	if config, ok := r.Get(name); ok {
		return config.URL
	}
	return ""
}

// IsAvailable checks if a service has a valid URL
func (r *ServiceRegistry) IsAvailable(name string) bool {
	if config, ok := r.Get(name); ok {
		return config.URL != ""
	}
	return false
}

// ListAll returns all registered services
func (r *ServiceRegistry) ListAll() []ServiceConfig {
	r.mu.RLock()
	defer r.mu.RUnlock()

	services := make([]ServiceConfig, 0, len(r.services))
	for _, config := range r.services {
		services = append(services, config)
	}
	return services
}

// ProxyURL builds a proxy URL for a service endpoint
func (r *ServiceRegistry) ProxyURL(serviceName, path string) string {
	baseURL := r.GetURL(serviceName)
	if baseURL == "" {
		return ""
	}
	return fmt.Sprintf("%s%s", baseURL, path)
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
