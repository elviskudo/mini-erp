import asyncio
import logging
from sqlalchemy import select
from database import engine, Base, SessionLocal
import models
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_users(db):
    logger.info("Seeding Users...")
    result = await db.execute(select(models.User).where(models.User.email == "admin@minierp.com"))
    if not result.scalar_one_or_none():
        admin = models.User(
            username="admin",
            email="admin@minierp.com",
            password_hash=pwd_context.hash("admin123"),
            role=models.UserRole.ADMIN
        )
        db.add(admin)
        
    result = await db.execute(select(models.User).where(models.User.email == "operator@minierp.com"))
    if not result.scalar_one_or_none():
        operator = models.User(
            username="operator",
            email="operator@minierp.com",
            password_hash=pwd_context.hash("operator123"),
            role=models.UserRole.OPERATOR
        )
        db.add(operator)
    await db.commit()

async def seed_manufacturing(db):
    logger.info("Seeding Manufacturing...")
    # Work Center
    wc_res = await db.execute(select(models.WorkCenter).where(models.WorkCenter.name == "Assembly Line 1"))
    wc = wc_res.scalar_one_or_none()
    if not wc:
        wc = models.WorkCenter(name="Assembly Line 1", location="Factory Floor A", capacity_per_hour=100)
        db.add(wc)
        await db.commit()
    
    # Products
    raw_material_res = await db.execute(select(models.Product).where(models.Product.name == "Steel Sheet"))
    rm = raw_material_res.scalar_one_or_none()
    if not rm:
        rm = models.Product(name="Steel Sheet", sku="RM-STEEL-001", type="Raw Material", unit="Sheet", cost_price=50.0)
        db.add(rm)
        await db.commit()
        await db.refresh(rm)
        
    finished_good_res = await db.execute(select(models.Product).where(models.Product.name == "Metal Box"))
    fg = finished_good_res.scalar_one_or_none()
    if not fg:
        fg = models.Product(name="Metal Box", sku="FG-BOX-001", type="Finished Good", unit="Pcs", sales_price=150.0)
        db.add(fg)
        await db.commit()
        await db.refresh(fg)

    # BOM
    bom_res = await db.execute(select(models.BOM).where(models.BOM.product_id == fg.id))
    if not bom_res.scalar_one_or_none():
        bom = models.BOM(product_id=fg.id, name="Standard Box BOM", version="1.0")
        db.add(bom)
        await db.flush()
        
        bom_item = models.BOMItem(bom_id=bom.id, component_id=rm.id, quantity=2.0)
        db.add(bom_item)
        await db.commit()

async def seed_inventory(db):
    logger.info("Seeding Inventory...")
    wh_res = await db.execute(select(models.Warehouse).where(models.Warehouse.name == "Main Warehouse"))
    wh = wh_res.scalar_one_or_none()
    if not wh:
        wh = models.Warehouse(name="Main Warehouse", location="Building A")
        db.add(wh)
        await db.commit()
        await db.refresh(wh)
        
        loc1 = models.Location(warehouse_id=wh.id, code="A-1-1", type="Storage")
        loc2 = models.Location(warehouse_id=wh.id, code="IN-DOCK", type="Receiving")
        db.add(loc1)
        db.add(loc2)
        await db.commit()

async def seed_procurement(db):
    logger.info("Seeding Procurement...")
    vendor_res = await db.execute(select(models.Vendor).where(models.Vendor.name == "Steel Supplier Inc"))
    if not vendor_res.scalar_one_or_none():
        vendor = models.Vendor(name="Steel Supplier Inc", email="sales@steelsupplier.com", payment_terms="Net 30")
        db.add(vendor)
        await db.commit()

async def seed_finance(db):
    logger.info("Seeding Finance...")
    # Simple COA check
    result = await db.execute(select(models.ChartOfAccount).limit(1))
    if not result.scalar_one_or_none():
        # Only seed if empty, use the router logic ideally but let's do minimal here
        assets = models.ChartOfAccount(code="1000", name="ASSETS", type="Asset")
        db.add(assets)
        await db.flush()
        
        cash = models.ChartOfAccount(code="1110", name="Cash", type="Asset", parent_id=assets.id)
        inventory = models.ChartOfAccount(code="1130", name="Inventory", type="Asset", parent_id=assets.id)
        ar = models.ChartOfAccount(code="1120", name="Accounts Receivable", type="Asset", parent_id=assets.id)
        db.add_all([cash, inventory, ar])
        
        liab = models.ChartOfAccount(code="2000", name="LIABILITIES", type="Liability")
        db.add(liab)
        await db.flush()
        ap = models.ChartOfAccount(code="2100", name="Accounts Payable", type="Liability", parent_id=liab.id)
        db.add(ap)
        
        income = models.ChartOfAccount(code="4000", name="REVENUE", type="Income")
        db.add(income)
        await db.flush()
        sales = models.ChartOfAccount(code="4100", name="Sales", type="Income", parent_id=income.id)
        db.add(sales)
        
        expense = models.ChartOfAccount(code="5000", name="EXPENSES", type="Expense")
        db.add(expense)
        await db.flush()
        cogs = models.ChartOfAccount(code="5100", name="COGS", type="Expense", parent_id=expense.id)
        db.add(cogs)
        
        await db.commit()

    # Fiscal Period
    fp_res = await db.execute(select(models.FiscalPeriod).where(models.FiscalPeriod.name == "2025-01"))
    if not fp_res.scalar_one_or_none():
        fp = models.FiscalPeriod(
            name="2025-01", 
            start_date=datetime(2025, 1, 1), 
            end_date=datetime(2025, 1, 31)
        )
        db.add(fp)
        await db.commit()

async def seed_customers(db):
    logger.info("Seeding Customers...")
    cust_res = await db.execute(select(models.Customer).where(models.Customer.name == "Loyal Client Ltd"))
    if not cust_res.scalar_one_or_none():
        cust = models.Customer(
            name="Loyal Client Ltd", 
            email="contact@loyalclient.com", 
            credit_limit=10000.0
        )
        db.add(cust)
        await db.commit()

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        await seed_users(db)
        await seed_manufacturing(db)
        await seed_inventory(db)
        await seed_procurement(db)
        await seed_finance(db)
        await seed_customers(db)
    
    logger.info("Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(main())
