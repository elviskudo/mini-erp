"""
Menu API Router - Serves menus based on role_menu_permissions table
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

import database
from auth import get_current_user
import models
from models.models_menu import Menu, RoleMenuPermission

router = APIRouter(prefix="/menus", tags=["menus"])


class MenuChild(BaseModel):
    label: str
    to: Optional[str] = None
    children: Optional[List["MenuChild"]] = None
    
    class Config:
        from_attributes = True

# Update forward references for recursive type
MenuChild.model_rebuild()


class MenuResponse(BaseModel):
    label: str
    icon: Optional[str] = None
    to: Optional[str] = None
    children: Optional[List[MenuChild]] = None
    
    class Config:
        from_attributes = True


def get_hardcoded_menus(user_role: str) -> list:
    """
    Return hardcoded menu structure when no permissions in database.
    Provides fallback for fresh installations.
    """
    all_menus = [
        {"label": "Dashboard", "icon": "i-heroicons-home", "to": "/"},
        {"label": "Analytics", "icon": "i-heroicons-chart-bar-square", "children": [
            {"label": "Production Dashboard", "to": "/dashboard/production"},
            {"label": "Failure Analysis", "to": "/dashboard/failures"}
        ]},
        {"label": "Procurement", "icon": "i-heroicons-shopping-cart", "children": [
            {"label": "Vendors", "to": "/procurement/vendors"},
            {"label": "Product Catalog", "to": "/procurement/products"},
            {"label": "Purchase Requests", "to": "/procurement/requests"},
            {"label": "RFQ", "to": "/procurement/rfq"},
            {"label": "Purchase Orders", "to": "/procurement/orders"},
            {"label": "Goods Receipt", "to": "/procurement/grn"},
            {"label": "Vendor Bills", "to": "/procurement/bills"},
            {"label": "Payments", "to": "/procurement/payments"},
            {"label": "Analytics", "to": "/procurement/analytics"}
        ]},
        {"label": "Manufacturing", "icon": "i-heroicons-wrench-screwdriver", "children": [
            {"label": "Work Centers", "to": "/manufacturing/work-centers"},
            {"label": "Products & BOM", "to": "/manufacturing/products"},
            {"label": "Routing", "to": "/manufacturing/routing"},
            {"label": "Production Orders", "to": "/manufacturing/production"},
            {"label": "Quality Control", "to": "/manufacturing/quality"}
        ]},
        {"label": "Inventory", "icon": "i-heroicons-cube", "children": [
            {"label": "Warehouses", "to": "/inventory/warehouses"},
            {"label": "Storage Zones", "to": "/inventory/storage-zones"},
            {"label": "Stock Status", "to": "/inventory/stock"},
            {"label": "Goods Receipt", "to": "/inventory/receiving"},
            {"label": "Movements", "to": "/inventory/movements"},
            {"label": "Overhead Report", "to": "/inventory/overhead"},
            {"label": "Stock Opname", "to": "/inventory/opname", "children": [
                {"label": "Schedule", "to": "/inventory/opname/schedule"},
                {"label": "Counting", "to": "/inventory/opname/counting"},
                {"label": "Matching", "to": "/inventory/opname/matching"},
                {"label": "Adjustment", "to": "/inventory/opname/adjustment"}
            ]}
        ]},
        {"label": "Logistics", "icon": "i-heroicons-truck", "to": "/logistics/delivery"},
        {"label": "Finance", "icon": "i-heroicons-banknotes", "children": [
            {"label": "Chart of Accounts", "to": "/finance/coa"},
            {"label": "General Ledger", "to": "/finance/gl"},
            {"label": "Reports", "to": "/finance/reports"},
            {"label": "Fixed Assets", "to": "/finance/assets"}
        ]},
        {"label": "HR & Payroll", "icon": "i-heroicons-user-group", "children": [
            {"label": "Employees", "to": "/hr/employees"},
            {"label": "Payroll Run", "to": "/hr/payroll"}
        ]},
        {"label": "CRM", "icon": "i-heroicons-users", "to": "/crm/orders"},
        {"label": "Projects", "icon": "i-heroicons-clipboard-document-list", "to": "/projects"},
        {"label": "Maintenance", "icon": "i-heroicons-cog-8-tooth", "to": "/maintenance"},
        {"label": "B2B Portal", "icon": "i-heroicons-building-storefront", "to": "/portal/shop"},
        {"label": "Compliance", "icon": "i-heroicons-shield-check", "to": "/compliance"},
        {"label": "Users", "icon": "i-heroicons-user-circle", "to": "/users"},
        {"label": "Config", "icon": "i-heroicons-cog-6-tooth", "to": "/setup"}
    ]
    
    # Admin / Manager see all
    if user_role in ['ADMIN', 'MANAGER']:
        return all_menus
    
    # Other roles - filter to allowed menus
    role_menu_map = {
        'PRODUCTION': ['Dashboard', 'Manufacturing', 'Users'],
        'WAREHOUSE': ['Dashboard', 'Inventory', 'Users'],
        'PROCUREMENT': ['Dashboard', 'Procurement', 'Users'],
        'FINANCE': ['Dashboard', 'Finance', 'Users'],
        'HR': ['Dashboard', 'HR & Payroll', 'Users'],
        'STAFF': ['Dashboard', 'Inventory', 'Manufacturing', 'Users'],
        'LAB_TECH': ['Dashboard', 'Quality Control', 'Manufacturing', 'Users'],
    }
    
    allowed_labels = role_menu_map.get(user_role, ['Dashboard'])
    return [m for m in all_menus if m['label'] in allowed_labels]


@router.get("", response_model=List[MenuResponse])
async def get_user_menus(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get menus accessible by the current user based on role_menu_permissions.
    
    Logic:
    - If user has no tenant_id (seed/demo user), show all menus
    - If tenant has permissions in role_menu_permissions, use them
    - If no permissions exist (new tenant), show only Config menu
    """
    user_role = current_user.role.value if current_user.role else 'STAFF'
    tenant_id = current_user.tenant_id
    
    # ADMIN always sees all menus - no restrictions
    if user_role == 'ADMIN':
        return get_hardcoded_menus(user_role)
    
    # If no tenant_id, use hardcoded fallback (demo/seed users)
    if not tenant_id:
        return get_hardcoded_menus(user_role)
    
    # Fetch permissions for this tenant and role
    result = await db.execute(
        select(RoleMenuPermission, Menu)
        .join(Menu, RoleMenuPermission.menu_id == Menu.id)
        .where(
            RoleMenuPermission.tenant_id == tenant_id,
            RoleMenuPermission.role == user_role,
            RoleMenuPermission.can_access == True,
            Menu.is_active == True
        )
        .order_by(Menu.sort_order)
    )
    permissions = result.all()
    
    # If no permissions exist, fallback to hardcoded menus
    # MANAGER should always see all menus even without DB permissions
    if not permissions:
        return get_hardcoded_menus(user_role)
    
    # Build a map of all menus by id
    all_menus_map = {}
    for perm, menu in permissions:
        all_menus_map[menu.id] = menu
    
    # Group menus by parent - handle 3 levels
    top_level_menus = []  # parent_id is None
    level_2_by_parent = {}  # parent is top-level
    level_3_by_parent = {}  # parent is level-2
    
    for perm, menu in permissions:
        if menu.parent_id is None:
            top_level_menus.append(menu)
        elif menu.parent_id in all_menus_map:
            parent = all_menus_map[menu.parent_id]
            if parent.parent_id is None:
                # This is a level-2 menu (child of top-level)
                if menu.parent_id not in level_2_by_parent:
                    level_2_by_parent[menu.parent_id] = []
                level_2_by_parent[menu.parent_id].append(menu)
            else:
                # This is a level-3 menu (grandchild)
                if menu.parent_id not in level_3_by_parent:
                    level_3_by_parent[menu.parent_id] = []
                level_3_by_parent[menu.parent_id].append(menu)
    
    # Sort by sort_order
    top_level_menus.sort(key=lambda x: x.sort_order)
    for key in level_2_by_parent:
        level_2_by_parent[key].sort(key=lambda x: x.sort_order)
    for key in level_3_by_parent:
        level_3_by_parent[key].sort(key=lambda x: x.sort_order)
    
    # Build menu response with 3 levels
    menus = []
    for menu in top_level_menus:
        menu_item = {
            "label": menu.label,
            "icon": menu.icon,
        }
        
        level2_children = level_2_by_parent.get(menu.id, [])
        if level2_children:
            children_list = []
            for child in level2_children:
                child_item = {"label": child.label, "to": child.path}
                
                # Check for level-3 children
                level3_children = level_3_by_parent.get(child.id, [])
                if level3_children:
                    child_item["children"] = [
                        {"label": gc.label, "to": gc.path}
                        for gc in level3_children
                    ]
                
                children_list.append(child_item)
            menu_item["children"] = children_list
        else:
            menu_item["to"] = menu.path
        
        menus.append(menu_item)
    
    return menus


