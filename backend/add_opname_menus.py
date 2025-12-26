"""
Script to add Stock Opname sub-menu items
Run with: docker compose exec backend_api python add_opname_menus.py
"""
import asyncio
from sqlalchemy import select, update
from database import engine, Base, SessionLocal
import models

async def add_opname_submenus():
    async with SessionLocal() as db:
        # Find the existing Opname menu
        result = await db.execute(
            select(models.Menu).where(models.Menu.code == "inventory.opname")
        )
        opname_menu = result.scalar_one_or_none()
        
        if not opname_menu:
            print("Opname menu not found. Creating parent menu...")
            # Find inventory menu
            inv_result = await db.execute(
                select(models.Menu).where(models.Menu.code == "inventory")
            )
            inventory_menu = inv_result.scalar_one_or_none()
            if not inventory_menu:
                print("Inventory menu not found!")
                return
            
            opname_menu = models.Menu(
                code="inventory.opname",
                label="Stock Opname",
                icon="i-heroicons-clipboard-document-check",
                path=None,  # Parent menu has no path
                parent_id=inventory_menu.id,
                sort_order=5
            )
            db.add(opname_menu)
            await db.flush()
        else:
            # Update existing menu to be a parent (no path, with icon)
            opname_menu.path = None
            opname_menu.icon = "i-heroicons-clipboard-document-check"
            opname_menu.label = "Stock Opname"
            await db.flush()
            print(f"Updated Opname menu (id: {opname_menu.id})")
        
        # Define sub-menus
        submenus = [
            {"code": "inventory.opname.dashboard", "label": "Dashboard", "path": "/inventory/opname", "sort_order": 1},
            {"code": "inventory.opname.schedule", "label": "Schedule", "path": "/inventory/opname/schedule", "sort_order": 2},
            {"code": "inventory.opname.counting", "label": "Counting", "path": "/inventory/opname/counting", "sort_order": 3},
            {"code": "inventory.opname.matching", "label": "Matching", "path": "/inventory/opname/matching", "sort_order": 4},
            {"code": "inventory.opname.adjustment", "label": "Adjustment", "path": "/inventory/opname/adjustment", "sort_order": 5},
            {"code": "inventory.opname.reports", "label": "Reports", "path": "/inventory/opname/reports", "sort_order": 6},
        ]
        
        for submenu_data in submenus:
            # Check if already exists
            check = await db.execute(
                select(models.Menu).where(models.Menu.code == submenu_data["code"])
            )
            if check.scalar_one_or_none():
                print(f"Menu {submenu_data['code']} already exists, skipping...")
                continue
            
            submenu = models.Menu(
                code=submenu_data["code"],
                label=submenu_data["label"],
                path=submenu_data["path"],
                parent_id=opname_menu.id,
                sort_order=submenu_data["sort_order"]
            )
            db.add(submenu)
            print(f"Created submenu: {submenu_data['label']}")
        
        await db.commit()
        print("Done! Stock Opname sub-menus added.")

if __name__ == "__main__":
    asyncio.run(add_opname_submenus())
