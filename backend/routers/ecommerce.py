from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid

import models, schemas
from database import get_db
from models.models_crm import OrderSource, SOStatus

router = APIRouter(
    prefix="/ecommerce",
    tags=["ecommerce"]
)

@router.get("/catalog", response_model=List[schemas.ProductCatalogItem])
def get_catalog(db: Session = Depends(get_db)):
    """
    Return all products with available stock (Mocking stock logic if aggregated inventory helper missing)
    For MVP: Just return all products and mock available stock or join with Inventory.
    """
    products = db.query(models.Product).all()
    catalog = []
    
    for p in products:
        # Calculate Total Available Stock across all locations
        # This is expensive N+1, but fine for MVP. Optimization: GroupBy query.
        stock = db.query(func.sum(models.Inventory.quantity_on_hand))\
            .filter(models.Inventory.product_id == p.id)\
            .scalar() or 0.0
            
        if stock > 0:
            catalog.append(schemas.ProductCatalogItem(
                id=p.id,
                name=p.name,
                code=p.code,
                price=p.standard_cost * 1.5, # Dummy markup pricing since we don't have Sales Price List yet
                description=p.description,
                category=p.category,
                available_stock=stock
            ))
            
    return catalog

@router.post("/checkout")
def checkout(request: schemas.CheckoutRequest, db: Session = Depends(get_db)):
    # 1. Create Sales Order
    so = models.SalesOrder(
        customer_id=request.customer_id,
        status=SOStatus.DRAFT, # Web orders start as Draft or Confirmed? Let's say Draft for review.
        source=OrderSource.WEB
    )
    db.add(so)
    db.flush() # Get ID
    
    total = 0.0
    
    # 2. Add Items
    for item in request.items:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            continue
            
        # Pricing logic
        price = prod.standard_cost * 1.5
        subtotal = item.quantity * price
        
        so_item = models.SOItem(
            sales_order_id=so.id,
            product_id=prod.id,
            quantity=item.quantity,
            unit_price=price,
            subtotal=subtotal
        )
        db.add(so_item)
        total += subtotal
        
    so.total_amount = total
    db.commit()
    db.refresh(so)
    
    return {"status": "success", "order_id": str(so.id), "message": "Order placed successfully"}

@router.get("/my-orders/{customer_id}")
def get_my_orders(customer_id: str, db: Session = Depends(get_db)):
    orders = db.query(models.SalesOrder)\
        .filter(models.SalesOrder.customer_id == customer_id)\
        .order_by(models.SalesOrder.date.desc())\
        .all()
    return orders
