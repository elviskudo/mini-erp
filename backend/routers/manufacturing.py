from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy.orm import selectinload
import database, models
import schemas

router = APIRouter(
    prefix="/manufacturing",
    tags=["Manufacturing"]
)

# Work Center Endpoints
@router.post("/work-centers", response_model=schemas.WorkCenterResponse)
async def create_work_center(wc: schemas.WorkCenterCreate, db: AsyncSession = Depends(database.get_db)):
    new_wc = models.WorkCenter(**wc.dict())
    db.add(new_wc)
    try:
        await db.commit()
        await db.refresh(new_wc)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_wc

@router.get("/work-centers", response_model=List[schemas.WorkCenterResponse])
async def read_work_centers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.WorkCenter).offset(skip).limit(limit))
    return result.scalars().all()

# Product Endpoints
@router.post("/products", response_model=schemas.ProductResponse)
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return new_product

@router.get("/products", response_model=List[schemas.ProductResponse])
async def read_products(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Product).offset(skip).limit(limit))
    return result.scalars().all()

# BOM Endpoints
@router.post("/boms", response_model=schemas.BOMResponse)
async def create_bom(bom: schemas.BOMCreate, db: AsyncSession = Depends(database.get_db)):
    # Create Header
    new_bom = models.BillOfMaterial(
        product_id=bom.product_id,
        version=bom.version,
        is_active=bom.is_active
    )
    db.add(new_bom)
    await db.flush() # Get ID

    # Create Items
    for item in bom.items:
        new_item = models.BOMItem(
            bom_id=new_bom.id,
            component_id=item.component_id,
            quantity=item.quantity,
            waste_percentage=item.waste_percentage
        )
        db.add(new_item)
    
    try:
        await db.commit()
        # Reload with relationships
        query = select(models.BillOfMaterial)\
            .where(models.BillOfMaterial.id == new_bom.id)\
            .options(selectinload(models.BillOfMaterial.product), selectinload(models.BillOfMaterial.items).selectinload(models.BOMItem.component))
        result = await db.execute(query)
        final_bom = result.scalar_one()
        return final_bom
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/boms", response_model=List[schemas.BOMResponse])
async def read_boms(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)):
    query = select(models.BillOfMaterial)\
        .options(selectinload(models.BillOfMaterial.product), selectinload(models.BillOfMaterial.items).selectinload(models.BOMItem.component))\
        .offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
