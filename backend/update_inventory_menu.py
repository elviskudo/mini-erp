"""
Script to update Inventory menu structure in database
Run with: docker compose exec backend_api python update_inventory_menu.py
"""

import asyncio
import logging
from sqlalchemy import select, delete, update
from database import engine, Base, SessionLocal
import models
from models.models_menu import Menu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_inventory_menu():
    """Update Inventory menu with new structure"""
    
    async with SessionLocal() as db:
        # Get the Inventory parent menu
        result = await db.execute(
            select(Menu).where(Menu.code == "inventory")
        )
        inventory_menu = result.scalar_one_or_none()
        
        if not inventory_menu:
            logger.error("Inventory menu not found! Run seed.py first.")
            return
        
        logger.info(f"Found Inventory menu: {inventory_menu.id}")
        
        # Delete all existing Inventory children
        await db.execute(
            delete(Menu).where(Menu.parent_id == inventory_menu.id)
        )
        await db.commit()
        logger.info("Deleted existing Inventory children")
        
        # Define new children with correct order
        new_children = [
            {"code": "inventory.warehouses", "label": "Warehouses", "path": "/inventory/warehouses", "sort_order": 1},
            {"code": "inventory.stock", "label": "Stock Status", "path": "/inventory/stock", "sort_order": 2},
            {"code": "inventory.receiving", "label": "Goods Receipt", "path": "/inventory/receiving", "sort_order": 3},
            {"code": "inventory.movements", "label": "Movements", "path": "/inventory/movements", "sort_order": 4},
            {"code": "inventory.reports", "label": "Reports", "path": "/inventory/overhead", "sort_order": 5},
            {"code": "inventory.opname", "label": "Stock Opname", "path": "/inventory/opname", "sort_order": 6},
        ]
        
        # Create main inventory children
        opname_menu_id = None
        for child_data in new_children:
            menu = Menu(
                code=child_data["code"],
                label=child_data["label"],
                path=child_data["path"],
                parent_id=inventory_menu.id,
                sort_order=child_data["sort_order"],
                is_active=True
            )
            db.add(menu)
            await db.flush()
            
            if child_data["code"] == "inventory.opname":
                opname_menu_id = menu.id
            
            logger.info(f"Created: {child_data['label']}")
        
        # Create Stock Opname children
        if opname_menu_id:
            opname_children = [
                {"code": "inventory.opname.schedule", "label": "Schedule", "path": "/inventory/opname/schedule", "sort_order": 1},
                {"code": "inventory.opname.counting", "label": "Counting", "path": "/inventory/opname/counting", "sort_order": 2},
                {"code": "inventory.opname.matching", "label": "Matching", "path": "/inventory/opname/matching", "sort_order": 3},
                {"code": "inventory.opname.adjustment", "label": "Adjustment", "path": "/inventory/opname/adjustment", "sort_order": 4},
            ]
            
            for child_data in opname_children:
                menu = Menu(
                    code=child_data["code"],
                    label=child_data["label"],
                    path=child_data["path"],
                    parent_id=opname_menu_id,
                    sort_order=child_data["sort_order"],
                    is_active=True
                )
                db.add(menu)
                logger.info(f"Created Stock Opname child: {child_data['label']}")
        
        await db.commit()
        logger.info("✅ Inventory menu updated successfully!")

if __name__ == "__main__":
    asyncio.run(update_inventory_menu())
