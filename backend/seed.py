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
    
    # Define all default users with their roles
    default_users = [
        {"username": "admin", "email": "admin@minierp.com", "role": models.UserRole.ADMIN},
        {"username": "manager", "email": "manager@minierp.com", "role": models.UserRole.MANAGER},
        {"username": "production", "email": "production@minierp.com", "role": models.UserRole.PRODUCTION},
        {"username": "warehouse", "email": "warehouse@minierp.com", "role": models.UserRole.WAREHOUSE},
        {"username": "staff", "email": "staff@minierp.com", "role": models.UserRole.STAFF},
        {"username": "procurement", "email": "procurement@minierp.com", "role": models.UserRole.PROCUREMENT},
        {"username": "finance", "email": "finance@minierp.com", "role": models.UserRole.FINANCE},
        {"username": "hr", "email": "hr@minierp.com", "role": models.UserRole.HR},
        {"username": "lab_tech", "email": "labtech@minierp.com", "role": models.UserRole.LAB_TECH},
    ]
    
    for user_data in default_users:
        result = await db.execute(select(models.User).where(models.User.email == user_data["email"]))
        if not result.scalar_one_or_none():
            user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=pwd_context.hash(f"{user_data['username']}123"),  # password = username + 123
                role=user_data["role"],
                is_verified=True  # Auto-verify seed users
            )
            db.add(user)
            logger.info(f"Created user: {user_data['username']} ({user_data['role'].value})")
    
    await db.commit()

async def seed_manufacturing(db):
    logger.info("Seeding Manufacturing...")
    # Work Center
    wc_res = await db.execute(select(models.WorkCenter).where(models.WorkCenter.name == "Assembly Line 1"))
    wc = wc_res.scalar_one_or_none()
    if not wc:
        wc = models.WorkCenter(code="WC-001", name="Assembly Line 1", capacity_per_hour=100, hourly_rate=25.0)
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

