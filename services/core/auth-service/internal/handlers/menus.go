package handlers

import (
	"github.com/elviskudo/mini-erp/services/auth-service/internal/database"
	"github.com/elviskudo/mini-erp/services/auth-service/internal/response"
	"github.com/gin-gonic/gin"
)

// MenuPermResult for DB query results
type MenuPermResult struct {
	MenuID    string  `gorm:"column:menu_id"`
	Label     string  `gorm:"column:label"`
	Icon      *string `gorm:"column:icon"`
	Path      *string `gorm:"column:path"`
	ParentID  *string `gorm:"column:parent_id"`
	SortOrder int     `gorm:"column:sort_order"`
}

// MenuChild represents a child menu item
type MenuChild struct {
	Label     string       `json:"label"`
	To        string       `json:"to,omitempty"`
	Children  []*MenuChild `json:"children,omitempty"`
	AdminOnly bool         `json:"-"` // Not sent to client, used for filtering
}

// MenuItem represents a top-level menu item
type MenuItem struct {
	Label    string       `json:"label"`
	Icon     string       `json:"icon,omitempty"`
	To       string       `json:"to,omitempty"`
	Children []*MenuChild `json:"children,omitempty"`
}

// GetAllMenus returns all menus (hardcoded for ADMIN/MANAGER)
func getAllMenus() []MenuItem {
	return []MenuItem{
		// 1. Dashboard
		{Label: "Dashboard", Icon: "i-heroicons-home", To: "/"},

		// 2. CRM (Customer first, before Sales)
		{Label: "CRM", Icon: "i-heroicons-users", Children: []*MenuChild{
			{Label: "Leads", To: "/crm/leads"},
			{Label: "Companies", To: "/crm/companies"},
			{Label: "Contacts", To: "/crm/contacts"},
			{Label: "Opportunities", To: "/crm/opportunities"},
			{Label: "Pipeline", To: "/crm/pipeline"},
			{Label: "Customers", To: "/crm/customers"},
			{Label: "Activities", To: "/crm/activities"},
			{Label: "Campaigns", To: "/crm/campaigns"},
			{Label: "Web Forms", To: "/crm/forms"},
			{Label: "Marketing", Children: []*MenuChild{
				{Label: "Page Builder", To: "/crm/marketing/pages"},
				{Label: "Email & Broadcast", To: "/crm/marketing/email"},
				{Label: "Promos", To: "/crm/promos"},
			}},
		}},

		// 3. Sales (Complete ERP Flow)
		{Label: "Sales", Icon: "i-heroicons-banknotes", Children: []*MenuChild{
			{Label: "Quotations", To: "/sales/quotations"},
			{Label: "Sales Orders", To: "/sales/orders"},
			{Label: "Invoices", To: "/sales/invoices"},
			{Label: "Credit Notes", To: "/sales/credit-notes"},
			{Label: "Price Lists", To: "/sales/price-lists"},
			{Label: "Discount Rules", To: "/sales/discount-rules"},
			{Label: "Contracts", To: "/sales/contracts"},
			{Label: "Commission", To: "/sales/commission"},
			{Label: "Analytics", To: "/sales/analytics"},
		}},

		// 4. Procurement
		{Label: "Procurement", Icon: "i-heroicons-shopping-cart", Children: []*MenuChild{
			{Label: "Vendors", To: "/procurement/vendors"},
			{Label: "Product Catalog", To: "/procurement/products"},
			{Label: "Purchase Requests", To: "/procurement/requests"},
			{Label: "RFQ", To: "/procurement/rfq"},
			{Label: "Purchase Orders", To: "/procurement/orders"},
			{Label: "Vendor Bills", To: "/procurement/bills"},
			{Label: "Payments", To: "/procurement/payments"},
			{Label: "Analytics", To: "/procurement/analytics"},
		}},

		// 5. Manufacturing
		{Label: "Manufacturing", Icon: "i-heroicons-wrench-screwdriver", Children: []*MenuChild{
			{Label: "MRP", Children: []*MenuChild{
				{Label: "MRP Run", To: "/manufacturing/mrp/run"},
				{Label: "Master Schedule (MPS)", To: "/manufacturing/mrp/mps"},
				{Label: "Demand Forecasting", To: "/manufacturing/mrp/forecast"},
				{Label: "Net Requirements", To: "/manufacturing/mrp/requirements"},
				{Label: "MRP Exceptions", To: "/manufacturing/mrp/exceptions"},
				{Label: "Analytics MRP", To: "/manufacturing/mrp/analytics"},
			}},
			{Label: "Categories", To: "/manufacturing/categories"},
			{Label: "Work Centers", To: "/manufacturing/work-centers"},
			{Label: "Products & BOM", To: "/manufacturing/products"},
			{Label: "Routing", To: "/manufacturing/routing"},
			{Label: "Production Orders", To: "/manufacturing/production"},
			{Label: "Work Orders", Children: []*MenuChild{
				{Label: "Open Work Orders", To: "/manufacturing/work-orders/open"},
				{Label: "Dashboard", To: "/manufacturing/work-orders/dashboard"},
			}},
			{Label: "Quality Control", To: "/manufacturing/quality"},
			{Label: "Analytics", To: "/manufacturing/analytics"},
		}},

		// 6. Inventory
		{Label: "Inventory", Icon: "i-heroicons-cube", Children: []*MenuChild{
			{Label: "Warehouses", To: "/inventory/warehouses"},
			{Label: "Storage Zones", To: "/inventory/storage-zones"},
			{Label: "Stock Status", To: "/inventory/stock"},
			{Label: "Goods Receipt", To: "/inventory/receiving"},
			{Label: "Movements", To: "/inventory/movements"},
			{Label: "Stock Opname", Children: []*MenuChild{
				{Label: "Schedule", To: "/inventory/opname/schedule"},
				{Label: "Counting", To: "/inventory/opname/counting"},
				{Label: "Matching", To: "/inventory/opname/matching"},
				{Label: "Adjustment", To: "/inventory/opname/adjustment"},
			}},
			{Label: "Analytics", To: "/inventory/analytics"},
		}},

		// 7. Logistics
		{Label: "Logistics", Icon: "i-heroicons-truck", Children: []*MenuChild{
			{Label: "Delivery Orders", To: "/logistics/delivery"},
			{Label: "Stock Transfers", To: "/logistics/transfers"},
			{Label: "Stock Picking", To: "/logistics/picking"},
			{Label: "Shipments", To: "/logistics/shipments"},
			{Label: "Returns", To: "/logistics/returns"},
			{Label: "Couriers", To: "/logistics/couriers"},
			{Label: "Analytics", To: "/logistics/analytics"},
		}},

		// 8. Finance (Existing maintained, Loyalty removed as it moves to #10)
		{Label: "Finance", Icon: "i-heroicons-banknotes", Children: []*MenuChild{
			{Label: "Dashboard", To: "/finance"},
			{Label: "Chart of Accounts", To: "/finance/coa"},
			{Label: "General Ledger", To: "/finance/gl"},
			{Label: "Accounts Payable", Children: []*MenuChild{
				{Label: "Vendor Bills", To: "/finance/ap/bills"},
				{Label: "Payments", To: "/finance/ap/payments"},
				{Label: "Aging Report", To: "/finance/ap/aging"},
			}},
			{Label: "Accounts Receivable", Children: []*MenuChild{
				{Label: "Invoices", To: "/finance/ar/invoices"},
				{Label: "Receipts", To: "/finance/ar/receipts"},
				{Label: "Aging Report", To: "/finance/ar/aging"},
			}},
			{Label: "Bank & Cash", Children: []*MenuChild{
				{Label: "Bank Accounts", To: "/finance/banking/accounts"},
				{Label: "Transactions", To: "/finance/banking/transactions"},
				{Label: "Reconciliation", To: "/finance/banking/reconciliation"},
				{Label: "Petty Cash", To: "/finance/banking/petty-cash"},
			}},
			{Label: "Taxes", Children: []*MenuChild{
				{Label: "Tax Configuration", To: "/finance/tax/config"},
				{Label: "PPN/VAT", To: "/finance/tax/ppn"},
				{Label: "Withholding Tax", To: "/finance/tax/withholding"},
				{Label: "e-Faktur", To: "/finance/tax/efaktur"},
			}},
			{Label: "Fixed Assets", To: "/finance/assets"},
			{Label: "Budgeting", Children: []*MenuChild{
				{Label: "Budgets", To: "/finance/budget"},
				{Label: "Budget vs Actual", To: "/finance/budget/variance"},
			}},
			{Label: "Cost Centers", To: "/finance/cost-centers"},
			{Label: "Reports", Children: []*MenuChild{
				{Label: "Trial Balance", To: "/finance/reports/trial-balance"},
				{Label: "Profit & Loss", To: "/finance/reports/pl"},
				{Label: "Balance Sheet", To: "/finance/reports/balance-sheet"},
				{Label: "Cash Flow", To: "/finance/reports/cash-flow"},
				{Label: "General Ledger", To: "/finance/reports/gl"},
			}},
		}},

		// 9. POS
		{Label: "POS", Icon: "i-heroicons-computer-desktop", Children: []*MenuChild{
			{Label: "Sessions", To: "/pos/sessions"},
			{Label: "Products", To: "/pos/products"},
			{Label: "Payments", To: "/pos/payments"},
		}},

		// 10. Loyalty & Rewards (New)
		{Label: "Loyalty & Rewards", Icon: "i-heroicons-gift", Children: []*MenuChild{
			{Label: "Coin Top-Up", To: "/finance/loyalty/topup"}, // Keeping finance route for backend compat
			{Label: "Redemption Rules", To: "/finance/loyalty/rules"},
			{Label: "Balance Tracking", To: "/finance/loyalty/balance"},
			{Label: "Analytics", To: "/finance/loyalty/analytics"},
		}},

		// 11. Projects
		{Label: "Projects", Icon: "i-heroicons-clipboard-document-list", Children: []*MenuChild{
			{Label: "Kanban Boards", To: "/projects/kanban"},
			{Label: "Tasks", To: "/projects/tasks"},
			{Label: "Timesheets", To: "/projects/timesheets"},
			{Label: "Reports", To: "/projects/reports"},
		}},

		// 12. Maintenance
		{Label: "Maintenance", Icon: "i-heroicons-wrench", Children: []*MenuChild{
			{Label: "Assets", To: "/maintenance/assets"},
			{Label: "Maintenance Requests", To: "/maintenance/requests"},
			{Label: "Schedules", To: "/maintenance/schedules"},
			{Label: "Reports", To: "/maintenance/reports"},
		}},

		// 13. Fleet
		{Label: "Fleet", Icon: "i-heroicons-truck", Children: []*MenuChild{
			{Label: "Dashboard", To: "/fleet"},
			{Label: "Vehicles", To: "/fleet/vehicles"},
			{Label: "Bookings", To: "/fleet/bookings"},
			{Label: "Fuel Logs", To: "/fleet/fuel"},
			{Label: "Maintenance", To: "/fleet/maintenance"},
			{Label: "Expense", To: "/fleet/expenses"},
			{Label: "Reminders", To: "/fleet/reminders"},
		}},

		// 14. HR & Payroll
		{Label: "HR & Payroll", Icon: "i-heroicons-user-group", Children: []*MenuChild{
			{Label: "Dashboard", To: "/hr"},
			{Label: "Employees", To: "/hr/employees"},
			{Label: "Organization", To: "/hr/organization"},
			{Label: "Attendance", To: "/hr/attendance"},
			{Label: "Leave", To: "/hr/leave"},
			{Label: "Leaderboard", To: "/hr/leaderboards"},
			{Label: "Payroll", To: "/hr/payroll"},
			{Label: "Analytics", To: "/hr/analytics"},
		}},

		// 15. Compliance
		{Label: "Compliance", Icon: "i-heroicons-shield-check", Children: []*MenuChild{
			{Label: "Regulatory Reports", To: "/compliance/reports"},
			{Label: "Audit Trails", To: "/compliance/audit"},
			{Label: "ISO Tools", To: "/compliance/iso"},
			{Label: "Risk Management", To: "/compliance/risk"},
			{Label: "Data Privacy", To: "/compliance/privacy"},
		}},

		// 16. Users
		{Label: "Users", Icon: "i-heroicons-user-circle", Children: []*MenuChild{
			{Label: "User List", To: "/users"},
			{Label: "Roles", To: "/users/roles"},
			{Label: "RBAC Permissions", To: "/users/rbac", AdminOnly: true},
		}},

		// 17. Setup
		{Label: "Setup", Icon: "i-heroicons-cog-6-tooth", To: "/setup"},
	}
}

