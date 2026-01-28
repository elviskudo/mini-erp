package database

import (
	"log"

	"github.com/elviskudo/mini-erp/services/auth-service/internal/models"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

// SeedMenus populates the database with the initial menu structure
func SeedMenus() error {
	if DB == nil {
		return nil
	}

	menus := getSeedMenus()

	return DB.Transaction(func(tx *gorm.DB) error {
		var touchedIDs []string

		for i, m := range menus {
			ids, err := seedRecursive(tx, m, nil, i)
			if err != nil {
				return err
			}
			touchedIDs = append(touchedIDs, ids...)
		}

		// Deactivate menus that are not in the seed list (Mark-and-Sweep)
		if len(touchedIDs) > 0 {
			if err := tx.Model(&models.Menu{}).Where("id NOT IN ?", touchedIDs).Update("is_active", false).Error; err != nil {
				return err
			}
		}

		log.Println("✅ Menus seeded and synced successfully")
		return nil
	})
}

// seedRecursive inserts/updates a menu and its children, returning list of touched IDs
func seedRecursive(tx *gorm.DB, item SeedMenuItem, parentID *string, order int) ([]string, error) {
	var touchedIDs []string

	// Generate unique code: use path if available, else combine UUID to make it unique
	code := item.Label
	if item.To != nil && *item.To != "" {
		code = *item.To // Path is unique
	} else {
		// For parent menus without path, append UUID suffix
		code = item.Label + "-" + uuid.New().String()[:8]
	}

	menu := models.Menu{
		Code:      code,
		Label:     item.Label,
		Icon:      item.Icon,
		Path:      item.To,
		ParentID:  parentID,
		SortOrder: order,
		IsActive:  true,
	}

	// Upsert based on Label and ParentID (approximation for uniqueness)
	var existing models.Menu
	var err error

	if parentID == nil {
		err = tx.Where("label = ? AND parent_id IS NULL", item.Label).First(&existing).Error
	} else {
		err = tx.Where("label = ? AND parent_id = ?", item.Label, *parentID).First(&existing).Error
	}

	if err == nil {
		// Update
		menu.ID = existing.ID
		if err := tx.Save(&menu).Error; err != nil {
			return nil, err
		}
	} else {
		// Create - generate UUID in Go
		menu.ID = uuid.New().String()
		if err := tx.Create(&menu).Error; err != nil {
			return nil, err
		}
	}
	touchedIDs = append(touchedIDs, menu.ID)

	// Seed Children
	for j, child := range item.Children {
		childIDs, err := seedRecursive(tx, child, &menu.ID, j)
		if err != nil {
			return nil, err
		}
		touchedIDs = append(touchedIDs, childIDs...)
	}

	return touchedIDs, nil
}

type SeedMenuItem struct {
	Label    string
	Icon     *string
	To       *string
	Children []SeedMenuItem
}

func strPtr(s string) *string {
	return &s
}

func getSeedMenus() []SeedMenuItem {
	return []SeedMenuItem{
		// 1. Dashboard
		{Label: "Dashboard", Icon: strPtr("i-heroicons-home"), To: strPtr("/")},

		// 2. CRM (Customer first, before Sales)
		{Label: "CRM", Icon: strPtr("i-heroicons-users"), Children: []SeedMenuItem{
			{Label: "Leads", To: strPtr("/crm/leads")},
			{Label: "Companies", To: strPtr("/crm/companies")},
			{Label: "Contacts", To: strPtr("/crm/contacts")},
			{Label: "Opportunities", To: strPtr("/crm/opportunities")},
			{Label: "Pipeline", To: strPtr("/crm/pipeline")},
			{Label: "Customers", To: strPtr("/crm/customers")},
			{Label: "Activities", To: strPtr("/crm/activities")},
			{Label: "Campaigns", To: strPtr("/crm/campaigns")},
			{Label: "Web Forms", To: strPtr("/crm/forms")},
			{Label: "Marketing", Children: []SeedMenuItem{
				{Label: "Page Builder", To: strPtr("/crm/marketing/pages")},
				{Label: "Email & Broadcast", To: strPtr("/crm/marketing/email")},
				{Label: "Promos", To: strPtr("/crm/promos")},
			}},
		}},

		// 3. Sales (Complete ERP Flow)
		{Label: "Sales", Icon: strPtr("i-heroicons-banknotes"), Children: []SeedMenuItem{
			{Label: "Quotations", To: strPtr("/sales/quotations")},
			{Label: "Sales Orders", To: strPtr("/sales/orders")},
			{Label: "Invoices", To: strPtr("/sales/invoices")},
			{Label: "Credit Notes", To: strPtr("/sales/credit-notes")},
			{Label: "Price Lists", To: strPtr("/sales/price-lists")},
			{Label: "Discount Rules", To: strPtr("/sales/discount-rules")},
			{Label: "Contracts", To: strPtr("/sales/contracts")},
			{Label: "Commission", To: strPtr("/sales/commission")},
			{Label: "Analytics", To: strPtr("/sales/analytics")},
		}},

		// 4. Procurement
		{Label: "Procurement", Icon: strPtr("i-heroicons-shopping-cart"), Children: []SeedMenuItem{
			{Label: "Vendors", To: strPtr("/procurement/vendors")},
			{Label: "Product Catalog", To: strPtr("/procurement/products")},
			{Label: "Purchase Requests", To: strPtr("/procurement/requests")},
			{Label: "RFQ", To: strPtr("/procurement/rfq")},
			{Label: "Purchase Orders", To: strPtr("/procurement/orders")},
			{Label: "Vendor Bills", To: strPtr("/procurement/bills")},
			{Label: "Payments", To: strPtr("/procurement/payments")},
			{Label: "Analytics", To: strPtr("/procurement/analytics")},
		}},

		// 5. Manufacturing
		{Label: "Manufacturing", Icon: strPtr("i-heroicons-wrench-screwdriver"), Children: []SeedMenuItem{
			{Label: "MRP", To: strPtr("/manufacturing/mrp")},
			{Label: "Categories", To: strPtr("/manufacturing/categories")},
			{Label: "Work Centers", To: strPtr("/manufacturing/work-centers")},
			{Label: "Products & BOM", To: strPtr("/manufacturing/products")},
			{Label: "Routing", To: strPtr("/manufacturing/routing")},
			{Label: "Production Orders", To: strPtr("/manufacturing/production")},
			{Label: "Work Orders", To: strPtr("/manufacturing/work-orders")},
			{Label: "Quality Control", To: strPtr("/manufacturing/quality")},
			{Label: "Analytics", To: strPtr("/manufacturing/analytics")},
		}},

		// 6. Inventory
		{Label: "Inventory", Icon: strPtr("i-heroicons-cube"), Children: []SeedMenuItem{
			{Label: "Warehouses", To: strPtr("/inventory/warehouses")},
			{Label: "Storage Zones", To: strPtr("/inventory/storage-zones")},
			{Label: "Stock Status", To: strPtr("/inventory/stock")},
			{Label: "Goods Receipt", To: strPtr("/inventory/receiving")},
			{Label: "Movements", To: strPtr("/inventory/movements")},
			{Label: "Stock Opname", Children: []SeedMenuItem{
				{Label: "Schedule", To: strPtr("/inventory/opname/schedule")},
				{Label: "Counting", To: strPtr("/inventory/opname/counting")},
				{Label: "Matching", To: strPtr("/inventory/opname/matching")},
				{Label: "Adjustment", To: strPtr("/inventory/opname/adjustment")},
			}},
			{Label: "Analytics", To: strPtr("/inventory/analytics")},
		}},

		// 7. Logistics
		{Label: "Logistics", Icon: strPtr("i-heroicons-truck"), Children: []SeedMenuItem{
			{Label: "Delivery Orders", To: strPtr("/logistics/delivery")},
			{Label: "Stock Transfers", To: strPtr("/logistics/transfers")},
			{Label: "Stock Picking", To: strPtr("/logistics/picking")},
			{Label: "Shipments", To: strPtr("/logistics/shipments")},
			{Label: "Returns", To: strPtr("/logistics/returns")},
			{Label: "Couriers", To: strPtr("/logistics/couriers")},
			{Label: "Analytics", To: strPtr("/logistics/analytics")},
		}},

		// 8. Finance
		{Label: "Finance", Icon: strPtr("i-heroicons-banknotes"), Children: []SeedMenuItem{
			{Label: "Dashboard", To: strPtr("/finance")},
			{Label: "Chart of Accounts", To: strPtr("/finance/coa")},
			{Label: "General Ledger", To: strPtr("/finance/gl")},
			{Label: "Accounts Payable", Children: []SeedMenuItem{
				{Label: "Vendor Bills", To: strPtr("/finance/ap/bills")},
				{Label: "Payments", To: strPtr("/finance/ap/payments")},
				{Label: "Aging Report", To: strPtr("/finance/ap/aging")},
			}},
			{Label: "Accounts Receivable", Children: []SeedMenuItem{
				{Label: "Invoices", To: strPtr("/finance/ar/invoices")},
				{Label: "Receipts", To: strPtr("/finance/ar/receipts")},
				{Label: "Aging Report", To: strPtr("/finance/ar/aging")},
			}},
			{Label: "Bank & Cash", Children: []SeedMenuItem{
				{Label: "Bank Accounts", To: strPtr("/finance/banking/accounts")},
				{Label: "Transactions", To: strPtr("/finance/banking/transactions")},
				{Label: "Reconciliation", To: strPtr("/finance/banking/reconciliation")},
				{Label: "Petty Cash", To: strPtr("/finance/banking/petty-cash")},
			}},
			{Label: "Taxes", Children: []SeedMenuItem{
				{Label: "Tax Configuration", To: strPtr("/finance/tax/config")},
				{Label: "PPN/VAT", To: strPtr("/finance/tax/ppn")},
				{Label: "Withholding Tax", To: strPtr("/finance/tax/withholding")},
				{Label: "e-Faktur", To: strPtr("/finance/tax/efaktur")},
			}},
			{Label: "Fixed Assets", To: strPtr("/finance/assets")},
			{Label: "Budgeting", Children: []SeedMenuItem{
				{Label: "Budgets", To: strPtr("/finance/budget")},
				{Label: "Budget vs Actual", To: strPtr("/finance/budget/variance")},
			}},
			{Label: "Cost Centers", To: strPtr("/finance/cost-centers")},
			{Label: "Reports", Children: []SeedMenuItem{
				{Label: "Trial Balance", To: strPtr("/finance/reports/trial-balance")},
				{Label: "Profit & Loss", To: strPtr("/finance/reports/pl")},
				{Label: "Balance Sheet", To: strPtr("/finance/reports/balance-sheet")},
				{Label: "Cash Flow", To: strPtr("/finance/reports/cash-flow")},
				{Label: "General Ledger", To: strPtr("/finance/reports/gl")},
			}},
		}},

		// 9. POS
		{Label: "POS", Icon: strPtr("i-heroicons-computer-desktop"), Children: []SeedMenuItem{
			{Label: "Sessions", To: strPtr("/pos/sessions")},
			{Label: "Products", To: strPtr("/pos/products")},
			{Label: "Payments", To: strPtr("/pos/payments")},
		}},

		// 10. Loyalty & Rewards
		{Label: "Loyalty & Rewards", Icon: strPtr("i-heroicons-gift"), Children: []SeedMenuItem{
			{Label: "Coin Top-Up", To: strPtr("/finance/loyalty/topup")},
			{Label: "Redemption Rules", To: strPtr("/finance/loyalty/rules")},
			{Label: "Balance Tracking", To: strPtr("/finance/loyalty/balance")},
			{Label: "Analytics", To: strPtr("/finance/loyalty/analytics")},
		}},

		// 11. Projects
		{Label: "Projects", Icon: strPtr("i-heroicons-clipboard-document-list"), Children: []SeedMenuItem{
			{Label: "Kanban Boards", To: strPtr("/projects/kanban")},
			{Label: "Tasks", To: strPtr("/projects/tasks")},
			{Label: "Timesheets", To: strPtr("/projects/timesheets")},
			{Label: "Reports", To: strPtr("/projects/reports")},
		}},

		// 12. Maintenance
		{Label: "Maintenance", Icon: strPtr("i-heroicons-wrench"), Children: []SeedMenuItem{
			{Label: "Assets", To: strPtr("/maintenance/assets")},
			{Label: "Maintenance Requests", To: strPtr("/maintenance/requests")},
			{Label: "Schedules", To: strPtr("/maintenance/schedules")},
			{Label: "Reports", To: strPtr("/maintenance/reports")},
		}},

		// 13. Fleet
		{Label: "Fleet", Icon: strPtr("i-heroicons-truck"), Children: []SeedMenuItem{
			{Label: "Dashboard", To: strPtr("/fleet")},
			{Label: "Vehicles", To: strPtr("/fleet/vehicles")},
			{Label: "Bookings", To: strPtr("/fleet/bookings")},
			{Label: "Fuel Logs", To: strPtr("/fleet/fuel")},
			{Label: "Maintenance", To: strPtr("/fleet/maintenance")},
			{Label: "Expense", To: strPtr("/fleet/expenses")},
			{Label: "Reminders", To: strPtr("/fleet/reminders")},
		}},

		// 14. HR & Payroll
		{Label: "HR & Payroll", Icon: strPtr("i-heroicons-user-group"), Children: []SeedMenuItem{
			{Label: "Dashboard", To: strPtr("/hr")},
			{Label: "Employees", To: strPtr("/hr/employees")},
			{Label: "Organization", To: strPtr("/hr/organization")},
			{Label: "Attendance", To: strPtr("/hr/attendance")},
			{Label: "Leave", To: strPtr("/hr/leave")},
			{Label: "Leaderboard", To: strPtr("/hr/leaderboards")},
			{Label: "Payroll", To: strPtr("/hr/payroll")},
			{Label: "Analytics", To: strPtr("/hr/analytics")},
		}},

		// 15. Compliance
		{Label: "Compliance", Icon: strPtr("i-heroicons-shield-check"), Children: []SeedMenuItem{
			{Label: "Regulatory Reports", To: strPtr("/compliance/reports")},
			{Label: "Audit Trails", To: strPtr("/compliance/audit")},
			{Label: "ISO Tools", To: strPtr("/compliance/iso")},
			{Label: "Risk Management", To: strPtr("/compliance/risk")},
			{Label: "Data Privacy", To: strPtr("/compliance/privacy")},
		}},

		// 16. Users
		{Label: "Users", Icon: strPtr("i-heroicons-user-circle"), Children: []SeedMenuItem{
			{Label: "User List", To: strPtr("/users")},
			{Label: "Roles", To: strPtr("/users/roles")},
			{Label: "RBAC Permissions", To: strPtr("/users/rbac")},
		}},

		// 17. Setup
		{Label: "Setup", Icon: strPtr("i-heroicons-cog-6-tooth"), To: strPtr("/setup")},
	}
}
