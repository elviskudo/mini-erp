# Mini ERP System

A modern, full-stack ERP system built with **Go microservices architecture** for efficiency and scalability. Designed for small to medium manufacturing businesses with **complete multi-tenancy support** and **25+ independent services**.

![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)
![Gin](https://img.shields.io/badge/Gin-00ADD8?style=flat&logo=go&logoColor=white)
![Nuxt](https://img.shields.io/badge/Nuxt.js-00DC82?style=flat&logo=nuxt.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat&logo=apachekafka&logoColor=white)

## ✨ Features

### Core Modules
- **Manufacturing** - Work centers, products, BOMs, production orders
- **Inventory** - Stock management, warehouses, stock opname
- **Procurement** - Purchase requests, purchase orders, vendors
- **Receiving** - Goods receiving, quality checks
- **Quality Control** - Inspections, batch tracking
- **Finance** - Chart of accounts, general ledger, fixed assets
- **HR** - Employees, payroll management
- **CRM** - Customer management, sales orders
- **Projects** - Project management, task tracking with Kanban board
- **Maintenance** - Asset management, work orders, schedules
- **POS** - Point of Sale system with customer credit, promos, transactions

### 🆕 Recent Updates (January 2026)

#### Go Microservices Architecture Migration
The system has been migrated from Python FastAPI to a **Go-based microservices architecture**:

| Service | Port | Technology |
|---------|------|------------|
| **API Gateway** | 8000 | Go + Gin |
| **Auth Service** | 8010 | Go + Gin + JWT |
| **Finance Service** | 8011 | Go + Gin |
| **HR Service** | 8012 | Go + Gin |
| **Inventory Service** | 8013 | Go + Gin |
| **Manufacturing Service** | 8014 | Go + Gin |
| **Fleet Service** | 8015 | Go + Gin |
| **CRM Service** | 8016 | Go + Gin |
| **Projects Service** | 8017 | Go + Gin |
| **Procurement Service** | 8018 | Go + Gin |
| **Logistics Service** | 8019 | Go + Gin |
| **Maintenance Service** | 8020 | Go + Gin |
| **POS Service** | 8021 | Go + Gin |

#### Phase 4.6: Standardized JSON Response & Pagination ✅
All API endpoints now return a standardized JSON format:
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Data retrieved successfully",
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 10,
      "total_items": 87,
      "total_pages": 9,
      "has_next": true,
      "has_prev": false
    }
  },
  "errors": null,
  "timestamp": "2026-01-16T10:30:45Z",
  "request_id": "req_8f92c1a7"
}
```

#### JSON Truncation Fix
- Fixed frontend `api-proxy.ts` returning raw response text to prevent Nuxt re-serialization truncation
- All API responses now return complete JSON through frontend proxy

#### Work Centers CRUD Fixed
- **Create**: UUID auto-generation with `gen_random_uuid()`, tenant_id from header
- **Update**: Partial updates with db.Save(), status toggle (is_active) working
- **Delete**: Proper database deletion with existence verification

#### Performance Improvements
- Dockerfile switched from dev mode (`bun run dev`) to production mode (`bun run build` + `bun run preview`)
- Warm request time: **0.24s** (down from 20s cold start)
- Socket.io lazy loaded with 3s timeout to prevent blocking

#### Frontend Enhancements
- **ServerDataTable.vue** - New component for server-side pagination
- **useApi.ts** - Composable for standardized API calls with pagination support
- **api-proxy.ts** - Cookie-based auth token extraction for API calls

#### CRM Module Fixes (January 2026)
Complete overhaul of CRM service to fix 500 errors and model-database mismatches:

**Model Schema Fixes:**
| Model | Issue | Fix |
|-------|-------|-----|
| **Activity** | Fields `Type`, `Subject` didn't match DB | Changed to `ActivityType`, `Title` + added `Status`, `DueTime`, `DurationMinutes`, `Priority`, `OpportunityID`, `Outcome`, `CreatedBy`, `UpdatedAt` |
| **Opportunity** | Fields `Amount`, `ExpectedDate` didn't match DB | Changed to `ExpectedValue`, `ExpectedCloseDate` + added `Description`, `ActualValue`, `LostReason`, `ClosedAt`, `CreatedBy`, `UpdatedAt` |

**Enum Uppercase Conversion:**
All PostgreSQL enums require uppercase values. Added automatic conversion:
| Enum | Frontend Value | DB Value |
|------|---------------|----------|
| `activitytype` | `Task`, `Follow Up` | `TASK`, `FOLLOW_UP` |
| `activitystatus` | `In Progress` | `IN_PROGRESS` |
| `opportunitystage` | `Qualification` | `QUALIFICATION` |

**UUID Handling Fixes:**
- Empty string UUID fields now converted to `nil` to prevent `invalid input syntax for type uuid: ""` errors
- Added `BeforeCreate` hooks for auto-generating UUIDs on Opportunity and Activity models

**API Gateway Routes:**
Added 55+ missing CRM routes to `gateway/internal/routes/routes.go`:
- Activities: Full CRUD + `/activities/:id/complete`
- Opportunities: Full CRUD + `/opportunities/:id/stage`
- Companies, Contacts, Campaigns, Forms: Full CRUD
- Customer Activity: Emails, Calls, Meetings, Documents

**Frontend Pipeline Fix:**
- Fixed `pipeline.vue` data extraction for nested API response `{data: {data: [...]}}`
- Updated stage values to uppercase for proper filtering

### 🏢 Multi-Tenancy (SaaS Architecture)
- **Tenant Isolation** - All data scoped by `tenant_id`
- **Company Registration** - 2-step wizard (Company → Admin)
- **Employee Join Flow** - 6-character company code system
- **Iron Wall Middleware** - Automatic tenant filtering on all queries
- **Real-time Isolation** - Socket.IO rooms per tenant
- **Audit Logging** - All logs tagged with `tenant_id`

### 🔐 Authentication & Security
- JWT-based authentication
- Email OTP verification
- Role-based access control (Owner, Admin, Member, Pending)
- Automatic `X-Tenant-ID` header injection

## 🛠 Tech Stack

### Backend (Go Microservices)
| Component | Technology |
|-----------|------------|
| Language | **Go 1.21+** |
| Framework | **Gin** (HTTP Router) |
| Database | PostgreSQL (via Supabase) |
| ORM | **GORM** |
| Message Queue | Kafka |
| Cache | Redis |
| API Gateway | Custom Go Gateway |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Nuxt 3 (Vue.js 3) |
| Runtime | **Bun** (oven/bun:1-alpine) |
| Styling | TailwindCSS + Nuxt UI (Gumroad-inspired pink theme) |
| State | Pinia |
| HTTP Client | Axios |

### Microservices Architecture (25+ Services)

**Core Services (14):**
| Service | Port | Description |
|---------|------|-------------|
| api-gateway | 8000 | Central API Gateway |
| auth-service | 8010 | JWT Authentication & Users |
| finance-service | 8011 | Chart of Accounts, GL, Fixed Assets |
| hr-service | 8012 | Employees, Payroll |
| inventory-service | 8013 | Stock, Warehouses, Opname |
| manufacturing-service | 8014 | BOM, Production Orders |
| fleet-service | 8015 | Vehicle Management |
| sales-service | 8016 | Sales Orders, Invoices |
| crm-service | 8017 | Leads, Opportunities, Activities |
| procurement-service | 8018 | Purchase Orders, Vendors |
| logistics-service | 8019 | Delivery, Shipments |
| maintenance-service | 8020 | Work Orders, Asset Maintenance |
| pos-service | 8021 | Point of Sale, Transactions |
| projects-service | 8022 | Project & Task Management |

**Vertical Industry Services (3):**
| Service | Description |
|---------|-------------|
| clinic-service | Healthcare/Clinic Management |
| sports-service | Sports Facility Management |
| travel-service | Travel & Tourism Management |

**Frontend Applications:**
| Service | Port | Description |
|---------|------|-------------|
| frontend_web | 3333 | Main ERP Frontend (Nuxt 3 + Bun) |
| pos_app | 3334 | Point of Sale App (Nuxt 3) |
| realtime_server | 3001 | Socket.IO for real-time updates |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/elviskudo/mini-erp.git
   cd mini-erp
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start all services**
   ```bash
   docker compose up --build -d
   ```

4. **Seed initial data** (optional)
   ```bash
   docker compose exec backend_api python seed.py
   ```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Main Frontend | http://localhost:3333 | - |
| POS Frontend | http://localhost:3334 | - |
| Backend API Docs | http://localhost:8000/docs | - |
| RabbitMQ Console | http://localhost:15672 | guest/guest |

## 🏢 Multi-Tenancy Flow

### For Company Owners (New Organizations)

1. Visit `/auth/register-company`
2. **Step 1**: Enter company details (name, domain, currency, timezone)
3. Receive unique 6-character **Company Code** (e.g., `ABC123`)
4. **Step 2**: Create admin account
5. Verify email via OTP
6. Login and start using the system

### For Employees (Joining Existing Company)

1. Visit `/auth/join-company`
2. Enter company code from your admin
3. Create your account
4. Verify email via OTP
5. Wait for admin approval (status: `PENDING`)
6. Login after approval

### SaaS API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/saas/register-tenant` | POST | Register new company |
| `/saas/register-owner` | POST | Register owner/admin |
| `/saas/find-company/{code}` | GET | Find company by code |
| `/saas/request-join` | POST | Employee join request |
| `/saas/pending-members` | GET | List pending requests |
| `/saas/approve-member` | POST | Approve/reject member |