// getMenusByRole returns menus filtered by role
func getMenusByRole(role string) []MenuItem {
	allMenus := getAllMenus()

	// ADMIN, MANAGER, and OWNER see all menus
	if role == "ADMIN" || role == "MANAGER" || role == "OWNER" {
		return allMenus
	}

	// Role-based menu filtering
	roleMenuMap := map[string][]string{
		"PRODUCTION":  {"Dashboard", "Manufacturing", "Users"},
		"WAREHOUSE":   {"Dashboard", "Inventory", "Users"},
		"PROCUREMENT": {"Dashboard", "Procurement", "Users"},
		"FINANCE":     {"Dashboard", "Finance", "Users"},
		"HR":          {"Dashboard", "HR & Payroll", "Users"},
		"STAFF":       {"Dashboard", "Inventory", "Manufacturing", "Users"},
		"LAB_TECH":    {"Dashboard", "Manufacturing", "Users"},
	}

	allowedLabels, exists := roleMenuMap[role]
	if !exists {
		allowedLabels = []string{"Dashboard"}
	}

	// Filter menus
	var filteredMenus []MenuItem
	for _, menu := range allMenus {
		for _, label := range allowedLabels {
			if menu.Label == label {
				filteredMenus = append(filteredMenus, menu)
				break
			}
		}
	}

	return filteredMenus
}

