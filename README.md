# Mini ERP System

A modern, full-stack ERP system built with efficiency and scalability in mind. Designed for small to medium manufacturing businesses with multi-tenancy support.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Nuxt](https://img.shields.io/badge/Nuxt.js-00DC82?style=flat&logo=nuxt.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

## ✨ Features

### Core Modules
- **Manufacturing** - Work centers, products, production orders
- **Inventory** - Stock management, warehouses, stock opname
- **Procurement** - Purchase requests, purchase orders, vendors
- **Receiving** - Goods receiving, quality checks
- **Quality Control** - Inspections, batch tracking
- **Finance** - Chart of accounts, general ledger, fixed assets
- **HR** - Employees, payroll management
- **CRM** - Customer management, sales orders
- **Projects** - Project management, task tracking
- **Maintenance** - Asset maintenance scheduling

### Authentication & Security
- JWT-based authentication
- Email OTP verification
- Multi-tenancy support
- Role-based access control (Admin, Operator, Manager, Lab Tech)

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
| Styling | TailwindCSS + Nuxt UI |
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

## 🔐 Authentication Flow

### Registration
1. User fills registration form with tenant selection
2. System generates 6-digit OTP (expires in 10 minutes)
3. OTP sent via email (or printed to console in dev mode)
4. User enters OTP on verification page
5. Account activated upon successful verification

### Login
1. User enters username/email and password
2. System validates credentials
3. Checks if email is verified
4. Returns JWT access token

### API Endpoints
```
POST /auth/register    - Register new user
POST /auth/token       - Login (OAuth2 form)
POST /auth/send-otp    - Resend OTP code
POST /auth/verify-otp  - Verify OTP and activate
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

# Alternative providers:
# Mailgun: smtp.mailgun.org:587
# SendGrid: smtp.sendgrid.net:587
# Mailtrap: sandbox.smtp.mailtrap.io:2525
```

> **Dev Mode**: If `SMTP_USER` is empty, OTP codes are printed to backend console.

## 🏢 Multi-Tenancy

Each user belongs to a tenant (organization). Tenants are created during registration:

```
POST /tenants/         - Create new tenant
GET  /tenants/         - List all tenants
GET  /tenants/{id}     - Get tenant details
```

## 📁 Project Structure

```
mini-erp/
├── backend/
│   ├── routers/        # API endpoints
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── connections/    # DB/Queue connections
│   └── main.py         # App entry point
├── frontend/
│   ├── pages/          # Nuxt pages
│   ├── layouts/        # App layouts
│   ├── stores/         # Pinia stores
│   ├── middleware/     # Route guards
│   └── plugins/        # Axios, etc.
├── realtime/           # Socket.io server
└── docker-compose.yml
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

### Frontend HMR
Frontend has Hot Module Replacement disabled in Docker. Restart container after changes:
```bash
docker compose restart frontend_web
```

### Database Migrations
```bash
docker compose exec backend_api alembic upgrade head
docker compose exec backend_api alembic revision --autogenerate -m "description"
```

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ using FastAPI, Nuxt 3, and Docker
