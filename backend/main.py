from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import (
    auth, manufacturing, iot, mrp, qc, inventory, 
    procurement, receiving, issuance, opname, delivery, logistics,
    finance, hr, crm, projects, maintenance, fleet, ecommerce, compliance,
    ap, ar, sales, subscription, upload, tenants, saas, menu, users, dashboard, export, settings,
    pos, config
)

from middleware import AuditMiddleware
from connections.mongodb import connect_to_mongo, close_mongo_connection
from connections.kafka_utils import get_kafka_producer, close_kafka_producer
from consumers.finance_consumer import start_finance_consumer
import asyncio
from connections.worker import consume_lab_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Initialize Kafka producer (connection pooling)
    await get_kafka_producer()
    
    # Start Worker (Simple background task for Phase 1)
    # In production, this should be a separate service.
    worker_task = asyncio.create_task(consume_lab_data())
    asyncio.create_task(start_finance_consumer())
    
    yield
    
    # Cleanup
    await close_mongo_connection()
    await close_kafka_producer()

app = FastAPI(title="Mini ERP API", version="1.0.0", lifespan=lifespan)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth.router)
app.include_router(manufacturing.router)
app.include_router(iot.router)
app.include_router(mrp.router)
app.include_router(qc.router)
app.include_router(inventory.router)
app.include_router(procurement.router)
app.include_router(receiving.router)
app.include_router(issuance.router)
app.include_router(opname.router)
app.include_router(delivery.router)
app.include_router(logistics.router)
app.include_router(finance.router)
app.include_router(ap.router)
app.include_router(ar.router)
app.include_router(sales.router)
app.include_router(hr.router)
app.include_router(crm.router)
app.include_router(projects.router)
app.include_router(maintenance.router)
app.include_router(fleet.router)
app.include_router(ecommerce.router)
app.include_router(compliance.router)
app.include_router(subscription.router)
app.include_router(upload.router)
app.include_router(tenants.router)
app.include_router(saas.router)
app.include_router(menu.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(export.router)
app.include_router(settings.router)
app.include_router(pos.router)
app.include_router(config.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini ERP API"}

@app.get("/health")
async def health_check():
    import redis as redis_lib
    from connections.mongodb import db as mongo_db
    import os
    import aio_pika
    
    status = {
        "postgres": "unknown",
        "mongo": "unknown",
        "redis": "unknown",
        "rabbitmq": "unknown"
    }
    
    # Check PostgreSQL (if we got this far, it's connected via lifespan)
    status["postgres"] = "connected"
    
    # Check MongoDB
    try:
        if mongo_db is not None:
            await mongo_db.command("ping")
            status["mongo"] = "connected"
        else:
            status["mongo"] = "not initialized"
    except Exception as e:
        status["mongo"] = f"error: {str(e)[:50]}"
    
    # Check Redis
    try:
        redis_host = os.getenv("REDIS_HOST", "redis_cache")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        r = redis_lib.Redis(host=redis_host, port=redis_port, socket_timeout=2)
        r.ping()
        status["redis"] = "connected"
    except Exception as e:
        status["redis"] = f"error: {str(e)[:50]}"
    
    # Check RabbitMQ using environment variable
    try:
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq_broker:5672/")
        conn = await aio_pika.connect_robust(rabbitmq_url, timeout=5)
        await conn.close()
        status["rabbitmq"] = "connected"
    except Exception as e:
        status["rabbitmq"] = f"error: {str(e)[:50]}"
    
    overall = "healthy" if all(s == "connected" for s in status.values()) else "degraded"
    
    return {
        "status": overall,
        "services": status
    }
    
    return {
        "status": overall,
        "services": status
    }