### Iron Wall Middleware

All API requests automatically include tenant context:

```
Frontend → X-Tenant-ID Header → Backend → Tenant Dependency → Filtered Queries
```

**Usage in Routers:**
```python
from dependencies.tenant import require_tenant

@router.get("/products")
async def get_products(
    tenant: Tenant = Depends(require_tenant),
    db: AsyncSession = Depends(get_db)
):
    # Queries automatically scoped to tenant
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant.id)
    )
```

## 🔐 Authentication Flow

### Registration (Legacy - Single User)
```
POST /auth/register    - Register new user
POST /auth/send-otp    - Resend OTP code
POST /auth/verify-otp  - Verify OTP and activate
```

### Login
```
POST /auth/token       - Login (OAuth2 form)
GET  /auth/me          - Get current user info
```

## 📧 Email Configuration

Configure SMTP in `.env` for OTP emails:

```env
# Gmail (use App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@minierp.com
SMTP_FROM_NAME=Mini ERP
```

> **Dev Mode**: If `SMTP_USER` is empty, OTP codes are printed to backend console.

## 📁 Project Structure

```
mini-erp/
├── backend/                    # FastAPI Backend (Python)
│   ├── routers/                # API endpoints
│   │   ├── auth.py             # Authentication & JWT
│   │   ├── saas.py             # Multi-tenant onboarding
│   │   ├── menu.py             # Dynamic menu system
│   │   ├── dashboard.py        # Analytics dashboard
│   │   ├── inventory.py        # Stock management
│   │   ├── opname.py           # Stock opname operations
│   │   ├── manufacturing.py    # Production & BOM
│   │   ├── procurement.py      # Purchase orders & vendors
│   │   ├── finance.py          # Chart of accounts & GL
│   │   ├── hr.py               # Employees & payroll
│   │   ├── crm.py              # Customer management
│   │   ├── projects.py         # Project tracking
│   │   ├── qc.py               # Quality control
│   │   ├── receiving.py        # Goods receipt
│   │   ├── delivery.py         # Logistics
│   │   ├── maintenance.py      # Asset maintenance
│   │   ├── settings.py         # System configuration
│   │   ├── export.py           # PDF/Excel exports
│   │   └── users.py            # User management
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── base.py             # TenantMixin base class
│   │   ├── user.py             # User model
│   │   ├── models_saas.py      # Tenant, TenantMember
│   │   ├── models_menu.py      # Menu & permissions
│   │   ├── models_inventory.py # Stock, Warehouse
│   │   ├── models_opname.py    # Stock opname entities
│   │   ├── models_manufacturing.py # Products, BOM, WorkCenter
│   │   ├── models_procurement.py   # PO, PR, Vendor
│   │   ├── models_finance.py   # COA, Journal, Assets
│   │   ├── models_hr.py        # Employee, Payroll
│   │   └── ...                 # Other domain models
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py             # Auth DTOs
│   │   ├── schemas_inventory.py
│   │   ├── schemas_opname.py
│   │   ├── schemas_manufacturing.py
│   │   └── ...                 # Other schemas
│   ├── services/               # Business logic
│   │   ├── email_service.py    # SMTP & OTP
│   │   ├── pdf_service.py      # PDF generation
│   │   ├── notification_service.py # RabbitMQ notifications
│   │   ├── hpp_service.py      # Cost calculation (HPP)
│   │   ├── gl_engine.py        # General ledger engine
│   │   ├── mrp_engine.py       # MRP planning
│   │   ├── matching_engine.py  # Stock opname matching
│   │   └── reporting_engine.py # Report generation
│   ├── connections/            # Database & queue connections
│   │   ├── mongodb.py          # MongoDB (logs/IoT)
│   │   ├── rabbitmq_utils.py   # RabbitMQ publisher
│   │   ├── worker.py           # Background workers
│   │   └── iot_simulator.py    # IoT data simulator
│   ├── dependencies/           # FastAPI dependencies
│   │   ├── tenant.py           # Iron Wall middleware
│   │   └── __init__.py         # Common deps (get_db, auth)
│   ├── utils/                  # Utilities
│   │   ├── cache.py            # Redis caching
│   │   ├── media.py            # Cloudinary upload
│   │   └── stripe_utils.py     # Payment processing
│   ├── alembic/                # Database migrations
│   ├── main.py                 # App entry point
│   ├── database.py             # Async SQLAlchemy setup
│   ├── auth.py                 # JWT utilities
│   ├── seed.py                 # Initial data seeder
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # Nuxt 3 Frontend (Vue.js)
│   ├── pages/                  # Route pages
│   │   ├── index.vue           # Dashboard home
│   │   ├── auth/               # Authentication pages
│   │   │   ├── login.vue       # Gumroad-style login
│   │   │   ├── register-company.vue # Company registration
│   │   │   ├── join-company.vue    # Employee join flow
│   │   │   └── verify.vue      # OTP verification
│   │   ├── inventory/          # Inventory module
│   │   │   ├── warehouses.vue
│   │   │   ├── stock.vue
│   │   │   ├── movements.vue
│   │   │   ├── receiving.vue
│   │   │   ├── storage-zones.vue
│   │   │   ├── overhead.vue
│   │   │   └── opname/         # Stock opname sub-pages
│   │   │       ├── index.vue   # Dashboard
│   │   │       ├── schedule.vue
│   │   │       ├── counting.vue
│   │   │       ├── matching.vue
│   │   │       ├── adjustment.vue
│   │   │       └── reports.vue
│   │   ├── manufacturing/      # Production module
│   │   ├── procurement/        # Purchase module
│   │   ├── finance/            # Finance module
│   │   ├── hr/                 # HR module
│   │   ├── crm/                # CRM module
│   │   ├── projects/           # Projects module
│   │   ├── qc/                 # Quality control
│   │   ├── logistics/          # Delivery tracking
│   │   ├── maintenance/        # Asset maintenance
│   │   └── settings/           # System settings
│   ├── components/             # Reusable components
│   │   ├── DataTable.vue       # Generic data table
│   │   ├── FormSlideover.vue   # Slide-over forms
│   │   ├── CurrencyInput.vue   # Formatted currency input
│   │   ├── Barcode.vue         # Barcode generator
│   │   ├── QRCode.vue          # QR code generator
│   │   └── ShimmerLoading.vue  # Loading skeleton
│   ├── layouts/                # Page layouts
│   │   └── default.vue         # Main layout with sidebar
│   ├── stores/                 # Pinia state stores
│   │   └── auth.ts             # Auth + tenant state
│   ├── composables/            # Vue composables
│   ├── plugins/                # Nuxt plugins
│   │   └── api.ts              # Axios with X-Tenant-ID
│   ├── middleware/             # Route middleware
│   │   └── auth.ts             # Auth guard
│   ├── utils/                  # Utility functions
│   ├── assets/                 # Static assets
│   ├── nuxt.config.ts          # Nuxt configuration
│   ├── tailwind.config.js      # TailwindCSS (pink theme)
│   └── package.json
│
├── pos/                        # POS Nuxt Application (Separate)
│   ├── pages/
│   │   └── pos.vue             # Main POS interface
│   ├── components/             # POS-specific components
│   ├── stores/                 # Pinia stores (cart, auth)
│   ├── composables/            # Vue composables
│   ├── Dockerfile              # npm-based container
│   └── nuxt.config.ts
│
├── realtime/                   # Socket.IO Server (Node.js)
│   ├── index.js                # WebSocket server with tenant rooms
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
└── README.md
```


