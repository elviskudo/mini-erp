"""
Grant permissions for Stock Opname menus to all roles
Run with: docker compose exec backend_api python grant_opname_permissions.py
"""
import asyncio
from sqlalchemy import select
from database import SessionLocal
import models
from models.models_menu import Menu, RoleMenuPermission

async def grant_permissions():
    async with SessionLocal() as db:
        # Find all opname-related menus
        result = await db.execute(
            select(Menu).where(Menu.code.like("inventory.opname%"))
        )
        opname_menus = result.scalars().all()
        
        if not opname_menus:
            print("No opname menus found!")
            return
        
        print(f"Found {len(opname_menus)} opname menus")
        
        # Find all tenants
        tenant_result = await db.execute(select(models.Tenant))
        tenants = tenant_result.scalars().all()
        
        # Define roles that should have access
        roles = ['ADMIN', 'MANAGER', 'WAREHOUSE', 'STAFF']
        
        for tenant in tenants:
            print(f"Processing tenant: {tenant.id}")
            for role in roles:
                for menu in opname_menus:
                    # Check if permission already exists
                    existing = await db.execute(
                        select(RoleMenuPermission).where(
                            RoleMenuPermission.tenant_id == tenant.id,
                            RoleMenuPermission.role == role,
                            RoleMenuPermission.menu_id == menu.id
                        )
                    )
                    if not existing.scalar_one_or_none():
                        perm = RoleMenuPermission(
                            tenant_id=tenant.id,
                            role=role,
                            menu_id=menu.id,
                            can_access=True
                        )
                        db.add(perm)
                        print(f"  Granted {menu.label} to {role}")
        
        await db.commit()
        print("Done! Permissions granted.")

if __name__ == "__main__":
    asyncio.run(grant_permissions())
