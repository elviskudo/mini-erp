"""
CRM API Router - Leads, Opportunities, Activities, Notes, Quotations
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
from models.models_crm import (
    Lead, LeadSource, LeadStatus,
    Opportunity, OpportunityStage,
    Activity, ActivityType, ActivityStatus,
    Note, Quotation, QuotationItem,
    SalesOrder, SOItem, SOStatus
)
from auth import get_current_user

router = APIRouter(
    prefix="/crm",
    tags=["CRM & Sales"]
)


# ==================== SCHEMAS ====================

class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: str  # Required
    phone: str  # Required
    website: Optional[str] = None
    source: str = "Other"  # Required
    industry: str  # Required
    company_size: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    score: Optional[int] = 0
    assigned_to: Optional[UUID] = None


class LeadResponse(BaseModel):
    id: UUID
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    source: str
    status: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    score: int = 0
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    stage: Optional[str] = "Qualification"
    probability: Optional[int] = 10
    expected_value: Optional[float] = 0
    expected_close_date: Optional[datetime] = None
    lead_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None


class OpportunityResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    stage: str
    probability: int = 10
    expected_value: float = 0
    expected_close_date: Optional[datetime] = None
    lead_name: Optional[str] = None
    customer_name: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    actual_value: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityCreate(BaseModel):
    title: str
    description: Optional[str] = None
    activity_type: Optional[str] = "Task"
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = "Normal"
    lead_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None


class ActivityResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    activity_type: str
    status: str
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    priority: str = "Normal"
    lead_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    customer_name: Optional[str] = None
    assignee_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    content: str
    lead_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    activity_id: Optional[UUID] = None


class NoteResponse(BaseModel):
    id: UUID
    content: str
    lead_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    creator_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== LEADS ENDPOINTS ====================

@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(Lead)\
        .where(Lead.tenant_id == current_user.tenant_id)\
        .options(selectinload(Lead.assignee))\
        .order_by(Lead.created_at.desc())
    
    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return [
        LeadResponse(
            id=l.id,
            name=l.name,
            company=l.company,
            email=l.email,
            phone=l.phone,
            website=l.website,
            source=l.source.value if l.source else "Other",
            status=l.status.value if l.status else "New",
            industry=l.industry,
            company_size=l.company_size,
            address=l.address,
            latitude=l.latitude,
            longitude=l.longitude,
            score=l.score or 0,
            assigned_to=l.assigned_to,
            assignee_name=l.assignee.username if l.assignee else None,
            created_at=l.created_at
        ) for l in leads
    ]


@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    lead = Lead(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        company=payload.company,
        email=payload.email,
        phone=payload.phone,
        website=payload.website,
        source=LeadSource[payload.source.upper().replace(" ", "_")] if payload.source else LeadSource.OTHER,
        industry=payload.industry,
        company_size=payload.company_size,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        notes=payload.notes,
        score=payload.score or 0,
        assigned_to=payload.assigned_to,
        created_by=current_user.id
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    return LeadResponse(
        id=lead.id,
        name=lead.name,
        company=lead.company,
        email=lead.email,
        phone=lead.phone,
        website=lead.website,
        source=lead.source.value,
        status=lead.status.value,
        industry=lead.industry,
        company_size=lead.company_size,
        address=lead.address,
        latitude=lead.latitude,
        longitude=lead.longitude,
        score=lead.score,
        assigned_to=lead.assigned_to,
        created_at=lead.created_at
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id
        ).options(selectinload(Lead.assignee))
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return LeadResponse(
        id=lead.id,
        name=lead.name,
        company=lead.company,
        email=lead.email,
        phone=lead.phone,
        source=lead.source.value,
        status=lead.status.value,
        score=lead.score,
        assigned_to=lead.assigned_to,
        assignee_name=lead.assignee.username if lead.assignee else None,
        created_at=lead.created_at
    )


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    payload: LeadCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "source" and value:
            value = LeadSource[value.upper().replace(" ", "_")]
        setattr(lead, key, value)
    
    lead.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(lead)
    
    return LeadResponse(
        id=lead.id,
        name=lead.name,
        company=lead.company,
        email=lead.email,
        phone=lead.phone,
        source=lead.source.value,
        status=lead.status.value,
        score=lead.score,
        assigned_to=lead.assigned_to,
        created_at=lead.created_at
    )


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    await db.delete(lead)
    await db.commit()
    return {"detail": "Lead deleted"}


@router.post("/leads/{lead_id}/convert")
async def convert_lead(
    lead_id: UUID,
    create_opportunity: bool = True,
    create_customer: bool = True,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == current_user.tenant_id
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.status == LeadStatus.CONVERTED:
        raise HTTPException(status_code=400, detail="Lead already converted")
    
    customer_id = None
    opportunity_id = None
    
    # Create Customer
    if create_customer:
        customer = models.Customer(
            tenant_id=current_user.tenant_id,
            name=lead.company or lead.name,
            email=lead.email,
            phone=lead.phone,
            address=lead.address
        )
        db.add(customer)
        await db.flush()
        customer_id = customer.id
        lead.converted_customer_id = customer_id
    
    # Create Opportunity
    if create_opportunity:
        opp = Opportunity(
            tenant_id=current_user.tenant_id,
            name=f"Opportunity from {lead.name}",
            lead_id=lead.id,
            customer_id=customer_id,
            assigned_to=lead.assigned_to,
            created_by=current_user.id
        )
        db.add(opp)
        await db.flush()
        opportunity_id = opp.id
        lead.converted_opportunity_id = opportunity_id
    
    lead.status = LeadStatus.CONVERTED
    lead.converted_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "detail": "Lead converted successfully",
        "customer_id": str(customer_id) if customer_id else None,
        "opportunity_id": str(opportunity_id) if opportunity_id else None
    }


# ==================== OPPORTUNITIES ENDPOINTS ====================

@router.get("/opportunities", response_model=List[OpportunityResponse])
async def list_opportunities(
    stage: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(Opportunity)\
        .where(Opportunity.tenant_id == current_user.tenant_id)\
        .options(
            selectinload(Opportunity.lead),
            selectinload(Opportunity.customer),
            selectinload(Opportunity.assignee)
        )\
        .order_by(Opportunity.created_at.desc())
    
    if stage:
        query = query.where(Opportunity.stage == stage)
    
    result = await db.execute(query)
    opps = result.scalars().all()
    
    return [
        OpportunityResponse(
            id=o.id,
            name=o.name,
            description=o.description,
            stage=o.stage.value if o.stage else "Qualification",
            probability=o.probability or 10,
            expected_value=o.expected_value or 0,
            expected_close_date=o.expected_close_date,
            lead_name=o.lead.name if o.lead else None,
            customer_name=o.customer.name if o.customer else None,
            assigned_to=o.assigned_to,
            assignee_name=o.assignee.username if o.assignee else None,
            actual_value=o.actual_value,
            created_at=o.created_at
        ) for o in opps
    ]


@router.post("/opportunities", response_model=OpportunityResponse)
async def create_opportunity(
    payload: OpportunityCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    opp = Opportunity(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        description=payload.description,
        stage=OpportunityStage[payload.stage.upper().replace(" ", "_")] if payload.stage else OpportunityStage.QUALIFICATION,
        probability=payload.probability or 10,
        expected_value=payload.expected_value or 0,
        expected_close_date=payload.expected_close_date,
        lead_id=payload.lead_id,
        customer_id=payload.customer_id,
        assigned_to=payload.assigned_to,
        created_by=current_user.id
    )
    db.add(opp)
    await db.commit()
    await db.refresh(opp)
    
    return OpportunityResponse(
        id=opp.id,
        name=opp.name,
        description=opp.description,
        stage=opp.stage.value,
        probability=opp.probability,
        expected_value=opp.expected_value,
        expected_close_date=opp.expected_close_date,
        created_at=opp.created_at
    )


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opp_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opp_id,
            Opportunity.tenant_id == current_user.tenant_id
        ).options(
            selectinload(Opportunity.lead),
            selectinload(Opportunity.customer),
            selectinload(Opportunity.assignee)
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return OpportunityResponse(
        id=opp.id,
        name=opp.name,
        description=opp.description,
        stage=opp.stage.value,
        probability=opp.probability,
        expected_value=opp.expected_value,
        expected_close_date=opp.expected_close_date,
        lead_name=opp.lead.name if opp.lead else None,
        customer_name=opp.customer.name if opp.customer else None,
        assigned_to=opp.assigned_to,
        assignee_name=opp.assignee.username if opp.assignee else None,
        actual_value=opp.actual_value,
        created_at=opp.created_at
    )


@router.put("/opportunities/{opp_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opp_id: UUID,
    payload: OpportunityCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opp_id,
            Opportunity.tenant_id == current_user.tenant_id
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "stage" and value:
            value = OpportunityStage[value.upper().replace(" ", "_")]
        setattr(opp, key, value)
    
    opp.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(opp)
    
    return OpportunityResponse(
        id=opp.id,
        name=opp.name,
        description=opp.description,
        stage=opp.stage.value,
        probability=opp.probability,
        expected_value=opp.expected_value,
        expected_close_date=opp.expected_close_date,
        created_at=opp.created_at
    )


@router.put("/opportunities/{opp_id}/stage")
async def update_opportunity_stage(
    opp_id: UUID,
    stage: str,
    actual_value: Optional[float] = None,
    lost_reason: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opp_id,
            Opportunity.tenant_id == current_user.tenant_id
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opp.stage = OpportunityStage[stage.upper().replace(" ", "_")]
    
    # Update probability based on stage
    stage_probabilities = {
        OpportunityStage.QUALIFICATION: 10,
        OpportunityStage.NEEDS_ANALYSIS: 25,
        OpportunityStage.PROPOSAL: 50,
        OpportunityStage.NEGOTIATION: 75,
        OpportunityStage.CLOSED_WON: 100,
        OpportunityStage.CLOSED_LOST: 0
    }
    opp.probability = stage_probabilities.get(opp.stage, opp.probability)
    
    if opp.stage in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]:
        opp.closed_at = datetime.utcnow()
        if actual_value:
            opp.actual_value = actual_value
        if lost_reason:
            opp.lost_reason = lost_reason
    
    opp.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"detail": f"Opportunity moved to {opp.stage.value}"}


@router.delete("/opportunities/{opp_id}")
async def delete_opportunity(
    opp_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Opportunity).where(
            Opportunity.id == opp_id,
            Opportunity.tenant_id == current_user.tenant_id
        )
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    await db.delete(opp)
    await db.commit()
    return {"detail": "Opportunity deleted"}


# ==================== ACTIVITIES ENDPOINTS ====================

@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    status: Optional[str] = None,
    activity_type: Optional[str] = None,
    lead_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(Activity)\
        .where(Activity.tenant_id == current_user.tenant_id)\
        .options(
            selectinload(Activity.lead),
            selectinload(Activity.opportunity),
            selectinload(Activity.customer),
            selectinload(Activity.assignee)
        )\
        .order_by(Activity.due_date.asc().nullslast(), Activity.created_at.desc())
    
    if status:
        query = query.where(Activity.status == status)
    if activity_type:
        query = query.where(Activity.activity_type == activity_type)
    if lead_id:
        query = query.where(Activity.lead_id == lead_id)
    if opportunity_id:
        query = query.where(Activity.opportunity_id == opportunity_id)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return [
        ActivityResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            activity_type=a.activity_type.value if a.activity_type else "Task",
            status=a.status.value if a.status else "Planned",
            due_date=a.due_date,
            due_time=a.due_time,
            priority=a.priority or "Normal",
            lead_name=a.lead.name if a.lead else None,
            opportunity_name=a.opportunity.name if a.opportunity else None,
            customer_name=a.customer.name if a.customer else None,
            assignee_name=a.assignee.username if a.assignee else None,
            completed_at=a.completed_at,
            created_at=a.created_at
        ) for a in activities
    ]


@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    payload: ActivityCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Parse activity_type safely
    try:
        act_type = ActivityType[payload.activity_type.upper().replace(" ", "_")] if payload.activity_type else ActivityType.TASK
    except KeyError:
        act_type = ActivityType.TASK
    
    # Strip timezone from due_date (database expects naive datetime)
    due_date_naive = None
    if payload.due_date:
        due_date_naive = payload.due_date.replace(tzinfo=None) if payload.due_date.tzinfo else payload.due_date
    
    activity = Activity(
        tenant_id=current_user.tenant_id,
        title=payload.title,
        description=payload.description,
        activity_type=act_type,
        status=ActivityStatus.PLANNED,
        due_date=due_date_naive,
        due_time=payload.due_time,
        duration_minutes=payload.duration_minutes,
        priority=payload.priority or "Normal",
        lead_id=payload.lead_id if payload.lead_id else None,
        opportunity_id=payload.opportunity_id if payload.opportunity_id else None,
        customer_id=payload.customer_id if payload.customer_id else None,
        assigned_to=payload.assigned_to or current_user.id,
        created_by=current_user.id
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    return ActivityResponse(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type.value,
        status=activity.status.value,
        due_date=activity.due_date,
        due_time=activity.due_time,
        priority=activity.priority,
        created_at=activity.created_at
    )


@router.put("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    payload: ActivityCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id,
            Activity.tenant_id == current_user.tenant_id
        )
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "activity_type" and value:
            try:
                value = ActivityType[value.upper().replace(" ", "_")]
            except KeyError:
                value = ActivityType.TASK
        # Strip timezone from due_date
        if key == "due_date" and value and hasattr(value, 'tzinfo') and value.tzinfo:
            value = value.replace(tzinfo=None)
        # Skip empty UUIDs
        if key in ["lead_id", "opportunity_id", "customer_id", "assigned_to"] and not value:
            value = None
        setattr(activity, key, value)
    
    activity.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(activity)
    
    return ActivityResponse(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type.value,
        status=activity.status.value,
        due_date=activity.due_date,
        due_time=activity.due_time,
        priority=activity.priority,
        created_at=activity.created_at
    )


@router.put("/activities/{activity_id}/complete")
async def complete_activity(
    activity_id: UUID,
    outcome: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id,
            Activity.tenant_id == current_user.tenant_id
        )
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    activity.status = ActivityStatus.COMPLETED
    activity.completed_at = datetime.utcnow()
    if outcome:
        activity.outcome = outcome
    
    await db.commit()
    return {"detail": "Activity completed"}


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id,
            Activity.tenant_id == current_user.tenant_id
        )
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    await db.delete(activity)
    await db.commit()
    return {"detail": "Activity deleted"}


# ==================== NOTES ENDPOINTS ====================

@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    lead_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = select(Note)\
        .where(Note.tenant_id == current_user.tenant_id)\
        .options(selectinload(Note.creator))\
        .order_by(Note.created_at.desc())
    
    if lead_id:
        query = query.where(Note.lead_id == lead_id)
    if opportunity_id:
        query = query.where(Note.opportunity_id == opportunity_id)
    if customer_id:
        query = query.where(Note.customer_id == customer_id)
    
    result = await db.execute(query)
    notes = result.scalars().all()
    
    return [
        NoteResponse(
            id=n.id,
            content=n.content,
            lead_id=n.lead_id,
            opportunity_id=n.opportunity_id,
            customer_id=n.customer_id,
            creator_name=n.creator.username if n.creator else None,
            created_at=n.created_at
        ) for n in notes
    ]


@router.post("/notes", response_model=NoteResponse)
async def create_note(
    payload: NoteCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    note = Note(
        tenant_id=current_user.tenant_id,
        content=payload.content,
        lead_id=payload.lead_id,
        opportunity_id=payload.opportunity_id,
        customer_id=payload.customer_id,
        activity_id=payload.activity_id,
        created_by=current_user.id
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    return NoteResponse(
        id=note.id,
        content=note.content,
        lead_id=note.lead_id,
        opportunity_id=note.opportunity_id,
        customer_id=note.customer_id,
        created_at=note.created_at
    )


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.tenant_id == current_user.tenant_id
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    await db.delete(note)
    await db.commit()
    return {"detail": "Note deleted"}


# ==================== CUSTOMERS ENDPOINTS (from AR) ====================

@router.get("/customers")
async def list_customers(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Customer)
        .where(models.Customer.tenant_id == current_user.tenant_id)
        .order_by(models.Customer.name)
    )
    return result.scalars().all()


# ==================== PIPELINE/DASHBOARD ====================

@router.get("/pipeline/summary")
async def pipeline_summary(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get pipeline summary for dashboard/kanban"""
    query = select(
        Opportunity.stage,
        func.count(Opportunity.id).label("count"),
        func.sum(Opportunity.expected_value).label("total_value")
    ).where(
        Opportunity.tenant_id == current_user.tenant_id
    ).group_by(Opportunity.stage)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "stage": row.stage.value if row.stage else "Unknown",
            "count": row.count,
            "total_value": row.total_value or 0
        } for row in rows
    ]