## 🎨 Design System (Gumroad-Inspired)

### Color Palette
| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#ec4899` | Buttons, links, accents |
| Accent | `#a855f7` | Secondary highlights |
| Background | `pink-50 → purple-100` | Gradient backgrounds |

### Custom Utilities
```css
.shadow-gumroad     /* Soft pink shadow */
.shadow-gumroad-lg  /* Large pink shadow */
.bg-gradient-gumroad /* Pink-to-purple gradient */
```

## 🧪 Default Users (after seeding)

| Username | Email | Password | Role |
|----------|-------|----------|------|
| admin | admin@minierp.com | admin123 | Admin |
| manager | manager@minierp.com | manager123 | Manager |
| production | production@minierp.com | production123 | Production |
| warehouse | warehouse@minierp.com | warehouse123 | Warehouse |
| procurement | procurement@minierp.com | procurement123 | Procurement |
| finance | finance@minierp.com | finance123 | Finance |
| hr | hr@minierp.com | hr123 | HR |
| staff | staff@minierp.com | staff123 | Staff |
| lab_tech | labtech@minierp.com | lab_tech123 | Lab Tech |

> **Password Format**: `{username}123` (e.g., admin → admin123, manager → manager123)
> Note: Seeded users have `is_verified=true` by default.

## 📊 Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "postgres": "connected",
    "mongo": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