// filterAdminOnlyMenus removes AdminOnly items from menu children
func filterAdminOnlyMenus(menus []MenuItem) []MenuItem {
	result := make([]MenuItem, len(menus))
	for i, menu := range menus {
		result[i] = MenuItem{
			Label: menu.Label,
			Icon:  menu.Icon,
			To:    menu.To,
		}
		if menu.Children != nil {
			var filteredChildren []*MenuChild
			for _, child := range menu.Children {
				if !child.AdminOnly {
					filteredChildren = append(filteredChildren, child)
				}
			}
			result[i].Children = filteredChildren
		}
	}
	return result
}

// GetMenus returns menus for the current user based on role and tenant
// GET /menus
// Logic:
// - ADMIN: All menus (including AdminOnly items like RBAC)
// - MANAGER/OWNER: All menus except AdminOnly items
// - Others with tenant: Query role_menu_permissions from DB
// - Fallback to hardcoded if no permissions in DB
func (h *AuthHandler) GetMenus(c *gin.Context) {
	// Get user info from headers (set by gateway after JWT validation)
	role := c.GetHeader("X-Role")
	tenantID := c.GetHeader("X-Tenant-ID")

	// ADMIN sees all menus including AdminOnly items
	if role == "ADMIN" {
		response.Success(c, getAllMenus(), "Menus retrieved successfully")
		return
	}

	// MANAGER and OWNER see all menus except AdminOnly items
	if role == "MANAGER" || role == "OWNER" || role == "" {
		response.Success(c, filterAdminOnlyMenus(getAllMenus()), "Menus retrieved successfully")
		return
	}

	// If no tenant, use role-based hardcoded menus
	if tenantID == "" {
		response.Success(c, getMenusByRole(role), "Menus retrieved successfully")
		return
	}

	// Query database for tenant-specific menu permissions
	db := database.GetDB()
	if db == nil {
		// No database, fallback to hardcoded
		response.Success(c, getMenusByRole(role), "Menus retrieved successfully (Fallback)")
		return
	}

	// Join role_menu_permissions with menus table
	var results []MenuPermResult
	err := db.Table("role_menu_permissions").
		Select("role_menu_permissions.menu_id, menus.label, menus.icon, menus.path, menus.parent_id, menus.sort_order").
		Joins("JOIN menus ON role_menu_permissions.menu_id = menus.id").
		Where("role_menu_permissions.tenant_id = ? AND role_menu_permissions.role = ? AND role_menu_permissions.can_access = true AND menus.is_active = true", tenantID, role).
		Order("menus.sort_order").
		Scan(&results).Error

	if err != nil || len(results) == 0 {
		// No permissions found, fallback to hardcoded
		response.Success(c, getMenusByRole(role), "Menus retrieved successfully (Default)")
		return
	}

	// Build menu structure from DB results
	// For now, return simple flat structure - can be enhanced for nested menus
	menus := buildMenusFromDB(results)
	response.Success(c, menus, "Menus retrieved successfully")
}

