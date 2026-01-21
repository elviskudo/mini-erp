export const MENUS = [
    {
        label: 'Dashboard',
        icon: 'i-heroicons-home',
        to: '/'
    },
    {
        label: 'CRM',
        icon: 'i-heroicons-user-group',
        children: [
            { label: 'Leads', to: '/crm/leads' },
            { label: 'Companies', to: '/crm/companies' },
            { label: 'Contacts', to: '/crm/contacts' },
            { label: 'Opportunities', to: '/crm/opportunities' },
            { label: 'Pipeline', to: '/crm/pipeline' },
            { label: 'Customers', to: '/crm/customers' },
            { label: 'Activities', to: '/crm/activities' },
            { label: 'Campaigns', to: '/crm/campaigns' },
            { label: 'Web Forms', to: '/crm/forms' }
        ]
    },
    {
        label: 'Sales',
        icon: 'i-heroicons-currency-dollar',
        children: [
            { label: 'Quotations', to: '/sales/quotations' },
            { label: 'Sales Orders', to: '/sales/orders' },
            { label: 'Invoices', to: '/sales/invoices' },
            { label: 'Credit Notes', to: '/sales/credit-notes' },
            { label: 'Price Lists', to: '/sales/price-lists' },
            { label: 'Discount Rules', to: '/sales/discount-rules' },
            { label: 'Contracts', to: '/sales/contracts' },
            { label: 'Commission', to: '/sales/commission' },
            { label: 'Analytics', to: '/sales/analytics' }
        ]
    },
    {
        label: 'Procurement',
        icon: 'i-heroicons-shopping-cart',
        children: [
            { label: 'Vendors', to: '/procurement/vendors' },
            { label: 'Product Catalog', to: '/procurement/catalog' },
            { label: 'Purchase Request', to: '/procurement/requests' },
            { label: 'RFQ', to: '/procurement/rfq' },
            { label: 'Purchase Orders', to: '/procurement/orders' },
            { label: 'Vendor Bill', to: '/procurement/bills' },
            { label: 'Payments', to: '/procurement/payments' },
            { label: 'Analytics', to: '/procurement/analytics' }
        ]
    },
    {
        label: 'Manufacturing',
        icon: 'i-heroicons-wrench-screwdriver',
        children: [
            {
                label: 'MRP',
                children: [
                    { label: 'MRP Run', to: '/manufacturing/mrp/run' },
                    { label: 'MPS', to: '/manufacturing/mrp/mps' },
                    { label: 'Demand Forecasting', to: '/manufacturing/mrp/forecast' },
                    { label: 'Net Requirements', to: '/manufacturing/mrp/requirements' },
                    { label: 'MRP Exceptions', to: '/manufacturing/mrp/exceptions' },
                    { label: 'Analytics', to: '/manufacturing/mrp/analytics' }
                ]
            },
            { label: 'Categories', to: '/manufacturing/categories' },
            { label: 'Work Centers', to: '/manufacturing/work-centers' },
            { label: 'Products & BOM', to: '/manufacturing/products' },
            { label: 'Routing', to: '/manufacturing/routings' },
            { label: 'Production Orders', to: '/manufacturing/production-orders' },
            {
                label: 'Work Orders',
                children: [
                    { label: 'Open Work Orders', to: '/manufacturing/work-orders' },
                    { label: 'WO Dashboard', to: '/manufacturing/work-orders/dashboard' }
                ]
            },
            { label: 'Quality Control', to: '/manufacturing/qc' },
            { label: 'Analytics', to: '/manufacturing/analytics' }
        ]
    },
    {
        label: 'Inventory',
        icon: 'i-heroicons-archive-box',
        children: [
            { label: 'Warehouses', to: '/inventory/warehouses' },
            { label: 'Storage Zone', to: '/inventory/zones' },
            { label: 'Stock Status', to: '/inventory/stock' },
            { label: 'Goods Receipt', to: '/inventory/receipts' },
            { label: 'Movements', to: '/inventory/movements' },
            {
                label: 'Stock Opname',
                children: [
                    { label: 'Schedule', to: '/inventory/opname/schedule' },
                    { label: 'Counting', to: '/inventory/opname/counting' },
                    { label: 'Matching', to: '/inventory/opname/matching' },
                    { label: 'Adjustment', to: '/inventory/opname/adjustment' }
                ]
            },
            { label: 'Analytics', to: '/inventory/analytics' }
        ]
    },
    {
        label: 'Logistics',
        icon: 'i-heroicons-truck',
        children: [
            { label: 'Delivery Orders', to: '/logistics/delivery-orders' },
            { label: 'Stock Transfers', to: '/logistics/transfers' },
            { label: 'Stock Picking', to: '/logistics/picking' },
            { label: 'Shipments', to: '/logistics/shipments' },
            { label: 'Returns', to: '/logistics/returns' },
            { label: 'Couriers', to: '/logistics/couriers' },
            { label: 'Analytics', to: '/logistics/analytics' }
        ]
    },
    {
        label: 'Finance',
        icon: 'i-heroicons-banknotes',
        children: [
            { label: 'Chart of Accounts', to: '/finance/coa' },
            { label: 'Invoices & Bills', to: '/finance/invoices' },
            { label: 'Payments & Receipts', to: '/finance/payments' },
            { label: 'Journals', to: '/finance/journals' },
            { label: 'Reports', to: '/finance/reports' },
            { label: 'Budgeting', to: '/finance/budgeting' },
            { label: 'Analytics', to: '/finance/analytics' }
        ]
    },
    {
        label: 'POS',
        icon: 'i-heroicons-computer-desktop',
        to: '/pos'
    },
    {
        label: 'Loyalty & Rewards',
        icon: 'i-heroicons-gift',
        children: [
            { label: 'Coin Top-Up', to: '/loyalty/topup' },
            { label: 'Redemption Rules', to: '/loyalty/rules' },
            { label: 'Balance Tracking', to: '/loyalty/balance' },
            { label: 'Analytics', to: '/loyalty/analytics' }
        ]
    },
    {
        label: 'Projects',
        icon: 'i-heroicons-clipboard-document-list',
        children: [
            { label: 'Kanban Boards', to: '/projects/kanban' },
            { label: 'Tasks', to: '/projects/tasks' },
            { label: 'Timesheets', to: '/projects/timesheets' },
            { label: 'Reports', to: '/projects/reports' }
        ]
    },
    {
        label: 'Maintenance',
        icon: 'i-heroicons-wrench',
        children: [
            { label: 'Assets', to: '/maintenance/assets' },
            { label: 'Requests', to: '/maintenance/requests' },
            { label: 'Schedules', to: '/maintenance/schedules' },
            { label: 'Reports', to: '/maintenance/reports' }
        ]
    },
    {
        label: 'Fleet',
        icon: 'i-heroicons-map',
        children: [
            { label: 'Dashboard', to: '/fleet/dashboard' },
            { label: 'Vehicles', to: '/fleet/vehicles' },
            { label: 'Booking', to: '/fleet/booking' },
            { label: 'Fuel Logs', to: '/fleet/fuel' },
            { label: 'Maintenance', to: '/fleet/maintenance' },
            { label: 'Expense', to: '/fleet/expense' },
            { label: 'Reminder', to: '/fleet/reminder' }
        ]
    },
    {
        label: 'HR & Payroll',
        icon: 'i-heroicons-users',
        children: [
            { label: 'Dashboard', to: '/hr/dashboard' },
            { label: 'Employees', to: '/hr/employees' },
            { label: 'Organization', to: '/hr/organization' },
            { label: 'Attendance', to: '/hr/attendance' },
            { label: 'Leave', to: '/hr/leave' },
            { label: 'Leaderboard', to: '/hr/leaderboard' },
            { label: 'Payroll', to: '/hr/payroll' },
            { label: 'Analytics', to: '/hr/analytics' }
        ]
    },
    {
        label: 'Compliance',
        icon: 'i-heroicons-shield-check',
        children: [
            { label: 'Regulatory Reports', to: '/compliance/reports' },
            { label: 'Audit Trails', to: '/compliance/audit' },
            { label: 'ISO Tools', to: '/compliance/iso' },
            { label: 'Risk Management', to: '/compliance/risk' },
            { label: 'Data Privacy', to: '/compliance/privacy' }
        ],
        roles: ['ADMIN', 'MANAGER', 'OWNER']
    },
    {
        label: 'Users',
        icon: 'i-heroicons-user-circle',
        children: [
            { label: 'Users', to: '/users' },
            { label: 'Roles', to: '/roles' },
            { label: 'Permissions', to: '/permissions' },
        ],
        roles: ['ADMIN', 'MANAGER', 'OWNER']
    },
    {
        label: 'Setup',
        icon: 'i-heroicons-cog-6-tooth',
        to: '/settings',
        roles: ['ADMIN', 'MANAGER', 'OWNER']
    }
]