## 📋 Business Processes

### 🏭 Manufacturing Process

```
1. Products & BOM Setup
   └─> Create Products → Define Bill of Materials (BOM) → Set Standard Costs

2. Production Planning
   └─> Create Production Order → Select Products → Set Quantity → Schedule Date

3. Production Execution
   └─> Start Production → Record Progress → Track Material Consumption

4. Quality Control Integration
   └─> Record QC Results (Good/Defect/Scrap) → Categorize Scrap Type

5. Cost Calculation (HPP/COGM)
   └─> Calculate Material Cost → Add Labor Cost → Add Overhead → Get HPP per Unit

6. Inventory Transfer
   └─> Complete Production → Transfer Finished Goods to Stock
```

**Key Features:**
- Multi-product production orders
- Work center assignment
- Real-time progress tracking
- Cost of Goods Manufactured (COGM) calculation
- Scrap tracking with Grade B/Rework options

---

### 📦 Inventory Management

```
1. Warehouse Setup
   └─> Create Warehouses → Define Storage Zones → Create Locations

2. Stock Receipt
   └─> Goods Receipt from PO/Production → Quality Check → Batch Assignment

3. Stock Movements
   └─> Transfer In/Out → Location Moves → Adjustments

4. Stock Monitoring
   └─> Real-time Stock Levels → Low Stock Alerts → Location Tracking

5. Reporting
   └─> Stock Status → Movement History → Overhead Analysis
```

