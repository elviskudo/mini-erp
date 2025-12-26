"""
Script to grant permissions for Inventory menu items to all roles
Run with: docker compose exec backend_api python grant_inventory_permissions.py
"""

import asyncio
import logging
from sqlalchemy import select
from database import engine, Base, SessionLocal
import models
from models.models_menu import Menu, RoleMenuPermission
from models.models_saas import Tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def grant_inventory_permissions():
    """Grant permissions for all Inventory menu items to existing tenants"""
    
    async with SessionLocal() as db:
        # Get all inventory-related menus
        result = await db.execute(
            select(Menu).where(Menu.code.like("inventory%"))
        )
        inventory_menus = result.scalars().all()
        
        if not inventory_menus:
            logger.error("No Inventory menus found!")
            return
        
        logger.info(f"Found {len(inventory_menus)} Inventory menu items")
        
        # Get all tenants
        tenant_result = await db.execute(select(Tenant))
        tenants = tenant_result.scalars().all()
        
        if not tenants:
            logger.warning("No tenants found - skipping permissions")
            return
        
        logger.info(f"Found {len(tenants)} tenants")
        
        # All roles that should have access
        roles = ['ADMIN', 'MANAGER', 'WAREHOUSE', 'STAFF', 'PRODUCTION']
        
        permissions_created = 0
        
        for tenant in tenants:
            for role in roles:
                for menu in inventory_menus:
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
                        permissions_created += 1
        
        await db.commit()
        logger.info(f"✅ Created {permissions_created} new permissions")

if __name__ == "__main__":
    asyncio.run(grant_inventory_permissions())
