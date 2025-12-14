# Mini ERP System

A modern, full-stack ERP system built with efficiency and scalability in mind. Designed for small to medium manufacturing businesses with **complete multi-tenancy support**.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Nuxt](https://img.shields.io/badge/Nuxt.js-00DC82?style=flat&logo=nuxt.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

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
- **Projects** - Project management, task tracking
- **Maintenance** - Asset maintenance scheduling

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

### Backend
| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Framework | FastAPI (Async) |
| Database | PostgreSQL (Relational), MongoDB (Logs/IoT) |
| Queue | RabbitMQ |
| Cache | Redis |
| ORM | SQLAlchemy 2.0 (Async) |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Nuxt 3 (Vue.js 3) |
| Styling | TailwindCSS + Nuxt UI (Gumroad-inspired pink theme) |
| State | Pinia |
| HTTP Client | Axios |

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
| Frontend | http://localhost:3333 | - |
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
├── backend/
│   ├── routers/           # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── saas.py        # Multi-tenant onboarding
│   │   └── ...
│   ├── models/            # SQLAlchemy models
│   │   ├── base.py        # TenantMixin base class
│   │   ├── models_saas.py # Tenant, TenantMember
│   │   └── ...
│   ├── dependencies/      # FastAPI dependencies
│   │   └── tenant.py      # Iron Wall middleware
│   ├── services/          # Business logic
│   ├── connections/       # DB/Queue connections
│   └── main.py            # App entry point
├── frontend/
│   ├── pages/
│   │   └── auth/
│   │       ├── login.vue           # Gumroad-style login
│   │       ├── register-company.vue # 2-step company registration
│   │       ├── join-company.vue    # Employee join flow
│   │       └── verify.vue          # OTP verification
│   ├── stores/auth.ts     # Auth + tenant state
│   ├── plugins/api.ts     # Axios with X-Tenant-ID
│   └── tailwind.config.js # Pink theme
├── realtime/              # Socket.IO with tenant rooms
└── docker-compose.yml
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
| operator | operator@minierp.com | operator123 | Operator |

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

## 🔧 Development

### Backend Hot Reload
Backend auto-reloads on file changes via uvicorn.

### Frontend Changes
Restart container after changes:
```bash
docker compose restart frontend_web
```

### Database Migrations
```bash
docker compose exec backend_api alembic upgrade head
docker compose exec backend_api alembic revision --autogenerate -m "description"
```

## 🔮 Roadmap

- [ ] Phase 1: Enhanced Manufacturing (MRP, Work Orders)
- [ ] Phase 2: Advanced Inventory (Batch/Serial Tracking)
- [ ] Phase 3: Financial Reporting
- [ ] Phase 4: Mobile App
- [ ] Phase 5: AI-Powered Analytics

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ using FastAPI, Nuxt 3, and Docker | Gumroad-inspired design 🎀
