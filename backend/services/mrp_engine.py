from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import BillOfMaterial, Product, ProductType, MRPRun, MaterialRequirement, MRPActionType
import uuid
from datetime import datetime

class MRPEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_bom(self, product_id: uuid.UUID):
        """Fetch the active BOM for a product."""
        query = select(BillOfMaterial).where(
            BillOfMaterial.product_id == product_id,
            BillOfMaterial.is_active == True
        ).options(selectinload(BillOfMaterial.items).selectinload("component"))
        result = await self.db.execute(query)
        # Assuming one active BOM per product for now
        return result.scalars().first()

    async def explode_bom(self, product_id: uuid.UUID, qty: float, requirements_list: list, level: int = 0):
        """Recursive function to determine material needs."""
        # 1. Check if product has a BOM (Main Assembly or Sub-Assembly)
        bom = await self.get_active_bom(product_id)

        # 2. Get Product Info to check type
        p_query = select(Product).where(Product.id == product_id)
        p_result = await self.db.execute(p_query)
        product = p_result.scalar_one_or_none()

        action = MRPActionType.MAKE
        if product and product.type == ProductType.RAW_MATERIAL:
            action = MRPActionType.BUY
        
        # 3. Add Requirement record
        req = {
            "product_id": product_id,
            "required_qty": qty,
            "action_type": action,
            "level": level
        }
        requirements_list.append(req)

        # 4. If it has a BOM, explode further
        if bom:
            for item in bom.items:
                # Calculate required component qty including waste
                waste_factor = 1 + (item.waste_percentage / 100)
                component_qty = qty * item.quantity * waste_factor
                
                await self.explode_bom(item.component_id, component_qty, requirements_list, level + 1)

    async def run_mrp(self, target_product_id: uuid.UUID, target_qty: float):
        """Orchestrate the MRP calculation."""
        # Create MRP Run Record
        mrp_run = MRPRun(status="Running", notes=f"Auto-generated for Product {target_product_id}")
        self.db.add(mrp_run)
        await self.db.flush()

        requirements_data = []
        
        # Start Explosion
        await self.explode_bom(target_product_id, target_qty, requirements_data)

        # Save Requirements to DB
        # TODO: In real logic, we would aggregate same items and subtract inventory here.
        # For Phase 1, we list gross requirements.
        for data in requirements_data:
            requirement = MaterialRequirement(
                mrp_run_id=mrp_run.id,
                product_id=data["product_id"],
                required_qty=data["required_qty"],
                action_type=data["action_type"],
                source=f"Explosion Level {data['level']}"
            )
            self.db.add(requirement)

        mrp_run.status = "Completed"
        await self.db.commit()
        return mrp_run