async def seed_menus(db):
    """Seed default menu items"""
    logger.info("Seeding Menus...")
    
    # Check if menus already exist
    result = await db.execute(select(models.Menu).limit(1))
    if result.scalar_one_or_none():
        logger.info("Menus already seeded, skipping...")
        return
    
    # Define all menus with parent-child relationships
    menus_data = [
        # Main menus (no parent)
        {"code": "dashboard", "label": "Dashboard", "icon": "i-heroicons-home", "path": "/", "sort_order": 1},
        {"code": "manufacturing", "label": "Manufacturing", "icon": "i-heroicons-wrench-screwdriver", "path": None, "sort_order": 2},
        {"code": "inventory", "label": "Inventory", "icon": "i-heroicons-cube", "path": None, "sort_order": 3},
        {"code": "procurement", "label": "Procurement", "icon": "i-heroicons-shopping-cart", "path": None, "sort_order": 4},
        {"code": "logistics", "label": "Logistics", "icon": "i-heroicons-truck", "path": None, "sort_order": 5},
        {"code": "crm", "label": "CRM & Sales", "icon": "i-heroicons-users", "path": None, "sort_order": 6},
        {"code": "projects", "label": "Projects", "icon": "i-heroicons-clipboard-document-list", "path": "/projects", "sort_order": 7},
        {"code": "maintenance", "label": "Maintenance", "icon": "i-heroicons-cog-8-tooth", "path": None, "sort_order": 8},
        {"code": "hr", "label": "HR & Payroll", "icon": "i-heroicons-user-group", "path": None, "sort_order": 9},
        {"code": "finance", "label": "Finance", "icon": "i-heroicons-banknotes", "path": None, "sort_order": 10},
        {"code": "portal", "label": "B2B Portal", "icon": "i-heroicons-building-storefront", "path": "/portal/shop", "sort_order": 11},
        {"code": "compliance", "label": "Compliance", "icon": "i-heroicons-shield-check", "path": "/compliance", "sort_order": 12},
        {"code": "config", "label": "Setup", "icon": "i-heroicons-cog-6-tooth", "path": "/setup", "sort_order": 99},
    ]
    
    # Create parent menus first
    menu_map = {}
    for menu_data in menus_data:
        menu = models.Menu(**menu_data)
        db.add(menu)
        await db.flush()
        menu_map[menu_data["code"]] = menu.id
    
    # Define child menus
    children_data = [
        # Manufacturing children
        {"code": "manufacturing.work-centers", "label": "Work Centers", "path": "/manufacturing/work-centers", "parent_code": "manufacturing", "sort_order": 1},
        {"code": "manufacturing.products", "label": "Products & BOM", "path": "/manufacturing/products", "parent_code": "manufacturing", "sort_order": 2},
        {"code": "manufacturing.production", "label": "Production", "path": "/manufacturing/production", "parent_code": "manufacturing", "sort_order": 3},
        # Inventory children
        {"code": "inventory.stock", "label": "Stock Status", "path": "/inventory/stock", "parent_code": "inventory", "sort_order": 1},
        {"code": "inventory.warehouses", "label": "Warehouses", "path": "/inventory/warehouses", "parent_code": "inventory", "sort_order": 2},
        {"code": "inventory.movements", "label": "Movements", "path": "/inventory/movements", "parent_code": "inventory", "sort_order": 3},
        {"code": "inventory.receiving", "label": "Goods Receipt", "path": "/inventory/receiving", "parent_code": "inventory", "sort_order": 4},
        {"code": "inventory.opname", "label": "Opname", "path": "/inventory/opname", "parent_code": "inventory", "sort_order": 5},
        # Procurement children
        {"code": "procurement.requests", "label": "Purchase Requests", "path": "/procurement/requests", "parent_code": "procurement", "sort_order": 1},
        {"code": "procurement.orders", "label": "Purchase Orders", "path": "/procurement/orders", "parent_code": "procurement", "sort_order": 2},
        {"code": "procurement.vendors", "label": "Vendors", "path": "/procurement/vendors", "parent_code": "procurement", "sort_order": 3},
        # Finance children
        {"code": "finance.coa", "label": "Chart of Accounts", "path": "/finance/coa", "parent_code": "finance", "sort_order": 1},
        {"code": "finance.gl", "label": "General Ledger", "path": "/finance/gl", "parent_code": "finance", "sort_order": 2},
        {"code": "finance.reports", "label": "Reports", "path": "/finance/reports", "parent_code": "finance", "sort_order": 3},
        {"code": "finance.assets", "label": "Fixed Assets", "path": "/finance/assets", "parent_code": "finance", "sort_order": 4},
        # HR children
        {"code": "hr.dashboard", "label": "Dashboard", "path": "/hr", "parent_code": "hr", "sort_order": 1},
        {"code": "hr.employees", "label": "Employees", "path": "/hr/employees", "parent_code": "hr", "sort_order": 2},
        {"code": "hr.organization", "label": "Organization", "path": "/hr/organization", "parent_code": "hr", "sort_order": 3},
        {"code": "hr.attendance", "label": "Attendance", "path": "/hr/attendance", "parent_code": "hr", "sort_order": 4},
        {"code": "hr.leave", "label": "Leave", "path": "/hr/leave", "parent_code": "hr", "sort_order": 5},
        {"code": "hr.leaderboards", "label": "Leaderboards", "path": "/hr/leaderboards", "parent_code": "hr", "sort_order": 6},
        {"code": "hr.payroll", "label": "Payroll", "path": "/hr/payroll", "parent_code": "hr", "sort_order": 7},
        # Logistics children
        {"code": "logistics.delivery", "label": "Delivery Orders", "path": "/logistics/delivery", "parent_code": "logistics", "sort_order": 1},
        {"code": "logistics.transfers", "label": "Stock Transfers", "path": "/logistics/transfers", "parent_code": "logistics", "sort_order": 2},
        {"code": "logistics.picking", "label": "Stock Picking", "path": "/logistics/picking", "parent_code": "logistics", "sort_order": 3},
        {"code": "logistics.shipments", "label": "Shipments", "path": "/logistics/shipments", "parent_code": "logistics", "sort_order": 4},
        {"code": "logistics.returns", "label": "Returns", "path": "/logistics/returns", "parent_code": "logistics", "sort_order": 5},
        {"code": "logistics.couriers", "label": "Couriers", "path": "/logistics/couriers", "parent_code": "logistics", "sort_order": 6},
        # CRM children
        {"code": "crm.leads", "label": "Leads", "path": "/crm/leads", "parent_code": "crm", "sort_order": 1},
        {"code": "crm.opportunities", "label": "Opportunities", "path": "/crm/opportunities", "parent_code": "crm", "sort_order": 2},
        {"code": "crm.customers", "label": "Customers", "path": "/crm/customers", "parent_code": "crm", "sort_order": 3},
        {"code": "crm.activities", "label": "Activities", "path": "/crm/activities", "parent_code": "crm", "sort_order": 4},
        {"code": "crm.pipeline", "label": "Pipeline", "path": "/crm/pipeline", "parent_code": "crm", "sort_order": 5},
        {"code": "crm.orders", "label": "Sales Orders", "path": "/crm/orders", "parent_code": "crm", "sort_order": 6},
        {"code": "crm.promos", "label": "Promo Management", "path": "/crm/promos", "parent_code": "crm", "sort_order": 7},
        # Projects children
        {"code": "projects.all", "label": "All Projects", "path": "/projects", "parent_code": "projects", "sort_order": 1},
        # Maintenance children
        {"code": "maintenance.assets", "label": "Assets", "path": "/maintenance/assets", "parent_code": "maintenance", "sort_order": 1},
        {"code": "maintenance.work-orders", "label": "Work Orders", "path": "/maintenance/work-orders", "parent_code": "maintenance", "sort_order": 2},
        {"code": "maintenance.schedules", "label": "Schedules", "path": "/maintenance/schedules", "parent_code": "maintenance", "sort_order": 3},
        # Portal children
        {"code": "portal.shop", "label": "Browse Catalog", "path": "/portal/shop", "parent_code": "portal", "sort_order": 1},
    ]
    
    for child_data in children_data:
        parent_code = child_data.pop("parent_code")
        child_data["parent_id"] = menu_map.get(parent_code)
        child_menu = models.Menu(**child_data)
        db.add(child_menu)
    
    await db.commit()
    logger.info(f"Created {len(menus_data) + len(children_data)} menu items")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        await seed_users(db)
        await seed_menus(db)
        await seed_manufacturing(db)
        await seed_inventory(db)
        await seed_procurement(db)
        await seed_finance(db)
        await seed_customers(db)
    
    logger.info("Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(main())
