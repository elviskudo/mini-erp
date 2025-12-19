from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
import database
import models
from auth import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/production")
async def get_production_dashboard(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get production dashboard data including live stats, OEE, and active orders"""
    today = datetime.utcnow().date()
    
    # Get today's production orders
    query = select(models.ProductionOrder).where(
        models.ProductionOrder.tenant_id == current_user.tenant_id,
        func.date(models.ProductionOrder.scheduled_date) == today
    )
    result = await db.execute(query)
    today_orders = result.scalars().all()
    
    # Calculate today's target and actual
    today_target = sum(o.quantity or 0 for o in today_orders)
    today_actual = sum(o.completed_qty or 0 for o in today_orders)
    
    # Count in-progress orders
    in_progress_query = select(func.count()).where(
        models.ProductionOrder.tenant_id == current_user.tenant_id,
        models.ProductionOrder.status == models.ProductionOrderStatus.IN_PROGRESS
    )
    in_progress_result = await db.execute(in_progress_query)
    in_progress = in_progress_result.scalar() or 0
    
    # Calculate OEE (simplified)
    # Availability = Uptime / Planned Time (assume 90% for now)
    # Performance = Actual Output / Theoretical Output
    # Quality = Good Units / Total Units
    
    availability = 92  # Default, could be calculated from downtime logs
    performance = min(100, int((today_actual / today_target * 100) if today_target > 0 else 0))
    
    # Get QC data for quality calculation
    qc_query = select(
        func.sum(models.ProductionQCResult.good_qty),
        func.sum(models.ProductionQCResult.defect_qty),
        func.sum(models.ProductionQCResult.scrap_qty)
    ).where(
        models.ProductionQCResult.tenant_id == current_user.tenant_id,
        func.date(models.ProductionQCResult.recorded_at) == today
    )
    qc_result = await db.execute(qc_query)
    qc_data = qc_result.first()
    
    good_qty = qc_data[0] or 0
    defect_qty = qc_data[1] or 0
    scrap_qty = qc_data[2] or 0
    total_produced = good_qty + defect_qty + scrap_qty
    
    quality = int((good_qty / total_produced * 100) if total_produced > 0 else 98)
    overall_oee = int((availability * performance * quality) / 10000)
    
    # Get active orders
    from sqlalchemy.orm import selectinload
    active_query = select(models.ProductionOrder).where(
        models.ProductionOrder.tenant_id == current_user.tenant_id,
        models.ProductionOrder.status.in_([
            models.ProductionOrderStatus.DRAFT,
            models.ProductionOrderStatus.IN_PROGRESS
        ])
    ).options(
        selectinload(models.ProductionOrder.products).selectinload(models.ProductionOrderProduct.product)
    ).order_by(models.ProductionOrder.scheduled_date).limit(10)
    
    active_result = await db.execute(active_query)
    active_orders = active_result.scalars().all()
    
    return {
        "today_target": today_target,
        "today_actual": today_actual,
        "in_progress": in_progress,
        "oee": {
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "overall": overall_oee
        },
        "active_orders": [
            {
                "id": str(o.id),
                "order_no": o.order_no,
                "product_name": o.products[0].product.name if o.products and o.products[0].product else "N/A",
                "quantity": o.quantity,
                "completed_qty": o.completed_qty or 0,
                "progress": o.progress or 0,
                "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                "scheduled_date": o.scheduled_date.isoformat() if o.scheduled_date else None
            }
            for o in active_orders
        ]
    }


@router.get("/failures")
async def get_failure_dashboard(
    period: str = "week",
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get failure analysis dashboard data including defect rate, pareto, COPQ"""
    # Calculate date range
    today = datetime.utcnow().date()
    if period == "today":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    else:  # month
        start_date = today - timedelta(days=30)
    
    # Get QC data for the period
    qc_query = select(models.ProductionQCResult).where(
        models.ProductionQCResult.tenant_id == current_user.tenant_id,
        func.date(models.ProductionQCResult.recorded_at) >= start_date
    )
    qc_result = await db.execute(qc_query)
    qc_records = qc_result.scalars().all()
    
    # Calculate totals
    total_good = sum(r.good_qty or 0 for r in qc_records)
    total_defects = sum(r.defect_qty or 0 for r in qc_records)
    total_scrap = sum(r.scrap_qty or 0 for r in qc_records)
    total_produced = total_good + total_defects + total_scrap
    
    defect_rate = round((total_defects / total_produced * 100) if total_produced > 0 else 0, 1)
    
    # Calculate COPQ
    scrap_cost = sum(r.spoilage_expense or 0 for r in qc_records)
    rework_cost = sum(r.rework_cost or 0 for r in qc_records)
    
    # Estimate other costs (returns and inspection) - could be from actual data
    returns_cost = int(scrap_cost * 0.25)  # Estimate
    inspection_cost = int(scrap_cost * 0.15)  # Estimate
    copq = scrap_cost + rework_cost + returns_cost + inspection_cost
    
    # Assume monthly revenue of 150M for percent calculation
    monthly_revenue = 150000000
    copq_percent = round((copq / monthly_revenue * 100) if monthly_revenue > 0 else 0, 1)
    
    # Generate trend data (last 7 days)
    trend_data = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(7):
        day_date = today - timedelta(days=6-i)
        day_good = sum(r.good_qty or 0 for r in qc_records if r.recorded_at and r.recorded_at.date() == day_date)
        day_defect = sum(r.defect_qty or 0 for r in qc_records if r.recorded_at and r.recorded_at.date() == day_date)
        day_total = day_good + day_defect
        day_rate = round((day_defect / day_total * 100) if day_total > 0 else 0, 1)
        trend_data.append({
            "label": days[day_date.weekday()],
            "rate": day_rate
        })
    
    # Generate Pareto data from scrap reasons
    reason_counts: dict = {}
    for r in qc_records:
        if r.scrap_reason and r.scrap_qty and r.scrap_qty > 0:
            reason_counts[r.scrap_reason] = reason_counts.get(r.scrap_reason, 0) + r.scrap_qty
    
    # Sort by count descending and calculate percentages
    sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    total_reason_count = sum(c for _, c in sorted_reasons) or 1
    pareto_data = [
        {
            "name": reason,
            "count": count,
            "percent": round(count / total_reason_count * 100)
        }
        for reason, count in sorted_reasons
    ]
    
    # Recent defects
    from sqlalchemy.orm import selectinload
    recent_query = select(models.ProductionQCResult).where(
        models.ProductionQCResult.tenant_id == current_user.tenant_id,
        models.ProductionQCResult.defect_qty > 0
    ).order_by(models.ProductionQCResult.recorded_at.desc()).limit(10)
    
    recent_result = await db.execute(recent_query)
    recent_records = recent_result.scalars().all()
    
    recent_defects = []
    for r in recent_records:
        # Get order number
        order_no = "N/A"
        if r.production_order_id:
            order_query = select(models.ProductionOrder).where(models.ProductionOrder.id == r.production_order_id)
            order_result = await db.execute(order_query)
            order = order_result.scalar_one_or_none()
            if order:
                order_no = order.order_no
        
        recent_defects.append({
            "recorded_at": r.recorded_at.strftime("%Y-%m-%d %H:%M") if r.recorded_at else "-",
            "order_no": order_no,
            "defect_qty": r.defect_qty,
            "scrap_qty": r.scrap_qty,
            "scrap_type": r.scrap_type.value if r.scrap_type and hasattr(r.scrap_type, 'value') else str(r.scrap_type) if r.scrap_type else None,
            "scrap_reason": r.scrap_reason,
            "spoilage_expense": r.spoilage_expense or 0
        })
    
    return {
        "defect_rate": defect_rate,
        "total_defects": total_defects,
        "total_scrap": total_scrap,
        "copq": copq,
        "copq_percent": copq_percent,
        "copq_breakdown": {
            "scrap": scrap_cost,
            "rework": rework_cost,
            "returns": returns_cost,
            "inspection": inspection_cost
        },
        "trend_data": trend_data,
        "pareto_data": pareto_data,
        "recent_defects": recent_defects
    }
