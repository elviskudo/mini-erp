# Mini ERP System

A modern, full-stack ERP system built with efficiency and scalability in mind.

## Tech Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI (Async)
- **Database**: 
  - PostgreSQL (Relational Data: Users, Inventory, Manufacturing)
  - MongoDB (Logs, IoT Data)
- **Queue**: RabbitMQ
- **Cache**: Redis

### Frontend
- **Framework**: Nuxt 3 (Vue.js)
- **Styling**: TailwindCSS + Nuxt UI
- **State Management**: Pinia

## Setup & Running

### Prerequisites
- Docker & Docker Compose

### Running the Application

1. **Clone the repository**
2. **Setup Environment**
   ```bash
   cp .env.example .env
   # Adjust credentials in .env if needed
   ```
3. **Start Services**
   ```bash
   docker compose up --build -d
   ```

## Development

- **Backend API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **RabbitMQ**: http://localhost:15672 (guest/guest)

## Phase Status
- [x] Phase 0: Infrastructure
- [x] Phase 1: Manufacturing
- [x] Phase 2: Supply Chain
- [ ] Phase 3: Finance (In Progress)
