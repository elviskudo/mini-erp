"""
Logistics API Router - Stock Transfers, Shipments, Returns, Couriers, Picking
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timedelta
import uuid as uuid_module

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/logistics", tags=["Logistics"])


# ==================== SCHEMAS ====================

class CourierBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    service_types: Optional[str] = "Regular,Express,Same Day"
    default_service: Optional[str] = "Regular"
    standard_lead_days: Optional[int] = 3
    express_lead_days: Optional[int] = 1
    base_cost: Optional[float] = 0
    cost_per_kg: Optional[float] = 0
    is_active: Optional[bool] = True

class CourierCreate(CourierBase):
    pass

class CourierResponse(CourierBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True


class TransferItemCreate(BaseModel):
    product_id: UUID
    quantity: float

class TransferCreate(BaseModel):
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    transfer_date: Optional[datetime] = None
    transfer_type: Optional[str] = "Standard"
    items: List[TransferItemCreate]
    notes: Optional[str] = None

class TransferResponse(BaseModel):
    id: UUID
    transfer_number: str
    from_warehouse: Optional[str] = None
    to_warehouse: Optional[str] = None
    transfer_date: Optional[datetime] = None
    transfer_type: str
    status: str
    items_count: int = 0
    created_at: datetime
    class Config:
        from_attributes = True


class ShipmentCreate(BaseModel):
    do_id: Optional[UUID] = None
    courier_id: Optional[UUID] = None
    service_type: Optional[str] = "Regular"
    tracking_number: Optional[str] = None
    ship_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    shipping_cost: Optional[float] = 0
    address: Optional[str] = None
    notes: Optional[str] = None

class ShipmentResponse(BaseModel):
    id: UUID
    shipment_number: str
    do_number: Optional[str] = None
    carrier: Optional[str] = None
    service_type: str
    tracking_number: Optional[str] = None
    status: str
    ship_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    shipping_cost: float = 0
    created_at: datetime
    class Config:
        from_attributes = True


class ReturnItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    condition: Optional[str] = "Good"

class ReturnCreate(BaseModel):
    return_type: str  # Sales or Purchase
    customer_name: Optional[str] = None
    vendor_id: Optional[UUID] = None
    reference: Optional[str] = None
    reason: str
    items: List[ReturnItemCreate]
    notes: Optional[str] = None

class ReturnResponse(BaseModel):
    id: UUID
    return_number: str
    return_type: str
    customer_name: Optional[str] = None
    vendor_name: Optional[str] = None
    reason: str
    return_date: Optional[datetime] = None
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


class PickingResponse(BaseModel):
    id: UUID
    pick_number: str
    so_number: Optional[str] = None
    priority: str
    status: str
    picker_name: Optional[str] = None
    items_count: int = 0
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# ==================== COURIER ENDPOINTS ====================

@router.get("/couriers", response_model=List[CourierResponse])
async def list_couriers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Courier)
        .where(models.Courier.tenant_id == current_user.tenant_id)
        .order_by(models.Courier.name)
    )
    return result.scalars().all()


@router.post("/couriers", response_model=CourierResponse)
async def create_courier(
    payload: CourierCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    courier = models.Courier(
        tenant_id=current_user.tenant_id,
        **payload.model_dump()
    )
    db.add(courier)
    await db.commit()
    await db.refresh(courier)
    return courier


@router.get("/couriers/{courier_id}", response_model=CourierResponse)
async def get_courier(
    courier_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Courier).where(
            models.Courier.id == courier_id,
            models.Courier.tenant_id == current_user.tenant_id
        )
    )
    courier = result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    return courier


@router.put("/couriers/{courier_id}", response_model=CourierResponse)
async def update_courier(
    courier_id: UUID,
    payload: CourierCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Courier).where(
            models.Courier.id == courier_id,
            models.Courier.tenant_id == current_user.tenant_id
        )
    )
    courier = result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(courier, key, value)
    
    await db.commit()
    await db.refresh(courier)
    return courier


@router.delete("/couriers/{courier_id}")
async def delete_courier(
    courier_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Courier).where(
            models.Courier.id == courier_id,
            models.Courier.tenant_id == current_user.tenant_id
        )
    )
    courier = result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    await db.delete(courier)
    await db.commit()
    return {"detail": "Courier deleted"}


# ==================== STOCK TRANSFER ENDPOINTS ====================

@router.get("/transfers", response_model=List[TransferResponse])
async def list_transfers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StockTransfer)
        .where(models.StockTransfer.tenant_id == current_user.tenant_id)
        .options(
            selectinload(models.StockTransfer.from_warehouse),
            selectinload(models.StockTransfer.to_warehouse),
            selectinload(models.StockTransfer.items)
        )
        .order_by(models.StockTransfer.created_at.desc())
    )
    transfers = result.scalars().all()
    
    return [
        TransferResponse(
            id=t.id,
            transfer_number=t.transfer_number,
            from_warehouse=t.from_warehouse.name if t.from_warehouse else None,
            to_warehouse=t.to_warehouse.name if t.to_warehouse else None,
            transfer_date=t.transfer_date,
            transfer_type=t.transfer_type,
            status=t.status.value,
            items_count=len(t.items),
            created_at=t.created_at
        ) for t in transfers
    ]


@router.post("/transfers", response_model=TransferResponse)
async def create_transfer(
    payload: TransferCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate transfer number
    count_result = await db.execute(
        select(func.count()).select_from(models.StockTransfer)
        .where(models.StockTransfer.tenant_id == current_user.tenant_id)
    )
    count = count_result.scalar() + 1
    transfer_number = f"TRF-{datetime.now().strftime('%Y%m')}-{count:04d}"
    
    transfer = models.StockTransfer(
        tenant_id=current_user.tenant_id,
        transfer_number=transfer_number,
        from_warehouse_id=payload.from_warehouse_id,
        to_warehouse_id=payload.to_warehouse_id,
        transfer_date=payload.transfer_date or datetime.utcnow(),
        transfer_type=payload.transfer_type,
        notes=payload.notes,
        created_by=current_user.id
    )
    db.add(transfer)
    await db.flush()
    
    # Add items
    for item in payload.items:
        transfer_item = models.StockTransferItem(
            tenant_id=current_user.tenant_id,
            transfer_id=transfer.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(transfer_item)
    
    await db.commit()
    await db.refresh(transfer)
    
    # Reload with relationships
    result = await db.execute(
        select(models.StockTransfer)
        .where(models.StockTransfer.id == transfer.id)
        .options(
            selectinload(models.StockTransfer.from_warehouse),
            selectinload(models.StockTransfer.to_warehouse),
            selectinload(models.StockTransfer.items)
        )
    )
    t = result.scalar_one()
    
    return TransferResponse(
        id=t.id,
        transfer_number=t.transfer_number,
        from_warehouse=t.from_warehouse.name if t.from_warehouse else None,
        to_warehouse=t.to_warehouse.name if t.to_warehouse else None,
        transfer_date=t.transfer_date,
        transfer_type=t.transfer_type,
        status=t.status.value,
        items_count=len(t.items),
        created_at=t.created_at
    )


@router.put("/transfers/{transfer_id}/start")
async def start_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StockTransfer).where(
            models.StockTransfer.id == transfer_id,
            models.StockTransfer.tenant_id == current_user.tenant_id
        )
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    transfer.status = models.TransferStatus.IN_TRANSIT
    transfer.started_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Transfer started"}


@router.put("/transfers/{transfer_id}/complete")
async def complete_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.StockTransfer)
        .where(
            models.StockTransfer.id == transfer_id,
            models.StockTransfer.tenant_id == current_user.tenant_id
        )
        .options(selectinload(models.StockTransfer.items).selectinload(models.StockTransferItem.product))
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    # TODO: Add inventory ledger movement for source and destination
    
    transfer.status = models.TransferStatus.COMPLETED
    transfer.completed_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Transfer completed"}


# ==================== SHIPMENT ENDPOINTS ====================

@router.get("/shipments", response_model=List[ShipmentResponse])
async def list_shipments(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Shipment)
        .where(models.Shipment.tenant_id == current_user.tenant_id)
        .options(
            selectinload(models.Shipment.courier),
            selectinload(models.Shipment.delivery_order)
        )
        .order_by(models.Shipment.created_at.desc())
    )
    shipments = result.scalars().all()
    
    return [
        ShipmentResponse(
            id=s.id,
            shipment_number=s.shipment_number,
            do_number=s.delivery_order.so_id if s.delivery_order else None,
            carrier=s.courier.name if s.courier else None,
            service_type=s.service_type,
            tracking_number=s.tracking_number,
            status=s.status.value,
            ship_date=s.ship_date,
            expected_delivery=s.expected_delivery,
            shipping_cost=s.shipping_cost or 0,
            created_at=s.created_at
        ) for s in shipments
    ]


@router.post("/shipments", response_model=ShipmentResponse)
async def create_shipment(
    payload: ShipmentCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate shipment number
    count_result = await db.execute(
        select(func.count()).select_from(models.Shipment)
        .where(models.Shipment.tenant_id == current_user.tenant_id)
    )
    count = count_result.scalar() + 1
    shipment_number = f"SHP-{datetime.now().strftime('%Y%m')}-{count:04d}"
    
    # Get courier details for expected delivery calculation
    expected_delivery = payload.expected_delivery
    if payload.courier_id and not expected_delivery:
        courier_result = await db.execute(
            select(models.Courier).where(models.Courier.id == payload.courier_id)
        )
        courier = courier_result.scalar_one_or_none()
        if courier:
            lead_days = courier.express_lead_days if payload.service_type == "Express" else courier.standard_lead_days
            expected_delivery = (payload.ship_date or datetime.utcnow()) + timedelta(days=lead_days)
    
    shipment = models.Shipment(
        tenant_id=current_user.tenant_id,
        shipment_number=shipment_number,
        delivery_order_id=payload.do_id,
        courier_id=payload.courier_id,
        service_type=payload.service_type,
        tracking_number=payload.tracking_number,
        ship_date=payload.ship_date or datetime.utcnow(),
        expected_delivery=expected_delivery,
        shipping_cost=payload.shipping_cost,
        address=payload.address,
        notes=payload.notes
    )
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    
    # Reload with relationships
    result = await db.execute(
        select(models.Shipment)
        .where(models.Shipment.id == shipment.id)
        .options(
            selectinload(models.Shipment.courier),
            selectinload(models.Shipment.delivery_order)
        )
    )
    s = result.scalar_one()
    
    return ShipmentResponse(
        id=s.id,
        shipment_number=s.shipment_number,
        do_number=s.delivery_order.so_id if s.delivery_order else None,
        carrier=s.courier.name if s.courier else None,
        service_type=s.service_type,
        tracking_number=s.tracking_number,
        status=s.status.value,
        ship_date=s.ship_date,
        expected_delivery=s.expected_delivery,
        shipping_cost=s.shipping_cost or 0,
        created_at=s.created_at
    )


@router.put("/shipments/{shipment_id}/dispatch")
async def dispatch_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Shipment).where(
            models.Shipment.id == shipment_id,
            models.Shipment.tenant_id == current_user.tenant_id
        )
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment.status = models.ShipmentStatus.IN_TRANSIT
    shipment.ship_date = datetime.utcnow()
    await db.commit()
    return {"detail": "Shipment dispatched"}


@router.put("/shipments/{shipment_id}/deliver")
async def mark_delivered(
    shipment_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Shipment).where(
            models.Shipment.id == shipment_id,
            models.Shipment.tenant_id == current_user.tenant_id
        )
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment.status = models.ShipmentStatus.DELIVERED
    shipment.actual_delivery = datetime.utcnow()
    await db.commit()
    return {"detail": "Shipment delivered"}


# ==================== RETURN ENDPOINTS ====================

@router.get("/returns", response_model=List[ReturnResponse])
async def list_returns(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Return)
        .where(models.Return.tenant_id == current_user.tenant_id)
        .options(selectinload(models.Return.vendor))
        .order_by(models.Return.created_at.desc())
    )
    returns = result.scalars().all()
    
    return [
        ReturnResponse(
            id=r.id,
            return_number=r.return_number,
            return_type=r.return_type.value,
            customer_name=r.customer_name,
            vendor_name=r.vendor.name if r.vendor else None,
            reason=r.reason,
            return_date=r.return_date,
            status=r.status.value,
            created_at=r.created_at
        ) for r in returns
    ]


@router.post("/returns", response_model=ReturnResponse)
async def create_return(
    payload: ReturnCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Generate return number
    count_result = await db.execute(
        select(func.count()).select_from(models.Return)
        .where(models.Return.tenant_id == current_user.tenant_id)
    )
    count = count_result.scalar() + 1
    return_type_prefix = "SR" if payload.return_type == "Sales" else "PR"
    return_number = f"{return_type_prefix}-{datetime.now().strftime('%Y%m')}-{count:04d}"
    
    return_order = models.Return(
        tenant_id=current_user.tenant_id,
        return_number=return_number,
        return_type=models.ReturnType[payload.return_type.upper()],
        customer_name=payload.customer_name,
        vendor_id=payload.vendor_id,
        so_reference=payload.reference if payload.return_type == "Sales" else None,
        po_reference=payload.reference if payload.return_type == "Purchase" else None,
        reason=payload.reason,
        notes=payload.notes,
        created_by=current_user.id
    )
    db.add(return_order)
    await db.flush()
    
    # Add items
    for item in payload.items:
        return_item = models.ReturnItem(
            tenant_id=current_user.tenant_id,
            return_id=return_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            condition=models.ItemCondition[item.condition.upper()]
        )
        db.add(return_item)
    
    await db.commit()
    await db.refresh(return_order)
    
    return ReturnResponse(
        id=return_order.id,
        return_number=return_order.return_number,
        return_type=return_order.return_type.value,
        customer_name=return_order.customer_name,
        vendor_name=None,
        reason=return_order.reason,
        return_date=return_order.return_date,
        status=return_order.status.value,
        created_at=return_order.created_at
    )


@router.put("/returns/{return_id}/process")
async def process_return(
    return_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Return).where(
            models.Return.id == return_id,
            models.Return.tenant_id == current_user.tenant_id
        )
    )
    return_order = result.scalar_one_or_none()
    if not return_order:
        raise HTTPException(status_code=404, detail="Return not found")
    
    return_order.status = models.ReturnStatus.PROCESSED
    return_order.processed_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Return processed"}


@router.put("/returns/{return_id}/ship")
async def ship_return(
    return_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Return).where(
            models.Return.id == return_id,
            models.Return.tenant_id == current_user.tenant_id
        )
    )
    return_order = result.scalar_one_or_none()
    if not return_order:
        raise HTTPException(status_code=404, detail="Return not found")
    
    return_order.status = models.ReturnStatus.IN_TRANSIT
    return_order.shipped_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Return shipped to vendor"}


# ==================== PICKING ENDPOINTS ====================

@router.get("/picking", response_model=List[PickingResponse])
async def list_picking(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.PickingList)
        .where(models.PickingList.tenant_id == current_user.tenant_id)
        .options(
            selectinload(models.PickingList.picker),
            selectinload(models.PickingList.items)
        )
        .order_by(models.PickingList.created_at.desc())
    )
    picks = result.scalars().all()
    
    return [
        PickingResponse(
            id=p.id,
            pick_number=p.pick_number,
            so_number=p.so_number,
            priority=p.priority,
            status=p.status.value,
            picker_name=p.picker.username if p.picker else None,
            items_count=len(p.items),
            progress=int(sum(i.picked_quantity for i in p.items) / max(sum(i.quantity for i in p.items), 1) * 100) if p.items else 0,
            started_at=p.started_at,
            completed_at=p.completed_at
        ) for p in picks
    ]


@router.put("/picking/{pick_id}/start")
async def start_picking(
    pick_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.PickingList).where(
            models.PickingList.id == pick_id,
            models.PickingList.tenant_id == current_user.tenant_id
        )
    )
    pick = result.scalar_one_or_none()
    if not pick:
        raise HTTPException(status_code=404, detail="Picking list not found")
    
    pick.status = models.PickingStatus.IN_PROGRESS
    pick.started_at = datetime.utcnow()
    pick.picker_id = current_user.id
    await db.commit()
    return {"detail": "Picking started"}


@router.put("/picking/{pick_id}/complete")
async def complete_picking(
    pick_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.PickingList).where(
            models.PickingList.id == pick_id,
            models.PickingList.tenant_id == current_user.tenant_id
        )
    )
    pick = result.scalar_one_or_none()
    if not pick:
        raise HTTPException(status_code=404, detail="Picking list not found")
    
    pick.status = models.PickingStatus.COMPLETED
    pick.completed_at = datetime.utcnow()
    await db.commit()
    return {"detail": "Picking completed"}


# ==================== REFERENCE SEARCH (for autocomplete) ====================

@router.get("/references/search")
async def search_references(
    q: str = Query(..., min_length=1),
    type: str = Query("all", regex="^(all|sales|purchase)$"),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Search for SO, DO, PO, GRN references for return autocomplete"""
    results = []
    
    if type in ["all", "sales"]:
        # Search Delivery Orders (for SO/DO reference)
        do_result = await db.execute(
            select(models.DeliveryOrder)
            .where(
                models.DeliveryOrder.tenant_id == current_user.tenant_id,
                models.DeliveryOrder.so_id.ilike(f"%{q}%")
            )
            .limit(10)
        )
        for do in do_result.scalars().all():
            results.append({
                "type": "DO",
                "reference": do.so_id,
                "id": str(do.id),
                "label": f"DO: {do.so_id}"
            })
    
    if type in ["all", "purchase"]:
        # Search Purchase Orders
        po_result = await db.execute(
            select(models.PurchaseOrder)
            .where(
                models.PurchaseOrder.tenant_id == current_user.tenant_id,
                models.PurchaseOrder.po_number.ilike(f"%{q}%")
            )
            .limit(10)
        )
        for po in po_result.scalars().all():
            results.append({
                "type": "PO",
                "reference": po.po_number,
                "id": str(po.id),
                "label": f"PO: {po.po_number}"
            })
        
        # Search GRNs (GoodsReceipt)
        grn_result = await db.execute(
            select(models.GoodsReceipt)
            .where(
                models.GoodsReceipt.tenant_id == current_user.tenant_id,
                models.GoodsReceipt.grn_number.ilike(f"%{q}%")
            )
            .limit(10)
        )
        for grn in grn_result.scalars().all():
            results.append({
                "type": "GRN",
                "reference": grn.grn_number,
                "id": str(grn.id),
                "label": f"GRN: {grn.grn_number}"
            })
    
    return results