@router.get("/dashboard/stats")
async def crm_dashboard_stats(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get CRM dashboard statistics"""
    tenant_id = current_user.tenant_id
    
    # Leads count by status
    leads_result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.tenant_id == tenant_id)
        .group_by(Lead.status)
    )
    leads_by_status = {row[0].value: row[1] for row in leads_result.all() if row[0]}
    
    # Opportunities count by stage
    opps_result = await db.execute(
        select(Opportunity.stage, func.count(Opportunity.id), func.sum(Opportunity.expected_value))
        .where(Opportunity.tenant_id == tenant_id)
        .group_by(Opportunity.stage)
    )
    opps_by_stage = [
        {"stage": row[0].value, "count": row[1], "value": row[2] or 0}
        for row in opps_result.all() if row[0]
    ]
    
    # Activities due today
    today = datetime.utcnow().date()
    activities_today = await db.execute(
        select(func.count(Activity.id))
        .where(
            Activity.tenant_id == tenant_id,
            func.date(Activity.due_date) == today,
            Activity.status != ActivityStatus.COMPLETED
        )
    )
    
    # Total pipeline value
    pipeline_value = await db.execute(
        select(func.sum(Opportunity.expected_value))
        .where(
            Opportunity.tenant_id == tenant_id,
            Opportunity.stage.notin_([OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST])
        )
    )
    
    return {
        "leads": leads_by_status,
        "opportunities": opps_by_stage,
        "activities_due_today": activities_today.scalar() or 0,
        "pipeline_value": pipeline_value.scalar() or 0
    }


# ==================== SALES ORDERS ====================

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float


class OrderCreate(BaseModel):
    customer_id: UUID
    items: List[OrderItemCreate]


class OrderItemResponse(BaseModel):
    product_id: UUID
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    date: datetime
    status: str
    total_amount: float
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all sales orders for this tenant"""
    query = select(SalesOrder).where(
        SalesOrder.tenant_id == current_user.tenant_id
    ).options(
        selectinload(SalesOrder.customer),
        selectinload(SalesOrder.items).selectinload(SOItem.product)
    ).order_by(SalesOrder.date.desc())
    
    if status:
        query = query.where(SalesOrder.status == status)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        OrderResponse(
            id=o.id,
            customer_id=o.customer_id,
            customer_name=o.customer.name if o.customer else None,
            date=o.date,
            status=o.status,
            total_amount=o.total_amount,
            items=[
                OrderItemResponse(
                    product_id=item.product_id,
                    product_name=item.product.name if item.product else None,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal
                ) for item in o.items
            ]
        ) for o in orders
    ]


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new sales order"""
    # Calculate total
    total = sum(item.quantity * item.unit_price for item in payload.items)
    
    order = SalesOrder(
        id=uuid_module.uuid4(),
        tenant_id=current_user.tenant_id,
        customer_id=payload.customer_id,
        status="Draft",
        total_amount=total
    )
    db.add(order)
    await db.flush()
    
    # Add items
    for item in payload.items:
        so_item = SOItem(
            id=uuid_module.uuid4(),
            tenant_id=current_user.tenant_id,
            sales_order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.quantity * item.unit_price
        )
        db.add(so_item)
    
    await db.commit()
    await db.refresh(order)
    
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        date=order.date,
        status=order.status,
        total_amount=order.total_amount,
        items=[]
    )


@router.post("/orders/{order_id}/confirm")
async def confirm_order(
    order_id: UUID,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Confirm a draft order"""
    result = await db.execute(
        select(SalesOrder).where(
            SalesOrder.id == order_id,
            SalesOrder.tenant_id == current_user.tenant_id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "Draft":
        raise HTTPException(status_code=400, detail="Only draft orders can be confirmed")
    
    order.status = "Confirmed"
    await db.commit()
    
    return {"message": "Order confirmed", "id": str(order_id)}