**Key Features:**
- Multi-warehouse support
- Zone-based storage
- Batch/lot tracking
- Movement ledger with full audit trail
- Inventory valuation (FIFO/Average)

---

### 🔍 Stock Opname (Physical Inventory Count)

```
1. Schedule Planning (/inventory/opname/schedule)
   └─> Create Schedule → Assign Warehouse → Set Frequency → Assign Team

2. Physical Counting (/inventory/opname/counting)
   └─> Snapshot Stock → Start Counting → Record Physical Qty → Save Progress

3. Variance Analysis (/inventory/opname/matching)
   └─> Compare System vs Counted → Calculate Variance % → Assign Reasons

4. Review & Approval (/inventory/opname/adjustment)
   └─> Manager Review → Approve/Reject → Post Adjustments to Inventory
```

**Variance Reasons:**
- Theft, Damage, Input Error
- Return Not Recorded, Receiving Error
- Expired, Shrinkage, System Error
- Unknown, Other

**Export Options:** CSV, XLS, PDF for all pages

---

### 🛒 Procurement Process

```
1. Purchase Request (PR)
   └─> Request from Department → Items Needed → Urgency Level

2. Vendor Selection
   └─> Maintain Vendor Master → Compare Prices → Select Vendor

3. Purchase Order (PO)
   └─> Create PO from PR → Send to Vendor → Track Status

4. Goods Receipt
   └─> Receive Goods → QC Inspection → Update Stock → Create Voucher
```