// buildMenusFromDB converts DB results to MenuItem structure
func buildMenusFromDB(results []MenuPermResult) []MenuItem {
	// Build maps for parent-child relationships
	menuMap := make(map[string]*MenuItem)
	var topLevelPtrs []*MenuItem // Use pointers so children get added correctly

	// First pass: create all parent menus
	for _, r := range results {
		if r.ParentID == nil {
			icon := ""
			if r.Icon != nil {
				icon = *r.Icon
			}
			to := ""
			if r.Path != nil {
				to = *r.Path
			}
			menu := &MenuItem{
				Label: r.Label,
				Icon:  icon,
				To:    to,
			}
			menuMap[r.MenuID] = menu
			topLevelPtrs = append(topLevelPtrs, menu)
		}
	}

	// Second pass: add children to their parents
	for _, r := range results {
		if r.ParentID != nil {
			if parent, ok := menuMap[*r.ParentID]; ok {
				to := ""
				if r.Path != nil {
					to = *r.Path
				}
				child := &MenuChild{
					Label: r.Label,
					To:    to,
				}
				parent.Children = append(parent.Children, child)
			}
		}
	}

	// Convert pointers to values for return
	topLevelMenus := make([]MenuItem, len(topLevelPtrs))
	for i, ptr := range topLevelPtrs {
		topLevelMenus[i] = *ptr
	}

	return topLevelMenus
}
