from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
from datetime import datetime
from services.gl_engine import post_journal_entry
from schemas.schemas_finance import JournalEntryCreate, JournalDetailCreate

async def run_depreciation(db: AsyncSession, asset_id, date: datetime = datetime.utcnow()):
    asset = await db.get(models.FixedAsset, asset_id)
    if not asset:
        raise ValueError("Asset not found")
        
    if asset.status != models.AssetStatus.ACTIVE:
        raise ValueError(f"Asset is {asset.status}, cannot depreciate")

    # Straight Line Calculation
    # Monthly Amount = (Cost - Salvage) / (Years * 12)
    total_depreciable_amount = asset.cost - asset.salvage_value
    total_months = asset.useful_life_years * 12
    monthly_amount = total_depreciable_amount / total_months
    
    # Check if already fully depreciated
    # In real app, sum up existing entries.
    existing_depr = await db.execute(select(models.DepreciationEntry).where(models.DepreciationEntry.asset_id == asset.id))
    total_depreciated = sum(d.amount for d in existing_depr.scalars().all())
    
    if total_depreciated >= total_depreciable_amount:
        asset.status = models.AssetStatus.FULLY_DEPRECIATED
        await db.commit()
        return {"status": "Fully Depreciated", "amount": 0}

    # Cap amount if remaining is less than monthly
    remaining = total_depreciable_amount - total_depreciated
    if remaining < monthly_amount:
        monthly_amount = remaining
        
    # Post Journal
    # Dr Depreciation Expense
    # Cr Accumulated Depreciation
    if not (asset.depr_expense_account_id and asset.acc_depr_account_id):
         raise ValueError("Asset missing GL account settings")

    entry = JournalEntryCreate(
        description=f"Depreciation - {asset.name} - {date.strftime('%Y-%m')}",
        reference_id=str(asset.id),
        reference_type="FixedAsset",
        details=[
            JournalDetailCreate(account_id=asset.depr_expense_account_id, debit=monthly_amount, credit=0),
            JournalDetailCreate(account_id=asset.acc_depr_account_id, debit=0, credit=monthly_amount)
        ]
    )
    
    journal = await post_journal_entry(db, entry)
    
    # Record History
    depr_entry = models.DepreciationEntry(
        asset_id=asset.id,
        date=date,
        amount=monthly_amount,
        journal_entry_id=journal.id
    )
    db.add(depr_entry)
    
    if total_depreciated + monthly_amount >= total_depreciable_amount:
         asset.status = models.AssetStatus.FULLY_DEPRECIATED
         
    await db.commit()
    
    return {"status": "Posted", "amount": monthly_amount, "journal_id": journal.id}