@router.get("/all")
async def get_all_menus(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all menus (admin only) for menu management.
    """
    if current_user.role.value not in ['ADMIN', 'MANAGER']:
        raise HTTPException(status_code=403, detail="Admin/Manager access required")
    
    result = await db.execute(
        select(Menu)
        .order_by(Menu.sort_order)
    )
    return result.scalars().all()


# ============ Helper Functions for Permission Management ============

async def grant_config_menu_permission(db: AsyncSession, tenant_id: UUID, role: str):
    """
    Grant access to Config menu only. Called after owner registration.
    """
    # Get config menu
    result = await db.execute(
        select(Menu).where(Menu.code == "config")
    )
    config_menu = result.scalar_one_or_none()
    
    if not config_menu:
        # Create config menu if not exists
        config_menu = Menu(
            code="config",
            label="Config",
            icon="i-heroicons-cog-6-tooth",
            path="/setup",
            sort_order=100,
            is_active=True
        )
        db.add(config_menu)
        await db.flush()
    
    # Check if permission already exists
    existing = await db.execute(
        select(RoleMenuPermission).where(
            RoleMenuPermission.tenant_id == tenant_id,
            RoleMenuPermission.role == role,
            RoleMenuPermission.menu_id == config_menu.id
        )
    )
    if not existing.scalar_one_or_none():
        perm = RoleMenuPermission(
            tenant_id=tenant_id,
            role=role,
            menu_id=config_menu.id,
            can_access=True
        )
        db.add(perm)


async def grant_all_menu_permissions(db: AsyncSession, tenant_id: UUID, role: str):
    """
    Grant access to all menus. Called after setup is complete.
    """
    # Get all active menus
    result = await db.execute(
        select(Menu).where(Menu.is_active == True)
    )
    all_menus = result.scalars().all()
    
    for menu in all_menus:
        # Check if permission already exists
        existing = await db.execute(
            select(RoleMenuPermission).where(
                RoleMenuPermission.tenant_id == tenant_id,
                RoleMenuPermission.role == role,
                RoleMenuPermission.menu_id == menu.id
            )
        )
        if not existing.scalar_one_or_none():
            perm = RoleMenuPermission(
                tenant_id=tenant_id,
                role=role,
                menu_id=menu.id,
                can_access=True
            )
            db.add(perm)