**PO Statuses:** Draft → Sent → Partially Received → Received → Closed

---

### 🔬 Quality Control (QC)

```
1. QC Inspection Setup
   └─> Define Inspection Criteria → Set Tolerances

2. Inspection Process
   └─> Receive Sample → Perform Tests → Record Results

3. Batch Decision
   └─> Pass/Fail Batch → Create Non-Conformance Report (NCR)

4. Corrective Actions
   └─> Define Root Cause → Plan Corrective Actions → Follow Up
```

**Integration Points:**
- Goods Receipt → Auto-trigger QC
- Production → QC before stock transfer
- Supplier Rating based on QC results

---

### 💰 Finance Module

```
1. Chart of Accounts (COA)
   └─> Define Account Structure → Categories (Asset, Liability, Equity, Revenue, Expense)

2. Journal Entries
   └─> Manual Journals → Auto-generated from Transactions

3. General Ledger (GL)
   └─> View Ledger by Account → Trial Balance → Period Close

4. Fixed Assets
   └─> Asset Registration → Depreciation Calculation → Disposal

5. Reports
   └─> Balance Sheet → Income Statement → Cash Flow
```

**Auto-generated Journals:**
- PO Receipt → Inventory Dr, AP Cr
- Sales → AR Dr, Revenue Cr
- Production → WIP Dr, Raw Materials Cr

---

### 👥 HR & Payroll

```
1. Employee Management
   └─> Employee Registration → Department Assignment → Position History

2. Attendance
   └─> Time Clock → Leave Requests → Overtime Tracking

3. Payroll Processing
   └─> Calculate Basic Salary → Add Allowances → Deduct Contributions → Net Pay

4. Payslip Generation
   └─> Generate Payslips → Batch Payment → Bank Transfer File
```

**Salary Components:**
- Basic Salary
- Position Allowance
- Transport Allowance
- BPJS (Health/Employment Insurance)
- Tax (PPh 21)

---

### 📊 CRM & Sales

