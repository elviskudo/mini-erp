"""
HPP (Harga Pokok Produksi) / COGM (Cost of Goods Manufactured) Service

This service calculates the Cost of Goods Manufactured for production orders,
including Material Cost, Direct Labor, and Factory Overhead.
"""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import models


async def calculate_hpp(
    db: AsyncSession,
    production_order_id: str,
    labor_hours: float = 0,
    hourly_rate: float = 0,
    overhead_rate: float = 0.15  # 15% of direct costs as overhead
) -> Dict:
    """
    Calculate HPP (Cost of Goods Manufactured) for a production order.
    
    Components:
    1. Material Cost - Sum of (component_qty * weighted_avg_cost) from BOM
    2. Direct Labor - labor_hours * hourly_rate
    3. Factory Overhead - percentage of (material + labor) or fixed allocation
    
    Returns:
        Dict with material_cost, labor_cost, overhead_cost, total_hpp, hpp_per_unit
    """
    # 1. Get production order with products
    query = select(models.ProductionOrder)\
        .where(models.ProductionOrder.id == production_order_id)\
        .options(
            selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product)
        )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        return {"error": "Production order not found"}
    
    # 2. Calculate Material Cost from BOM
    material_cost = 0.0
    
    for order_product in order.products:
        product = order_product.product
        if not product:
            continue
            
        # Get BOM for this product
        bom_query = select(models.BillOfMaterial)\
            .where(models.BillOfMaterial.product_id == product.id)\
            .options(selectinload(models.BillOfMaterial.items).selectinload(models.BOMItem.component))
        bom_result = await db.execute(bom_query)
        bom = bom_result.scalar_one_or_none()
        
        if bom:
            for item in bom.items:
                component = item.component
                if component:
                    # Use weighted average cost, fallback to standard cost
                    unit_cost = component.weighted_avg_cost or component.standard_cost or 0
                    # Apply waste percentage
                    qty_with_waste = item.quantity * (1 + (item.waste_percentage or 0) / 100)
                    material_cost += qty_with_waste * unit_cost * order.quantity
        else:
            # No BOM - use product's standard cost if available
            material_cost += (product.weighted_avg_cost or 0) * order.quantity
    
    # 3. Calculate Labor Cost
    labor_cost = labor_hours * hourly_rate
    
    # 4. Calculate Overhead (percentage of direct costs)
    direct_costs = material_cost + labor_cost
    overhead_cost = direct_costs * overhead_rate
    
    # 5. Total HPP
    total_hpp = material_cost + labor_cost + overhead_cost
    
    # 6. HPP per unit
    hpp_per_unit = total_hpp / order.quantity if order.quantity > 0 else 0
    
    return {
        "material_cost": round(material_cost, 2),
        "labor_cost": round(labor_cost, 2),
        "overhead_cost": round(overhead_cost, 2),
        "total_hpp": round(total_hpp, 2),
        "hpp_per_unit": round(hpp_per_unit, 2),
        "quantity": order.quantity
    }


async def update_order_hpp(
    db: AsyncSession,
    production_order_id: str,
    labor_hours: float,
    hourly_rate: float,
    overhead_rate: float = 0.15
) -> Dict:
    """
    Calculate and save HPP to production order.
    """
    hpp_data = await calculate_hpp(
        db, production_order_id, labor_hours, hourly_rate, overhead_rate
    )
    
    if "error" in hpp_data:
        return hpp_data
    
    # Update production order
    query = select(models.ProductionOrder).where(models.ProductionOrder.id == production_order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if order:
        order.material_cost = hpp_data["material_cost"]
        order.labor_cost = hpp_data["labor_cost"]
        order.overhead_cost = hpp_data["overhead_cost"]
        order.total_hpp = hpp_data["total_hpp"]
        order.hpp_per_unit = hpp_data["hpp_per_unit"]
        order.labor_hours = labor_hours
        order.hourly_rate = hourly_rate
        
        await db.commit()
    
    return hpp_data


async def calculate_suggested_price(
    hpp_per_unit: float,
    desired_margin: float = 0.30  # 30% margin
) -> Dict:
    """
    Calculate suggested selling price based on HPP and desired margin.
    
    Formula: Selling Price = HPP / (1 - margin)
    Example: HPP 70,000 with 30% margin = 70,000 / 0.7 = 100,000
    """
    if desired_margin >= 1:
        return {"error": "Margin must be less than 100%"}
    
    suggested_price = hpp_per_unit / (1 - desired_margin)
    profit_per_unit = suggested_price - hpp_per_unit
    
    return {
        "hpp_per_unit": round(hpp_per_unit, 2),
        "margin_percentage": desired_margin * 100,
        "suggested_price": round(suggested_price, 2),
        "profit_per_unit": round(profit_per_unit, 2)
    }


async def get_production_cost_breakdown(
    db: AsyncSession,
    production_order_id: str
) -> Dict:
    """
    Get detailed cost breakdown for a production order.
    """
    query = select(models.ProductionOrder)\
        .where(models.ProductionOrder.id == production_order_id)\
        .options(
            selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product),
            selectinload(models.ProductionOrder.work_centers).selectinload(models.ProductionOrderWorkCenter.work_center)
        )
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        return {"error": "Production order not found"}
    
    # Material breakdown
    materials = []
    for order_product in order.products:
        product = order_product.product
        if product:
            materials.append({
                "product_code": product.code,
                "product_name": product.name,
                "unit_cost": product.weighted_avg_cost or 0
            })
    
    # Work center breakdown (machine costs)
    machine_costs = []
    for order_wc in order.work_centers:
        wc = order_wc.work_center
        if wc:
            machine_costs.append({
                "work_center_code": wc.code,
                "work_center_name": wc.name,
                "cost_per_hour": wc.cost_per_hour if hasattr(wc, 'cost_per_hour') else 0
            })
    
    return {
        "order_no": order.order_no,
        "quantity": order.quantity,
        "materials": materials,
        "machine_costs": machine_costs,
        "material_cost": order.material_cost or 0,
        "labor_cost": order.labor_cost or 0,
        "overhead_cost": order.overhead_cost or 0,
        "total_hpp": order.total_hpp or 0,
        "hpp_per_unit": order.hpp_per_unit or 0
    }
