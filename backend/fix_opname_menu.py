"""
Fix Stock Opname menu structure - make children direct children of Inventory
Run with: docker compose exec backend_api python fix_opname_menu.py
"""
import asyncio
from sqlalchemy import select, delete
from database import SessionLocal
import models

async def fix_opname_menu():
    async with SessionLocal() as db:
        # 1. Find the Inventory parent menu
        inv_result = await db.execute(
            select(models.Menu).where(models.Menu.code == "inventory")
        )
        inventory_menu = inv_result.scalar_one_or_none()
        
        if not inventory_menu:
            print("Inventory menu not found!")
            return
        
        print(f"Found Inventory menu: {inventory_menu.id}")
        
        # 2. Find the inventory.opname menu
        opname_result = await db.execute(
            select(models.Menu).where(models.Menu.code == "inventory.opname")
        )
        opname_menu = opname_result.scalar_one_or_none()
        
        if opname_menu:
            print(f"Found inventory.opname menu: {opname_menu.id}")
            
            # 3. Find all children of inventory.opname and move them to be children of inventory
            children_result = await db.execute(
                select(models.Menu).where(models.Menu.parent_id == opname_menu.id)
            )
            children = children_result.scalars().all()
            
            for child in children:
                # Update parent_id to point to inventory instead
                child.parent_id = inventory_menu.id
                print(f"Moved {child.code} to be child of inventory")
            
            # IMPORTANT: Flush the changes to update parent_id before deleting
            await db.flush()
            
            # 4. Now delete the intermediate inventory.opname menu 
            await db.execute(
                delete(models.Menu).where(models.Menu.id == opname_menu.id)
            )
            print("Deleted intermediate inventory.opname menu")
        else:
            print("inventory.opname not found - checking direct children")
        
        # 5. Rename the dashboard to be "Stock Opname"
        dashboard_result = await db.execute(
            select(models.Menu).where(models.Menu.code == "inventory.opname.dashboard")
        )
        dashboard_menu = dashboard_result.scalar_one_or_none()
        if dashboard_menu:
            dashboard_menu.label = "Stock Opname"
            dashboard_menu.icon = "i-heroicons-clipboard-document-check"
            print("Updated dashboard label to 'Stock Opname'")
        
        await db.commit()
        print("Done! Refresh browser to see changes.")

if __name__ == "__main__":
    asyncio.run(fix_opname_menu())