```
1. Customer Management
   └─> Create Customers → Contact Persons → Credit Limits

2. Sales Quotation
   └─> Create Quote → Product Selection → Pricing → Validity Period

3. Sales Order (SO)
   └─> Convert Quote → Order Confirmation → Delivery Scheduling

4. Invoicing
   └─> Create Invoice → Payment Tracking → Credit Notes
```

**Customer Types:** Retail, Wholesale, Distributor, Online

---

### 📁 Project Management

```
1. Project Setup
   └─> Create Project → Define Scope → Set Budget → Timeline

2. Task Management
   └─> Create Tasks → Assign Members → Set Deadlines

3. Time Tracking
   └─> Log Hours → Track Progress → Compare Budget

4. Project Closure
   └─> Final Report → Lessons Learned → Archive
```

**Project Statuses:** Planning → Active → On Hold → Completed → Cancelled

---

### 🚚 Logistics & Delivery

```
1. Delivery Order
   └─> Create from SO → Pick Items → Pack → Ship

2. Shipment Tracking
   └─> Assign Carrier → Track Status → Proof of Delivery

3. Returns Processing
   └─> Receive Return → QC Check → Restock/Dispose
```

**Delivery Statuses:** Pending → In Transit → Delivered → Returned

---

### 🔧 Maintenance Management

```
1. Asset Setup
   └─> Register Equipment → Assign Location → Set Maintenance Schedule

2. Preventive Maintenance (PM)
   └─> Schedule PM → Create Work Order → Execute → Record Results

3. Corrective Maintenance (CM)
   └─> Report Issue → Diagnose → Repair → Close Ticket

4. Spare Parts
   └─> Track Parts Usage → Reorder Point → Stock Replenishment
```

**Work Order Types:** Preventive, Corrective, Predictive, Emergency

---

### 🌐 B2B Portal

```
1. Catalog Browsing
   └─> View Products → Check Prices → Availability

2. Order Placement
   └─> Add to Cart → Checkout → SO Created → Confirmation

3. Order Tracking
   └─> View Order Status → Delivery Updates → Invoice Download
```

---

### 🛒 Point of Sale (POS)

```
1. Product Display
   └─> Browse Products → Filter by Category → View Stock Qty

2. Customer Management
   └─> Quick Search → Create New → KTP Image Upload → Credit Top-up

3. Transaction Flow
   └─> Add Items to Cart → Apply Promo → Select Payment → Complete Sale

4. Payment Methods
   └─> Cash / Credit Card / Customer Credit / QRIS / Transfer
```

**POS Features:**
- Multi-tenant isolated transactions
- Customer credit system with balance tracking
- Promo/discount code application
- Product stock validation
- Transaction history and receipts
- Cloudinary for KTP image storage

**API Endpoints:** `/pos/*`
- `GET /pos/products` - Get products for POS display
- `POST /pos/customers` - Create customer with KTP upload
- `POST /pos/customers/{id}/topup` - Add credit to customer
- `POST /pos/transactions` - Create new transaction
- `GET /pos/transactions` - List transactions

---

## 🔧 Development

### Backend (Go Microservices)
Each microservice is built separately using Docker:
```bash
# Rebuild a specific service
docker compose up -d --build crm-service

# Rebuild all services
docker compose up -d --build
```

### Frontend Changes
Restart container after changes:
```bash
docker compose restart frontend_web
```

### Database
Using Supabase PostgreSQL. Migrations managed via GORM AutoMigrate.

## 🔮 Roadmap

- [x] Phase 1: Go Microservices Migration (25+ services)
- [x] Phase 2: CRM Module Complete Overhaul
- [ ] Phase 3: Enhanced Manufacturing (MRP, Work Orders)
- [ ] Phase 4: Advanced Inventory (Batch/Serial Tracking)
- [ ] Phase 5: Financial Reporting
- [ ] Phase 6: Mobile App
- [ ] Phase 7: AI-Powered Analytics

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ using **Go + Gin**, **Nuxt 3**, and **Docker** | Gumroad-inspired design 🎀
